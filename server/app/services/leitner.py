from datetime import datetime, timedelta, timezone


def next_after_done(box: int, intervals: dict[int, int], now: datetime | None = None) -> tuple[int, int, datetime]:
    base_time = now or datetime.now(timezone.utc)
    new_box = min(5, box + 1)
    interval_days = intervals.get(new_box, 1)
    next_review_at = base_time + timedelta(days=interval_days)
    return new_box, interval_days, next_review_at


def next_after_snooze(box: int, snooze_days: int, now: datetime | None = None) -> tuple[int, int, datetime]:
    base_time = now or datetime.now(timezone.utc)
    interval_days = snooze_days
    next_review_at = base_time + timedelta(days=snooze_days)
    return box, interval_days, next_review_at
