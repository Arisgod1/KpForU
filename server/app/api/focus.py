from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session

from app.core.errors import http_error
from app.core.security import get_current_principal
from app.db.session import get_db
from app.models.focus import FocusSession
from app.schemas.focus import (
    FocusSession as FocusSessionSchema,
    FocusSessionCreate,
    FocusSessionCreateResponse,
    PaginatedFocusSessions,
)

router = APIRouter(tags=["Focus"])


@router.post("/focus/sessions", response_model=FocusSessionCreateResponse, status_code=status.HTTP_201_CREATED)
def create_focus_session(
    payload: FocusSessionCreate,
    db: Session = Depends(get_db),
    principal=Depends(get_current_principal),
):
    user, device = principal

    # Idempotency by client_generated_id within the same user
    if payload.client_generated_id:
        existing = (
            db.query(FocusSession)
            .filter(
                FocusSession.user_id == user.id,
                FocusSession.client_generated_id == payload.client_generated_id,
            )
            .first()
        )
        if existing:
            return FocusSessionCreateResponse(session_id=str(existing.id), created=False)

    session = FocusSession(
        user_id=user.id,
        device_id=device.id if device else None,
        template_snapshot=payload.template_snapshot.model_dump(),
        started_at=payload.started_at,
        ended_at=payload.ended_at,
        ended_reason=payload.ended_reason,
        ended_phase_index=payload.ended_phase_index,
        manual_confirm_required=payload.manual_confirm_required,
        saved_confirmed=payload.saved_confirmed,
        client_generated_id=payload.client_generated_id,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return FocusSessionCreateResponse(session_id=str(session.id), created=True)


@router.get("/focus/sessions", response_model=PaginatedFocusSessions)
def list_focus_sessions(
    request: Request,
    from_date: str | None = Query(default=None, alias="from"),
    to_date: str | None = Query(default=None, alias="to"),
    cursor: str | None = Query(default=None),
    limit: int = Query(default=20, le=100),
    db: Session = Depends(get_db),
    principal=Depends(get_current_principal),
):
    user, _ = principal
    query = db.query(FocusSession).filter(FocusSession.user_id == user.id).order_by(FocusSession.started_at.desc())
    if from_date:
        try:
            query = query.filter(FocusSession.started_at >= datetime.fromisoformat(from_date))
        except ValueError:
            pass
    if to_date:
        try:
            query = query.filter(FocusSession.started_at <= datetime.fromisoformat(to_date))
        except ValueError:
            pass
    if cursor:
        try:
            cursor_dt = datetime.fromisoformat(cursor)
            query = query.filter(FocusSession.started_at < cursor_dt)
        except ValueError:
            pass
    items = query.limit(limit + 1).all()
    next_cursor = None
    if len(items) > limit:
        next_cursor = items[-1].started_at.isoformat()
        items = items[:limit]
    data = [
        FocusSessionSchema(
            id=str(i.id),
            template_snapshot=i.template_snapshot,
            started_at=i.started_at,
            ended_at=i.ended_at,
            ended_reason=i.ended_reason,
            ended_phase_index=i.ended_phase_index,
            manual_confirm_required=i.manual_confirm_required,
            saved_confirmed=i.saved_confirmed,
            client_generated_id=i.client_generated_id,
        )
        for i in items
    ]
    return PaginatedFocusSessions(data=data, next_cursor=next_cursor)


@router.delete("/focus/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_focus_session(
    session_id: UUID,
    db: Session = Depends(get_db),
    principal=Depends(get_current_principal),
):
    user, _ = principal
    session = db.query(FocusSession).filter(FocusSession.id == session_id, FocusSession.user_id == user.id).first()
    if not session:
        raise http_error(status.HTTP_404_NOT_FOUND, "Focus session not found")
    db.delete(session)
    db.commit()
    return None
