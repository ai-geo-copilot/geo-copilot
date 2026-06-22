import json

import httpx

from apps.api.app.llm.deepseek_client import DeepSeekClient
from apps.api.app.llm.errors import DeepSeekAuthError, DeepSeekInvalidResponseError, DeepSeekUnavailableError


def test_deepseek_client_sends_json_mode_request_without_leaking_key() -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["authorization"] = request.headers.get("authorization")
        captured["body"] = json.loads(request.content)
        return httpx.Response(
            200,
            json={
                "model": "deepseek-v4-flash",
                "choices": [{"message": {"content": '{"geo_score":50}'}, "finish_reason": "stop"}],
                "usage": {"total_tokens": 10},
            },
        )

    client = DeepSeekClient(
        api_key="secret-key",
        model="deepseek-v4-flash",
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    result = client.create_json_completion(
        messages=[{"role": "system", "content": "Output json."}],
        user_id="analysis_11111111111111111111111111111111",
        max_tokens=256,
    )

    body = captured["body"]
    assert isinstance(body, dict)
    assert body["response_format"] == {"type": "json_object"}
    assert body["thinking"] == {"type": "disabled"}
    assert body["user_id"] == "analysis_11111111111111111111111111111111"
    assert result.content == '{"geo_score":50}'
    assert result.retry_count == 0
    assert "secret-key" not in result.request_hash


def test_deepseek_client_does_not_retry_auth_errors() -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(401, json={"error": "bad key"})

    client = DeepSeekClient(
        api_key="secret-key",
        model="deepseek-v4-flash",
        client=httpx.Client(transport=httpx.MockTransport(handler)),
        max_retries=2,
    )

    try:
        client.create_json_completion(messages=[{"role": "system", "content": "json"}], user_id="analysis_x", max_tokens=128)
    except DeepSeekAuthError as exc:
        assert "secret-key" not in str(exc)
    else:  # pragma: no cover
        raise AssertionError("Expected auth error")
    assert calls == 1


def test_deepseek_client_retries_429_and_empty_content() -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(429, json={"error": "rate limited"})
        if calls == 2:
            return httpx.Response(200, json={"choices": [{"message": {"content": ""}, "finish_reason": "stop"}]})
        return httpx.Response(200, json={"choices": [{"message": {"content": '{"geo_score":50}'}, "finish_reason": "stop"}]})

    client = DeepSeekClient(
        api_key="secret-key",
        model="deepseek-v4-flash",
        client=httpx.Client(transport=httpx.MockTransport(handler)),
        max_retries=2,
    )

    result = client.create_json_completion(messages=[{"role": "system", "content": "json"}], user_id="analysis_x", max_tokens=128)

    assert calls == 3
    assert result.retry_count == 2


def test_deepseek_client_fails_closed_on_truncated_output() -> None:
    client = DeepSeekClient(
        api_key="secret-key",
        model="deepseek-v4-flash",
        client=httpx.Client(
            transport=httpx.MockTransport(
                lambda request: httpx.Response(
                    200,
                    json={"choices": [{"message": {"content": '{"geo_score":'}, "finish_reason": "length"}]},
                )
            )
        ),
    )

    try:
        client.create_json_completion(messages=[{"role": "system", "content": "json"}], user_id="analysis_x", max_tokens=128)
    except DeepSeekInvalidResponseError as exc:
        assert "truncated" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("Expected truncated output failure")


def test_deepseek_client_fails_closed_on_missing_choices() -> None:
    client = DeepSeekClient(
        api_key="secret-key",
        model="deepseek-v4-flash",
        client=httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(200, json={"choices": []}))),
    )

    try:
        client.create_json_completion(messages=[{"role": "system", "content": "json"}], user_id="analysis_x", max_tokens=128)
    except DeepSeekInvalidResponseError as exc:
        assert "invalid response" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("Expected invalid response failure")
