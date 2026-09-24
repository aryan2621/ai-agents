"""Restore Ollama as the primary local LLM."""

import sqlalchemy as sa
from alembic import op

revision = "012_ollama_primary"
down_revision = "011_llm_provider_keys"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {col["name"] for col in inspector.get_columns("user_settings")}
    if "ollama_base_url" not in columns:
        op.add_column(
            "user_settings",
            sa.Column(
                "ollama_base_url",
                sa.String(length=255),
                server_default="http://127.0.0.1:11434",
                nullable=False,
            ),
        )
    op.execute(
        "UPDATE user_settings SET default_model = 'qwen2.5:7b' "
        "WHERE default_model IN ('gemini-2.5-flash', 'gemini-2.0-flash', 'gemini-flash')"
    )


def downgrade() -> None:
    op.execute(
        "UPDATE user_settings SET default_model = 'gemini-2.5-flash' "
        "WHERE default_model = 'qwen2.5:7b'"
    )
