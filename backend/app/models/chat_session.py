from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.base import Base


class ChatSession(Base):
    """
    Chat session model to track conversations.
    now tracks current email being discussed.
    """
    __tablename__ = "chat_sessions"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    user_id = Column(
        Integer,
        nullable=True
    )

    title = Column(
        String(255),
        default="New Chat",
        nullable=False
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

    # ✅ NEW: Track current email being discussed
    last_email_id = Column(
        Integer,
        ForeignKey("emails.id"),
        nullable=True
    )

    # Relationship
    # last_email = relationship("Email")

    def __repr__(self):
        return f"<ChatSession {self.id}: {self.title}>"