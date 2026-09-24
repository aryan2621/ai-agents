"""Migrate default LLM to tiered qwen3 models."""

from alembic import op

revision = "003_default_model_qwen3"
down_revision = "002_default_model_qwen"
branch_labels = None
depends_on = None

SPECIALIST_AGENTS = ("gmail", "calendar", "drive", "docs", "sheets")


def upgrade() -> None:
    op.execute(
        "UPDATE user_settings SET default_model = 'qwen3:8b' "
        "WHERE default_model ILIKE 'llama%' OR default_model ILIKE 'qwen2.5:7b%'"
    )
    for agent in SPECIALIST_AGENTS:
        op.execute(
            f"""
            UPDATE user_settings
            SET agent_overrides = jsonb_set(
                COALESCE(agent_overrides, '{{}}'::jsonb),
                '{{{agent},model}}',
                '"qwen3:14b"'::jsonb,
                true
            )
            WHERE agent_overrides->'{agent}'->>'model' IS NULL
               OR agent_overrides->'{agent}'->>'model' ILIKE 'llama%'
               OR agent_overrides->'{agent}'->>'model' ILIKE 'qwen2.5:7b%'
            """
        )


def downgrade() -> None:
    pass
