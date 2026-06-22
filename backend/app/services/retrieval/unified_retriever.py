import logging
from sqlalchemy.orm import Session
from app.services.rag.retrieval_service import RetrievalService

logger = logging.getLogger(__name__)


class UnifiedRetriever:
    """
    Thin facade over RetrievalService used by the chat / search routes.
    The actual hybrid logic (Chroma semantic + Postgres SQL fallback) lives in RetrievalService.
    """

    @staticmethod
    def search(question: str, db: Session, top_k: int = 5) -> dict:
        logger.info(f"[UNIFIED] question={question!r} top_k={top_k}")
        results = RetrievalService.search(query=question, db=db, top_k=top_k)
        logger.info(
            f"[UNIFIED] -> docs={len(results['documents'])} "
            f"emails={len(results['emails'])}"
        )
        return results