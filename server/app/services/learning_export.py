import json
from datetime import datetime, timezone
from io import BytesIO
from typing import Any

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from sqlalchemy.orm import Session

from app.models.card import Card
from app.models.focus import FocusSession
from app.models.review import ReviewEvent
from app.models.timeflow import TimeFlowTemplate
from app.services.qwen_client import stream_chat


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


def _build_export_payload(db: Session, user_id: str) -> dict[str, Any]:
    templates = db.query(TimeFlowTemplate).filter(TimeFlowTemplate.user_id == user_id).all()
    cards = db.query(Card).filter(Card.user_id == user_id).all()
    focus_sessions = db.query(FocusSession).filter(FocusSession.user_id == user_id).all()
    review_events = db.query(ReviewEvent).filter(ReviewEvent.user_id == user_id).all()

    review_done = sum(1 for e in review_events if e.event_type == "done")
    review_snooze = sum(1 for e in review_events if e.event_type == "snooze")

    total_focus_minutes = 0
    for session in focus_sessions:
        duration = int((session.ended_at - session.started_at).total_seconds() // 60)
        if duration > 0:
            total_focus_minutes += duration

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "overview": {
            "template_count": len(templates),
            "card_count": len(cards),
            "active_card_count": sum(1 for c in cards if c.status == "active"),
            "draft_card_count": sum(1 for c in cards if c.status == "draft"),
            "focus_session_count": len(focus_sessions),
            "focus_total_minutes": total_focus_minutes,
            "review_done_count": review_done,
            "review_snooze_count": review_snooze,
        },
        "timeflow_templates": [
            {
                "name": template.name,
                "phases": template.phases,
                "loop": template.loop,
                "created_at": template.created_at.isoformat() if template.created_at else None,
            }
            for template in templates
        ],
        "cards": [
            {
                "front": card.front,
                "back": card.back,
                "tags": card.tags,
                "status": card.status,
                "created_at": card.created_at.isoformat() if card.created_at else None,
            }
            for card in cards
        ],
    }


def _build_summary(payload: dict[str, Any]) -> tuple[str, list[str]]:
    prompt = (
        "你是学习分析助手。请根据 JSON 学习数据，输出 JSON："
        "summary(<=160字), highlights(3条), actions(3条)。"
        "不要输出 JSON 以外的内容。"
        f"数据如下：{json.dumps(payload, ensure_ascii=False)}"
    )

    try:
        raw, _ = stream_chat(prompt, want_audio=False)
        parsed = _safe_json_loads(raw or "") or {}
        summary = str(parsed.get("summary") or "").strip()
        highlights = parsed.get("highlights") if isinstance(parsed.get("highlights"), list) else []
        actions = parsed.get("actions") if isinstance(parsed.get("actions"), list) else []
        bullets = [str(item).strip() for item in [*highlights, *actions] if str(item).strip()]
        if not summary:
            summary = "本周期学习节奏整体稳定，建议保持固定专注时段并优先清理高优先级复习卡片。"
        if not bullets:
            bullets = [
                "优先完成到期复习，减少延后事件。",
                "保持每日至少一次完整专注流程。",
                "每周回顾并精简低价值卡片。",
            ]
        return summary, bullets[:6]
    except Exception:
        return (
            "本周期学习数据已汇总。整体上专注与复习在持续进行，建议优化时间流配置并提升按期复习率。",
            [
                "每天固定时段完成至少一轮专注。",
                "先处理到期卡片，再做新增学习。",
                "每周检查并调整时间流模板。",
            ],
        )


def _draw_wrapped_text(pdf: canvas.Canvas, text: str, x: float, y: float, max_width: float, line_height: float) -> float:
    lines: list[str] = []
    current = ""
    for ch in text:
        trial = current + ch
        if pdf.stringWidth(trial, "Helvetica", 11) <= max_width:
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


def generate_learning_summary_pdf(db: Session, user_id: str) -> bytes:
    payload = _build_export_payload(db, user_id)
    summary_text, bullets = _build_summary(payload)

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    margin_x = 16 * mm
    y = height - 20 * mm

    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(margin_x, y, "KpForU 学习数据总结报告")
    y -= 10 * mm

    pdf.setFont("Helvetica", 10)
    pdf.drawString(margin_x, y, f"Generated At (UTC): {payload['generated_at']}")
    y -= 10 * mm

    overview = payload["overview"]
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(margin_x, y, "数据概览")
    y -= 7 * mm
    pdf.setFont("Helvetica", 11)
    for key, value in overview.items():
        pdf.drawString(margin_x, y, f"- {key}: {value}")
        y -= 6 * mm

    y -= 2 * mm
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(margin_x, y, "AI 总结")
    y -= 7 * mm
    pdf.setFont("Helvetica", 11)
    y = _draw_wrapped_text(pdf, summary_text, margin_x, y, width - 2 * margin_x, 5.2 * mm)

    y -= 2 * mm
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(margin_x, y, "重点建议")
    y -= 7 * mm
    pdf.setFont("Helvetica", 11)
    for item in bullets:
        y = _draw_wrapped_text(pdf, f"- {item}", margin_x, y, width - 2 * margin_x, 5.2 * mm)

    if y < 24 * mm:
        pdf.showPage()
        y = height - 20 * mm

    y -= 4 * mm
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(margin_x, y, "时间流模板")
    y -= 7 * mm
    pdf.setFont("Helvetica", 10)
    for template in payload["timeflow_templates"][:10]:
        line = f"- {template['name']} | phases={len(template['phases'])}"
        pdf.drawString(margin_x, y, line)
        y -= 5.5 * mm
        if y < 20 * mm:
            pdf.showPage()
            y = height - 20 * mm
            pdf.setFont("Helvetica", 10)

    pdf.showPage()
    pdf.save()
    buffer.seek(0)
    return buffer.read()
