from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.card import Card

ReviewEventType = Literal["done", "snooze"]
ReviewEventSource = Literal["watch", "phone"]
DueState = Literal["due", "not_due"]


class ReviewSchedule(BaseModel):
    card_id: str
    box: int
    next_review_at: datetime
    interval_days: int
    due_state: DueState


class DueListItem(BaseModel):
    card: Card
    schedule: ReviewSchedule


class DueListResponse(BaseModel):
    date: date
    due_count: int
    data: list[DueListItem]


class ReviewEventCreate(BaseModel):
    card_id: UUID
    event_type: ReviewEventType
    occurred_at: datetime
    source: ReviewEventSource
    snooze_days: int | None = Field(default=None, description="Only for snooze")


class ReviewEventResponse(BaseModel):
    event_id: str
    card_id: str
    box: int
    next_review_at: datetime
    interval_days: int


class TodayMetrics(BaseModel):
    planned: int
    done: int


class WatchReviewMetrics(BaseModel):
    today: TodayMetrics
    next_review_at: datetime | None
    countdown_sec: int | None
