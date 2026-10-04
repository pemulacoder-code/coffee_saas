import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api.router import api_router
from app.core.config import settings
from app.core.exceptions import AppException
from app.core.logging import setup_logging
from app.db.engine import engine
from app.db.redis import redis_client


setup_logging()

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting application")

    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))

        logger.info("PostgreSQL connection: OK")

        await redis_client.ping()

        logger.info("Redis connection: OK")

        logger.info("Application startup complete")

        yield

    finally:
        logger.info("Shutting down application")

        await redis_client.aclose()
        logger.info("Redis connection closed")

        await engine.dispose()
        logger.info("SQLAlchemy engine disposed")

        logger.info("Application shutdown complete")


app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AppException)
async def app_exception_handler(
    request: Request,
    exc: AppException,
) -> JSONResponse:
    logger.warning(
        "Application error: %s %s - %s",
        request.method,
        request.url.path,
        exc.message,
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
            }
        },
    )


@app.get("/")
async def root() -> dict[str, str]:
    logger.info("Root endpoint requested")

    return {
        "message": "Coffee SaaS API",
        "environment": settings.app_env,
    }


app.include_router(api_router)