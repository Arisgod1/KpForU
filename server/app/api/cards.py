from datetime import datetime, timezone, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import http_error
from app.core.security import get_current_principal
from app.db.session import get_db
from app.models.card import Card
from app.models.review import ReviewSchedule
from app.schemas.card import Card as CardSchema, CardCreate, CardUpdate

router = APIRouter(tags=["Cards"])


@router.post("/cards", response_model=CardSchema, status_code=status.HTTP_201_CREATED)
def create_card(
    payload: CardCreate,
    db: Session = Depends(get_db),
    principal=Depends(get_current_principal),
):
    user, _ = principal
    card = Card(
        user_id=user.id,
        front=payload.front,
        back=payload.back,
        tags=payload.tags,
        status=payload.status,
    )
    db.add(card)
    db.flush()

    if payload.status == "active":
        settings = get_settings()
        interval_days = settings.leitner_intervals.get(1, 1)
        schedule = ReviewSchedule(
            card_id=card.id,
            user_id=user.id,
            box=1,
            next_review_at=datetime.now(timezone.utc) + timedelta(days=interval_days),
            interval_days=interval_days,
        )
        db.add(schedule)

    db.commit()
    db.refresh(card)

    return CardSchema(
        id=str(card.id),
        front=card.front,
        back=card.back,
        tags=card.tags,
        status=card.status,
        created_at=card.created_at,
        updated_at=card.updated_at,
        generated_from_draft_id=str(card.generated_from_draft_id) if card.generated_from_draft_id else None,
    )


@router.put("/cards/{card_id}", response_model=CardSchema)
def update_card(
    card_id: UUID,
    payload: CardUpdate,
    db: Session = Depends(get_db),
    principal=Depends(get_current_principal),
):
    user, _ = principal
    card = db.query(Card).filter(Card.id == card_id, Card.user_id == user.id).first()
    if card is None:
        raise http_error(status.HTTP_404_NOT_FOUND, "not_found", "Card not found")

    card.front = payload.front
    card.back = payload.back
    card.tags = payload.tags
    card.status = payload.status

    if payload.status == "active":
        schedule = db.get(ReviewSchedule, card.id)
        if schedule is None:
            settings = get_settings()
            interval_days = settings.leitner_intervals.get(1, 1)
            schedule = ReviewSchedule(
                card_id=card.id,
                user_id=user.id,
                box=1,
                next_review_at=datetime.now(timezone.utc) + timedelta(days=interval_days),
                interval_days=interval_days,
            )
            db.add(schedule)

    db.commit()
    db.refresh(card)

    return CardSchema(
        id=str(card.id),
        front=card.front,
        back=card.back,
        tags=card.tags,
        status=card.status,
        created_at=card.created_at,
        updated_at=card.updated_at,
        generated_from_draft_id=str(card.generated_from_draft_id) if card.generated_from_draft_id else None,
    )
