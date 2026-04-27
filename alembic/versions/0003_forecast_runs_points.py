"""create forecast_runs and forecast_points

Revision ID: 0003
Revises: 0002
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "forecast_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("site_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("sites.id", ondelete="CASCADE"), nullable=False),
        sa.Column("generated_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("horizon_start", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("horizon_end", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("model_name", sa.Text, nullable=False),
        sa.Column("model_version", sa.Text, nullable=False),
        sa.Column("quantile", sa.Float, nullable=True),
        sa.Column("metrics", postgresql.JSONB, nullable=True),
        sa.UniqueConstraint(
            "site_id", "generated_at", "model_version", "quantile",
            name="uq_forecast_runs_site_genat_modelver_q",
        ),
    )
    op.create_index(
        "idx_forecast_runs_site_genat",
        "forecast_runs", ["site_id", sa.text("generated_at DESC")],
    )

    op.create_table(
        "forecast_points",
        sa.Column("run_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("forecast_runs.id", ondelete="CASCADE"),
                  nullable=False),
        sa.Column("ts", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("kw_pred", sa.Float, nullable=False),
        sa.PrimaryKeyConstraint("run_id", "ts"),
    )
    op.create_index("idx_forecast_points_ts", "forecast_points", ["ts"])


def downgrade() -> None:
    op.drop_index("idx_forecast_points_ts", table_name="forecast_points")
    op.drop_table("forecast_points")
    op.drop_index("idx_forecast_runs_site_genat", table_name="forecast_runs")
    op.drop_table("forecast_runs")
