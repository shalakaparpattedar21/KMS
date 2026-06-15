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
                Email.subject.ilike(
                    f"%{keyword}%"
                ),
                Email.sender.ilike(
                    f"%{keyword}%"
                ),
                Email.body.ilike(
                    f"%{keyword}%"
                )
            ])

        return (
            db.query(Email)
            .filter(
                or_(*filters)
            )
            .limit(limit)
            .all()
        )