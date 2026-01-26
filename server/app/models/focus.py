import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class FocusSession(Base):
    __tablename__ = "focus_sessions"
    __table_args__ = (
        UniqueConstraint("user_id", "client_generated_id", name="uq_focus_client"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    device_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("devices.id"), nullable=True)
    template_snapshot: Mapped[dict] = mapped_column(JSON)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ended_reason: Mapped[str] = mapped_column(String(32))
    ended_phase_index: Mapped[int] = mapped_column(Integer, default=0)
    manual_confirm_required: Mapped[bool] = mapped_column(Boolean, default=False)
    saved_confirmed: Mapped[bool] = mapped_column()
    client_generated_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    user = relationship("User")
    device = relationship("Device")
