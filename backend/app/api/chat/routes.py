import json
import logging
import re

from app.services.ai.context_builder import ContextBuilder
from app.services.ai.llm_service import LLMService
from fastapi import APIRouter, Depends, HTTPException, Request
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
# Helpers (unchanged from original)
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
# Session memory helpers
# -----------------------------------------------------------------------

def _save_last_context(request: Request, documents: list, emails: list):
    """
    Persist the most-recently retrieved item IDs into the session.
    This enables follow-up commands like "reply to that email" or "summarize it".
    Stored keys:
        last_email_id       — DB id of the most relevant email
        last_email_subject  — for display in draft prompts
        last_email_sender   — for draft context
        last_email_body     — for draft context
        last_email_gmail_id — gmail_message_id for reply/forward API calls
        last_email_thread_id — gmail_thread_id for threaded replies
        last_document_id    — DB id of the most relevant document
        last_document_name  — for display
    """
    if emails:
        top = emails[0]
        request.session["last_email_id"] = top.id
        request.session["last_email_subject"] = top.subject or ""
        request.session["last_email_sender"] = top.sender or ""
        request.session["last_email_body"] = (top.body or "")[:2000]  # cap size
        request.session["last_email_gmail_id"] = top.gmail_message_id or ""
        request.session["last_email_thread_id"] = top.gmail_thread_id or ""

    if documents:
        top = documents[0]
        request.session["last_document_id"] = top.id
        request.session["last_document_name"] = top.name or ""


# -----------------------------------------------------------------------
# Session / CRUD endpoints (unchanged)
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


# -----------------------------------------------------------------------
# Main message handler
# -----------------------------------------------------------------------

