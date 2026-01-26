from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.timeflow import LoopSetting, Phase

FocusEndedReason = Literal["natural", "user_ended"]


class TimeFlowTemplateSnapshot(BaseModel):
    name: str
    phases: list[Phase]
    loop: LoopSetting


class FocusSessionCreate(BaseModel):
    template_snapshot: TimeFlowTemplateSnapshot
    started_at: datetime
    ended_at: datetime
    ended_reason: FocusEndedReason
    ended_phase_index: int = 0
    manual_confirm_required: bool = False
    saved_confirmed: bool
    client_generated_id: str | None = Field(default=None)


class FocusSessionCreateResponse(BaseModel):
    session_id: str
    created: bool


class FocusSession(BaseModel):
    id: str
    template_snapshot: TimeFlowTemplateSnapshot
    started_at: datetime
    ended_at: datetime
    ended_reason: FocusEndedReason
    ended_phase_index: int = 0
    manual_confirm_required: bool = False
    saved_confirmed: bool
    client_generated_id: str | None = None


class PaginatedFocusSessions(BaseModel):
    data: list[FocusSession]
    next_cursor: str | None = None
