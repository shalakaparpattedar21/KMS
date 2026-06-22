from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.email import Email


class EmailRetriever:

    @staticmethod
    def search(
        keywords: list[str],
        db: Session,
        limit: int = 10
    ):

        filters = []

        for keyword in keywords:

            filters.extend([
                Email.subject.ilike(f"%{keyword}%"),
                Email.sender.ilike(f"%{keyword}%"),
                Email.body.ilike(f"%{keyword}%")
            ])

        return (
            db.query(Email)
            .filter(or_(*filters))
            .limit(limit)
            .all()
        )

    @staticmethod
    def search_by_sender(
        sender_name: str,
        db: Session,
        limit: int = 15
    ):

        return (
            db.query(Email)
            .filter(
                Email.sender.ilike(
                    f"%{sender_name}%"
                )
            )
            .order_by(
                Email.id.desc()
            )
            .limit(limit)
            .all()
        )