#backend/app/api/chat/routes.py

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc
from app.services.ai.gemini_service import GeminiService
from app.database.session import get_db
from app.models.document import Document
from app.models.document_content import DocumentContent
from app.models.chat_session import ChatSession
from app.models.chat_message import ChatMessage
from app.schemas.chat import SendMessageRequest
from app.services.rag.retrieval_service import RetrievalService
from app.services.retrieval.unified_retriever import UnifiedRetriever
from app.services.ai.intent_service import IntentService
from app.models.email import Email
import re
import json

router = APIRouter(
    prefix="/api/chat",
    tags=["AI Chat"]
)

def extract_best_answer(content: str, keywords: list[str]):
    lines = content.split("\n")

    for i, line in enumerate(lines):
        if any(keyword.lower() in line.lower() for keyword in keywords):
            answer_lines = lines[i:i+5]
            answer_text = "\n".join(answer_lines)
            return {
                "question": line,
                "answer": answer_text
            }

    return {
        "question": "",
        "answer": "No answer found."
    }

_STOP_WORDS = {"what", "is", "the", "a", "an", "of", "for", "in", "to", "and"}


def extract_keywords(question: str) -> list[str]:
    return [
        word.lower()
        for word in question.lower().split()
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
    q = question.lower().strip()
    return any(phrase in q for phrase in _FOLLOWUP_PHRASES)


def build_sources_payload(documents, emails) -> str:
    data = {
        "sources": {
            "documents": [
                {
                    "id": doc.id,
                    "name": doc.name,
                    "web_view_link": doc.web_view_link
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
                        )
                    }
                    for email in emails
                ]
        }
    }
    return f"\n[SOURCES_START]{json.dumps(data)}[SOURCES_END]"


# ---------------------------------------------------------------------------
# Helper: build context string from documents + emails
# ---------------------------------------------------------------------------

def build_context(documents, emails) -> str:
    document_context = "\n\n".join(
        doc.name
        for doc in documents
    )

    email_context = "\n\n".join(
        f"Subject: {email.subject}\nFrom: {email.sender}\nBody:\n{email.body if email.body else ''}"
        for email in emails
    )

    return f"=== DOCUMENTS ===\n{document_context}\n\n=== EMAILS ===\n{email_context}"


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/sessions")
def create_session(db: Session = Depends(get_db)):
    session = ChatSession(title="New Chat")
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.get("/sessions")
def get_sessions(db: Session = Depends(get_db)):
    return (
        db.query(ChatSession)
        .order_by(desc(ChatSession.updated_at))
        .all()
    )


