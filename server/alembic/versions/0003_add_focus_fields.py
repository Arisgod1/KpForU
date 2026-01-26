"""add ended_phase_index and manual_confirm_required to focus_sessions

Revision ID: 0003_add_focus_fields
Revises: 0002_add_ai_summary_audio
Create Date: 2026-01-24
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0003_add_focus_fields"
down_revision = "0002_add_ai_summary_audio"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "focus_sessions",
        sa.Column("ended_phase_index", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "focus_sessions",
        sa.Column("manual_confirm_required", sa.Boolean(), nullable=False, server_default=sa.sql.expression.false()),
    )
    # remove server defaults after backfill for cleanliness
    op.alter_column("focus_sessions", "ended_phase_index", server_default=None)
    op.alter_column("focus_sessions", "manual_confirm_required", server_default=None)


def downgrade() -> None:
    op.drop_column("focus_sessions", "manual_confirm_required")
    op.drop_column("focus_sessions", "ended_phase_index")
