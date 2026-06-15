from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.document import Document
from app.models.document_content import DocumentContent


class DocumentRetriever:

    @staticmethod
    def search(
        keywords: list[str],
        db: Session
    ):

        filters = [
            DocumentContent.content.ilike(
                f"%{keyword}%"
            )
            for keyword in keywords
        ]

        return (
            db.query(
                Document.id,
                Document.name,
                Document.web_view_link,
                DocumentContent.content
            )
            .join(
                DocumentContent,
                Document.id == DocumentContent.document_id
            )
            .filter(
                or_(*filters)
            )
            .limit(5)
            .all()
        )