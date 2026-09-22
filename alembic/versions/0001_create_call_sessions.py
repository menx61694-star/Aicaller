"""create call sessions

Revision ID: 0001
Revises:
"""

from alembic import op

import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "call_sessions",
        sa.Column("call_id", sa.String(length=128), nullable=False),
        sa.Column("caller_number", sa.String(length=64), nullable=True),
        sa.Column("state", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("failure_reason", sa.String(length=512), nullable=True),
        sa.Column("provider_call_id", sa.String(length=128), nullable=True),
        sa.Column("last_provider_event", sa.String(length=128), nullable=True),
        sa.PrimaryKeyConstraint("call_id"),
    )
    op.create_index("ix_call_sessions_state", "call_sessions", ["state"])
    op.create_index("ix_call_sessions_provider_call_id", "call_sessions", ["provider_call_id"])


def downgrade() -> None:
    op.drop_index("ix_call_sessions_provider_call_id", table_name="call_sessions")
    op.drop_index("ix_call_sessions_state", table_name="call_sessions")
    op.drop_table("call_sessions")
