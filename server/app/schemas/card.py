from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

CardStatus = Literal["active", "archived", "draft"]


class CardCreate(BaseModel):
    front: str
    back: str
    tags: list[str] = Field(default_factory=list)
    status: CardStatus


class CardUpdate(CardCreate):
    pass


class Card(CardCreate):
    id: str
    created_at: datetime
    updated_at: datetime
    generated_from_draft_id: str | None = None
