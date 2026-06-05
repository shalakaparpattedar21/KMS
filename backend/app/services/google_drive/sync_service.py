from sqlalchemy.orm import Session
from datetime import datetime
from app.models.document import Document
from app.services.google_drive.drive_service import DriveService


class SyncService:

    @staticmethod
    def sync_files(
        access_token: str,
        user_id: int,
        db: Session
    ):
       
        data = DriveService.get_files(access_token)

        files = data.get("files", [])

        synced = 0

        for file in files:

            existing = (
    db.query(Document)
    .filter(
        Document.drive_file_id == file["id"],
        Document.user_id == user_id
    )
    .first()
)

            if existing:
                continue

            owner_email = None

            if file.get("owners"):
                owner_email = (
                    file["owners"][0]
                    .get("emailAddress")
                )

            document = Document(
                user_id=user_id,
    drive_file_id=file["id"],
    name=file["name"],
    mime_type=file.get("mimeType"),
    owner_email=owner_email,
    web_view_link=file.get("webViewLink"),
    size=int(file["size"])
    if file.get("size")
    else None,
    sync_status="synced",
    last_synced_at=datetime.utcnow()
)

            db.add(document)

            synced += 1

        db.commit()

        return synced