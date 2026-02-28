from datetime import datetime, timezone
from uuid import UUID

from app.db.session import SessionLocal
from app.models.card import Card
from app.models.voice import VoiceDraft
from app.services.qwen_client import generate_card_from_audio


def process_voice_draft(draft_id: str):
    db = SessionLocal()
    try:
        draft = db.get(VoiceDraft, UUID(str(draft_id)))
        if draft is None:
            return
        if not draft.audio_path:
            draft.status = "failed"
            draft.text = "音频路径缺失"
            draft.updated_at = datetime.now(timezone.utc)
            db.commit()
            return

        try:
            with open(draft.audio_path, "rb") as audio_file:
                audio_bytes = audio_file.read()
            front, back, tags, transcript = generate_card_from_audio(audio_bytes, draft.audio_format)
            draft.text = transcript
            draft.status = "done"
        except Exception as exc:  # noqa: BLE001
            fallback_text = f"语音处理失败：{exc}"
            draft.text = fallback_text
            draft.status = "done"
            front = "语音学习卡片（待完善）"
            back = fallback_text
            tags = ["语音", "待编辑"]

        draft.updated_at = datetime.now(timezone.utc)

        card = Card(
            user_id=draft.user_id,
            front=front,
            back=back,
            tags=tags,
            status="draft",
            generated_from_draft_id=draft.id,
        )
        db.add(card)
        db.flush()
        draft.generated_card_id = card.id

        db.commit()
    finally:
        db.close()
