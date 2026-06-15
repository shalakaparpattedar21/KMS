from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.document_content import DocumentContent


class RetrievalService:

    @staticmethod
    def retrieve(
        query: str,
        db: Session
    ):

        results = (
            db.query(
                Document.name,
                DocumentContent.content
            )
            .join(
                DocumentContent,
                Document.id == DocumentContent.document_id
            )
            .filter(
                DocumentContent.content.ilike(
                    f"%{query}%"
                )
            )
            .limit(3)
            .all()
        )

        return results