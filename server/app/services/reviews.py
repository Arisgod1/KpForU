from datetime import datetime, timezone
from typing import Iterable, Tuple

from sqlalchemy.orm import Session

from app.models.review import ReviewSchedule, ReviewEvent


def get_due_schedules_for_date(
    db: Session, user_id, date_start: datetime, date_end: datetime
) -> list[ReviewSchedule]:
    return (
        db.query(ReviewSchedule)
        .filter(
            ReviewSchedule.user_id == user_id,
            ReviewSchedule.next_review_at <= date_end,
        )
        .all()
    )


def count_today_done(
    db: Session, user_id, start: datetime, end: datetime
) -> int:
    return (
        db.query(ReviewEvent)
        .filter(
            ReviewEvent.user_id == user_id,
            ReviewEvent.occurred_at >= start,
            ReviewEvent.occurred_at <= end,
            ReviewEvent.event_type == "done",
        )
        .count()
    )


def next_upcoming_review(db: Session, user_id) -> datetime | None:
    record = (
        db.query(ReviewSchedule)
        .filter(ReviewSchedule.user_id == user_id)
        .order_by(ReviewSchedule.next_review_at.asc())
        .first()
    )
    return record.next_review_at if record else None
