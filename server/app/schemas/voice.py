from datetime import datetime

from pydantic import BaseModel


class VoiceDraftCreateResponse(BaseModel):
    draft_id: str
    status: str


class VoiceDraft(BaseModel):
    draft_id: str
    audio_format: str
    status: str
    created_at: datetime
    updated_at: datetime
    text: str | None = None
    generated_card_id: str | None = None
