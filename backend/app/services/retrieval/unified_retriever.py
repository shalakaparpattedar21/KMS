from app.services.retrieval.document_retriever import DocumentRetriever
from app.services.retrieval.email_retriever import EmailRetriever


class UnifiedRetriever:

    @staticmethod
    def search(
        question: str,
        keywords: list[str],
        db
    ):

        docs = DocumentRetriever.search(
            keywords,
            db
        )

        emails = EmailRetriever.search(
           keywords,
            db
        )

        return {
            "documents": docs,
            "emails": emails
        }