from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.security import get_current_principal
from app.db.session import get_db
from app.schemas.ai import AIDailySummaryRequest, AIWeeklySummaryRequest, AISummary as AISummarySchema
from app.services.ai_summary import (
    delete_summary,
    get_or_create_daily_summary,
    get_or_create_weekly_summary,
    list_summaries,
)

router = APIRouter(tags=["AI"])


@router.post("/ai/summaries/daily", response_model=AISummarySchema)
def daily_summary(
    payload: AIDailySummaryRequest,
    db: Session = Depends(get_db),
    principal=Depends(get_current_principal),
):
    user, _ = principal
    summary = get_or_create_daily_summary(db, user.id, payload.date)
    return AISummarySchema(
        summary_id=str(summary.id),
        range=summary.range,
        range_start=summary.range_start,
        range_end=summary.range_end,
        text=summary.text,
        suggestions=summary.suggestions,
        audio_base64=summary.audio_data,
        audio_format=summary.audio_format,
        created_at=summary.created_at,
    )


@router.post("/ai/summaries/weekly", response_model=AISummarySchema)
def weekly_summary(
    payload: AIWeeklySummaryRequest,
    db: Session = Depends(get_db),
    principal=Depends(get_current_principal),
):
    user, _ = principal
    summary = get_or_create_weekly_summary(db, user.id, payload.week_start)
    return AISummarySchema(
        summary_id=str(summary.id),
        range=summary.range,
        range_start=summary.range_start,
        range_end=summary.range_end,
        text=summary.text,
        suggestions=summary.suggestions,
        audio_base64=summary.audio_data,
        audio_format=summary.audio_format,
        created_at=summary.created_at,
    )


@router.get("/ai/summaries", response_model=list[AISummarySchema])
def list_ai_summaries(
    range: str | None = Query(default=None, regex="^(daily|weekly)$"),
    limit: int = Query(default=50, le=200),
    db: Session = Depends(get_db),
    principal=Depends(get_current_principal),
):
    user, _ = principal
    items = list_summaries(db, user.id, range_filter=range, limit=limit)
    return [
        AISummarySchema(
            summary_id=str(s.id),
            range=s.range,
            range_start=s.range_start,
            range_end=s.range_end,
            text=s.text,
            suggestions=s.suggestions,
            audio_base64=s.audio_data,
            audio_format=s.audio_format,
            created_at=s.created_at,
        )
        for s in items
    ]


@router.delete("/ai/summaries/{summary_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ai_summary(
    summary_id: str,
    db: Session = Depends(get_db),
    principal=Depends(get_current_principal),
):
    user, _ = principal
    ok = delete_summary(db, user.id, summary_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Summary not found")
    return None
