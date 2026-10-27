import pytest
from pydantic import ValidationError

from src.core.config.settings import Settings


def test_environment_overrides_and_optional_secrets(monkeypatch):
    monkeypatch.setenv("API_PORT", "9001")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    settings = Settings(_env_file=None)
    assert settings.api_port == 9001
    assert settings.database_url is None
    assert settings.openai_api_key is None


def test_invalid_port():
    with pytest.raises(ValidationError):
        Settings(_env_file=None, api_port=70000)


def test_invalid_url_does_not_leak_password():
    with pytest.raises(ValidationError) as error:
        Settings(_env_file=None, database_url="secret-password")
    # Pydantic's input representation must also be hidden for invalid secrets.
    assert "secret-password" not in str(error.value)
