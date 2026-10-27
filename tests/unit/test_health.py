import asyncio
from fastapi.testclient import TestClient

from apps.api.dependencies import get_database
from apps.api.main import app


class FakeDatabase:
    timeout = 0.02

    def __init__(self, result=True, delay=0, fail=False):
        self.result, self.delay, self.fail = result, delay, fail

    async def is_ready(self):
        await asyncio.sleep(self.delay)
        if self.fail:
            raise RuntimeError("secret-password")
        return self.result


def test_live_is_independent_from_database():
    app.dependency_overrides[get_database] = lambda: FakeDatabase(fail=True)
    try:
        with TestClient(app) as client:
            assert client.get("/health/live").status_code == 200
    finally:
        app.dependency_overrides.clear()


def test_readiness_success_failure_and_timeout():
    try:
        with TestClient(app) as client:
            for database, status in [(FakeDatabase(), 200), (FakeDatabase(fail=True), 503), (FakeDatabase(delay=1), 503)]:
                app.dependency_overrides[get_database] = lambda: database
                response = client.get("/health/ready")
                assert response.status_code == status
                assert "secret-password" not in response.text
    finally:
        app.dependency_overrides.clear()
