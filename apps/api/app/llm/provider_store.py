from __future__ import annotations

from dataclasses import replace
from threading import Lock

from pydantic import BaseModel, Field, HttpUrl

from .settings import LLMProviderSettings, ProviderName


class ProviderConfigRequest(BaseModel):
    provider: ProviderName
    api_key: str = Field(min_length=1, max_length=4096)
    model: str = Field(min_length=1, max_length=160)
    base_url: HttpUrl
    timeout_seconds: float = Field(default=60.0, ge=5.0, le=180.0)
    max_retries: int = Field(default=2, ge=0, le=5)
    max_tokens: int = Field(default=4096, ge=256, le=16000)


class ProviderConfigPublic(BaseModel):
    provider: ProviderName
    model: str
    base_url: str
    timeout_seconds: float
    max_retries: int
    max_tokens: int
    configured: bool
    api_key_preview: str | None = None


class ProviderTestResponse(BaseModel):
    ok: bool
    provider: ProviderName
    model: str
    base_url: str
    message: str


class ProviderConfigStore:
    def __init__(self, default_settings: LLMProviderSettings) -> None:
        self._default_settings = default_settings
        self._override: LLMProviderSettings | None = None
        self._lock = Lock()

    def get_effective(self) -> LLMProviderSettings:
        with self._lock:
            return self._override or self._default_settings

    def set_override(self, request: ProviderConfigRequest) -> LLMProviderSettings:
        settings = LLMProviderSettings(
            provider=request.provider,
            api_key=request.api_key,
            model=request.model,
            base_url=str(request.base_url).rstrip("/"),
            timeout_seconds=request.timeout_seconds,
            max_retries=request.max_retries,
            max_tokens=request.max_tokens,
        )
        with self._lock:
            self._override = settings
        return settings

    def clear_override(self) -> LLMProviderSettings:
        with self._lock:
            self._override = None
            return self._default_settings

    def public_config(self) -> ProviderConfigPublic:
        settings = self.get_effective()
        return to_public_config(settings, configured=bool(settings.api_key))


def to_public_config(settings: LLMProviderSettings, *, configured: bool) -> ProviderConfigPublic:
    return ProviderConfigPublic(
        provider=settings.provider,
        model=settings.model,
        base_url=settings.base_url,
        timeout_seconds=settings.timeout_seconds,
        max_retries=settings.max_retries,
        max_tokens=settings.max_tokens,
        configured=configured,
        api_key_preview=_preview_key(settings.api_key) if settings.api_key else None,
    )


def without_api_key(settings: LLMProviderSettings) -> LLMProviderSettings:
    return replace(settings, api_key="")


def _preview_key(api_key: str) -> str:
    if len(api_key) <= 8:
        return "***"
    return f"{api_key[:4]}...{api_key[-4:]}"
