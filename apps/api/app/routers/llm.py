from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status

from ..llm.deepseek_client import build_llm_client
from ..llm.errors import DeepSeekAuthError, DeepSeekBillingError, DeepSeekClientError, DeepSeekInvalidResponseError, DeepSeekUnavailableError
from ..llm.provider_store import (
    ProviderConfigPublic,
    ProviderConfigRequest,
    ProviderConfigStore,
    ProviderTestResponse,
    to_public_config,
)
from ..llm.settings import LLMProviderSettings

router = APIRouter(prefix="/llm", tags=["llm"])


def get_provider_store(request: Request) -> ProviderConfigStore:
    return request.app.state.provider_config_store


@router.get("/provider", response_model=ProviderConfigPublic)
def get_provider_config(store: ProviderConfigStore = Depends(get_provider_store)) -> ProviderConfigPublic:
    return store.public_config()


@router.put("/provider", response_model=ProviderConfigPublic)
def set_provider_config(
    payload: ProviderConfigRequest,
    store: ProviderConfigStore = Depends(get_provider_store),
) -> ProviderConfigPublic:
    if payload.provider == "anthropic":
        raise HTTPException(status_code=422, detail="anthropic provider is not supported yet")
    settings = store.set_override(payload)
    return to_public_config(settings, configured=True)


@router.delete("/provider", response_model=ProviderConfigPublic)
def clear_provider_config(store: ProviderConfigStore = Depends(get_provider_store)) -> ProviderConfigPublic:
    settings = store.clear_override()
    return to_public_config(settings, configured=bool(settings.api_key))


@router.post("/provider/test", response_model=ProviderTestResponse)
def test_provider_config(
    payload: ProviderConfigRequest,
) -> ProviderTestResponse:
    if payload.provider == "anthropic":
        raise HTTPException(status_code=422, detail="anthropic provider is not supported yet")
    settings = storeless_settings(payload)
    try:
        llm_client = build_llm_client(settings)
        try:
            result = llm_client.create_json_completion(
                messages=[
                    {"role": "system", "content": "Output only JSON."},
                    {"role": "user", "content": 'Return exactly {"ok":true}.'},
                ],
                user_id="provider_test",
                max_tokens=64,
            )
        finally:
            llm_client.close()
    except DeepSeekAuthError as exc:
        raise HTTPException(status_code=502, detail="provider auth failed") from exc
    except DeepSeekBillingError as exc:
        raise HTTPException(status_code=502, detail="provider billing unavailable") from exc
    except DeepSeekInvalidResponseError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except DeepSeekUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except DeepSeekClientError as exc:
        raise HTTPException(status_code=exc.status_code or status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    return ProviderTestResponse(
        ok=True,
        provider=settings.provider,
        model=result.model,
        base_url=settings.base_url,
        message="provider test completed",
    )


def storeless_settings(payload: ProviderConfigRequest):
    return LLMProviderSettings(
        provider=payload.provider,
        api_key=payload.api_key,
        model=payload.model,
        base_url=str(payload.base_url).rstrip("/"),
        timeout_seconds=payload.timeout_seconds,
        max_retries=payload.max_retries,
        max_tokens=payload.max_tokens,
    )
