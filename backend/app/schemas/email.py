from pydantic import BaseModel, EmailStr
from typing import Optional


class ReplyRequest(BaseModel):
    """Request body for replying to an email"""
    message_id: str
    thread_id: str
    content: str


class ForwardRequest(BaseModel):
    """Request body for forwarding an email"""
    message_id: str
    recipient: EmailStr
    content: Optional[str] = ""


class SendRequest(BaseModel):
    """Request body for sending a new email"""
    to: EmailStr
    subject: str
    body: str


class DraftRequest(BaseModel):
    """Request body for creating a draft"""
    to: EmailStr
    subject: str
    body: str