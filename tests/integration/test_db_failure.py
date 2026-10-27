import pytest
from src.core.config.settings import Settings
from src.storage.database import Database


@pytest.mark.asyncio
async def test_unconfigured_database_is_not_ready():
    db = Database(Settings(_env_file=None, database_url=None))
    try:
        assert await db.is_ready() is False
    finally:
        await db.close()
