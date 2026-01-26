"""add audio fields to ai_summaries

Revision ID: 0002_add_ai_summary_audio
Revises: 0001_initial
Create Date: 2026-01-24
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0002_add_ai_summary_audio"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("ai_summaries", sa.Column("audio_data", sa.Text(), nullable=True))
    op.add_column("ai_summaries", sa.Column("audio_format", sa.String(length=16), nullable=True))


def downgrade() -> None:
    op.drop_column("ai_summaries", "audio_format")
    op.drop_column("ai_summaries", "audio_data")
