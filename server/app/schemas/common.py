from datetime import datetime, date
from typing import Any

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    error: dict


class Pagination(BaseModel):
    next_cursor: str | None = None


class MessageResponse(BaseModel):
    message: str


class Timestamped(BaseModel):
    created_at: datetime | None = Field(default=None)
    updated_at: datetime | None = Field(default=None)


class DateRange(BaseModel):
    start: date
    end: date
