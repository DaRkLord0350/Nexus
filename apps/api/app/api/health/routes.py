import time

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis import redis_client
from app.db import get_db

router = APIRouter(tags=["health"])

_START_TIME = time.time()


@router.get("/live")
async def liveness() -> dict:
    """Shallow check: the process is up and serving requests. Used by the ALB/ASG health check."""
    return {"status": "ok", "uptime_seconds": round(time.time() - _START_TIME, 2)}


@router.get("/health")
async def health() -> dict:
    """Alias of /live kept shallow on purpose so a transient DB/Redis blip doesn't flap the target group."""
    return {"status": "ok"}


@router.get("/ready")
async def readiness(response: Response, db: AsyncSession = Depends(get_db)) -> dict:
    """Deep check used by deployment scripts before shifting traffic to a new instance."""
    checks: dict[str, str] = {}
    healthy = True

    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as exc:  # noqa: BLE001
        checks["database"] = f"error: {exc}"
        healthy = False

    try:
        await redis_client.ping()
        checks["redis"] = "ok"
    except Exception as exc:  # noqa: BLE001
        checks["redis"] = f"error: {exc}"
        healthy = False

    if not healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {"status": "ok" if healthy else "unavailable", "checks": checks}
