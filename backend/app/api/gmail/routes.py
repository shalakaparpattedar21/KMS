# app/api/gmail/routes.py
#
# The sync logic has been moved to GmailSyncService so it can be reused
# from the OAuth callback (auto-sync on login) without duplicating code.
# The POST /api/gmail/sync endpoint still works exactly as before —
# it now just delegates to the shared service.

from fastapi import APIRouter, Request, Depends
from sqlalchemy import or_
from sqlalchemy.orm import Session

import requests

from app.database.session import get_db
from app.models.email import Email
from app.services.rag.index_service import IndexService
from app.services.gmail.gmail_sync_service import GmailSyncService

router = APIRouter(
    prefix="/api/gmail",
    tags=["Gmail"]
)


# -----------------------------------------------------------------------
# Utility / debug endpoints (unchanged)
# -----------------------------------------------------------------------

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


# -----------------------------------------------------------------------
# Sync endpoint — now delegates to GmailSyncService
# -----------------------------------------------------------------------

@router.post("/sync")
def sync_gmail(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Manually sync emails from Gmail to the KMS database.
    This is also called automatically on login via the OAuth callback.
    """
    token = request.session.get("access_token")
    user_id = request.session.get("user_id")

    result = GmailSyncService.sync(
        access_token=token,
        user_id=user_id,
        db=db,
    )

    return result


# -----------------------------------------------------------------------
# Read / search endpoints (unchanged)
# -----------------------------------------------------------------------

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


@router.post("/reindex-emails")
def reindex_emails(db: Session = Depends(get_db)):
    """Reindex all emails into Chroma (run after schema changes)"""
    emails = db.query(Email).all()

    for email in emails:
        IndexService.index_email(
            email_id=email.id,
            subject=email.subject,
            sender=email.sender,
            body=email.body,
            received_at=str(email.received_at) if email.received_at else None
        )

    return {"emails": len(emails)}


@router.get("/debug-senders")
def debug_senders(db: Session = Depends(get_db)):
    emails = (
        db.query(Email)
        .limit(20)
        .all()
    )
    return [{"id": e.id, "sender": e.sender} for e in emails]