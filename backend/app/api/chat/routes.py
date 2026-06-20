import json
import logging
import re

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.chat_message import ChatMessage
from app.models.chat_session import ChatSession
from app.models.email import Email
from app.schemas.chat import SendMessageRequest
from app.services.ai.gemini_service import GeminiService
from app.services.ai.intent_service import IntentService, SENDER_EXTRACT_RE
from app.services.retrieval.unified_retriever import UnifiedRetriever

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["AI Chat"])

# -----------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------

_STOP_WORDS = {"what", "is", "the", "a", "an", "of", "for", "in", "to", "and"}


def extract_keywords(question: str) -> list:
    return [
        word.lower()
        for word in (question or "").lower().split()
        if word.lower() not in _STOP_WORDS
    ]


_FOLLOWUP_PHRASES = [
    "elaborate",
    "explain",
    "explain more",
    "explain in detail",
    "tell me more",
    "more details",
    "give example",
    "give examples",
    "simplify",
    "why",
    "how does that work",
]


def is_follow_up(question: str) -> bool:
    q = (question or "").lower().strip()
    return any(phrase in q for phrase in _FOLLOWUP_PHRASES)


def build_sources_payload(documents, emails) -> str:
    data = {
        "sources": {
            "documents": [
                {
                    "id": doc.id,
                    "name": doc.name,
                    "web_view_link": doc.web_view_link,
                }
                for doc in documents
            ],
            "emails": [
                {
                    "id": email.id,
                    "subject": email.subject,
                    "sender": email.sender,
                    "gmail_message_id": email.gmail_message_id,
                    "gmail_url": (
                        f"https://mail.google.com/mail/u/0/#inbox/{email.gmail_message_id}"
                    ),
                }
                for email in emails
            ],
        }
    }
    return f"\n[SOURCES_START]{json.dumps(data)}[SOURCES_END]"


def build_context(documents, emails) -> str:
    document_context = "\n\n".join(doc.name for doc in documents)

    email_context = "\n\n".join(
        f"Subject: {email.subject}\nFrom: {email.sender}\nBody:\n{email.body or ''}"
        for email in emails
    )

    return f"=== DOCUMENTS ===\n{document_context}\n\n=== EMAILS ===\n{email_context}"


# -----------------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------------


@router.post("/sessions")
def create_session(db: Session = Depends(get_db)):
    session = ChatSession(title="New Chat")
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.get("/sessions")
def get_sessions(db: Session = Depends(get_db)):
    return db.query(ChatSession).order_by(desc(ChatSession.updated_at)).all()


