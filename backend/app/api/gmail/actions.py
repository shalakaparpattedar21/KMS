from fastapi import (
    APIRouter,
    Request,
    Depends
)
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.email import Email
from app.services.gmail.gmail_service import GmailService
from app.schemas.email import (
    ReplyRequest,
    ForwardRequest,
    SendRequest,
    DraftRequest
)

router = APIRouter(
    prefix="/api/gmail/actions",
    tags=["Gmail Actions"]
)


@router.post("/reply")
def reply_email(
    request_data: ReplyRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Reply to an email
    """
    access_token = request.session.get("access_token")

    result = GmailService.reply_email(
        access_token=access_token,
        message_id=request_data.message_id,
        thread_id=request_data.thread_id,
        content=request_data.content
    )

    return result


@router.post("/forward")
def forward_email(
    request_data: ForwardRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Forward an email to another recipient
    """
    access_token = request.session.get("access_token")

    result = GmailService.forward_email(
        access_token=access_token,
        message_id=request_data.message_id,
        recipient=request_data.recipient,
        content=request_data.content or ""
    )

    return result


@router.post("/send")
def send_email(
    request_data: SendRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Send a new email
    """
    access_token = request.session.get("access_token")

    result = GmailService.send_email(
        access_token=access_token,
        to=request_data.to,
        subject=request_data.subject,
        body=request_data.body
    )

    return result


@router.post("/draft")
def create_draft(
    request_data: DraftRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Create a draft email
    """
    access_token = request.session.get("access_token")

    result = GmailService.create_draft(
        access_token=access_token,
        to=request_data.to,
        subject=request_data.subject,
        body=request_data.body
    )

    return result