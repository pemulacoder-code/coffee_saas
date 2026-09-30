from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import settings


app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
)


@app.get("/")
async def root() -> dict[str, str]:
    return {
        "message": "Coffee SaaS API",
        "environment": settings.app_env,
    }


app.include_router(api_router)