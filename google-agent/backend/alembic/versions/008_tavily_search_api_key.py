"""Rename brave_search_api_key to tavily_search_api_key."""

from alembic import op

revision = "008_tavily_search_api_key"
down_revision = "007_brave_search_api_key"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "user_settings",
        "brave_search_api_key",
        new_column_name="tavily_search_api_key",
    )


def downgrade() -> None:
    op.alter_column(
        "user_settings",
        "tavily_search_api_key",
        new_column_name="brave_search_api_key",
    )
