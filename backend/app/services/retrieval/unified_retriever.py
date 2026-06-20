from app.services.rag.retrieval_service import RetrievalService
from sqlalchemy.orm import Session


class UnifiedRetriever:
    """
    Unified retriever that bridges Chroma semantic search with PostgreSQL.
    
    New architecture:
    1. Uses RetrievalService for semantic search (Chroma)
    2. Fetches full objects from PostgreSQL
    3. Returns SQLAlchemy objects with all attributes
    4. Chat routes continue to work unchanged
    """

    @staticmethod
    def search(
        question: str,
        db: Session,
        top_k: int = 5
    ) -> dict:
        """
        Perform unified hybrid search.
        
        Args:
            question: User's question
            db: Database session
            top_k: Number of results per type
        
        Returns:
            {
                "documents": [Document objects],
                "emails": [Email objects]
            }
        """
        print(f"\n[UNIFIED] Question: {question}")
        
        # Use semantic search (Chroma) + PostgreSQL fetch
        results = RetrievalService.search(
            query=question,
            db=db,
            top_k=top_k
        )
        
        print(f"[UNIFIED] Returning: {len(results['documents'])} docs, {len(results['emails'])} emails\n")
        
        return results