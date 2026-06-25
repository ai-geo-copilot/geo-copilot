from __future__ import annotations

import hashlib
import json
import random
import time
from dataclasses import dataclass
from typing import Any

import httpx

from .errors import (
    DeepSeekAuthError,
    DeepSeekBillingError,
    DeepSeekClientError,
    DeepSeekInvalidResponseError,
    DeepSeekUnavailableError,
)
from .settings import LLMProviderSettings


@dataclass(frozen=True)
class DeepSeekCompletionResult:
    content: str
    model: str
    finish_reason: str | None
    usage: dict[str, Any] | None
    latency_ms: int
    retry_count: int
    request_hash: str
    response_hash: str


class DeepSeekClient:
    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        base_url: str = "https://api.deepseek.com",
        client: httpx.Client | None = None,
        timeout_seconds: float = 60.0,
        max_retries: int = 2,
        provider: str = "deepseek",
    ) -> None:
        if not api_key:
            raise ValueError("api_key is required")
        if not model:
            raise ValueError("model is required")
        self._api_key = api_key
        self._model = model
        self._base_url = base_url.rstrip("/")
        self._provider = provider
        self._client = client or httpx.Client(
            timeout=httpx.Timeout(timeout_seconds),
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
            trust_env=False,
        )
        self._owns_client = client is None
        self._max_retries = max(0, max_retries)

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def create_json_completion(
        self,
        *,
        messages: list[dict[str, str]],
        user_id: str,
        max_tokens: int,
    ) -> DeepSeekCompletionResult:
        return self._create_completion(
            messages=messages,
            user_id=user_id,
            max_tokens=max_tokens,
            json_mode=True,
            temperature=0,
            disable_thinking=True,
        )

    def create_text_completion(
        self,
        *,
        messages: list[dict[str, str]],
        user_id: str,
        max_tokens: int,
    ) -> DeepSeekCompletionResult:
        return self._create_completion(
            messages=messages,
            user_id=user_id,
            max_tokens=max_tokens,
            json_mode=False,
            temperature=0.4,
            disable_thinking=False,
        )

    def _create_completion(
        self,
        *,
        messages: list[dict[str, str]],
        user_id: str,
        max_tokens: int,
        json_mode: bool,
        temperature: float,
        disable_thinking: bool,
    ) -> DeepSeekCompletionResult:
        body: dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "max_tokens": max_tokens,
            "stream": False,
            "temperature": temperature,
        }
        if json_mode:
            body["response_format"] = {"type": "json_object"}
        if self._provider == "deepseek":
            if disable_thinking:
                body["thinking"] = {"type": "disabled"}
            body["user_id"] = user_id
        else:
            body["user"] = user_id
        request_hash = _hash_json(body)
        started = time.perf_counter()
        retry_count = 0

        while True:
            try:
                response = self._client.post(
                    f"{self._base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {self._api_key}", "Content-Type": "application/json"},
                    json=body,
                )
                self._raise_for_status(response)
                try:
                    payload = response.json()
                except ValueError as exc:
                    raise DeepSeekInvalidResponseError("diagnosis provider returned invalid json") from exc
                choices = payload.get("choices")
                if not isinstance(choices, list) or not choices:
                    raise DeepSeekInvalidResponseError("diagnosis provider returned invalid response")
                choice = choices[0]
                content = choice.get("message", {}).get("content")
                finish_reason = choice.get("finish_reason")
                if finish_reason == "length":
                    raise DeepSeekInvalidResponseError("diagnosis provider output truncated")
                if not isinstance(content, str) or not content.strip():
                    raise DeepSeekUnavailableError("diagnosis provider returned empty content", retryable=True)
                latency_ms = int((time.perf_counter() - started) * 1000)
                return DeepSeekCompletionResult(
                    content=content,
                    model=str(payload.get("model") or self._model),
                    finish_reason=finish_reason,
                    usage=payload.get("usage") if isinstance(payload.get("usage"), dict) else None,
                    latency_ms=latency_ms,
                    retry_count=retry_count,
                    request_hash=request_hash,
                    response_hash=_hash_text(content),
                )
            except (httpx.TimeoutException, httpx.NetworkError) as exc:
                error: DeepSeekClientError = DeepSeekUnavailableError(
                    "diagnosis provider unavailable",
                    retryable=True,
                )
                error.__cause__ = exc
            except DeepSeekClientError as exc:
                error = exc

            if not error.retryable or retry_count >= self._max_retries:
                raise error
            retry_count += 1
            time.sleep(min(0.2 * (2 ** (retry_count - 1)), 1.0) + random.uniform(0, 0.05))

    def _raise_for_status(self, response: httpx.Response) -> None:
        status_code = response.status_code
        if status_code < 400:
            return
        if status_code == 401:
            raise DeepSeekAuthError("diagnosis provider auth failed", status_code=status_code)
        if status_code == 402:
            raise DeepSeekBillingError("diagnosis provider billing unavailable", status_code=status_code)
        if status_code in {429, 500, 503}:
            raise DeepSeekUnavailableError(
                "diagnosis provider unavailable",
                retryable=True,
                status_code=status_code,
            )
        raise DeepSeekClientError("diagnosis provider request failed", status_code=status_code)


def build_llm_client(
    settings: LLMProviderSettings,
    *,
    client: httpx.Client | None = None,
) -> DeepSeekClient:
    if settings.provider == "anthropic":
        raise DeepSeekClientError("anthropic provider is not supported in this build", status_code=422)
    return DeepSeekClient(
        api_key=settings.api_key,
        base_url=settings.base_url,
        model=settings.model,
        client=client,
        timeout_seconds=settings.timeout_seconds,
        max_retries=settings.max_retries,
        provider=settings.provider,
    )


def _hash_json(payload: dict[str, Any]) -> str:
    return _hash_text(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")))


def _hash_text(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()
