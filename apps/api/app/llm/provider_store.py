from __future__ import annotations

from dataclasses import replace
from threading import Lock
from typing import Protocol
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl

from apps.api.app.auth import AuthenticatedUser

from .secrets import AesGcmSecretCipher, ProviderSecretError
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


class StoredProviderConfig(BaseModel):
    user_id: UUID
    provider: ProviderName
    api_key_ciphertext: str
    model: str
    base_url: str
    timeout_seconds: float = 60.0
    max_retries: int = 2
    max_tokens: int = 4096
    is_active: bool = True


class ProviderConfigRepository(Protocol):
    def save_active(
        self,
        user: AuthenticatedUser,
        settings: LLMProviderSettings,
        *,
        api_key_ciphertext: str,
    ) -> None:
        ...

    def get_active(self, user_id: UUID) -> StoredProviderConfig | None:
        ...

    def clear_active(self, user_id: UUID) -> None:
        ...


class ProviderConfigStoreError(RuntimeError):
    def __init__(self, message: str, *, status_code: int = 503) -> None:
        super().__init__(message)
        self.status_code = status_code


class ProviderConfigStore:
    def __init__(
        self,
        default_settings: LLMProviderSettings,
        *,
        repository: ProviderConfigRepository | None = None,
        cipher: AesGcmSecretCipher | None = None,
    ) -> None:
        self._default_settings = default_settings
        self._repository = repository
        self._cipher = cipher
        self._override: LLMProviderSettings | None = None
        self._lock = Lock()

    def get_effective(self, user: AuthenticatedUser | None = None) -> LLMProviderSettings:
        if user is not None:
            persisted = self._load_persisted(user)
            if persisted is not None:
                return persisted
            return self._default_settings
        with self._lock:
            return self._override or self._default_settings

    def set_override(
        self,
        request: ProviderConfigRequest,
        *,
        user: AuthenticatedUser | None = None,
    ) -> LLMProviderSettings:
        settings = LLMProviderSettings(
            provider=request.provider,
            api_key=request.api_key,
            model=request.model,
            base_url=str(request.base_url).rstrip("/"),
            timeout_seconds=request.timeout_seconds,
            max_retries=request.max_retries,
            max_tokens=request.max_tokens,
        )
        if user is not None:
            repository = self._require_persistence()
            cipher = self._cipher
            assert cipher is not None
            repository.save_active(
                user,
                settings,
                api_key_ciphertext=cipher.encrypt(settings.api_key),
            )
            return settings
        with self._lock:
            self._override = settings
        return settings

    def clear_override(self, *, user: AuthenticatedUser | None = None) -> LLMProviderSettings:
        if user is not None:
            repository = self._require_persistence()
            repository.clear_active(user.user_id)
            return self._default_settings
        with self._lock:
            self._override = None
            return self._default_settings

    def public_config(self, user: AuthenticatedUser | None = None) -> ProviderConfigPublic:
        settings = self.get_effective(user)
        return to_public_config(settings, configured=bool(settings.api_key))

    def _load_persisted(self, user: AuthenticatedUser) -> LLMProviderSettings | None:
        if self._repository is None or self._cipher is None:
            return None
        record = self._repository.get_active(user.user_id)
        if record is None:
            return None
        try:
            api_key = self._cipher.decrypt(record.api_key_ciphertext)
        except ProviderSecretError as exc:
            raise ProviderConfigStoreError("provider config decryption failed", status_code=503) from exc
        return LLMProviderSettings(
            provider=record.provider,
            api_key=api_key,
            model=record.model,
            base_url=record.base_url,
            timeout_seconds=record.timeout_seconds,
            max_retries=record.max_retries,
            max_tokens=record.max_tokens,
        )

    def _require_persistence(self) -> ProviderConfigRepository:
        if self._repository is None or self._cipher is None:
            raise ProviderConfigStoreError(
                "provider config persistence requires authenticated identity, database repository, and GEO_PROVIDER_MASTER_KEY"
            )
        return self._repository


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
