"""Add debug_mode setting and turn_traces table."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "005_debug_traces"
down_revision = "004_tiered_qwen_models"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "user_settings",
        sa.Column("debug_mode", sa.Boolean(), server_default="false", nullable=False),
    )
    op.create_table(
        "turn_traces",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=64), sa.ForeignKey("users.id", ondelete="CASCADE"), index=True),
        sa.Column(
            "conversation_id",
            sa.String(length=32),
            sa.ForeignKey("conversations.id", ondelete="CASCADE"),
            index=True,
        ),
        sa.Column("assistant_message_id", sa.String(length=32), nullable=True),
        sa.Column("user_input", sa.Text(), server_default=""),
        sa.Column("ai_input", postgresql.JSONB(), server_default="{}"),
        sa.Column("ai_output", sa.Text(), server_default=""),
        sa.Column("agent_name", sa.String(length=32), server_default="orchestrator"),
        sa.Column("model", sa.String(length=128), server_default=""),
        sa.Column("routing_method", sa.String(length=32), server_default=""),
        sa.Column("routing_detail", postgresql.JSONB(), server_default="{}"),
        sa.Column("tool_calls", postgresql.JSONB(), server_default="[]"),
        sa.Column("workspace_context_before", postgresql.JSONB(), server_default="{}"),
        sa.Column("workspace_context_after", postgresql.JSONB(), server_default="{}"),
        sa.Column("latency_ms", sa.Float(), server_default="0"),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), index=True),
    )


def downgrade() -> None:
    op.drop_table("turn_traces")
    op.drop_column("user_settings", "debug_mode")
