from fastapi import (
    APIRouter,
    Depends,
    Request,
    HTTPException
)
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.services.google_drive.drive_service import DriveService
from app.database.session import get_db
from app.models.document import Document
from app.models.document_content import DocumentContent
from app.services.rag.index_service import (IndexService)

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
            "content_extracted": doc.content_extracted,
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
@router.get("/preview/{document_id}")
def preview_document(
    document_id: int,
    db: Session = Depends(get_db)
):

    document = (
        db.query(Document)
        .filter(Document.id == document_id)
        .first()
    )

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    content = (
        db.query(DocumentContent)
        .filter(
            DocumentContent.document_id == document.id
        )
        .first()
    )

    if not content:
        raise HTTPException(
            status_code=404,
            detail="Content not extracted"
        )

    return {
        "id": document.id,
        "name": document.name,
        "owner_email": document.owner_email,
        "mime_type": document.mime_type,
        "preview": content.content
    }
@router.post("/extract/{document_id}")
def extract_document(
    document_id: int,
    request: Request,
    db: Session = Depends(get_db)
):

    document = (
        db.query(Document)
        .filter(Document.id == document_id)
        .first()
    )

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    access_token = request.session.get(
        "access_token"
    )

    if not access_token:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated"
        )

    if document.mime_type != "application/vnd.google-apps.document":
        return {
            "message": "Only Google Docs supported for now"
        }

    text = DriveService.export_google_doc(
        access_token,
        document.drive_file_id
    )
  
    text = text.replace("ï»¿", "")

    existing_content = (
        db.query(DocumentContent)
        .filter(
            DocumentContent.document_id == document.id
        )
        .first()
    )

    if existing_content:

        existing_content.content = text

    else:

        content = DocumentContent(
            document_id=document.id,
            content=text
        )

        db.add(content)

    document.content_extracted = True

    db.commit()

    IndexService.index_document(
        document.id,
        document.name,
        text
    )

    return {
        "status": "success",
        "document_id": document.id,
        "characters": len(text)
    }

@router.post("/extract-all")
def extract_all_documents(
    request: Request,
    db: Session = Depends(get_db)
):

    access_token = request.session.get(
        "access_token"
    )

    if not access_token:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated"
        )

    documents = (
        db.query(Document)
        .filter(
            Document.mime_type ==
            "application/vnd.google-apps.document"
        )
        .all()
    )

    processed = 0

    for document in documents:

        # if document.content_extracted:
        #     continue

        try:

            text = DriveService.export_google_doc(
                access_token,
                document.drive_file_id
            )

            text = (
                text
                .replace("\ufeff", "")
                .replace("ï»¿", "")
            )

            existing_content = (
                db.query(DocumentContent)
                .filter(
                    DocumentContent.document_id
                    == document.id
                )
                .first()
            )

            if existing_content:

                existing_content.content = text

            else:

                content = DocumentContent(
                    document_id=document.id,
                    content=text
                )

                db.add(content)

            document.content_extracted = True

            IndexService.index_document(
                document.id,
                document.name,
                text
            )

            processed += 1

        except Exception as e:

            import traceback

            print(f"\nFAILED DOCUMENT: {document.name}")

            traceback.print_exc()

    db.commit()

    return {
        "processed": processed
    }