from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel


class AIDailySummaryRequest(BaseModel):
    date: date


class AIWeeklySummaryRequest(BaseModel):
    week_start: date


class AISummary(BaseModel):
    summary_id: str
    range: Literal["daily", "weekly"]
    range_start: date
    range_end: date
    text: str
    suggestions: list[str]
    audio_base64: str | None = None
    audio_format: str | None = None
    created_at: datetime