@router.post("/sessions/{session_id}/messages")
def send_message(
    session_id: int,
    request: SendMessageRequest,
    http_request: Request,
    db: Session = Depends(get_db),
):
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")

    user_message = ChatMessage(
        session_id=session_id,
        role="user",
        content=request.message,
    )
    db.add(user_message)
    db.commit()

    question = request.message or ""
    intent = IntentService.detect(question)
    sender_name = IntentService.extract_sender(question)

    logger.info(
        f"[CHAT] session={session_id} question={question!r} "
        f"intent={intent['intent']} sender_name={sender_name!r} "
        f"follow_up={is_follow_up(question)}"
    )

    history = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )
    conversation_history = "".join(
        f"{msg.role}: {msg.content}\n" for msg in history[:-1]
    )

    # -------------------------------------------------------------------
    # INTENT: search_sender (original, unchanged)
    # -------------------------------------------------------------------
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
        if not emails:
            logger.info(
                "[CHAT] sender ILIKE empty -> falling back to UnifiedRetriever"
            )
            retrieval_results = UnifiedRetriever.search(question, db, top_k=4)
            emails = retrieval_results["emails"]

        logger.info(f"[CHAT] sender search -> {len(emails)} emails")

        # Save session memory
        _save_last_context(http_request, [], emails)

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

    # -------------------------------------------------------------------
    # INTENT: reply_email
    # -------------------------------------------------------------------
    if intent["intent"] == "reply_email":
        last_email_id = http_request.session.get("last_email_id")

        if not last_email_id:
            answer = (
                "I don't have a recent email in context. "
                "Please search for or open an email first, then ask me to reply."
            )

            def stream_no_ctx_reply():
                yield answer
                _save_assistant_message(db, session, session_id, question, answer)

            return StreamingResponse(
                stream_no_ctx_reply(), media_type="text/event-stream"
            )

        subject = http_request.session.get("last_email_subject", "")
        sender = http_request.session.get("last_email_sender", "")
        body = http_request.session.get("last_email_body", "")
        gmail_id = http_request.session.get("last_email_gmail_id", "")
        thread_id = http_request.session.get("last_email_thread_id", "")

        logger.info(
            f"[CHAT] reply_email | last_email_id={last_email_id} "
            f"gmail_id={gmail_id!r} thread_id={thread_id!r}"
        )

        draft = LLMService.draft_email_reply(
            original_subject=subject,
            original_sender=sender,
            original_body=body,
            instruction=question,
        )

        # Return the draft plus metadata so the frontend can pre-fill EmailModal
        reply_meta = {
            "action": "open_reply",
            "gmail_message_id": gmail_id,
            "thread_id": thread_id,
            "draft_body": draft,
            "original_subject": subject,
            "original_sender": sender,
        }
        full_answer = f"Here's a draft reply to the email from {sender}:\n\n{draft}"

        def stream_reply_draft():
            yield full_answer
            yield f"\n[ACTION_START]{json.dumps(reply_meta)}[ACTION_END]"
            _save_assistant_message(db, session, session_id, question, full_answer)

        return StreamingResponse(
            stream_reply_draft(), media_type="text/event-stream"
        )

    # -------------------------------------------------------------------
    # INTENT: forward_email
    # -------------------------------------------------------------------
    if intent["intent"] == "forward_email":
        last_email_id = http_request.session.get("last_email_id")

        if not last_email_id:
            answer = (
                "I don't have a recent email in context. "
                "Please search for or open an email first, then ask me to forward it."
            )

            def stream_no_ctx_fwd():
                yield answer
                _save_assistant_message(db, session, session_id, question, answer)

            return StreamingResponse(
                stream_no_ctx_fwd(), media_type="text/event-stream"
            )

        gmail_id = http_request.session.get("last_email_gmail_id", "")
        subject = http_request.session.get("last_email_subject", "")
        recipient = intent.get("recipient")  # extracted by IntentService

        logger.info(
            f"[CHAT] forward_email | last_email_id={last_email_id} "
            f"gmail_id={gmail_id!r} recipient={recipient!r}"
        )

        forward_meta = {
            "action": "open_forward",
            "gmail_message_id": gmail_id,
            "recipient": recipient or "",
            "original_subject": subject,
        }

        if recipient:
            answer = (
                f"I'll forward the email '{subject}' to {recipient}. "
                "Opening the forward window for your confirmation."
            )
        else:
            answer = (
                f"I'll forward the email '{subject}'. "
                "Please enter the recipient in the forward window."
            )

        def stream_forward():
            yield answer
            yield f"\n[ACTION_START]{json.dumps(forward_meta)}[ACTION_END]"
            _save_assistant_message(db, session, session_id, question, answer)

        return StreamingResponse(stream_forward(), media_type="text/event-stream")

    # -------------------------------------------------------------------
    # INTENT: draft_email
    # -------------------------------------------------------------------
    if intent["intent"] == "draft_email":
        last_email_id = http_request.session.get("last_email_id")

        if not last_email_id:
            answer = (
                "I don't have a recent email in context to base the draft on. "
                "Please search for an email first."
            )

            def stream_no_ctx_draft():
                yield answer
                _save_assistant_message(db, session, session_id, question, answer)

            return StreamingResponse(
                stream_no_ctx_draft(), media_type="text/event-stream"
            )

        subject = http_request.session.get("last_email_subject", "")
        sender = http_request.session.get("last_email_sender", "")
        body = http_request.session.get("last_email_body", "")

        logger.info(
            f"[CHAT] draft_email | last_email_id={last_email_id} subject={subject!r}"
        )

        draft = LLMService.draft_email_reply(
            original_subject=subject,
            original_sender=sender,
            original_body=body,
            instruction=question,
        )

        full_answer = f"Here's a draft based on the email from {sender}:\n\n{draft}"

        def stream_draft():
            yield full_answer
            _save_assistant_message(db, session, session_id, question, full_answer)

        return StreamingResponse(stream_draft(), media_type="text/event-stream")

    # -------------------------------------------------------------------
    # INTENT: summarize_last
    # -------------------------------------------------------------------
    if intent["intent"] == "summarize_last":
        last_email_id = http_request.session.get("last_email_id")
        last_doc_id = http_request.session.get("last_document_id")

        if not last_email_id and not last_doc_id:
            answer = (
                "I don't have a recent email or document in context to summarize. "
                "Please search for something first."
            )

            def stream_no_ctx_summ():
                yield answer
                _save_assistant_message(db, session, session_id, question, answer)

            return StreamingResponse(
                stream_no_ctx_summ(), media_type="text/event-stream"
            )

        # Build context from session memory
        summ_context = ""
        if last_email_id:
            summ_context += (
                f"EMAIL\n"
                f"Subject: {http_request.session.get('last_email_subject', '')}\n"
                f"From: {http_request.session.get('last_email_sender', '')}\n"
                f"Body:\n{http_request.session.get('last_email_body', '')}\n"
            )
        if last_doc_id:
            summ_context += (
                f"\nDOCUMENT\n"
                f"Title: {http_request.session.get('last_document_name', '')}\n"
            )

        logger.info(
            f"[CHAT] summarize_last | email_id={last_email_id} doc_id={last_doc_id}"
        )

        answer = LLMService.answer(question="Summarize this.", context=summ_context)

        def stream_summary():
            yield answer
            _save_assistant_message(db, session, session_id, question, answer)

        return StreamingResponse(stream_summary(), media_type="text/event-stream")

    # -------------------------------------------------------------------
    # INTENT: semantic_search (original path, unchanged logic)
    # -------------------------------------------------------------------
    if not is_follow_up(question):
        retrieval_results = UnifiedRetriever.search(question, db, top_k=10)
        documents = retrieval_results["documents"]
        emails = retrieval_results["emails"]

        logger.info(
            f"[CHAT] semantic | docs={len(documents)} emails={len(emails)}"
        )

        # Save session memory so follow-up commands work
        _save_last_context(http_request, documents, emails)

        if not documents and not emails:

            def stream_no_results():
                full_text = "I could not find that information in the documents."
                yield full_text
                _save_assistant_message(db, session, session_id, question, full_text)

            return StreamingResponse(
                stream_no_results(), media_type="text/event-stream"
            )

        context = ContextBuilder.build(retrieval_results, db=db)
        answer = LLMService.answer(question=question, context=context)

        def stream_direct():
            full_text = answer
            yield full_text

            if documents or emails:
                yield build_sources_payload(documents, emails)

            _save_assistant_message(db, session, session_id, question, full_text)
            logger.info(f"[CHAT] direct answered: {question[:50]!r}")

        return StreamingResponse(stream_direct(), media_type="text/event-stream")

    # -------------------------------------------------------------------
    # FOLLOW-UP PATH — use Gemini (original, unchanged)
    # -------------------------------------------------------------------
    retrieval_results = UnifiedRetriever.search(question, db)
    documents = retrieval_results["documents"]
    emails = retrieval_results["emails"]

    logger.info(
        f"[CHAT] follow-up | docs={len(documents)} emails={len(emails)}"
    )

    context = ContextBuilder.build(retrieval_results, db=db) if (documents or emails) else ""

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
# Shared helper (unchanged)
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
# Session management endpoints (unchanged)
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