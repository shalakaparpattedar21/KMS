import re

# ---------------------------------------------------------------------------
# Sender search patterns (unchanged from original)
# ---------------------------------------------------------------------------

_SENDER_PATTERNS = [
    r"\bemails?\s+from\b",
    r"\bmails?\s+from\b",
    r"\bemails?\s+by\b",
    r"\bmails?\s+by\b",
    r"\b(?:emails?|mails?)\s+sent\s+by\b",
    r"\bsender\s+is\b",
    r"\bsender:\b",
    r"\bfrom\s+sender\b",
    r"\bwho\s+sent\b",
]

_SENDER_RE = re.compile("|".join(_SENDER_PATTERNS), re.IGNORECASE)

# Regex that also extracts the sender name (unchanged)
SENDER_EXTRACT_RE = re.compile(
    r"(?:emails?|mails?)\s+(?:from|by|sent\s+by)\s+(?P<name>.+)",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# New action intent patterns (V2)
# ---------------------------------------------------------------------------

# Reply — "reply to this", "reply to that email", "write a reply"
_REPLY_RE = re.compile(
    r"\breply\b|\bwrite\s+a\s+reply\b|\brespond\s+to\b",
    re.IGNORECASE,
)

# Forward — "forward this email", "forward it to HR"
_FORWARD_RE = re.compile(
    r"\bforward\b",
    re.IGNORECASE,
)

# Recipient extraction from forward commands — "forward this to <name>"
_FORWARD_RECIPIENT_RE = re.compile(
    r"\bforward\b.*?\bto\s+(?P<recipient>.+)",
    re.IGNORECASE,
)

# Draft — "draft a reply", "compose an email", "write a response"
_DRAFT_RE = re.compile(
    r"\bdraft\b|\bcompose\b|\bwrite\s+a\s+(professional\s+)?(response|email|message)\b",
    re.IGNORECASE,
)

# Summarize last item — "summarize it", "summarize that", "summarize the email"
_SUMMARIZE_LAST_RE = re.compile(
    r"\bsummarize\s+(it|that|this|the\s+(email|document|doc|mail))\b",
    re.IGNORECASE,
)


class IntentService:
    """
    Lightweight rule-based intent detector.

    Returns one of:
        {"intent": "search_sender"}
        {"intent": "reply_email"}
        {"intent": "forward_email", "recipient": str | None}
        {"intent": "draft_email"}
        {"intent": "summarize_last"}
        {"intent": "semantic_search"}

    Detection order matters — more specific patterns run first.
    Existing "search_sender" logic is completely unchanged.
    """

    @staticmethod
    def detect(question: str) -> dict:
        if not question:
            return {"intent": "semantic_search"}

        q = question.strip()

        # 1. Sender search (original, unchanged)
        if _SENDER_RE.search(q):
            return {"intent": "search_sender"}

        # 2. Forward (check before reply — "forward and reply" edge case handled by order)
        if _FORWARD_RE.search(q):
            recipient = None
            m = _FORWARD_RECIPIENT_RE.search(q)
            if m:
                raw = (m.group("recipient") or "").strip(" '\".,")
                # strip trailing punctuation / filler words
                raw = re.sub(r"[?.!,]+$", "", raw).strip()
                recipient = raw or None
            return {"intent": "forward_email", "recipient": recipient}

        # 3. Reply
        if _REPLY_RE.search(q):
            return {"intent": "reply_email"}

        # 4. Draft / compose
        if _DRAFT_RE.search(q):
            return {"intent": "draft_email"}

        # 5. Summarize last context item
        if _SUMMARIZE_LAST_RE.search(q):
            return {"intent": "summarize_last"}

        # 6. Default — semantic search
        return {"intent": "semantic_search"}

    @staticmethod
    def extract_sender(question: str) -> str:
        """Return the sender name fragment from a 'emails from X' style query."""
        if not question:
            return None
        m = SENDER_EXTRACT_RE.search(question)
        if not m:
            return None
        name = (m.group("name") or "").strip(" '\"")
        # strip trailing punctuation
        name = re.sub(r"[?.!,]+$", "", name).strip()
        return name or None