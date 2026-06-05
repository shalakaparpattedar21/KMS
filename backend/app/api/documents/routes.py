from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.document import Document

router = APIRouter(
    prefix="/api/documents",
    tags=["Documents"]
)


@router.get("/")
def get_documents(
    db: Session = Depends(get_db)
):

    documents = (
       db.query(Document)\
.order_by(Document.name)\
.all()
    )

    return [
        {
            "id": doc.id,
            "drive_file_id": doc.drive_file_id,
            "name": doc.name,
            "mime_type": doc.mime_type,
            "owner_email": doc.owner_email,
            "size": doc.size,
            "sync_status": doc.sync_status,
            "web_view_link": doc.web_view_link,
            "modified_time": doc.modified_time
        }
        for doc in documents
    ]
@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):

    total = db.query(Document).count()

    return {
        "total_documents": total
    }