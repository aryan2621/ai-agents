"""Migrate default LLM from llama to qwen2.5:7b."""

from alembic import op

revision = "002_default_model_qwen"
down_revision = "001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "UPDATE user_settings SET default_model = 'qwen2.5:7b' "
        "WHERE default_model ILIKE 'llama%'"
    )


def downgrade() -> None:
    pass
