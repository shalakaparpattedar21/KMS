import logging
import re
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.services.rag.vector_store import collection
from app.services.embeddings.embedding_service import EmbeddingService
from app.models.document import Document
from app.models.document_content import DocumentContent
from app.models.email import Email

logger = logging.getLogger(__name__)

_STOP_WORDS = {
    "what", "is", "the", "a", "an", "of", "for", "in", "to", "and",
    "from", "by", "me", "show", "list", "find", "give", "all", "emails",
    "email", "mails", "mail", "documents", "document", "doc", "docs",
    "please", "can", "you", "i", "want", "need", "about", "on", "with",
    "any", "some", "this", "that", "these", "those",
}


def _extract_keywords(query: str) -> list:
    """Extract non-stopword tokens of length >=2 from the query."""
    tokens = re.findall(r"[A-Za-z0-9_]+", (query or "").lower())
    return [t for t in tokens if len(t) >= 2 and t not in _STOP_WORDS]


def _safe_int(value):
    try:
        if value is None:
            return None
        return int(str(value))
    except (ValueError, TypeError):
        return None


class RetrievalService:
    """
    Hybrid Chroma + PostgreSQL retrieval service.
    Flow:
    1. Generate embedding for the query
    2. Search Chroma (semantic) with a metadata filter ($eq)
    3. Map metadata ids -> Postgres ids
    4. Fetch full ORM objects from Postgres
    5. If Chroma/Postgres yields nothing, FALL BACK to SQL ILIKE keyword search
    """

    @staticmethod
    def search_documents(query: str, db: Session, top_k: int = 5) -> list:
        logger.info(f"[RAG] search_documents | query={query!r} top_k={top_k}")
        documents: list = []

        # ---- Semantic (Chroma) ----
        try:
            embedding = EmbeddingService.embed(query)
            chroma_results = collection.query(
                query_embeddings=[embedding],
                n_results=top_k,
                where={"type": {"$eq": "document"}},
            )
            metadatas = (chroma_results or {}).get("metadatas") or [[]]
            metadatas = metadatas[0] if metadatas else []
            logger.info(f"[RAG] Chroma returned {len(metadatas)} document metas")

            doc_ids: list = []
            for md in metadatas:
                did = _safe_int(md.get("id"))
                if did is not None:
                    doc_ids.append(did)
                else:
                    logger.warning(f"[RAG] dropping doc with invalid id meta: {md}")

            if doc_ids:
                logger.info(f"[RAG] semantic doc ids -> {doc_ids}")
                documents = (
                    db.query(Document)
                    .filter(Document.id.in_(doc_ids))
                    .all()
                )
                # preserve Chroma order
                order = {d: i for i, d in enumerate(doc_ids)}
                documents.sort(key=lambda d: order.get(d.id, 1_000_000))
        except Exception as e:
            logger.exception(f"[RAG] document semantic search failed: {e}")
            documents = []

        # ---- SQL fallback ----
        if not documents:
            keywords = _extract_keywords(query)
            logger.info(f"[RAG] doc SQL fallback | keywords={keywords}")
            if keywords:
                try:
                    name_filters = [
                        Document.name.ilike(f"%{kw}%")
                        for kw in keywords
                    ]
                    content_filters = [
                        DocumentContent.content.ilike(f"%{kw}%")
                        for kw in keywords
                    ]
                    documents = (
                        db.query(Document)
                        .outerjoin(
                            DocumentContent,
                            Document.id == DocumentContent.document_id,
                        )
                        .filter(or_(*name_filters, *content_filters))
                        .distinct()
                        .limit(top_k)
                        .all()
                    )
                except Exception as e:
                    logger.exception(f"[RAG] doc SQL fallback failed: {e}")
                    documents = []

        logger.info(f"[RAG] search_documents -> {len(documents)} docs")
        return documents

    @staticmethod
    def search_emails(query: str, db: Session, top_k: int = 5) -> list:
        logger.info(f"[RAG] search_emails | query={query!r} top_k={top_k}")
        emails: list = []

        # ---- Semantic (Chroma) ----
        try:
            embedding = EmbeddingService.embed(query)
            chroma_results = collection.query(
                query_embeddings=[embedding],
                n_results=top_k,
                where={"type": {"$eq": "email"}},
            )
            metadatas = (chroma_results or {}).get("metadatas") or [[]]
            metadatas = metadatas[0] if metadatas else []
            logger.info(f"[RAG] Chroma returned {len(metadatas)} email metas")

            email_ids: list = []
            for md in metadatas:
                eid = _safe_int(md.get("id"))
                if eid is not None:
                    email_ids.append(eid)
                else:
                    logger.warning(f"[RAG] dropping email with invalid id meta: {md}")

            if email_ids:
                logger.info(f"[RAG] semantic email ids -> {email_ids}")
                emails = (
                    db.query(Email)
                    .filter(Email.id.in_(email_ids))
                    .all()
                )
                order = {e: i for i, e in enumerate(email_ids)}
                emails.sort(key=lambda e: order.get(e.id, 1_000_000))
        except Exception as e:
            logger.exception(f"[RAG] email semantic search failed: {e}")
            emails = []

        # ---- SQL fallback ----
        if not emails:
            keywords = _extract_keywords(query)
            logger.info(f"[RAG] email SQL fallback | keywords={keywords}")
            if keywords:
                try:
                    filters = []
                    for kw in keywords:
                        like = f"%{kw}%"
                        filters.extend([
                            Email.subject.ilike(like),
                            Email.sender.ilike(like),
                            Email.body.ilike(like),
                        ])
                    emails = (
                        db.query(Email)
                        .filter(or_(*filters))
                        .order_by(Email.id.desc())
                        .limit(top_k)
                        .all()
                    )
                except Exception as e:
                    logger.exception(f"[RAG] email SQL fallback failed: {e}")
                    emails = []

        logger.info(f"[RAG] search_emails -> {len(emails)} emails")
        return emails

    @staticmethod
    def search(query: str, db: Session, top_k: int = 5) -> dict:
        logger.info(f"[RAG] ===== UNIFIED SEARCH START | q={query!r} k={top_k} =====")
        documents = RetrievalService.search_documents(query, db, top_k)
        emails = RetrievalService.search_emails(query, db, top_k)
        logger.info(
            f"[RAG] ===== UNIFIED SEARCH END | docs={len(documents)} emails={len(emails)} ====="
        )
        return {"documents": documents, "emails": emails}