from datetime import datetime
from app.models.document_content import DocumentContent
from sqlalchemy import (
    String,
    Boolean,
    DateTime,
    BigInteger,
    ForeignKey,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)

    drive_file_id: Mapped[str] = mapped_column(String(255), unique=True)

    name: Mapped[str] = mapped_column(String(500))

    mime_type: Mapped[str] = mapped_column(String(255))

    owner_email: Mapped[str | None] = mapped_column(String(255), nullable=True)

    web_view_link: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    size: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    modified_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    indexed: Mapped[bool] = mapped_column(Boolean, default=False)

    content_extracted: Mapped[bool] = mapped_column(Boolean, default=False)

    sync_status: Mapped[str] = mapped_column(String(50), default="pending")

    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    # ── This is the fix ──────────────────────────────────────────────────
    # ContextBuilder does `for content in doc.contents` — that attribute
    # must be a SQLAlchemy relationship, not a plain Python attribute.
    # Without this, hasattr(doc, "contents") is always False and Gemini
    # receives only the document title with no actual text.
    contents: Mapped[list[DocumentContent]] = relationship(
        DocumentContent,
        foreign_keys=[DocumentContent.document_id],
        lazy="select",
    )
