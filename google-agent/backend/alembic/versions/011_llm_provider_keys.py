"""Add Gemini and Groq API key columns to user_settings."""

import sqlalchemy as sa
from alembic import op

revision = "011_llm_provider_keys"
down_revision = "010_default_model_ministral"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "user_settings",
        sa.Column("gemini_api_key", sa.String(length=255), server_default="", nullable=False),
    )
    op.add_column(
        "user_settings",
        sa.Column("groq_api_key", sa.String(length=255), server_default="", nullable=False),
    )


def downgrade() -> None:
    op.drop_column("user_settings", "groq_api_key")
    op.drop_column("user_settings", "gemini_api_key")
