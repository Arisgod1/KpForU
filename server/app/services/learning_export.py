import json
import logging
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from io import BytesIO
from typing import Any

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfgen import canvas
from sqlalchemy.orm import Session

from app.models.card import Card
from app.models.focus import FocusSession
from app.models.review import ReviewEvent
from app.models.timeflow import TimeFlowTemplate
from app.core.config import get_settings
from app.services.qwen_client import text_chat

logger = logging.getLogger(__name__)
settings = get_settings()


def _as_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _safe_json_loads(raw: str) -> dict[str, Any] | None:
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        pass
    start = raw.find("{")
    end = raw.rfind("}")
    if start >= 0 and end > start:
        try:
            parsed = json.loads(raw[start : end + 1])
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            return None
    return None


def _resolve_pdf_font() -> str:
    """Use a built-in CJK font to avoid Chinese garbling in exported PDF."""
    try:
        pdfmetrics.getFont("STSong-Light")
    except KeyError:
        pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
    return "STSong-Light"


def _build_export_payload(db: Session, user_id: str) -> dict[str, Any]:
    templates = db.query(TimeFlowTemplate).filter(TimeFlowTemplate.user_id == user_id).all()
    cards = db.query(Card).filter(Card.user_id == user_id).all()
    focus_sessions = db.query(FocusSession).filter(FocusSession.user_id == user_id).all()
    review_events = db.query(ReviewEvent).filter(ReviewEvent.user_id == user_id).all()

    now = datetime.now(timezone.utc)
    last_7_start = now - timedelta(days=7)
    last_30_start = now - timedelta(days=30)

    review_done = sum(1 for e in review_events if e.event_type == "done")
    review_snooze = sum(1 for e in review_events if e.event_type == "snooze")
    review_done_7d = sum(
        1
        for e in review_events
        if e.event_type == "done" and (_as_utc(e.occurred_at) or datetime.min.replace(tzinfo=timezone.utc)) >= last_7_start
    )
    review_done_30d = sum(
        1
        for e in review_events
        if e.event_type == "done" and (_as_utc(e.occurred_at) or datetime.min.replace(tzinfo=timezone.utc)) >= last_30_start
    )

    total_focus_minutes = 0
    focus_minutes_7d = 0
    focus_minutes_30d = 0
    daily_focus_7d: dict[str, int] = defaultdict(int)
    daily_review_done_7d: dict[str, int] = defaultdict(int)

    for session in focus_sessions:
        started_at_utc = _as_utc(session.started_at)
        ended_at_utc = _as_utc(session.ended_at)
        if started_at_utc is None or ended_at_utc is None:
            continue

        duration = int((ended_at_utc - started_at_utc).total_seconds() // 60)
        if duration > 0:
            total_focus_minutes += duration
            if ended_at_utc >= last_7_start:
                focus_minutes_7d += duration
                daily_focus_7d[ended_at_utc.strftime("%m-%d")] += duration
            if ended_at_utc >= last_30_start:
                focus_minutes_30d += duration

    for event in review_events:
        occurred_at_utc = _as_utc(event.occurred_at)
        if event.event_type == "done" and occurred_at_utc and occurred_at_utc >= last_7_start:
            daily_review_done_7d[occurred_at_utc.strftime("%m-%d")] += 1

    tag_counter: Counter[str] = Counter()
    for card in cards:
        if isinstance(card.tags, list):
            for tag in card.tags:
                t = str(tag).strip()
                if t:
                    tag_counter[t] += 1

    template_snapshots = []
    for template in templates:
        phases = template.phases if isinstance(template.phases, list) else []
        total_minutes = 0
        for p in phases:
            if isinstance(p, dict):
                v = p.get("minutes") or p.get("duration_minutes") or p.get("duration")
                try:
                    total_minutes += int(v)
                except Exception:
                    pass
        template_snapshots.append(
            {
                "name": template.name,
                "phase_count": len(phases),
                "total_minutes": total_minutes,
            }
        )

    top_cards = sorted(cards, key=lambda c: _as_utc(c.created_at) or now, reverse=True)[:8]
    card_snapshots = [
        {
            "front": (card.front or "")[:60],
            "status": card.status,
            "tags": card.tags[:3] if isinstance(card.tags, list) else [],
            "created_at": card.created_at.isoformat() if card.created_at else None,
        }
        for card in top_cards
    ]

    trend_labels = []
    for i in range(6, -1, -1):
        d = (now - timedelta(days=i)).strftime("%m-%d")
        trend_labels.append(d)

    trend_7d = [
        {
            "date": d,
            "focus_minutes": int(daily_focus_7d.get(d, 0)),
            "review_done": int(daily_review_done_7d.get(d, 0)),
        }
        for d in trend_labels
    ]

    return {
        "generated_at": now.isoformat(),
        "period": {
            "last_7_start": last_7_start.date().isoformat(),
            "last_30_start": last_30_start.date().isoformat(),
            "end": now.date().isoformat(),
        },
        "overview": {
            "template_count": len(templates),
            "card_count": len(cards),
            "active_card_count": sum(1 for c in cards if c.status == "active"),
            "draft_card_count": sum(1 for c in cards if c.status == "draft"),
            "focus_session_count": len(focus_sessions),
            "focus_total_minutes": total_focus_minutes,
            "focus_minutes_7d": focus_minutes_7d,
            "focus_minutes_30d": focus_minutes_30d,
            "review_done_count": review_done,
            "review_snooze_count": review_snooze,
            "review_done_7d": review_done_7d,
            "review_done_30d": review_done_30d,
        },
        "top_tags": [{"tag": k, "count": v} for k, v in tag_counter.most_common(8)],
        "trend_7d": trend_7d,
        "timeflow_templates": template_snapshots,
        "cards": card_snapshots,
    }


def _build_summary(payload: dict[str, Any]) -> tuple[str, str, list[str], list[str]]:
    llm_input = {
        "period": payload.get("period", {}),
        "overview": payload.get("overview", {}),
        "top_tags": payload.get("top_tags", []),
        "trend_7d": payload.get("trend_7d", []),
        "template_samples": payload.get("timeflow_templates", [])[:6],
    }

    prompt = (
        "请根据以下学习数据编写一份简明的学习总结报告。\n\n"
        "数据来自用户过去 7 天的学习行为记录（专注时长、复习完成情况、卡片管理状态等）。\n\n"
        "请输出严格的 JSON 格式，只包含以下字段：\n"
        "- headline: 本周学习状态的简要描述（≤20字）\n"
        "- summary: 基于数据的客观总结，包括学习节奏、复习完成度、时间管理现状等（≤220字）\n"
        "- strengths: 用户已经养成的积极行为列表（3条），每条要有具体数据支撑\n"
        "- risks: 从数据观察到的实际问题或潜在风险（2条），陈述事实而非过度解读\n"
        "- actions: 基于现状的具体改进方向（3条），应可直接执行而非空泛理论\n\n"
        "分析原则：\n"
        "1. 基于给定的数据事实，避免猜测和夸大\n"
        "2. strengths 和 risks 应该互补完整地反映学习现状\n"
        "3. actions 应该具体可行，考虑到用户的现有习惯和数据约束\n"
        "4. 保持客观、平衡的语气\n"
        "5. 只输出 JSON，不输出其他文字\n\n"
        f"数据如下：\n{json.dumps(llm_input, ensure_ascii=False, indent=2)}"
    )

    try:
        logger.info(
            "LLM_EXPORT_SUMMARY_START model=%s timeout=%ss",
            settings.qwen_text_model,
            settings.qwen_export_timeout_seconds,
        )
        raw = text_chat(prompt, timeout_seconds=settings.qwen_export_timeout_seconds)
        parsed = _safe_json_loads(raw or "") or {}
        headline = str(parsed.get("headline") or "").strip()
        summary = str(parsed.get("summary") or "").strip()
        strengths = parsed.get("strengths") if isinstance(parsed.get("strengths"), list) else []
        risks = parsed.get("risks") if isinstance(parsed.get("risks"), list) else []
        actions = parsed.get("actions") if isinstance(parsed.get("actions"), list) else []
        strengths_list = [str(item).strip() for item in strengths if str(item).strip()][:3]
        risks_list = [str(item).strip() for item in risks if str(item).strip()][:2]
        actions_list = [str(item).strip() for item in actions if str(item).strip()][:3]

        if not headline:
            headline = "学习进展稳定"
        if not summary:
            summary = "近 7 天学习节奏总体稳定，建议保持固定专注时段并优先处理到期复习卡，提升完成率。"
        if not strengths_list:
            strengths_list = [
                "专注行为持续发生，具备稳定学习习惯。",
                "复习链路完整，卡片管理和复习动作持续进行。",
                "时间流模板已形成基础结构，可持续复用。",
            ]
        if not risks_list:
            risks_list = [
                "复习延后比例偏高时会影响记忆巩固节奏。",
                "若模板与科目负载不匹配，专注效率会下降。",
            ]
        if not actions_list:
            actions_list = [
                "每天固定 1 个高确定性专注时段，先做最难任务。",
                "将到期复习放在每日首个学习块，避免滚雪球式积压。",
                "每周末清理低价值卡片并补充高频错题卡。",
            ]
        logger.info(
            "LLM_EXPORT_SUMMARY_OK summary_len=%s strengths=%s risks=%s actions=%s",
            len(summary),
            len(strengths_list),
            len(risks_list),
            len(actions_list),
        )
        return headline, summary, strengths_list, [*risks_list, *actions_list]
    except Exception:
        logger.exception("LLM_EXPORT_SUMMARY_FALLBACK reason=call_error")
        return (
            "学习进展稳定",
            "本周期学习数据已汇总。整体上专注与复习在持续进行，建议优化时间流配置并提升按期复习率。",
            [
                "专注行为持续发生，具备稳定学习习惯。",
                "卡片体系在持续扩展，复习流程已形成闭环。",
                "学习记录可追踪，便于复盘与优化。",
            ],
            [
                "复习延后比例偏高时会影响记忆巩固节奏。",
                "每天固定时段完成至少一轮专注。",
                "先处理到期卡片，再做新增学习。",
                "每周检查并调整时间流模板。",
            ],
        )


def _draw_wrapped_text(
    pdf: canvas.Canvas,
    text: str,
    x: float,
    y: float,
    max_width: float,
    line_height: float,
    font_name: str,
    font_size: float,
) -> float:
    lines: list[str] = []
    current = ""
    for ch in text:
        trial = current + ch
        if pdf.stringWidth(trial, font_name, font_size) <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = ch
    if current:
        lines.append(current)

    for line in lines:
        pdf.drawString(x, y, line)
        y -= line_height
    return y


def _ensure_page_space(pdf: canvas.Canvas, y: float, need: float, page_height: float, font_name: str) -> float:
    if y - need >= 18 * mm:
        return y
    pdf.showPage()
    pdf.setFont(font_name, 11)
    return page_height - 20 * mm


def _compute_score_cards(payload: dict[str, Any]) -> list[dict[str, Any]]:
    overview = payload.get("overview", {}) if isinstance(payload.get("overview"), dict) else {}
    trend = payload.get("trend_7d", []) if isinstance(payload.get("trend_7d"), list) else []

    focus_values = [int(item.get("focus_minutes", 0)) for item in trend if isinstance(item, dict)]
    if not focus_values:
        focus_stability_score = 0
        focus_note = "近 7 天暂无专注数据"
    else:
        avg = sum(focus_values) / len(focus_values)
        nonzero_days = sum(1 for v in focus_values if v > 0)
        variance = sum((v - avg) ** 2 for v in focus_values) / len(focus_values)
        std = variance ** 0.5
        cv = (std / avg) if avg > 0 else 1.0
        consistency = max(0.0, 1.0 - min(cv, 1.0))
        active_ratio = nonzero_days / max(len(focus_values), 1)
        focus_stability_score = int(round((consistency * 0.6 + active_ratio * 0.4) * 100))
        focus_note = f"活跃 {nonzero_days}/7 天，日均 {avg:.1f} 分钟"

    review_done = int(overview.get("review_done_count", 0))
    review_snooze = int(overview.get("review_snooze_count", 0))
    review_total = review_done + review_snooze
    if review_total == 0:
        review_completion_score = 0
        review_note = "暂无复习事件"
    else:
        rate = review_done / review_total
        review_completion_score = int(round(rate * 100))
        review_note = f"完成 {review_done} / 总计 {review_total}"

    card_count = int(overview.get("card_count", 0))
    active_cards = int(overview.get("active_card_count", 0))
    draft_cards = int(overview.get("draft_card_count", 0))
    top_tags = payload.get("top_tags", []) if isinstance(payload.get("top_tags"), list) else []
    distinct_tags = len(top_tags)

    if card_count <= 0:
        card_health_score = 0
        card_note = "暂无卡片"
    else:
        active_ratio = active_cards / card_count
        draft_penalty = draft_cards / card_count
        diversity = min(distinct_tags / 6, 1.0)
        card_health_score = int(round((active_ratio * 0.6 + diversity * 0.3 + (1 - draft_penalty) * 0.1) * 100))
        card_note = f"激活 {active_cards}/{card_count}，标签类型 {distinct_tags}"

    return [
        {"name": "专注稳定度", "score": max(0, min(100, focus_stability_score)), "note": focus_note},
        {"name": "复习完成率", "score": max(0, min(100, review_completion_score)), "note": review_note},
        {"name": "卡片健康度", "score": max(0, min(100, card_health_score)), "note": card_note},
    ]


def _draw_trend_barchart(
    pdf: canvas.Canvas,
    trend_rows: list[dict[str, Any]],
    x: float,
    y: float,
    chart_width: float,
    font_name: str,
) -> float:
    if not trend_rows:
        pdf.drawString(x, y, "- 暂无趋势数据")
        return y - 6 * mm

    bar_h = 4.2 * mm
    row_gap = 2.2 * mm
    label_w = 16 * mm
    value_w = 20 * mm
    max_focus = max(int(r.get("focus_minutes", 0)) for r in trend_rows)
    max_focus = max(max_focus, 1)
    usable_w = max(chart_width - label_w - value_w, 30 * mm)

    for row in trend_rows:
        date_text = str(row.get("date", "--"))
        focus_minutes = int(row.get("focus_minutes", 0))
        review_done = int(row.get("review_done", 0))
        bar_w = usable_w * (focus_minutes / max_focus)

        pdf.setFillColor(colors.HexColor("#4A90E2"))
        pdf.rect(x + label_w, y - bar_h + 1, bar_w, bar_h, stroke=0, fill=1)
        pdf.setFillColor(colors.black)
        pdf.setFont(font_name, 10)
        pdf.drawString(x, y - 2, date_text)
        pdf.drawString(
            x + label_w + usable_w + 2 * mm,
            y - 2,
            f"{focus_minutes}m / 复习{review_done}",
        )
        y -= bar_h + row_gap

    pdf.setFont(font_name, 9)
    pdf.drawString(x, y - 1, f"注：蓝色柱表示专注分钟数，基准最大值 {max_focus} 分钟")
    return y - 5 * mm


def _draw_score_cards(
    pdf: canvas.Canvas,
    score_cards: list[dict[str, Any]],
    x: float,
    y: float,
    width: float,
    font_name: str,
) -> float:
    box_h = 18 * mm
    gap = 3 * mm
    count = max(len(score_cards), 1)
    box_w = (width - gap * (count - 1)) / count

    for idx, item in enumerate(score_cards):
        bx = x + idx * (box_w + gap)
        score = int(item.get("score", 0))
        name = str(item.get("name", "评分"))
        note = str(item.get("note", ""))

        if score >= 80:
            fill = colors.HexColor("#E8F5E9")
            accent = colors.HexColor("#2E7D32")
        elif score >= 60:
            fill = colors.HexColor("#FFF8E1")
            accent = colors.HexColor("#F9A825")
        else:
            fill = colors.HexColor("#FFEBEE")
            accent = colors.HexColor("#C62828")

        pdf.setStrokeColor(colors.HexColor("#D9D9D9"))
        pdf.setFillColor(fill)
        pdf.roundRect(bx, y - box_h, box_w, box_h, 2 * mm, stroke=1, fill=1)

        pdf.setFillColor(colors.black)
        pdf.setFont(font_name, 10)
        pdf.drawString(bx + 2 * mm, y - 5 * mm, name)

        pdf.setFillColor(accent)
        pdf.setFont(font_name, 14)
        pdf.drawString(bx + 2 * mm, y - 10.5 * mm, f"{score}")

        pdf.setFillColor(colors.black)
        pdf.setFont(font_name, 8.5)
        note_short = note[:16] + ("..." if len(note) > 16 else "")
        pdf.drawString(bx + 2 * mm, y - 15.5 * mm, note_short)

    return y - box_h - 3 * mm


def generate_learning_summary_pdf(db: Session, user_id: str) -> bytes:
    logger.info("LEARNING_PDF_EXPORT_START user_id=%s", user_id)
    payload = _build_export_payload(db, user_id)
    headline, summary_text, strengths, bullets = _build_summary(payload)
    score_cards = _compute_score_cards(payload)
    font_name = _resolve_pdf_font()

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    margin_x = 16 * mm
    y = height - 20 * mm

    pdf.setFont(font_name, 16)
    pdf.drawString(margin_x, y, "KpForU 学习报告（AI 增强）")
    y -= 10 * mm

    pdf.setFont(font_name, 10)
    pdf.drawString(margin_x, y, f"生成时间（UTC）：{payload['generated_at']}")
    period = payload.get("period", {})
    y -= 6 * mm
    pdf.drawString(
        margin_x,
        y,
        f"统计区间：{period.get('last_30_start', '-') } 至 {period.get('end', '-') }（近 30 天）",
    )
    y -= 10 * mm

    overview = payload["overview"]
    total_focus_minutes = int(overview.get("focus_total_minutes", 0))
    focus_hours = total_focus_minutes // 60
    focus_minutes = total_focus_minutes % 60
    focus_count = int(overview.get("focus_session_count", 0))
    review_done = int(overview.get("review_done_count", 0))
    review_snooze = int(overview.get("review_snooze_count", 0))
    review_total = review_done + review_snooze
    done_rate = (review_done / review_total * 100) if review_total > 0 else 0.0
    avg_focus_minutes = (total_focus_minutes / focus_count) if focus_count > 0 else 0.0
    focus_7d = int(overview.get("focus_minutes_7d", 0))
    review_done_7d = int(overview.get("review_done_7d", 0))

    pdf.setFont(font_name, 13)
    pdf.drawString(margin_x, y, "关键指标")
    y -= 7 * mm
    pdf.setFont(font_name, 11)
    total_lines = [
        f"- 报告标题：{headline}",
        f"- 近 7 天专注时长：{focus_7d} 分钟",
        f"- 近 7 天复习完成：{review_done_7d} 次",
        f"- 专注总次数：{focus_count}",
        f"- 专注总时长：{focus_hours} 小时 {focus_minutes} 分钟（{total_focus_minutes} 分钟）",
        f"- 平均单次专注：{avg_focus_minutes:.1f} 分钟",
        f"- 复习总次数：{review_total}（完成 {review_done}，延后 {review_snooze}）",
        f"- 复习完成率：{done_rate:.1f}%",
        f"- 卡片总数：{int(overview.get('card_count', 0))}（激活 {int(overview.get('active_card_count', 0))}，草稿 {int(overview.get('draft_card_count', 0))}）",
        f"- 时间流模板数：{int(overview.get('template_count', 0))}",
    ]
    for line in total_lines:
        y = _ensure_page_space(pdf, y, 8 * mm, height, font_name)
        pdf.drawString(margin_x, y, line)
        y -= 6 * mm

    y -= 1 * mm
    y = _ensure_page_space(pdf, y, 26 * mm, height, font_name)
    pdf.setFont(font_name, 13)
    pdf.drawString(margin_x, y, "学习评分卡")
    y -= 4 * mm
    y = _draw_score_cards(pdf, score_cards, margin_x, y, width - 2 * margin_x, font_name)

    y -= 2 * mm
    y = _ensure_page_space(pdf, y, 52 * mm, height, font_name)
    pdf.setFont(font_name, 13)
    pdf.drawString(margin_x, y, "近 7 天趋势")
    y -= 7 * mm
    y = _draw_trend_barchart(
        pdf,
        payload.get("trend_7d", []),
        margin_x,
        y,
        width - 2 * margin_x,
        font_name,
    )

    y -= 2 * mm
    y = _ensure_page_space(pdf, y, 30 * mm, height, font_name)
    pdf.setFont(font_name, 13)
    pdf.drawString(margin_x, y, "标签分布（Top）")
    y -= 7 * mm
    pdf.setFont(font_name, 11)
    tags = payload.get("top_tags", [])
    if not tags:
        pdf.drawString(margin_x, y, "- 暂无标签数据")
        y -= 6 * mm
    else:
        for item in tags:
            y = _ensure_page_space(pdf, y, 8 * mm, height, font_name)
            pdf.drawString(margin_x, y, f"- {item.get('tag', '未分类')}：{int(item.get('count', 0))} 张")
            y -= 6 * mm

    y -= 2 * mm
    y = _ensure_page_space(pdf, y, 30 * mm, height, font_name)
    pdf.setFont(font_name, 13)
    pdf.drawString(margin_x, y, "AI 总结")
    y -= 7 * mm
    pdf.setFont(font_name, 11)
    y = _draw_wrapped_text(pdf, summary_text, margin_x, y, width - 2 * margin_x, 5.2 * mm, font_name, 11)

    y -= 2 * mm
    y = _ensure_page_space(pdf, y, 24 * mm, height, font_name)
    pdf.setFont(font_name, 13)
    pdf.drawString(margin_x, y, "优势观察")
    y -= 7 * mm
    pdf.setFont(font_name, 11)
    for item in strengths:
        y = _ensure_page_space(pdf, y, 8 * mm, height, font_name)
        y = _draw_wrapped_text(pdf, f"- {item}", margin_x, y, width - 2 * margin_x, 5.2 * mm, font_name, 11)

    y -= 2 * mm
    y = _ensure_page_space(pdf, y, 24 * mm, height, font_name)
    pdf.setFont(font_name, 13)
    pdf.drawString(margin_x, y, "风险与行动建议")
    y -= 7 * mm
    pdf.setFont(font_name, 11)
    for item in bullets:
        y = _ensure_page_space(pdf, y, 8 * mm, height, font_name)
        y = _draw_wrapped_text(pdf, f"- {item}", margin_x, y, width - 2 * margin_x, 5.2 * mm, font_name, 11)

    y -= 4 * mm
    y = _ensure_page_space(pdf, y, 24 * mm, height, font_name)
    pdf.setFont(font_name, 13)
    pdf.drawString(margin_x, y, "时间流模板概览")
    y -= 7 * mm
    pdf.setFont(font_name, 11)
    for template in payload["timeflow_templates"][:10]:
        line = (
            f"- {template.get('name', '未命名模板')} | 阶段 {int(template.get('phase_count', 0))} 个"
            f" | 预计 {int(template.get('total_minutes', 0))} 分钟"
        )
        y = _ensure_page_space(pdf, y, 8 * mm, height, font_name)
        pdf.drawString(margin_x, y, line)
        y -= 5.5 * mm

    y -= 2 * mm
    y = _ensure_page_space(pdf, y, 24 * mm, height, font_name)
    pdf.setFont(font_name, 13)
    pdf.drawString(margin_x, y, "近期新增卡片样本")
    y -= 7 * mm
    pdf.setFont(font_name, 10)
    cards = payload.get("cards", [])
    if not cards:
        pdf.drawString(margin_x, y, "- 暂无卡片样本")
    else:
        for card in cards:
            y = _ensure_page_space(pdf, y, 10 * mm, height, font_name)
            tags_text = ",".join(card.get("tags", [])[:3]) if isinstance(card.get("tags", []), list) else ""
            text = f"- {card.get('front', '')} | 状态={card.get('status', '')} | 标签={tags_text}"
            y = _draw_wrapped_text(pdf, text, margin_x, y, width - 2 * margin_x, 4.8 * mm, font_name, 10)

    pdf.showPage()
    pdf.save()
    buffer.seek(0)
    data = buffer.read()
    logger.info("LEARNING_PDF_EXPORT_OK user_id=%s bytes=%s", user_id, len(data))
    return data
