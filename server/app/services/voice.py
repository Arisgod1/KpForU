from datetime import datetime, timezone

from app.db.session import SessionLocal
from app.models.card import Card
from app.models.voice import VoiceDraft


def process_voice_draft(draft_id: str):
    db = SessionLocal()
    try:
        draft = db.get(VoiceDraft, draft_id)
        if draft is None:
            return
        # Stub transcription logic
        transcription = f"Transcription for draft {draft.id}"
        draft.text = transcription
        draft.status = "done"
        draft.updated_at = datetime.now(timezone.utc)

        # Auto-create draft card for user
        card = Card(
            user_id=draft.user_id,
            front=transcription,
            back="",
            tags=[],
            status="draft",
            generated_from_draft_id=draft.id,
        )
        db.add(card)
        db.flush()
        draft.generated_card_id = card.id

        db.commit()
    finally:
        db.close()
