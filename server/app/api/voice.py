import os
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, File, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import http_error
from app.core.security import get_current_principal
from app.db.session import get_db
from app.models.voice import VoiceDraft
from app.schemas.voice import VoiceDraft as VoiceDraftSchema, VoiceDraftCreateResponse
from app.services.voice import process_voice_draft

router = APIRouter(tags=["Voice"])


@router.post("/voice/drafts", response_model=VoiceDraftCreateResponse, status_code=status.HTTP_201_CREATED)
async def upload_voice_draft(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    principal=Depends(get_current_principal),
):
    user, _ = principal
    settings = get_settings()
    os.makedirs(settings.upload_dir, exist_ok=True)

    original_name = file.filename or "voice"
    audio_format = Path(original_name).suffix.lstrip(".").lower() or "bin"
    if audio_format not in {"wav", "mp3"}:
        raise http_error(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "unsupported_audio_format",
            "Only wav/mp3 audio is supported.",
        )

    max_bytes = settings.upload_max_mb * 1024 * 1024
    saved_path = os.path.join(settings.upload_dir, f"{uuid4().hex}.{audio_format}")
    size = 0
    with open(saved_path, "wb") as buffer:
        while True:
            chunk = await file.read(1024 * 1024)
            if not chunk:
                break
            size += len(chunk)
            if size > max_bytes:
                raise http_error(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "payload_too_large", "File exceeds limit")
            buffer.write(chunk)
    await file.close()

    draft = VoiceDraft(
        user_id=user.id,
        audio_format=audio_format,
        status="processing",
        audio_path=saved_path,
    )
    db.add(draft)
    db.commit()
    db.refresh(draft)

    background_tasks.add_task(process_voice_draft, str(draft.id))

    return VoiceDraftCreateResponse(draft_id=str(draft.id), status=draft.status)


@router.get("/voice/drafts/{draft_id}", response_model=VoiceDraftSchema)
def get_voice_draft(
    draft_id: UUID,
    db: Session = Depends(get_db),
    principal=Depends(get_current_principal),
):
    user, _ = principal
    draft = db.get(VoiceDraft, draft_id)
    if draft is None or draft.user_id != user.id:
        raise http_error(status.HTTP_404_NOT_FOUND, "not_found", "Draft not found")

    return VoiceDraftSchema(
        draft_id=str(draft.id),
        audio_format=draft.audio_format,
        status=draft.status,
        created_at=draft.created_at,
        updated_at=draft.updated_at,
        text=draft.text,
        transcript_text=draft.text,
        generated_card_id=str(draft.generated_card_id) if draft.generated_card_id else None,
    )
