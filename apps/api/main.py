import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from apps.api.routes.health import router as health_router
from src.core.config.logging import configure_logging
from src.core.config.settings import get_settings
from src.storage.database import Database

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(settings.log_level)
    app.state.settings = settings
    app.state.database = Database(settings)
    try:
        yield
    finally:
        await app.state.database.close()


app = FastAPI(title="RAG Researcher", version="0.1.0", lifespan=lifespan)
app.include_router(health_router)


@app.exception_handler(Exception)
async def unexpected_error(request: Request, exc: Exception) -> JSONResponse:
    # Avoid exception text: external libraries can include connection information.
    logger.error("Unhandled API error")
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
