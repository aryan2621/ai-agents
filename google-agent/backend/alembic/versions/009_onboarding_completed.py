"""Add onboarding_completed to user_settings."""

from alembic import op
import sqlalchemy as sa


revision = "009_onboarding_completed"
down_revision = "008_tavily_search_api_key"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "user_settings",
        sa.Column("onboarding_completed", sa.Boolean(), server_default=sa.false(), nullable=False),
    )


def downgrade() -> None:
    op.drop_column("user_settings", "onboarding_completed")
