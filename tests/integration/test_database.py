import os
import pytest
from src.core.config.settings import Settings
from src.storage.database import Database


@pytest.mark.asyncio
async def test_real_database_readiness():
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("Set TEST_DATABASE_URL to an existing test database to run this check")
    database = Database(Settings(_env_file=None, database_url=url))
    try:
        assert await database.is_ready()
    finally:
        await database.close()
