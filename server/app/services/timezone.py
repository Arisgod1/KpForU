from datetime import date, datetime, time, timezone
from zoneinfo import ZoneInfo


def resolve_timezone(header_value: str | None) -> ZoneInfo:
    try:
        if header_value:
            return ZoneInfo(header_value)
    except Exception:
        pass
    return ZoneInfo("UTC")


def to_client_date(dt: datetime, tz: ZoneInfo) -> date:
    return dt.astimezone(tz).date()


def start_end_of_date(target_date: date, tz: ZoneInfo) -> tuple[datetime, datetime]:
    start_dt = datetime.combine(target_date, time.min, tzinfo=tz).astimezone(timezone.utc)
    end_dt = datetime.combine(target_date, time.max, tzinfo=tz).astimezone(timezone.utc)
    return start_dt, end_dt
