from sqlalchemy import (
    Column,
    Integer,
    Text,
    DateTime,
    ForeignKey
)

from datetime import datetime
from app.database.base import Base


class Email(Base):
    """
    Stores synced Gmail emails.
    """

    __tablename__ = "emails"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    gmail_message_id = Column(
        Text,
        unique=True,
        index=True,
        nullable=False
    )

    gmail_thread_id = Column(
        Text,
        nullable=True
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    subject = Column(
        Text,
        nullable=True
    )

    sender = Column(
        Text,
        nullable=True
    )

    recipient = Column(
        Text,
        nullable=True
    )

    body = Column(
        Text,
        nullable=True
    )

    # Store Gmail header date exactly as received
    received_at = Column(
        Text,
        nullable=True
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    def __repr__(self):
        return (
            f"<Email "
            f"id={self.id} "
            f"subject={self.subject}>"
        )