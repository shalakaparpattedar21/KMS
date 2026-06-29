# app/api/sync/routes.py

import logging
import threading

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database.session import get_db, SessionLocal
from app.models.document import Document
from app.models.document_content import DocumentContent
from app.services.google_drive.sync_service import SyncService
from app.services.rag.index_service import IndexService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/sync",
    tags=["Sync"]
)


def _sync_in_background(access_token: str, user_id: int):
    """
    Runs SyncService.sync_files() in a background thread with its own
    DB session so it doesn't block the HTTP request.
    Render's 30-second request timeout won't affect this.
    """
    db = SessionLocal()
    try:
        count = SyncService.sync_files(access_token, user_id, db)
        logger.info(f"[SYNC] Background sync complete for user_id={user_id} count={count}")
    except Exception as e:
        logger.error(f"[SYNC] Background sync failed for user_id={user_id}: {e}")
    finally:
        db.close()


@router.post("/start")
async def start_sync(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Kicks off a Google Drive sync for the current user in a background thread.
    Returns immediately with 202 Accepted — sync runs in the background.
    """
    access_token = request.session.get("access_token")
    user_id = request.session.get("user_id")

    if not access_token:
        raise HTTPException(status_code=401, detail="Google account not connected")

    if not user_id:
        raise HTTPException(status_code=401, detail="User not authenticated")

    thread = threading.Thread(
        target=_sync_in_background,
        args=(access_token, user_id),
        daemon=True,
    )
    thread.start()

    return {"message": "Sync started in background. Refresh documents in a minute."}


@router.post("/reindex-documents")
async def reindex_documents(db: Session = Depends(get_db)):
    """
    One-time recovery endpoint.

    Re-indexes all documents that already exist in the `documents` table
    but have a matching row in `document_contents` (text already extracted).

    Use this after restoring the indexing pipeline to backfill Chroma
    without re-downloading everything from Google Drive.

    Does NOT download from Drive — only works with content already saved
    in document_contents.
    """
    documents = db.query(Document).all()

    indexed = 0
    skipped = 0

    for doc in documents:
        content_row = (
            db.query(DocumentContent)
            .filter(DocumentContent.document_id == doc.id)
            .first()
        )

        if not content_row or not content_row.content.strip():
            skipped += 1
            continue

        try:
            IndexService.index_document(
                document_id=doc.id,
                document_name=doc.name,
                content=content_row.content,
                mime_type=doc.mime_type,
                owner_email=doc.owner_email,
            )
            indexed += 1
        except Exception as e:
            logger.error(f"[REINDEX] Failed for doc_id={doc.id} name={doc.name}: {e}")
            skipped += 1

    logger.info(f"[REINDEX] Done. indexed={indexed} skipped={skipped}")
    return {"indexed": indexed, "skipped": skipped}