"""Add ai_messages and turn_timeline to turn_traces."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "006_trace_timeline"
down_revision = "005_debug_traces"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "turn_traces",
        sa.Column("ai_messages", postgresql.JSONB(), server_default="[]", nullable=False),
    )
    op.add_column(
        "turn_traces",
        sa.Column("turn_timeline", postgresql.JSONB(), server_default="[]", nullable=False),
    )


def downgrade() -> None:
    op.drop_column("turn_traces", "turn_timeline")
    op.drop_column("turn_traces", "ai_messages")
