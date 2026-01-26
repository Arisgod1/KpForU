from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

from app.core.security import get_current_principal
from app.db.session import get_db
from app.models.review import ReviewEvent, ReviewSchedule
from app.schemas.review import TodayMetrics, WatchReviewMetrics
from app.services.reviews import count_today_done, get_due_schedules_for_date, next_upcoming_review
from app.services.timezone import resolve_timezone, start_end_of_date

router = APIRouter(tags=["Watch"])


@router.get("/watch/review/metrics", response_model=WatchReviewMetrics)
def review_metrics(
    x_client_timezone: str | None = Header(default=None, alias="X-Client-Timezone"),
    db: Session = Depends(get_db),
    principal=Depends(get_current_principal),
):
    user, _ = principal
    tz = resolve_timezone(x_client_timezone)
    now = datetime.now(timezone.utc)
    today = now.astimezone(tz).date()
    start_dt, end_dt = start_end_of_date(today, tz)

    schedules = get_due_schedules_for_date(db, user.id, start_dt, end_dt)
    planned = len(schedules)
    done = count_today_done(db, user.id, start_dt, end_dt)

    next_review_at = next_upcoming_review(db, user.id)
    countdown = None
    if next_review_at:
        delta = next_review_at - now
        countdown = max(int(delta.total_seconds()), 0)

    return WatchReviewMetrics(
        today=TodayMetrics(planned=planned, done=done),
        next_review_at=next_review_at,
        countdown_sec=countdown,
    )
