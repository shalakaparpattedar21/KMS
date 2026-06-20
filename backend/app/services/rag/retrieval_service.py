from app.services.rag.vector_store import collection
from app.services.embeddings.embedding_service import EmbeddingService
from app.models.document import Document
from app.models.email import Email
from sqlalchemy.orm import Session


class RetrievalService:
    """
    Hybrid Chroma + PostgreSQL retrieval service.
    
    Flow:
    1. Generate embedding for query
    2. Search Chroma for semantic matches
    3. Extract IDs from Chroma metadata
    4. Fetch full objects from PostgreSQL
    5. Return full SQLAlchemy objects with all attributes
    """

    @staticmethod
    def search_documents(
        query: str,
        db: Session,
        top_k: int = 5
    ) -> list:
        """
        Search for documents using semantic similarity.
        
        Returns: List of full Document objects
        """
        try:
            print(f"[RAG] Searching documents for: {query}")
            
            # Step 1: Generate embedding
            embedding = EmbeddingService.embed(query)
            print(f"[RAG] Embedding generated (dims: {len(embedding)})")
            
            # Step 2: Search Chroma with type filter
            chroma_results = collection.query(
                query_embeddings=[embedding],
                n_results=top_k,
                where={"type": "document"}
            )
            
            if not chroma_results or not chroma_results["metadatas"][0]:
                print("[RAG] No document results from Chroma")
                return []
            
            print(f"[RAG] Found {len(chroma_results['metadatas'][0])} documents in Chroma")
            
            # Step 3: Extract document IDs from metadata
            doc_ids = []
            for metadata in chroma_results["metadatas"][0]:
                try:
                    doc_id = int(metadata.get("id"))
                    doc_ids.append(doc_id)
                except (ValueError, TypeError):
                    print(f"[RAG WARNING] Invalid doc ID in metadata: {metadata}")
                    continue
            
            if not doc_ids:
                print("[RAG] No valid document IDs extracted")
                return []
            
            print(f"[RAG] Extracted IDs: {doc_ids}")
            
            # Step 4: Fetch full Document objects from PostgreSQL
            documents = (
                db.query(Document)
                .filter(Document.id.in_(doc_ids))
                .all()
            )
            
            print(f"[RAG] Fetched {len(documents)} documents from PostgreSQL")
            
            return documents
            
        except Exception as e:
            print(f"[RAG ERROR] Document search failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return []

    @staticmethod
    def search_emails(
        query: str,
        db: Session,
        top_k: int = 5
    ) -> list:
        """
        Search for emails using semantic similarity.
        
        Returns: List of full Email objects
        """
        try:
            print(f"[RAG] Searching emails for: {query}")
            
            # Step 1: Generate embedding
            embedding = EmbeddingService.embed(query)
            print(f"[RAG] Embedding generated (dims: {len(embedding)})")
            
            # Step 2: Search Chroma with type filter
            chroma_results = collection.query(
                query_embeddings=[embedding],
                n_results=top_k,
                where={"type": "email"}
            )
            
            if not chroma_results or not chroma_results["metadatas"][0]:
                print("[RAG] No email results from Chroma")
                return []
            
            print(f"[RAG] Found {len(chroma_results['metadatas'][0])} emails in Chroma")
            
            # Step 3: Extract email IDs from metadata
            email_ids = []
            for metadata in chroma_results["metadatas"][0]:
                try:
                    email_id = int(metadata.get("id"))
                    email_ids.append(email_id)
                except (ValueError, TypeError):
                    print(f"[RAG WARNING] Invalid email ID in metadata: {metadata}")
                    continue
            
            if not email_ids:
                print("[RAG] No valid email IDs extracted")
                return []
            
            print(f"[RAG] Extracted IDs: {email_ids}")
            
            # Step 4: Fetch full Email objects from PostgreSQL
            emails = (
                db.query(Email)
                .filter(Email.id.in_(email_ids))
                .all()
            )
            
            print(f"[RAG] Fetched {len(emails)} emails from PostgreSQL")
            
            return emails
            
        except Exception as e:
            print(f"[RAG ERROR] Email search failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return []

    @staticmethod
    def search(
        query: str,
        db: Session,
        top_k: int = 5
    ) -> dict:
        """
        Unified search for both documents and emails.
        
        Returns:
        {
            "documents": [Document, ...],
            "emails": [Email, ...]
        }
        """
        print(f"\n[RAG] ========== UNIFIED SEARCH START ==========")
        print(f"[RAG] Query: {query}")
        print(f"[RAG] Top K: {top_k}")
        
        documents = RetrievalService.search_documents(query, db, top_k)
        emails = RetrievalService.search_emails(query, db, top_k)
        
        result = {
            "documents": documents,
            "emails": emails
        }
        
        print(f"[RAG] ========== UNIFIED SEARCH END ==========")
        print(f"[RAG] Results: {len(documents)} docs, {len(emails)} emails\n")
        
        return result