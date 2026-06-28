from pathlib import Path
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from starlette.requests import Request

from apps.api.app.auth import AuthenticatedUser, AuthenticatedUserResolver
from apps.api.app.db import SqlAlchemyProviderConfigRepository, create_sqlalchemy_engine
from apps.api.app.llm.provider_store import ProviderConfigRequest, ProviderConfigStore
from apps.api.app.llm.secrets import AesGcmSecretCipher, ProviderSecretSettings
from apps.api.app.llm.settings import LLMProviderSettings
from apps.api.app.main import app
from apps.api.app.routers.llm import get_optional_authenticated_user, get_provider_store


def test_authenticated_user_resolver_prefers_request_headers_over_default() -> None:
    default_user = AuthenticatedUser(
        user_id=UUID("11111111-1111-1111-1111-111111111111"),
        email="default@example.com",
    )
    resolver = AuthenticatedUserResolver(default_user=default_user)
    request = Request(
        {
            "type": "http",
            "headers": [
                (b"x-geo-user-id", b"22222222-2222-2222-2222-222222222222"),
                (b"x-geo-user-email", b"owner@example.com"),
                (b"x-geo-user-name", b"Owner"),
            ],
        }
    )

    resolved = resolver.resolve_request_user(request)

    assert resolved == AuthenticatedUser(
        user_id=UUID("22222222-2222-2222-2222-222222222222"),
        email="owner@example.com",
        display_name="Owner",
    )


def test_provider_secret_settings_reads_base64_master_key(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text(
        "GEO_PROVIDER_MASTER_KEY=QUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUE",
        encoding="utf-8",
    )

    settings = ProviderSecretSettings.from_env()

    assert settings is not None
    assert settings.master_key == b"A" * 32


def test_provider_store_persists_user_config_encrypted_in_sqlite(tmp_path: Path) -> None:
    engine = create_sqlalchemy_engine(f"sqlite:///{tmp_path / 'provider-store.db'}")
    repository = SqlAlchemyProviderConfigRepository(engine)
    repository.create_schema()
    store = ProviderConfigStore(
        LLMProviderSettings(
            provider="deepseek",
            api_key="",
            model="deepseek-v4-flash",
            base_url="https://api.deepseek.com",
        ),
        repository=repository,
        cipher=AesGcmSecretCipher(b"A" * 32),
    )
    user = AuthenticatedUser(user_id=uuid4(), email="owner@example.com")

    store.set_override(
        ProviderConfigRequest(
            provider="openai_compatible",
            api_key="sk-user-secret",
            model="gpt-compatible",
            base_url="https://example.invalid/v1",
            timeout_seconds=45.5,
            max_retries=1,
            max_tokens=2048,
        ),
        user=user,
    )

    effective = store.get_effective(user)
    persisted = repository.get_active(user.user_id)

    assert effective.provider == "openai_compatible"
    assert effective.api_key == "sk-user-secret"
    assert effective.timeout_seconds == 45.5
    assert persisted is not None
    assert persisted.model == "gpt-compatible"
    assert persisted.timeout_seconds == 45.5
    assert "sk-user-secret" not in persisted.api_key_ciphertext


def test_provider_config_api_persists_and_clears_authenticated_user_config(tmp_path: Path) -> None:
    engine = create_sqlalchemy_engine(f"sqlite:///{tmp_path / 'provider-api.db'}")
    repository = SqlAlchemyProviderConfigRepository(engine)
    repository.create_schema()
    store = ProviderConfigStore(
        LLMProviderSettings(
            provider="deepseek",
            api_key="",
            model="deepseek-v4-flash",
            base_url="https://api.deepseek.com",
        ),
        repository=repository,
        cipher=AesGcmSecretCipher(b"B" * 32),
    )
    user = AuthenticatedUser(user_id=uuid4(), email="owner@example.com")
    app.dependency_overrides[get_provider_store] = lambda request=None: store
    app.dependency_overrides[get_optional_authenticated_user] = lambda request=None: user
    try:
        with TestClient(app) as client:
            put_response = client.put(
                "/api/llm/provider",
                json={
                    "provider": "openai_compatible",
                    "api_key": "sk-authenticated-secret",
                    "model": "gpt-compatible",
                    "base_url": "https://example.invalid/v1",
                    "timeout_seconds": 30.5,
                    "max_retries": 1,
                    "max_tokens": 3072,
                },
            )
            get_response = client.get("/api/llm/provider")
            delete_response = client.delete("/api/llm/provider")
    finally:
        app.dependency_overrides.clear()

    persisted = repository.get_active(user.user_id)
    assert put_response.status_code == 200
    assert get_response.status_code == 200
    assert put_response.json()["api_key_preview"] == "sk-a...cret"
    assert get_response.json()["model"] == "gpt-compatible"
    assert get_response.json()["configured"] is True
    assert delete_response.status_code == 200
    assert delete_response.json()["configured"] is False
    assert persisted is None


def test_provider_config_api_rejects_authenticated_persistence_without_master_key(tmp_path: Path) -> None:
    engine = create_sqlalchemy_engine(f"sqlite:///{tmp_path / 'provider-api-missing-key.db'}")
    repository = SqlAlchemyProviderConfigRepository(engine)
    repository.create_schema()
    store = ProviderConfigStore(
        LLMProviderSettings(
            provider="deepseek",
            api_key="",
            model="deepseek-v4-flash",
            base_url="https://api.deepseek.com",
        ),
        repository=repository,
    )
    user = AuthenticatedUser(user_id=uuid4(), email="owner@example.com")
    app.dependency_overrides[get_provider_store] = lambda request=None: store
    app.dependency_overrides[get_optional_authenticated_user] = lambda request=None: user
    try:
        with TestClient(app) as client:
            response = client.put(
                "/api/llm/provider",
                json={
                    "provider": "openai_compatible",
                    "api_key": "sk-authenticated-secret",
                    "model": "gpt-compatible",
                    "base_url": "https://example.invalid/v1",
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert "GEO_PROVIDER_MASTER_KEY" in response.json()["detail"]
