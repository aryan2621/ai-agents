"""Initial schema for GitHub Agent."""

from alembic import op
import sqlalchemy as sa

revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("picture", sa.Text(), server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )
    op.create_table(
        "oauth_tokens",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("user_id", sa.String(length=64), sa.ForeignKey("users.id", ondelete="CASCADE"), unique=True),
        sa.Column("access_token", sa.String(length=512), unique=True, index=True),
        sa.Column("github_access_token", sa.Text(), server_default=""),
        sa.Column("refresh_token", sa.Text(), server_default=""),
        sa.Column("expires_at", sa.Integer(), nullable=False),
        sa.Column("granted_scopes", sa.Text(), server_default=""),
    )
    op.create_table(
        "conversations",
        sa.Column("id", sa.String(length=32), primary_key=True),
        sa.Column("user_id", sa.String(length=64), sa.ForeignKey("users.id", ondelete="CASCADE"), index=True),
        sa.Column("title", sa.String(length=255), server_default="New Chat"),
        sa.Column("agent_filter", sa.String(length=32), server_default="github"),
        sa.Column("workspace_context", sa.JSON(), server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )
    op.create_table(
        "messages",
        sa.Column("id", sa.String(length=32), primary_key=True),
        sa.Column("conversation_id", sa.String(length=32), sa.ForeignKey("conversations.id", ondelete="CASCADE"), index=True),
        sa.Column("role", sa.String(length=16), nullable=False),
        sa.Column("content", sa.Text(), server_default=""),
        sa.Column("agent_name", sa.String(length=32), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True)),
    )
    op.create_table(
        "user_settings",
        sa.Column("user_id", sa.String(length=64), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("ollama_base_url", sa.String(length=255), server_default="http://127.0.0.1:11434"),
        sa.Column("default_model", sa.String(length=128), server_default="qwen2.5:7b"),
        sa.Column("temperature", sa.Float(), server_default="0.7"),
        sa.Column("max_tokens", sa.Integer(), server_default="2048"),
        sa.Column("send_on_enter", sa.Boolean(), server_default="true"),
        sa.Column("auto_scroll", sa.Boolean(), server_default="true"),
        sa.Column("font_size", sa.String(length=8), server_default="md"),
        sa.Column("theme", sa.String(length=8), server_default="system"),
        sa.Column("debug_mode", sa.Boolean(), server_default="false"),
        sa.Column("agent_overrides", sa.JSON(), server_default="{}"),
        sa.Column("tavily_search_api_key", sa.String(length=255), server_default=""),
        sa.Column("gemini_api_key", sa.String(length=255), server_default=""),
        sa.Column("groq_api_key", sa.String(length=255), server_default=""),
        sa.Column("onboarding_completed", sa.Boolean(), server_default="false"),
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
        sa.Column("ai_input", sa.JSON(), server_default="{}"),
        sa.Column("ai_output", sa.Text(), server_default=""),
        sa.Column("agent_name", sa.String(length=32), server_default="orchestrator"),
        sa.Column("model", sa.String(length=128), server_default=""),
        sa.Column("routing_method", sa.String(length=32), server_default=""),
        sa.Column("routing_detail", sa.JSON(), server_default="{}"),
        sa.Column("tool_calls", sa.JSON(), server_default="[]"),
        sa.Column("ai_messages", sa.JSON(), server_default="[]"),
        sa.Column("turn_timeline", sa.JSON(), server_default="[]"),
        sa.Column("workspace_context_before", sa.JSON(), server_default="{}"),
        sa.Column("workspace_context_after", sa.JSON(), server_default="{}"),
        sa.Column("latency_ms", sa.Float(), server_default="0"),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), index=True),
    )


def downgrade() -> None:
    op.drop_table("turn_traces")
    op.drop_table("user_settings")
    op.drop_table("messages")
    op.drop_table("conversations")
    op.drop_table("oauth_tokens")
    op.drop_table("users")
