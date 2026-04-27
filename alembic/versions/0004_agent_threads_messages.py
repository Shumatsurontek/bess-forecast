"""create agent_threads and agent_messages

Revision ID: 0004
Revises: 0003
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "agent_threads",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("forecast_run_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("forecast_runs.id", ondelete="SET NULL"),
                  nullable=True),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_agent_threads_run", "agent_threads", ["forecast_run_id"])
    op.create_index("idx_agent_threads_updated", "agent_threads",
                    [sa.text("updated_at DESC")])

    op.create_table(
        "agent_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("thread_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("agent_threads.id", ondelete="CASCADE"),
                  nullable=False),
        sa.Column("role", sa.Text, nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("tool_name", sa.Text, nullable=True),
        sa.Column("tool_args", postgresql.JSONB, nullable=True),
        sa.Column("tool_result", postgresql.JSONB, nullable=True),
        sa.Column("tokens", sa.Integer, nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(
            "role IN ('user','assistant','tool','system')", name="ck_agent_messages_role"
        ),
    )
    op.create_index("idx_agent_messages_thread", "agent_messages",
                    ["thread_id", "created_at"])


def downgrade() -> None:
    op.drop_index("idx_agent_messages_thread", "agent_messages")
    op.drop_table("agent_messages")
    op.drop_index("idx_agent_threads_updated", "agent_threads")
    op.drop_index("idx_agent_threads_run", "agent_threads")
    op.drop_table("agent_threads")
