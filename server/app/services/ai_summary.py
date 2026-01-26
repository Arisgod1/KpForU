import json
import logging
from datetime import date, datetime, time, timedelta, timezone
from typing import Tuple

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.ai_summary import AISummary
from app.models.focus import FocusSession
from app.models.review import ReviewEvent
from app.services.qwen_client import stream_chat

logger = logging.getLogger(__name__)


def _range_bounds(start_date: date, end_date: date) -> tuple[datetime, datetime]:
    start_dt = datetime.combine(start_date, time.min, tzinfo=timezone.utc)
    end_dt = datetime.combine(end_date, time.max, tzinfo=timezone.utc)
    return start_dt, end_dt


def _fallback_summary(focus_count: int, review_done: int, review_snooze: int, days: int) -> Tuple[str, list[str]]:
    text = (
        f"Past {days} day(s): focus sessions {focus_count}, reviews done {review_done}, "
        f"snoozed {review_snooze}. Keep steady pacing and adjust loop lengths if completion dips."
    )
    suggestions: list[str] = []
    if focus_count < 1:
        suggestions.append("Schedule at least one short focus block today.")
    if review_snooze > review_done:
        suggestions.append("Reduce daily load or pick shorter sessions to cut snoozes.")
    if not suggestions:
        suggestions.append("Great consistency—keep the current rhythm.")
    return text, suggestions


def _build_prompt(focus_count: int, review_done: int, review_snooze: int, days: int) -> str:
    return (
        "你是学习效率教练。根据给定统计，生成简短中文总结和 2-3 条行动建议。"
        "只输出 JSON，字段 text(<=120 字)、suggestions(字符串数组，动宾结构，避免赘述)，不要额外文字。"
        f"统计窗口：最近 {days} 天；专注次数 {focus_count}；完成复习 {review_done}；延后复习 {review_snooze}。"
    )


def _llm_summary(focus_count: int, review_done: int, review_snooze: int, days: int, want_audio: bool):
    settings = get_settings()
    prompt = _build_prompt(focus_count, review_done, review_snooze, days)
    raw_text, audio_b64 = stream_chat(prompt, want_audio=want_audio)

    text = ""
    suggestions: list[str] = []

    if raw_text:
        try:
            data = json.loads(raw_text)
            if isinstance(data, dict):
                text = data.get("text") or ""
                suggestions = [s for s in data.get("suggestions", []) if isinstance(s, str)]
        except Exception as exc:  # noqa: BLE001
            logger.warning("Model response not JSON, using raw text: %s", exc)
            text = raw_text.strip()

    if not text:
        text, suggestions = _fallback_summary(focus_count, review_done, review_snooze, days)

    return text, suggestions, audio_b64


def get_or_create_daily_summary(db: Session, user_id, target_date: date) -> AISummary:
    existing = (
        db.query(AISummary)
        .filter(
            AISummary.user_id == user_id,
            AISummary.range == "daily",
            AISummary.range_start == target_date,
        )
        .first()
    )
    if existing:
        return existing

    start_dt, end_dt = _range_bounds(target_date, target_date)
    focus_count = (
        db.query(FocusSession)
        .filter(FocusSession.user_id == user_id, FocusSession.started_at >= start_dt, FocusSession.started_at <= end_dt)
        .count()
    )
    review_done = (
        db.query(ReviewEvent)
        .filter(
            ReviewEvent.user_id == user_id,
            ReviewEvent.event_type == "done",
            ReviewEvent.occurred_at >= start_dt,
            ReviewEvent.occurred_at <= end_dt,
        )
        .count()
    )
    review_snooze = (
        db.query(ReviewEvent)
        .filter(
            ReviewEvent.user_id == user_id,
            ReviewEvent.event_type == "snooze",
            ReviewEvent.occurred_at >= start_dt,
            ReviewEvent.occurred_at <= end_dt,
        )
        .count()
    )
    want_audio = get_settings().ai_summary_audio_enabled
    text, suggestions, audio_b64 = _llm_summary(focus_count, review_done, review_snooze, 1, want_audio)

    summary = AISummary(
        user_id=user_id,
        range="daily",
        range_start=target_date,
        range_end=target_date,
        text=text,
        suggestions=suggestions,
        audio_data=audio_b64,
        audio_format=get_settings().qwen_audio_format if audio_b64 else None,
    )
    db.add(summary)
    db.commit()
    db.refresh(summary)
    return summary


def get_or_create_weekly_summary(db: Session, user_id, week_start: date) -> AISummary:
    week_end = week_start + timedelta(days=6)
    existing = (
        db.query(AISummary)
        .filter(
            AISummary.user_id == user_id,
            AISummary.range == "weekly",
            AISummary.range_start == week_start,
        )
        .first()
    )
    if existing:
        return existing

    start_dt, end_dt = _range_bounds(week_start, week_end)
    focus_count = (
        db.query(FocusSession)
        .filter(FocusSession.user_id == user_id, FocusSession.started_at >= start_dt, FocusSession.started_at <= end_dt)
        .count()
    )
    review_done = (
        db.query(ReviewEvent)
        .filter(
            ReviewEvent.user_id == user_id,
            ReviewEvent.event_type == "done",
            ReviewEvent.occurred_at >= start_dt,
            ReviewEvent.occurred_at <= end_dt,
        )
        .count()
    )
    review_snooze = (
        db.query(ReviewEvent)
        .filter(
            ReviewEvent.user_id == user_id,
            ReviewEvent.event_type == "snooze",
            ReviewEvent.occurred_at >= start_dt,
            ReviewEvent.occurred_at <= end_dt,
        )
        .count()
    )
    want_audio = get_settings().ai_summary_audio_enabled
    text, suggestions, audio_b64 = _llm_summary(focus_count, review_done, review_snooze, 7, want_audio)

    summary = AISummary(
        user_id=user_id,
        range="weekly",
        range_start=week_start,
        range_end=week_end,
        text=text,
        suggestions=suggestions,
        audio_data=audio_b64,
        audio_format=get_settings().qwen_audio_format if audio_b64 else None,
    )
    db.add(summary)
    db.commit()
    db.refresh(summary)
    return summary


def list_summaries(db: Session, user_id, range_filter: str | None = None, limit: int = 50) -> list[AISummary]:
    query = db.query(AISummary).filter(AISummary.user_id == user_id).order_by(AISummary.created_at.desc())
    if range_filter:
        query = query.filter(AISummary.range == range_filter)
    return query.limit(limit).all()


def delete_summary(db: Session, user_id, summary_id: str) -> bool:
    summary = (
        db.query(AISummary)
        .filter(AISummary.id == summary_id, AISummary.user_id == user_id)
        .first()
    )
    if not summary:
        return False
    db.delete(summary)
    db.commit()
    return True
