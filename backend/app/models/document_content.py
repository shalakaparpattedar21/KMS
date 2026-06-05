from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class DocumentContent(Base):
    __tablename__ = "document_contents"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id")
    )

    content: Mapped[str] = mapped_column(
        Text
    )