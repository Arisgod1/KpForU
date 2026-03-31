import json
import logging
import uuid
from datetime import date, datetime, time, timedelta, timezone
from typing import Tuple

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.ai_summary import AISummary
from app.models.focus import FocusSession
from app.models.review import ReviewEvent
from app.services.qwen_client import text_chat

logger = logging.getLogger(__name__)


def _range_bounds(start_date: date, end_date: date) -> tuple[datetime, datetime]:
    start_dt = datetime.combine(start_date, time.min, tzinfo=timezone.utc)
    end_dt = datetime.combine(end_date, time.max, tzinfo=timezone.utc)
    return start_dt, end_dt


def _fallback_summary(focus_count: int, review_done: int, review_snooze: int, days: int) -> Tuple[str, list[str]]:
    if days == 1:
        text = (
            f"今日学习成果：完成了 {review_done} 次复习，专注 {focus_count} 场{'课程' if focus_count > 1 else '课程'}。"
            f"{'表现稳定，请继续保持节奏。' if review_snooze == 0 else f'有 {review_snooze} 次复习延后，建议适当减少单日负荷。'}"
        )
    else:
        text = (
            f"本周学习概览：完成 {review_done} 次复习，进行 {focus_count} 场专注学习。"
            f"{'整体节奏稳定，坚持即可见效。' if review_snooze <= review_done / 2 else '延后复习较多，建议优化每日规划。'}"
        )
    
    suggestions: list[str] = []
    if focus_count < 2:
        suggestions.append("增加专注学习频次，建议每天安排至少 2 场专注环节")
    if review_snooze > review_done:
        suggestions.append("优先完成到期复习，减少延后次数，提高学习效率")
    if review_done > 0:
        suggestions.append("继续保持当前复习频率，建立长期学习习惯")
    if not suggestions:
        suggestions.append("学习节奏良好，继续按计划进行")
    
    return text, suggestions[:3]


def _build_prompt(focus_count: int, review_done: int, review_snooze: int, days: int) -> str:
    period = "今天" if days == 1 else f"最近 {days} 天"
    return (
        "你是一位专业的学习效率教练。请根据用户的学习数据，生成一份鼓励性且实用的总结报告。\n"
        f"数据统计（{period}）：\n"
        f"- 专注学习场次：{focus_count} 场\n"
        f"- 完成复习卡片：{review_done} 张\n"
        f"- 延后复习卡片：{review_snooze} 张\n\n"
        "请用 JSON 格式输出，包含以下字段：\n"
        '{"text": "一句话总结（≤120字，评价学习状态并提出改进方向）", '
        '"suggestions": ["建议1（动宾结构，具体可行）", "建议2", "建议3"]}'
        "\n注意：\n"
        "1. text 字段必须用中文，言辞鼓励但务实\n"
        "2. suggestions 数组包含 2-3 条动宾结构建议，便于用户立即执行\n"
        "3. 不输出任何 JSON 之外的文字\n"
        "4. 根据数据自动调整建议侧重点（如复习延后多，则建议优化任务量）"
    )


def _llm_summary(
    focus_count: int,
    review_done: int,
    review_snooze: int,
    days: int,
    want_audio: bool,
) -> tuple[str, list[str], str | None, bool, str]:
    settings = get_settings()
    prompt = _build_prompt(focus_count, review_done, review_snooze, days)
    logger.info(
        "LLM_SUMMARY_START days=%s focus=%s review_done=%s review_snooze=%s want_audio=%s model=%s",
        days,
        focus_count,
        review_done,
        review_snooze,
        want_audio,
        settings.qwen_text_model,
    )
    try:
        raw_text = text_chat(prompt)
    except Exception as exc:  # noqa: BLE001
        logger.warning("LLM summary failed, fallback used: %s", exc)
        text, suggestions = _fallback_summary(focus_count, review_done, review_snooze, days)
        logger.warning("LLM_SUMMARY_FALLBACK reason=call_error days=%s", days)
        return text, suggestions, None, False, "call_error"

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
            logger.warning("LLM_SUMMARY_NON_JSON days=%s raw_text_len=%s", days, len(raw_text))

    if not text:
        text, suggestions = _fallback_summary(focus_count, review_done, review_snooze, days)
        logger.warning("LLM_SUMMARY_FALLBACK reason=empty_text days=%s", days)
        return text, suggestions, None, False, "empty_text"

    logger.info(
        "LLM_SUMMARY_OK days=%s text_len=%s suggestions=%s audio=%s",
        days,
        len(text),
        len(suggestions),
        False,
    )
    return text, suggestions, None, True, "ok"


