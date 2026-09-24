"""Align stored models with installed qwen2.5:7b + qwen3:8b tier."""

from alembic import op

revision = "004_tiered_qwen_models"
down_revision = "003_default_model_qwen3"
branch_labels = None
depends_on = None

SPECIALIST_AGENTS = ("gmail", "calendar", "drive", "docs", "sheets")


def upgrade() -> None:
    op.execute(
        "UPDATE user_settings SET default_model = 'qwen3:8b' "
        "WHERE default_model ILIKE 'llama%'"
    )
    op.execute(
        "UPDATE user_settings SET default_model = 'qwen3:8b' "
        "WHERE default_model ILIKE 'qwen3:14b%'"
    )
    for agent in SPECIALIST_AGENTS:
        op.execute(
            f"""
            UPDATE user_settings
            SET agent_overrides = jsonb_set(
                COALESCE(agent_overrides, '{{}}'::jsonb),
                '{{{agent},model}}',
                '"qwen3:8b"'::jsonb,
                true
            )
            WHERE agent_overrides->'{agent}'->>'model' IS NULL
               OR agent_overrides->'{agent}'->>'model' ILIKE 'llama%'
               OR agent_overrides->'{agent}'->>'model' ILIKE 'qwen3:14b%'
            """
        )
    op.execute(
        """
        UPDATE user_settings
        SET agent_overrides = jsonb_set(
            COALESCE(agent_overrides, '{}'::jsonb),
            '{orchestrator,model}',
            '"qwen2.5:7b"'::jsonb,
            true
        )
        WHERE agent_overrides->'orchestrator'->>'model' IS NULL
           OR agent_overrides->'orchestrator'->>'model' ILIKE 'llama%'
        """
    )


def downgrade() -> None:
    pass
