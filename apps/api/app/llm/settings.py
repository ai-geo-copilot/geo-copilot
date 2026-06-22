from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Literal
from pathlib import Path


ProviderName = Literal["deepseek", "openai_compatible", "anthropic"]


@dataclass(frozen=True)
class LLMProviderSettings:
    provider: ProviderName
    api_key: str
    model: str
    base_url: str
    timeout_seconds: float = 60.0
    max_retries: int = 2
    max_tokens: int = 4096


@dataclass(frozen=True)
class DeepSeekSettings:
    api_key: str
    base_url: str = "https://api.deepseek.com"
    model: str = "deepseek-v4-flash"
    timeout_seconds: float = 60.0
    max_retries: int = 2
    max_tokens: int = 4096

    @classmethod
    def from_env(cls) -> "DeepSeekSettings":
        dotenv = _load_dotenv()
        return cls(
            api_key=_env_value("DEEPSEEK_API_KEY", dotenv, ""),
            base_url=_env_value("DEEPSEEK_BASE_URL", dotenv, "https://api.deepseek.com"),
            model=_env_value("DEEPSEEK_MODEL", dotenv, "deepseek-v4-flash"),
            timeout_seconds=float(_env_value("DEEPSEEK_TIMEOUT_SECONDS", dotenv, "60")),
            max_retries=int(_env_value("DEEPSEEK_MAX_RETRIES", dotenv, "2")),
            max_tokens=int(_env_value("DEEPSEEK_MAX_TOKENS", dotenv, "4096")),
        )

    def to_provider_settings(self) -> LLMProviderSettings:
        return LLMProviderSettings(
            provider="deepseek",
            api_key=self.api_key,
            base_url=self.base_url,
            model=self.model,
            timeout_seconds=self.timeout_seconds,
            max_retries=self.max_retries,
            max_tokens=self.max_tokens,
        )


def _env_value(name: str, dotenv: dict[str, str], default: str) -> str:
    return os.environ.get(name) or dotenv.get(name) or default


def _load_dotenv() -> dict[str, str]:
    env_path = Path.cwd() / ".env"
    if not env_path.exists():
        return {}
    values: dict[str, str] = {}
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        if key:
            values[key] = value
    return values
