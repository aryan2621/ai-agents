"""Switch default and specialist models to ministral-3:8b."""

from alembic import op

revision = "010_default_model_ministral"
down_revision = "009_onboarding_completed"
branch_labels = None
depends_on = None

SPECIALIST_AGENTS = ("gmail", "calendar", "drive", "docs", "sheets", "web")


def upgrade() -> None:
    op.execute(
        "UPDATE user_settings SET default_model = 'ministral-3:8b' "
        "WHERE default_model = 'qwen3:8b'"
    )
    for agent in SPECIALIST_AGENTS:
        op.execute(
            f"""
            UPDATE user_settings
            SET agent_overrides = jsonb_set(
                COALESCE(agent_overrides, '{{}}'::jsonb),
                '{{{agent},model}}',
                '"ministral-3:8b"'::jsonb,
                true
            )
            WHERE agent_overrides->'{agent}'->>'model' = 'qwen3:8b'
            """
        )


def downgrade() -> None:
    op.execute(
        "UPDATE user_settings SET default_model = 'qwen3:8b' "
        "WHERE default_model = 'ministral-3:8b'"
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
            WHERE agent_overrides->'{agent}'->>'model' = 'ministral-3:8b'
            """
        )
