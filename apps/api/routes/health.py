import asyncio
import logging

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from apps.api.dependencies import get_database
from src.storage.database import Database

router = APIRouter(tags=["health"])
logger = logging.getLogger(__name__)


@router.get("/health/live")
async def liveness() -> dict[str, str]:
    return {"status": "alive"}


@router.get("/health/ready")
async def readiness(database: Database = Depends(get_database)) -> JSONResponse:
    try:
        ready = await asyncio.wait_for(database.is_ready(), timeout=database.timeout)
    except Exception:
        logger.warning("Database readiness check failed")
        ready = False
    return JSONResponse(
        status_code=200 if ready else 503,
        content={"status": "ready" if ready else "not_ready"},
    )
