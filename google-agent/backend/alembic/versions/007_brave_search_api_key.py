"""Add brave_search_api_key to user_settings."""

from alembic import op
import sqlalchemy as sa

revision = "007_brave_search_api_key"
down_revision = "006_trace_timeline"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "user_settings",
        sa.Column("brave_search_api_key", sa.String(length=255), server_default="", nullable=False),
    )


def downgrade() -> None:
    op.drop_column("user_settings", "brave_search_api_key")
