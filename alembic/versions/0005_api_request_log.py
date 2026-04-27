"""create api_request_log

Revision ID: 0005
Revises: 0004
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "api_request_log",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("received_at", sa.TIMESTAMP(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("method", sa.Text, nullable=False),
        sa.Column("path", sa.Text, nullable=False),
        sa.Column("query", sa.Text, nullable=True),
        sa.Column("status_code", sa.SmallInteger, nullable=True),
        sa.Column("duration_ms", sa.Integer, nullable=True),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("thread_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("error", sa.Text, nullable=True),
        sa.Column("user_agent", sa.Text, nullable=True),
        sa.Column("client_ip", postgresql.INET, nullable=True),
    )
    op.create_index("idx_api_request_log_received", "api_request_log",
                    [sa.text("received_at DESC")])
    op.create_index("idx_api_request_log_status", "api_request_log", ["status_code"])
    op.execute("CREATE INDEX idx_api_request_log_job ON api_request_log (job_id) "
               "WHERE job_id IS NOT NULL")
    op.execute("CREATE INDEX idx_api_request_log_thread ON api_request_log (thread_id) "
               "WHERE thread_id IS NOT NULL")


def downgrade() -> None:
    op.drop_index("idx_api_request_log_thread", "api_request_log")
    op.drop_index("idx_api_request_log_job", "api_request_log")
    op.drop_index("idx_api_request_log_status", "api_request_log")
    op.drop_index("idx_api_request_log_received", "api_request_log")
    op.drop_table("api_request_log")