@router.post("/sessions/{session_id}/messages")
def send_message(
    session_id: int,
    request: SendMessageRequest,
    db: Session = Depends(get_db)
):
    # --- Validate session ---
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")

    # --- Save user message ---
    user_message = ChatMessage(
        session_id=session_id,
        role="user",
        content=request.message
    )
    db.add(user_message)
    db.commit()

    question = request.message
    question_lower = question.lower()

    keywords = extract_keywords(question)
    sender_search = False
    sender_name = None

    match = re.search(
        r"(?:emails?|mails?)\s+(?:from|by|sent by)\s+(.+)",
        question_lower
    )

    if match:

        sender_search = True

        sender_name = (
            match.group(1)
            .strip()
        )

    # --- Build conversation history (exclude the just-saved user message) ---
    history = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )
    conversation_history = "".join(
        f"{msg.role}: {msg.content}\n"
        for msg in history[:-1]
    )

    print(f"[DEBUG] Question: '{question}'")
    print(f"[DEBUG] Is Follow-up: {is_follow_up(question)}")

    # -----------------------------------------------------------------------
    # DIRECT ANSWER PATH — no Gemini
    # -----------------------------------------------------------------------
    if not is_follow_up(question):
        if sender_search:

            intent = IntentService.detect(
                question
            )

            if intent["intent"] == "search_sender":

                emails = (
                    db.query(Email)
                    .filter(
                        Email.sender.ilike(
                            f"%{sender_name}%"
                        )
                    )
                    .order_by(
                        Email.id.desc()
                    )
                    .limit(15)
                    .all()
                )


                answer = (
                    f"Found {len(emails)} emails "
                    f"from {sender_name}\n\n"
                )

                if not emails:

                    answer = (
                        f"No emails found from '{sender_name}'."
                    )

                    def stream_no_sender():

                        yield answer

                        _save_assistant_message(
                            db,
                            session,
                            session_id,
                            question,
                            answer
                        )

                    return StreamingResponse(
                        stream_no_sender(),
                        media_type="text/event-stream"
                    )

            else:

                retrieval_results = UnifiedRetriever.search(
                    question,
                    db,
                    top_k=10
                )

                emails = retrieval_results["emails"]
                answer = (
                    f"Found {len(emails)} emails "
                    f"from {sender_name}\n\n"
                )

            for index, email in enumerate(
                emails,
                start=1
            ):

                answer += (
                    f"{index}. {email.subject}\n"
                    f"From: {email.sender}\n"
                    f"Date: {email.received_at}\n\n"
                )

            def stream_sender_results():

                yield answer

                yield build_sources_payload(
                    [],
                    emails
                )

                _save_assistant_message(
                    db,
                    session,
                    session_id,
                    question,
                    answer
                )

            return StreamingResponse(
                stream_sender_results(),
                media_type="text/event-stream"
            )

        retrieval_results = UnifiedRetriever.search(
            question,
            db,
            top_k=10
        )
        documents = retrieval_results["documents"]
        emails = retrieval_results["emails"]

        if not documents and not emails:
            def stream_no_results():
                full_text = "I could not find that information in the documents."
                yield full_text
                _save_assistant_message(db, session, session_id, question, full_text)

            return StreamingResponse(stream_no_results(), media_type="text/event-stream")

        # Extract best answer from first document (if any)
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

            answer = (
                f"Relevant document found:\n\n"
                f"{first_doc.name}"
            )

        else:

            answer = (
                "I could not find that information "
                "in the documents or emails."
            )

        def stream_direct():

            full_text = answer

            print("FULL_TEXT =", repr(full_text))

            yield full_text

            if documents or emails:
                yield build_sources_payload(
                    documents,
                    emails
                )

            _save_assistant_message(
                db,
                session,
                session_id,
                question,
                full_text
            )

            print(
                f"[DIRECT] Answered without Gemini: "
                f"{question[:50]}..."
            )

        return StreamingResponse(
            stream_direct(),
            media_type="text/event-stream"
        )
                
    # -----------------------------------------------------------------------
    # FOLLOW-UP PATH — use Gemini
    # -----------------------------------------------------------------------
    else:
        retrieval_results = UnifiedRetriever.search(question,db)
        print(retrieval_results)
        documents = retrieval_results["documents"]
        emails = retrieval_results["emails"]

        context = build_context(documents, emails) if (documents or emails) else ""

        prompt = GeminiService.answer_question(
            question=question,
            context=context,
            conversation_history=conversation_history
        )

        def stream_gemini():
            full_text = ""

            try:
                for chunk in GeminiService.stream_answer(prompt):
                    full_text += chunk
                    yield chunk
            except Exception as e:
                print(f"[GEMINI ERROR] {e}")
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
            print(f"[GEMINI] Follow-up answered: {question[:50]}...")

        return StreamingResponse(stream_gemini(), media_type="text/event-stream")

# ---------------------------------------------------------------------------
# Shared helper: save assistant message + update session title
# ---------------------------------------------------------------------------

def _save_assistant_message(db, session, session_id, question, full_text):
    assistant_message = ChatMessage(
        session_id=session_id,
        role="assistant",
        content=full_text
    )
    db.add(assistant_message)
    if session.title == "New Chat":
        session.title = question[:50]
    db.commit()


# ---------------------------------------------------------------------------
# Session management endpoints
# ---------------------------------------------------------------------------

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

