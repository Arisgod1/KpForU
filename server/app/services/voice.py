from datetime import datetime, timezone, timedelta
import logging
from uuid import UUID

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models.card import Card
from app.models.review import ReviewSchedule
from app.models.voice import VoiceDraft
from app.services.qwen_client import generate_card_from_audio

logger = logging.getLogger(__name__)


def process_voice_draft(draft_id: str):
    logger.info("VOICE_DRAFT_PROCESS_START draft_id=%s", draft_id)
    db = SessionLocal()
    try:
        draft = db.get(VoiceDraft, UUID(str(draft_id)))
        if draft is None:
            logger.warning("VOICE_DRAFT_PROCESS_SKIP draft_id=%s reason=not_found", draft_id)
            return
        if not draft.audio_path:
            draft.status = "failed"
            draft.text = "音频路径缺失"
            draft.updated_at = datetime.now(timezone.utc)
            db.commit()
            logger.warning("VOICE_DRAFT_PROCESS_FAIL draft_id=%s reason=missing_audio_path", draft_id)
            return

        try:
            with open(draft.audio_path, "rb") as audio_file:
                audio_bytes = audio_file.read()
            front, back, tags, transcript = generate_card_from_audio(audio_bytes, draft.audio_format)
            draft.text = transcript
            draft.status = "done"
            logger.info(
                "VOICE_DRAFT_LLM_OK draft_id=%s transcript_len=%s tags=%s",
                draft_id,
                len(transcript),
                len(tags),
            )
        except Exception as exc:  # noqa: BLE001
            fallback_text = f"语音处理失败：{exc}"
            draft.text = fallback_text
            draft.status = "done"
            front = "语音学习卡片（待完善）"
            back = fallback_text
            tags = ["语音", "待编辑"]
            logger.exception("VOICE_DRAFT_LLM_FALLBACK draft_id=%s", draft_id)

        draft.updated_at = datetime.now(timezone.utc)

        card = Card(
            user_id=draft.user_id,
            front=front,
            back=back,
            tags=tags,
            status="active",
            generated_from_draft_id=draft.id,
        )
        db.add(card)
        db.flush()

        settings = get_settings()
        interval_days = settings.leitner_intervals.get(1, 1)
        schedule = ReviewSchedule(
            card_id=card.id,
            user_id=draft.user_id,
            box=1,
            next_review_at=datetime.now(timezone.utc) + timedelta(days=interval_days),
            interval_days=interval_days,
        )
        db.add(schedule)

        draft.generated_card_id = card.id

        db.commit()
        logger.info("VOICE_DRAFT_PROCESS_OK draft_id=%s generated_card_id=%s", draft_id, card.id)
    finally:
        db.close()