@router.post("/sessions/{session_id}/messages")
def send_message(
    session_id: int,
    request: SendMessageRequest,
    db: Session = Depends(get_db),
):
    # --- Validate session ---
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")

    # --- Save user message ---
    user_message = ChatMessage(
        session_id=session_id,
        role="user",
        content=request.message,
    )
    db.add(user_message)
    db.commit()

    question = request.message or ""

    # Detect intent
    intent = IntentService.detect(question)
    sender_name = IntentService.extract_sender(question)

    logger.info(
        f"[CHAT] session={session_id} question={question!r} "
        f"intent={intent['intent']} sender_name={sender_name!r} "
        f"follow_up={is_follow_up(question)}"
    )

    # --- Conversation history ---
    history = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )
    conversation_history = "".join(
        f"{msg.role}: {msg.content}\n" for msg in history[:-1]
    )

    # -----------------------------------------------------------------------
    # SENDER SEARCH PATH
    # -----------------------------------------------------------------------
    if intent["intent"] == "search_sender" and not is_follow_up(question):
        if not sender_name:
            sender_name = " ".join(extract_keywords(question)) or question

        logger.info(f"[CHAT] sender search | name={sender_name!r}")

        emails = (
            db.query(Email)
            .filter(Email.sender.ilike(f"%{sender_name}%"))
            .order_by(Email.id.desc())
            .limit(15)
            .all()
        )

        # Fallback to unified search if no results
        if not emails:
            logger.info(
                "[CHAT] sender ILIKE empty -> falling back to UnifiedRetriever"
            )
            retrieval_results = UnifiedRetriever.search(question, db, top_k=10)
            emails = retrieval_results["emails"]

        logger.info(f"[CHAT] sender search -> {len(emails)} emails")

        if not emails:
            answer = f"No emails found from '{sender_name}'."

            def stream_no_sender():
                yield answer
                _save_assistant_message(db, session, session_id, question, answer)

            return StreamingResponse(
                stream_no_sender(), media_type="text/event-stream"
            )

        answer = f"Found {len(emails)} emails from {sender_name}\n\n"
        for index, email in enumerate(emails, start=1):
            answer += (
                f"{index}. {email.subject}\n"
                f"From: {email.sender}\n"
                f"Date: {email.received_at}\n\n"
            )

        def stream_sender_results():
            yield answer
            yield build_sources_payload([], emails)
            _save_assistant_message(db, session, session_id, question, answer)

        return StreamingResponse(
            stream_sender_results(), media_type="text/event-stream"
        )

    # -----------------------------------------------------------------------
    # SEMANTIC / DIRECT PATH
    # -----------------------------------------------------------------------
    if not is_follow_up(question):
        retrieval_results = UnifiedRetriever.search(question, db, top_k=10)
        documents = retrieval_results["documents"]
        emails = retrieval_results["emails"]

        logger.info(
            f"[CHAT] semantic | docs={len(documents)} emails={len(emails)}"
        )

        if not documents and not emails:

            def stream_no_results():
                full_text = "I could not find that information in the documents."
                yield full_text
                _save_assistant_message(db, session, session_id, question, full_text)

            return StreamingResponse(
                stream_no_results(), media_type="text/event-stream"
            )

        # EMAILS TAKE PRIORITY
        if emails:
            email = emails[0]
            session.last_email_id = email.id
            db.commit()

            answer = f"""
━━━━━━━━━━━━━━━━━━━━

SUBJECT:
{email.subject}

FROM:
{email.sender}

TO:
{email.recipient}

DATE:
{email.received_at}

━━━━━━━━━━━━━━━━━━━━

BODY:

{email.body[:5000] if email.body else ''}

━━━━━━━━━━━━━━━━━━━━
"""
        elif documents:
            first_doc = documents[0]
            answer = f"Relevant document found:\n\n{first_doc.name}"
        else:
            answer = "I could not find that information in the documents or emails."

        def stream_direct():
            full_text = answer
            yield full_text

            if documents or emails:
                yield build_sources_payload(documents, emails)

            _save_assistant_message(db, session, session_id, question, full_text)
            logger.info(f"[CHAT] direct answered: {question[:50]!r}")

        return StreamingResponse(stream_direct(), media_type="text/event-stream")

    # -----------------------------------------------------------------------
    # FOLLOW-UP PATH — use Gemini
    # -----------------------------------------------------------------------
    retrieval_results = UnifiedRetriever.search(question, db)
    documents = retrieval_results["documents"]
    emails = retrieval_results["emails"]

    logger.info(
        f"[CHAT] follow-up | docs={len(documents)} emails={len(emails)}"
    )

    context = build_context(documents, emails) if (documents or emails) else ""

    prompt = GeminiService.answer_question(
        question=question,
        context=context,
        conversation_history=conversation_history,
    )

    def stream_gemini():
        full_text = ""
        try:
            for chunk in GeminiService.stream_answer(prompt):
                full_text += chunk
                yield chunk
        except Exception as e:
            logger.error(f"[GEMINI ERROR] {e}")
            fallback = (
                "AI explanation is temporarily unavailable. "
                "Here is the relevant information from the documents:\n\n"
                + (context[:800] if context else "No additional context available.")
            )
            full_text = fallback
            yield fallback

        if documents or emails:
            yield build_sources_payload(documents, emails)

        _save_assistant_message(db, session, session_id, question, full_text)
        logger.info(f"[CHAT] follow-up answered: {question[:50]!r}")

    return StreamingResponse(stream_gemini(), media_type="text/event-stream")


# -----------------------------------------------------------------------
# Shared helper
# -----------------------------------------------------------------------


def _save_assistant_message(db, session, session_id, question, full_text):
    assistant_message = ChatMessage(
        session_id=session_id,
        role="assistant",
        content=full_text,
    )
    db.add(assistant_message)
    if session.title == "New Chat":
        session.title = (question or "")[:50]
    db.commit()


# -----------------------------------------------------------------------
# Session management endpoints
# -----------------------------------------------------------------------


@router.get("/sessions/{session_id}/messages")
def get_messages(session_id: int, db: Session = Depends(get_db)):
    return (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )


@router.delete("/sessions/{session_id}")
def delete_session(session_id: int, db: Session = Depends(get_db)):
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")

    db.query(ChatMessage).filter(ChatMessage.session_id == session_id).delete()
    db.delete(session)
    db.commit()
    return {"message": "Chat deleted successfully"}