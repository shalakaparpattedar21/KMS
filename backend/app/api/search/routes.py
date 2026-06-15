from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.services.retrieval.unified_retriever import UnifiedRetriever
from app.database.session import get_db
from app.models.document import Document
from app.models.document_content import DocumentContent

router = APIRouter(
    prefix="/api/search",
    tags=["Search"]
)


@router.get("/")
def search_documents(
    q: str,
    db: Session = Depends(get_db)
):

    stop_words = {
        "what",
        "is",
        "the",
        "a",
        "an",
        "of",
        "for",
        "in",
        "to",
        "and"
    }

    keywords = [
        word.lower()
        for word in q.split()
        if word.lower() not in stop_words
    ]

    results = UnifiedRetriever.search(
        q,
        keywords,
        db
    )

    documents = results["documents"]
    emails = results["emails"]

    return {
    "documents": [
        {
            "id": doc.id,
            "name": doc.name,
            "mime_type": doc.mime_type,
            "web_view_link": doc.web_view_link,
            "snippet": doc.content[:200]
        }
        for doc in documents
    ],

    "emails": [
        {
            "id": email.id,
            "subject": email.subject,
            "sender": email.sender,
            "snippet": (
                email.body[:200]
                if email.body
                else ""
            )
        }
        for email in emails
    ]
}