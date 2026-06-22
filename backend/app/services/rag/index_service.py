from app.services.rag.vector_store import collection
from app.services.embeddings.embedding_service import EmbeddingService


class IndexService:
    """
    Service for indexing documents and emails into Chroma.
    
    Stores rich metadata for better filtering and retrieval.
    """

    @staticmethod
    def index_document(
        document_id: int,
        document_name: str,
        content: str,
        mime_type: str = None,
        owner_email: str = None
    ):
        """
        Index a document into Chroma.
        
        Args:
            document_id: PostgreSQL Document.id
            document_name: Document name
            content: Full document content
            mime_type: MIME type (pdf, docx, etc)
            owner_email: Document owner email
        """
        try:
            print(f"[RAG] DOCUMENT INDEXING STARTED: {document_name}")

            # Step 1: Generate embedding
            embedding = EmbeddingService.embed(content)
            print(f"[RAG] DOCUMENT EMBEDDING GENERATED: {document_name}")

            # Step 2: Store in Chroma with rich metadata
            collection.upsert(
                ids=[f"doc_{document_id}"],
                embeddings=[embedding],
                documents=[content],
                metadatas=[{
                    "type": "document",
                    "id": str(document_id),
                    "name": document_name,
                    "mime_type": mime_type or "unknown",
                    "owner": owner_email or "unknown"
                }]
            )

            print(f"[RAG] DOCUMENT INDEXED: {document_name}")

        except Exception as e:
            print(f"[RAG ERROR] Document indexing failed: {document_name}")
            print(f"[RAG ERROR] {str(e)}")
            import traceback
            traceback.print_exc()

    @staticmethod
    def index_email(
        email_id: int,
        subject: str = None,
        sender: str = None,
        body: str = None,
        received_at: str = None
    ):
        """
        Index an email into Chroma.
        
        Args:
            email_id: PostgreSQL Email.id
            subject: Email subject
            sender: Sender email
            body: Email body content
            received_at: Date received (ISO format)
        """
        try:
            subject = subject or "(No Subject)"
            print(f"[RAG] EMAIL INDEXING STARTED: {subject}")

            # Step 1: Combine content for embedding
            content = f"""
Subject: {subject}

From: {sender or ''}

Body:
{body or ''}
""".strip()

            # Step 2: Generate embedding
            embedding = EmbeddingService.embed(content)
            print(f"[RAG] EMAIL EMBEDDING GENERATED: {subject}")

            # Step 3: Store in Chroma with rich metadata
            collection.upsert(
                ids=[f"email_{email_id}"],
                embeddings=[embedding],
                documents=[content],
                metadatas=[{
                    "type": "email",
                    "id": str(email_id),
                    "subject": subject,
                    "sender": sender or "unknown",
                    "received_date": received_at or "unknown"
                }]
            )

            print(f"[RAG] EMAIL INDEXED: {subject}")

        except Exception as e:
            print(f"[RAG ERROR] Email indexing failed: {subject}")
            print(f"[RAG ERROR] {str(e)}")
            import traceback
            traceback.print_exc()

    @staticmethod
    def delete_document(document_id: int):
        """Delete a document from Chroma"""
        try:
            collection.delete(ids=[f"doc_{document_id}"])
            print(f"[RAG] Document deleted: {document_id}")
        except Exception as e:
            print(f"[RAG ERROR] Failed to delete document: {str(e)}")

    @staticmethod
    def delete_email(email_id: int):
        """Delete an email from Chroma"""
        try:
            collection.delete(ids=[f"email_{email_id}"])
            print(f"[RAG] Email deleted: {email_id}")
        except Exception as e:
            print(f"[RAG ERROR] Failed to delete email: {str(e)}")

    @staticmethod
    def reindex_all(db, documents, emails):
        """
        Reindex all documents and emails.
        Use sparingly - expensive operation.
        """
        print("[RAG] ========== FULL REINDEX START ==========")
        
        doc_count = 0
        email_count = 0

        # Index all documents
        for doc in documents:
            from app.models.document_content import DocumentContent
            content = (
                db.query(DocumentContent)
                .filter(DocumentContent.document_id == doc.id)
                .first()
            )
            
            if content:
                IndexService.index_document(
                    document_id=doc.id,
                    document_name=doc.name,
                    content=content.content,
                    mime_type=doc.mime_type,
                    owner_email=doc.owner_email
                )
                doc_count += 1

        # Index all emails
        for email in emails:
            IndexService.index_email(
                email_id=email.id,
                subject=email.subject,
                sender=email.sender,
                body=email.body,
                received_at=str(email.received_at) if email.received_at else None
            )
            email_count += 1

        print(f"[RAG] Reindexed {doc_count} documents and {email_count} emails")
        print("[RAG] ========== FULL REINDEX END ==========")