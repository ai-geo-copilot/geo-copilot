from fastapi.testclient import TestClient

from apps.api.app.llm.provider_store import ProviderConfigStore
from apps.api.app.llm.settings import LLMProviderSettings
from apps.api.app.main import app
from apps.api.app.routers.llm import get_provider_store


def test_provider_config_api_sets_public_config_without_leaking_key() -> None:
    store = ProviderConfigStore(
        LLMProviderSettings(
            provider="deepseek",
            api_key="",
            model="deepseek-v4-flash",
            base_url="https://api.deepseek.com",
        )
    )
    app.dependency_overrides[get_provider_store] = lambda request=None: store
    try:
        with TestClient(app) as client:
            response = client.put(
                "/api/llm/provider",
                json={
                    "provider": "openai_compatible",
                    "api_key": "sk-test-secret",
                    "model": "gpt-compatible",
                    "base_url": "https://example.invalid/v1",
                    "timeout_seconds": 30,
                    "max_retries": 1,
                    "max_tokens": 2048,
                },
            )
            get_response = client.get("/api/llm/provider")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["provider"] == "openai_compatible"
    assert body["configured"] is True
    assert body["api_key_preview"] == "sk-t...cret"
    assert "sk-test-secret" not in str(body)
    assert get_response.status_code == 200
    assert get_response.json()["model"] == "gpt-compatible"


def test_provider_config_api_rejects_anthropic_until_adapter_exists() -> None:
    store = ProviderConfigStore(
        LLMProviderSettings(
            provider="deepseek",
            api_key="",
            model="deepseek-v4-flash",
            base_url="https://api.deepseek.com",
        )
    )
    app.dependency_overrides[get_provider_store] = lambda request=None: store
    try:
        with TestClient(app) as client:
            response = client.put(
                "/api/llm/provider",
                json={
                    "provider": "anthropic",
                    "api_key": "secret",
                    "model": "claude-test",
                    "base_url": "https://api.anthropic.com",
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    assert response.json()["detail"] == "anthropic provider is not supported yet"
