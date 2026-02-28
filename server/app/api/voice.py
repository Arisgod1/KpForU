import os
from datetime import datetime, timezone
from uuid import UUID

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

    max_bytes = settings.upload_max_mb * 1024 * 1024
    saved_path = os.path.join(settings.upload_dir, file.filename or "voice")
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

    audio_format = (file.filename or "").split(".")[-1] or "bin"
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
