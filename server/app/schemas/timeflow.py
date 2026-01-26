from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


PhaseType = Literal["study", "break", "long_break"]


class Phase(BaseModel):
    type: PhaseType
    duration_sec: int = Field(gt=0)
    vibrate_interval_sec: int | None = Field(default=None, description="Optional periodic vibration during study")


class LoopSetting(BaseModel):
    mode: Literal["repeat", "until_time"]
    repeat: int | None = Field(default=None, description="Number of loops if mode=repeat")
    until_time: str | None = Field(default=None, description="HH:MM target end if mode=until_time")


class TimeFlowTemplateCreate(BaseModel):
    name: str
    phases: list[Phase]
    loop: LoopSetting


class TimeFlowTemplate(TimeFlowTemplateCreate):
    id: str
    created_at: datetime
    updated_at: datetime


class PaginatedTimeFlowTemplates(BaseModel):
    data: list[TimeFlowTemplate]
    next_cursor: str | None = None
