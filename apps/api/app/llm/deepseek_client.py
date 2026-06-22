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
    ) -> None:
        if not api_key:
            raise ValueError("api_key is required")
        if not model:
            raise ValueError("model is required")
        self._api_key = api_key
        self._model = model
        self._base_url = base_url.rstrip("/")
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
        body: dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "response_format": {"type": "json_object"},
            "max_tokens": max_tokens,
            "stream": False,
            "thinking": {"type": "disabled"},
            "temperature": 0,
            "user_id": user_id,
        }
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


def _hash_json(payload: dict[str, Any]) -> str:
    return _hash_text(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")))


def _hash_text(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()
