# app/services/google_drive/sync_service.py
#
# FIXED: Error handler now calls db.rollback() before logging when db.flush()
# fails (e.g. NUL bytes in content). Without this, SQLAlchemy leaves the
# session in PendingRollbackError state and crashes every subsequent file.
#
# TEMPORARY SAFEGUARD (Render Free tier, 512 MB RAM):
# "Sync Now" used to process every Drive file in a single request, which
# blows past Render Free's memory/time limits on large Drive accounts.
# Until we move sync to a background worker, we cap each sync run to the
# first MAX_SYNC_FILES files. Remove this cap once we're off Render Free
# or have a proper background job runner in place.

import logging
import os
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.document_content import DocumentContent
from app.services.google_drive.drive_service import DriveService
from app.services.rag.index_service import IndexService

logger = logging.getLogger(__name__)

# Temporary production safeguard for Render Free (512 MB RAM).
# Override via env var SYNC_BATCH_SIZE if needed. Default: 20.
MAX_SYNC_FILES = int(os.getenv("SYNC_BATCH_SIZE", "20"))

_GOOGLE_DOC_MIME = "application/vnd.google-apps.document"

_SKIP_MIME_TYPES = {
    "application/vnd.google-apps.spreadsheet",
    "application/vnd.google-apps.presentation",
    "application/vnd.google-apps.form",
    "application/vnd.google-apps.drawing",
    "application/vnd.google-apps.map",
    "application/vnd.google-apps.folder",
    "application/vnd.google-apps.shortcut",
}

_CONTENT_LIMIT = 50_000


class SyncService:

    @staticmethod
    def sync_files(access_token: str, user_id: int, db: Session) -> int:
        data = DriveService.get_files(access_token)
        files = data.get("files", [])

        total_available = len(files)
        logger.info(f"[SYNC] Drive returned {total_available} files for user_id={user_id}")

        # TEMPORARY SAFEGUARD: only process the first MAX_SYNC_FILES files
        # per sync run so this stays within Render Free's memory/time limits.
        if total_available > MAX_SYNC_FILES:
            files = files[:MAX_SYNC_FILES]

        logger.info(
            f"[SYNC] Processing {len(files)} of {total_available} files "
            f"(user_id={user_id}, MAX_SYNC_FILES={MAX_SYNC_FILES})"
        )

        synced = 0

        for file in files:
            drive_id = file["id"]
            mime_type = file.get("mimeType", "")
            file_name = file.get("name", "(Untitled)")

            if mime_type in _SKIP_MIME_TYPES:
                continue

            existing = (
                db.query(Document)
                .filter(
                    Document.drive_file_id == drive_id,
                    Document.user_id == user_id,
                )
                .first()
            )

            if existing:
                already_indexed = (
                    db.query(DocumentContent)
                    .filter(DocumentContent.document_id == existing.id)
                    .first()
                )
                if not already_indexed:
                    logger.info(f"[SYNC] Re-indexing existing doc without content: {file_name}")
                    SyncService._extract_and_index(
                        access_token=access_token,
                        document=existing,
                        mime_type=mime_type,
                        file_name=file_name,
                        db=db,
                    )
                continue

            owner_email = None
            if file.get("owners"):
                owner_email = file["owners"][0].get("emailAddress")

            document = Document(
                user_id=user_id,
                drive_file_id=drive_id,
                name=file_name,
                mime_type=mime_type,
                owner_email=owner_email,
                web_view_link=file.get("webViewLink"),
                size=int(file["size"]) if file.get("size") else None,
                sync_status="synced",
                last_synced_at=datetime.utcnow(),
            )

            db.add(document)
            db.flush()

            SyncService._extract_and_index(
                access_token=access_token,
                document=document,
                mime_type=mime_type,
                file_name=file_name,
                db=db,
            )

            synced += 1

        db.commit()

        logger.info(f"[SYNC] Done. Newly synced: {synced} for user_id={user_id}")
        return synced

    @staticmethod
    def _extract_and_index(
        access_token: str,
        document: Document,
        mime_type: str,
        file_name: str,
        db: Session,
    ):
        drive_id = document.drive_file_id
        try:
            if mime_type == _GOOGLE_DOC_MIME:
                text = DriveService.export_google_doc(
                    access_token=access_token,
                    file_id=drive_id,
                )
            else:
                text = DriveService.download_file(
                    access_token=access_token,
                    file_id=drive_id,
                    mime_type=mime_type,
                    file_name=file_name,
                )

            if not text or not text.strip():
                logger.warning(f"[SYNC] Empty content for: {file_name} — skipping index")
                return

            text = text[:_CONTENT_LIMIT]

            doc_content = DocumentContent(
                document_id=document.id,
                content=text,
            )
            db.add(doc_content)
            db.flush()

            IndexService.index_document(
                document_id=document.id,
                document_name=file_name,
                content=text,
                mime_type=mime_type,
                owner_email=document.owner_email,
            )

            logger.info(f"[SYNC] Indexed: {file_name} (doc_id={document.id})")

        except Exception as e:
            # Rollback the failed flush so the session is clean for the next file.
            # Without this, SQLAlchemy raises PendingRollbackError on every
            # subsequent db operation in this session.
            try:
                db.rollback()
            except Exception:
                pass
            logger.error(f"[SYNC] Failed to index '{file_name}' (drive_id={drive_id}): {e}")