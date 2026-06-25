# app/services/ai/context_builder.py
#
# PERFORMANCE FIX: Email bodies were passed raw to Ollama — some were
# 50,000+ characters (HTML newsletters). Ollama processes every token,
# so a huge context = very slow inference.
#
# Now: body is truncated to 500 chars, HTML tags stripped.
# Subject + sender are always preserved in full (most useful for search).
# This alone cuts Ollama response time significantly.

import re

# Max characters of email body to include in the LLM context.
# 500 chars is ~100 words — enough for Ollama to understand the email
# without being overwhelmed by newsletter boilerplate.
_EMAIL_BODY_LIMIT = 500

# Max characters of document content per document chunk.
_DOC_CONTENT_LIMIT = 1000


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
    def build(results: dict, db=None) -> str:
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

            if hasattr(doc, "contents"):
                for content in doc.contents:
                    chunk = _truncate(content.content or "", _DOC_CONTENT_LIMIT)
                    context += f"{chunk}\n"

            context += "-------------------------\n"

        return context