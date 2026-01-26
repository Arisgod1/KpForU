from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import http_error
from app.core.security import get_current_principal
from app.db.session import get_db
from app.models.card import Card
from app.schemas.card import Card as CardSchema
from app.models.review import ReviewEvent, ReviewSchedule
from app.schemas.review import (
    DueListItem,
    DueListResponse,
    ReviewEventCreate,
    ReviewEventResponse,
    ReviewSchedule as ReviewScheduleSchema,
)
from app.services.leitner import next_after_done, next_after_snooze
from app.services.timezone import resolve_timezone, start_end_of_date

router = APIRouter(tags=["Reviews"])


@router.get("/reviews/due", response_model=DueListResponse)
def due_list(
    date: str | None = Query(default=None),
    x_client_timezone: str | None = Header(default=None, alias="X-Client-Timezone"),
    db: Session = Depends(get_db),
    principal=Depends(get_current_principal),
):
    user, _ = principal
    tz = resolve_timezone(x_client_timezone)
    target_date = datetime.now(timezone.utc).astimezone(tz).date()
    if date:
        try:
            target_date = datetime.fromisoformat(date).date()
        except ValueError:
            pass
    start_dt, end_dt = start_end_of_date(target_date, tz)

    schedules = (
        db.query(ReviewSchedule)
        .filter(ReviewSchedule.user_id == user.id)
        .order_by(ReviewSchedule.next_review_at.asc())
        .all()
    )

    items: list[DueListItem] = []
    due_count = 0
    for s in schedules:
        card = db.get(Card, s.card_id)
        if card is None:
            continue
        due_state = "due" if s.next_review_at <= end_dt else "not_due"
        if due_state == "due":
            due_count += 1
        items.append(
            DueListItem(
                card=CardSchema(
                    id=str(card.id),
                    front=card.front,
                    back=card.back,
                    tags=card.tags,
                    status=card.status,
                    created_at=card.created_at,
                    updated_at=card.updated_at,
                    generated_from_draft_id=str(card.generated_from_draft_id) if card.generated_from_draft_id else None,
                ),
                schedule=ReviewScheduleSchema(
                    card_id=str(s.card_id),
                    box=s.box,
                    next_review_at=s.next_review_at,
                    interval_days=s.interval_days,
                    due_state=due_state,
                ),
            )
        )

    return DueListResponse(date=target_date, due_count=due_count, data=items)


@router.post("/reviews/events", response_model=ReviewEventResponse, status_code=status.HTTP_201_CREATED)
def create_review_event(
    payload: ReviewEventCreate,
    db: Session = Depends(get_db),
    principal=Depends(get_current_principal),
):
    user, _ = principal
    schedule = db.get(ReviewSchedule, payload.card_id)
    if schedule is None or schedule.user_id != user.id:
        raise http_error(status.HTTP_404_NOT_FOUND, "not_found", "Schedule not found")

    settings = get_settings()
    now = datetime.now(timezone.utc)
    if payload.event_type == "done":
        new_box, interval_days, next_review_at = next_after_done(schedule.box, settings.leitner_intervals, now=now)
    else:
        snooze_days = payload.snooze_days or 1
        if snooze_days not in (1, 2, 3):
            raise http_error(status.HTTP_422_UNPROCESSABLE_ENTITY, "unprocessable", "snooze_days must be 1/2/3")
        new_box, interval_days, next_review_at = next_after_snooze(schedule.box, snooze_days, now=now)

    schedule.box = new_box
    schedule.interval_days = interval_days
    schedule.next_review_at = next_review_at

    event = ReviewEvent(
        card_id=schedule.card_id,
        user_id=user.id,
        event_type=payload.event_type,
        occurred_at=payload.occurred_at,
        source=payload.source,
        box=new_box,
        next_review_at=next_review_at,
        interval_days=interval_days,
    )
    db.add(event)
    db.commit()
    db.refresh(event)

    return ReviewEventResponse(
        event_id=str(event.id),
        card_id=str(event.card_id),
        box=new_box,
        next_review_at=next_review_at,
        interval_days=interval_days,
    )
