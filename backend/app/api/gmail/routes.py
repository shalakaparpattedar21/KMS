from fastapi import (
    APIRouter,
    Request,
    Depends
)
from sqlalchemy import or_

from app.models.email import Email
from app.database.session import get_db
from sqlalchemy.orm import Session
import base64
import requests

router = APIRouter(
    prefix="/api/gmail",
    tags=["Gmail"]
)

def get_header(headers, name):
    """Extract header value by name"""
    for header in headers:
        if header["name"].lower() == name.lower():
            return header["value"]
    return None


def extract_body(payload):
    """Extract email body from Gmail payload"""
    if payload.get("body", {}).get("data"):
        return base64.urlsafe_b64decode(
            payload["body"]["data"]
        ).decode(
            "utf-8",
            errors="ignore"
        )

    parts = payload.get("parts", [])

    for part in parts:
        mime_type = part.get("mimeType")

        if mime_type == "text/plain":
            data = (
                part.get("body", {})
                .get("data")
            )
            if data:
                return base64.urlsafe_b64decode(
                    data
                ).decode(
                    "utf-8",
                    errors="ignore"
                )

        if part.get("parts"):
            body = extract_body(part)
            if body:
                return body

    return ""


@router.get("/test")
def test_gmail(request: Request):
    """Test Gmail API connection"""
    token = request.session.get("access_token")

    response = requests.get(
        "https://gmail.googleapis.com/gmail/v1/users/me/profile",
        headers={"Authorization": f"Bearer {token}"}
    )

    return response.json()


@router.get("/messages")
def get_messages(request: Request):
    """List recent Gmail messages"""
    token = request.session.get("access_token")

    response = requests.get(
        "https://gmail.googleapis.com/gmail/v1/users/me/messages?maxResults=10",
        headers={"Authorization": f"Bearer {token}"}
    )
    return response.json()


@router.get("/message/{message_id}")
def get_message(message_id: str, request: Request):
    """Get full Gmail message details"""
    token = request.session.get("access_token")

    response = requests.get(
        f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{message_id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    return response.json()


@router.post("/sync")
def sync_gmail(
    request: Request,
    db: Session = Depends(get_db)
):
    """Sync emails from Gmail to database"""
    token = request.session.get("access_token")
    user_id = request.session.get("user_id")

    headers = {"Authorization": f"Bearer {token}"}

    messages_response = requests.get(
        "https://gmail.googleapis.com/gmail/v1/users/me/messages?maxResults=100",
        headers=headers
    )

    messages = messages_response.json().get("messages", [])
    synced = 0

    for msg in messages:
        gmail_id = msg["id"]

        # Check if already synced
        existing = (
            db.query(Email)
            .filter(Email.gmail_message_id == gmail_id)
            .first()
        )

        if existing:
            continue

        # Fetch full message
        detail_response = requests.get(
            f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{gmail_id}",
            headers=headers
        )

        email_data = detail_response.json()
        payload = email_data.get("payload", {})
        headers_list = payload.get("headers", [])

        # ✅ Extract all metadata
        subject = get_header(headers_list, "Subject")
        sender = get_header(headers_list, "From")
        recipient = get_header(headers_list, "To")
        received_at = get_header(headers_list, "Date")
        body = extract_body(payload)

        email = Email(
            gmail_message_id=gmail_id,
            gmail_thread_id=email_data.get("threadId"),
            subject=subject,
            sender=sender,
            recipient=recipient,
            body=body,
            received_at=received_at,
            user_id=user_id
        )

        db.add(email)
        synced += 1

    db.commit()

    return {"synced": synced}


@router.get("/emails")
def get_emails(db: Session = Depends(get_db)):
    """List all synced emails"""
    emails = (
        db.query(Email)
        .order_by(Email.id.desc())
        .limit(50)
        .all()
    )
    return emails


@router.get("/search")
def search_emails(
    query: str,
    db: Session = Depends(get_db)
):
    """Search emails by subject, sender, or body"""
    results = (
        db.query(Email)
        .filter(
            or_(
                Email.subject.ilike(f"%{query}%"),
                Email.sender.ilike(f"%{query}%"),
                Email.body.ilike(f"%{query}%")
            )
        )
        .limit(20)
        .all()
    )
    return results