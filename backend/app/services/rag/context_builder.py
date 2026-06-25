# app/services/ai/context_builder.py
#
# Builds the context string that gets passed to Gemini.
#
# The previous bug: ContextBuilder checked hasattr(doc, "contents") which
# was always False because Document had no SQLAlchemy relationship defined.
# Gemini was receiving only document titles ("OS Lab Questions") with zero
# actual content, so it correctly replied "I could not find that information."
#
# The fix: Document.contents is now a proper relationship (see models/document.py).
# ContextBuilder now also falls back to a direct DB lookup for any doc whose
# relationship loads empty, so it works even if the relationship is not eager-loaded.

import re
import logging

from sqlalchemy.orm import Session

from app.models.document_content import DocumentContent

logger = logging.getLogger(__name__)

# Max characters of email body included per email.
# 800 chars ≈ 150 words — enough to answer most email questions.
_EMAIL_BODY_LIMIT = 800

# Max characters of document content per document.
# 3000 chars ≈ 600 words — enough for a detailed answer.
# Increase if you have long technical documents (e.g. lab manuals).
_DOC_CONTENT_LIMIT = 3000


def _strip_html(text: str) -> str:
    """Remove HTML tags and collapse whitespace."""
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _truncate(text: str, limit: int) -> str:
    """Strip HTML then truncate to limit chars, appending '…' if cut."""
    clean = _strip_html(text or "")
    if len(clean) <= limit:
        return clean
    return clean[:limit] + "…"


class ContextBuilder:

    @staticmethod
    def build(results: dict, db: Session | None = None) -> str:
        """
        Convert retrieved documents and emails into a context string for Gemini.

        Args:
            results: dict with keys "documents" (list[Document]) and "emails" (list[Email])
            db:      SQLAlchemy session — used as fallback to load DocumentContent
                     if the relationship comes back empty (e.g. lazy load didn't fire).
        """
        context = ""

        # ── Emails ────────────────────────────────────────────────────────
        for email in results.get("emails", []):
            body_preview = _truncate(email.body or "", _EMAIL_BODY_LIMIT)
            context += (
                f"\nEMAIL\n"
                f"Subject: {email.subject or '(No Subject)'}\n"
                f"From: {email.sender or ''}\n"
                f"Body:\n{body_preview}\n"
                f"-------------------------\n"
            )

        # ── Documents ─────────────────────────────────────────────────────
        for doc in results.get("documents", []):
            context += f"\nDOCUMENT\nTitle: {doc.name}\n"

            # Primary path: use the SQLAlchemy relationship (fixed in document.py)
            doc_contents = getattr(doc, "contents", None) or []

            # Fallback: if relationship is empty but we have a DB session,
            # do a direct query. This handles edge cases where the relationship
            # didn't load (e.g. object was detached from session).
            if not doc_contents and db is not None:
                logger.debug(
                    f"[CONTEXT] relationship empty for doc_id={doc.id}, "
                    "falling back to direct DB query"
                )
                doc_contents = (
                    db.query(DocumentContent)
                    .filter(DocumentContent.document_id == doc.id)
                    .all()
                )

            if doc_contents:
                for content_row in doc_contents:
                    chunk = _truncate(content_row.content or "", _DOC_CONTENT_LIMIT)
                    if chunk:
                        context += f"{chunk}\n"
            else:
                # DocumentContent row doesn't exist for this doc at all.
                # This happens when a file was synced to Drive but content
                # extraction hasn't run yet (or failed).
                logger.warning(
                    f"[CONTEXT] No content found for doc_id={doc.id} name={doc.name!r}. "
                    "Run a sync to extract document text."
                )
                context += "(Document text not yet extracted — run Sync Now to fix this.)\n"

            context += "-------------------------\n"

        return context
