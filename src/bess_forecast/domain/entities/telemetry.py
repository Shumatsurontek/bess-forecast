from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class TelemetryReading:
    site_id: str
    asset_id: str
    ts: datetime
    kw: float
    quality_flag: int = 0  # 0=ok, 1=interpolated, 2=suspect
