"""Access-log middleware: writes one row per request into api_request_log.

Inserts run on the request thread (sync engine) but errors are swallowed so a DB
hiccup never breaks an API response.
"""
from __future__ import annotations

import logging
import re
import time

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)

_UUID_RE = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")


def _extract_id(path: str, prefix: str) -> str | None:
    """`/threads/<uuid>/...` → uuid. Returns None if not matching."""
    if prefix not in path:
        return None
    after = path.split(prefix, 1)[1].lstrip("/")
    seg = after.split("/", 1)[0]
    return seg if _UUID_RE.fullmatch(seg) else None


class AccessLogMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, database_url: str | None) -> None:
        super().__init__(app)
        self._engine: Engine | None = create_engine(database_url, future=True) if database_url else None

    async def dispatch(self, request: Request, call_next) -> Response:
        start = time.perf_counter()
        status: int | None = None
        error: str | None = None
        try:
            response: Response = await call_next(request)
            status = response.status_code
            return response
        except Exception as exc:
            error = f"{exc.__class__.__name__}: {exc}"
            status = 500
            raise
        finally:
            if self._engine is not None:
                try:
                    self._insert(request, status, error,
                                 int((time.perf_counter() - start) * 1000))
                except Exception as e:  # noqa: BLE001
                    logger.warning("access log insert failed: %s", e)

    def _insert(self, request: Request, status: int | None,
                error: str | None, duration_ms: int) -> None:
        path = request.url.path
        client_ip = request.client.host if request.client else None
        ua = request.headers.get("user-agent")
        sql = text("""
            INSERT INTO api_request_log
                (method, path, query, status_code, duration_ms,
                 job_id, thread_id, error, user_agent, client_ip)
            VALUES (:m, :p, :q, :s, :d, :j, :t, :e, :ua, CAST(:ip AS INET))
        """)
        assert self._engine is not None
        with self._engine.begin() as conn:
            conn.execute(sql, {
                "m": request.method,
                "p": path,
                "q": request.url.query or None,
                "s": status,
                "d": duration_ms,
                "j": _extract_id(path, "/jobs/") or _extract_id(path, "/ws/jobs/"),
                "t": _extract_id(path, "/threads/"),
                "e": error,
                "ua": ua,
                "ip": client_ip,
            })
