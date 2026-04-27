"""create telemetry_15m partitioned table

Revision ID: 0002
Revises: 0001
"""
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE telemetry_15m (
            site_id      UUID NOT NULL REFERENCES sites(id),
            asset_id     UUID NOT NULL REFERENCES assets(id),
            ts           TIMESTAMPTZ NOT NULL,
            kw           DOUBLE PRECISION NOT NULL,
            quality_flag SMALLINT NOT NULL DEFAULT 0,
            ingested_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
            PRIMARY KEY (site_id, asset_id, ts)
        ) PARTITION BY RANGE (ts);
    """)
    op.execute("CREATE INDEX idx_telemetry_15m_site_ts ON telemetry_15m (site_id, ts DESC);")

    # Default partition catches anything outside the explicit ranges (safety net).
    op.execute("""
        CREATE TABLE telemetry_15m_default
            PARTITION OF telemetry_15m DEFAULT;
    """)
    # 2025 monthly partitions — production setup would automate this.
    for m in range(1, 13):
        start = f"2025-{m:02d}-01"
        end = f"2025-{m + 1:02d}-01" if m < 12 else "2026-01-01"
        op.execute(f"""
            CREATE TABLE telemetry_15m_2025m{m:02d}
                PARTITION OF telemetry_15m
                FOR VALUES FROM ('{start}') TO ('{end}');
        """)


def downgrade() -> None:
    for m in range(1, 13):
        op.execute(f"DROP TABLE IF EXISTS telemetry_15m_2025m{m:02d};")
    op.execute("DROP TABLE IF EXISTS telemetry_15m_default;")
    op.execute("DROP TABLE IF EXISTS telemetry_15m;")
