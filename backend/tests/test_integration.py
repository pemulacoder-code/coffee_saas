import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.engine import engine
from app.db.redis import redis_client


@pytest.fixture(autouse=True)
async def cleanup_engine() -> None:
    yield

    await engine.dispose()


@pytest.mark.asyncio
async def test_postgres_connection() -> None:
    async with engine.connect() as connection:
        result = await connection.execute(text("SELECT 1"))

        assert result.scalar_one() == 1


@pytest.mark.asyncio
async def test_redis_connection() -> None:
    result = await redis_client.ping()

    assert result is True


@pytest.mark.asyncio
async def test_database_session() -> None:
    async with AsyncSession(
        bind=engine,
        expire_on_commit=False,
    ) as session:
        result = await session.execute(text("SELECT 1"))

        assert result.scalar_one() == 1