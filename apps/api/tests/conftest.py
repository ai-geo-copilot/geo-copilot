import pytest


@pytest.fixture(autouse=True)
def disable_dotenv_database(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("GEO_DISABLE_DOTENV_DATABASE", "1")