def _collect_stats(db: Session, user_id, start_dt: datetime, end_dt: datetime) -> tuple[int, int, int]:
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
    return focus_count, review_done, review_snooze


def _has_data_changed_since(db: Session, user_id, start_dt: datetime, end_dt: datetime, since: datetime) -> bool:
    new_focus = (
        db.query(FocusSession)
        .filter(
            FocusSession.user_id == user_id,
            FocusSession.started_at >= start_dt,
            FocusSession.started_at <= end_dt,
            FocusSession.started_at > since,
        )
        .count()
    )
    if new_focus > 0:
        return True

    new_review = (
        db.query(ReviewEvent)
        .filter(
            ReviewEvent.user_id == user_id,
            ReviewEvent.occurred_at >= start_dt,
            ReviewEvent.occurred_at <= end_dt,
            ReviewEvent.occurred_at > since,
        )
        .count()
    )
    return new_review > 0


def _is_fallback_cached(summary: AISummary, focus_count: int, review_done: int, review_snooze: int, days: int) -> bool:
    fallback_text, fallback_suggestions = _fallback_summary(focus_count, review_done, review_snooze, days)
    return summary.text == fallback_text and summary.suggestions == fallback_suggestions


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

    start_dt, end_dt = _range_bounds(target_date, target_date)
    focus_count, review_done, review_snooze = _collect_stats(db, user_id, start_dt, end_dt)

    if existing is not None:
        data_changed = _has_data_changed_since(db, user_id, start_dt, end_dt, existing.created_at)
        fallback_cached = _is_fallback_cached(existing, focus_count, review_done, review_snooze, 1)
        if not data_changed and not fallback_cached:
            logger.info("AI_SUMMARY_CACHE_HIT range=daily user_id=%s", user_id)
            return existing
        db.delete(existing)
        db.commit()

    want_audio = get_settings().ai_summary_audio_enabled
    text, suggestions, audio_b64, llm_used, source = _llm_summary(focus_count, review_done, review_snooze, 1, want_audio)
    logger.info(
        "AI_SUMMARY_PERSIST range=daily user_id=%s llm_used=%s source=%s text_len=%s",
        user_id,
        llm_used,
        source,
        len(text),
    )

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

    start_dt, end_dt = _range_bounds(week_start, week_end)
    focus_count, review_done, review_snooze = _collect_stats(db, user_id, start_dt, end_dt)

    if existing is not None:
        data_changed = _has_data_changed_since(db, user_id, start_dt, end_dt, existing.created_at)
        fallback_cached = _is_fallback_cached(existing, focus_count, review_done, review_snooze, 7)
        if not data_changed and not fallback_cached:
            logger.info("AI_SUMMARY_CACHE_HIT range=weekly user_id=%s", user_id)
            return existing
        db.delete(existing)
        db.commit()

    want_audio = get_settings().ai_summary_audio_enabled
    text, suggestions, audio_b64, llm_used, source = _llm_summary(focus_count, review_done, review_snooze, 7, want_audio)
    logger.info(
        "AI_SUMMARY_PERSIST range=weekly user_id=%s llm_used=%s source=%s text_len=%s",
        user_id,
        llm_used,
        source,
        len(text),
    )

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
    try:
        summary_uuid = uuid.UUID(str(summary_id))
    except (ValueError, TypeError):
        return False

    summary = (
        db.query(AISummary)
        .filter(AISummary.id == summary_uuid, AISummary.user_id == user_id)
        .first()
    )
    if not summary:
        return False
    db.delete(summary)
    db.commit()
    return True
