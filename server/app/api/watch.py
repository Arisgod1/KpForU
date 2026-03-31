from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, status
from sqlalchemy.orm import Session

from app.core.errors import http_error
from app.core.security import get_current_principal
from app.db.session import get_db
from app.models.review import ReviewEvent, ReviewSchedule
from app.models.watch_setting import WatchSetting
from app.schemas.review import TodayMetrics, WatchReviewMetrics
from app.schemas.watch import WatchWallpaperResponse, WatchWallpaperUpdateRequest
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
        if next_review_at.tzinfo is None:
            next_review_at = next_review_at.replace(tzinfo=timezone.utc)
        delta = next_review_at - now
        countdown = max(int(delta.total_seconds()), 0)

    return WatchReviewMetrics(
        today=TodayMetrics(planned=planned, done=done),
        next_review_at=next_review_at,
        countdown_sec=countdown,
    )


@router.get("/watch/wallpaper", response_model=WatchWallpaperResponse)
def get_watch_wallpaper(db: Session = Depends(get_db), principal=Depends(get_current_principal)):
    user, _ = principal
    settings = db.query(WatchSetting).filter(WatchSetting.user_id == user.id).first()
    return WatchWallpaperResponse(url=settings.wallpaper_url if settings else None)


@router.put("/watch/wallpaper", response_model=WatchWallpaperResponse)
def update_watch_wallpaper(
    payload: WatchWallpaperUpdateRequest,
    db: Session = Depends(get_db),
    principal=Depends(get_current_principal),
):
    user, _ = principal
    url = payload.url.strip() if payload.url else None
    if url:
        if not (url.startswith("http://") or url.startswith("https://")):
            raise http_error(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                "invalid_wallpaper_url",
                "Wallpaper URL must start with http:// or https://",
            )
    settings = db.query(WatchSetting).filter(WatchSetting.user_id == user.id).first()
    if settings is None:
        settings = WatchSetting(user_id=user.id, wallpaper_url=url)
        db.add(settings)
    else:
        settings.wallpaper_url = url

    db.commit()
    db.refresh(settings)
    return WatchWallpaperResponse(url=settings.wallpaper_url)
