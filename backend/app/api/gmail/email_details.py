from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.email import Email

router = APIRouter(
    prefix="/api/gmail",
    tags=["Gmail"]
)

@router.get("/email/{email_id}")
def get_email(
    email_id: int,
    db: Session = Depends(get_db)
):

    email = (
        db.query(Email)
        .filter(
            Email.id == email_id
        )
        .first()
    )

    if not email:
        return {
            "error": "Email not found"
        }

    return {
        "id": email.id,
        "subject": email.subject,
        "sender": email.sender,
        "recipient": email.recipient,
        "received_at": email.received_at,
        "body": email.body,
        "gmail_message_id": email.gmail_message_id
    }