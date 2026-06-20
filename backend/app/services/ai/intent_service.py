import re

# Phrases that indicate the user wants emails from a specific sender.
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

# Regex that also extracts the sender name
SENDER_EXTRACT_RE = re.compile(
    r"(?:emails?|mails?)\s+(?:from|by|sent\s+by)\s+(?P<name>.+)",
    re.IGNORECASE,
)


class IntentService:
    """
    Lightweight rule-based intent detector.
    Returns one of:
    {"intent": "search_sender"}
    {"intent": "semantic_search"}
    """

    @staticmethod
    def detect(question: str) -> dict:
        if not question:
            return {"intent": "semantic_search"}
        if _SENDER_RE.search(question):
            return {"intent": "search_sender"}
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