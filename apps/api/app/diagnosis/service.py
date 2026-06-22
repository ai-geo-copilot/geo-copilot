from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from pydantic import ValidationError

from apps.api.app.llm.deepseek_client import DeepSeekClient, DeepSeekCompletionResult, build_llm_client
from apps.api.app.llm.errors import DeepSeekInvalidResponseError
from apps.api.app.llm.provider_store import ProviderConfigStore
from apps.api.app.llm.settings import DeepSeekSettings
from apps.api.app.page_evidence.storage import SnapshotStorage
from apps.api.app.safe_prompt.validator import validate_safe_prompt_pack

from .models import DeepSeekDiagnosis
from .prompt import DiagnosisPromptBuilder
from .validator import validate_deepseek_diagnosis


class DiagnosisServiceError(RuntimeError):
    def __init__(self, message: str, *, status_code: int) -> None:
        super().__init__(message)
        self.status_code = status_code


class DiagnosisService:
    def __init__(
        self,
        *,
        storage: SnapshotStorage,
        client: DeepSeekClient | None = None,
        settings: DeepSeekSettings | None = None,
        provider_store: ProviderConfigStore | None = None,
        prompt_builder: DiagnosisPromptBuilder | None = None,
    ) -> None:
        self._storage = storage
        self._settings = settings or DeepSeekSettings.from_env()
        self._provider_store = provider_store
        self._client = client
        self._prompt_builder = prompt_builder or DiagnosisPromptBuilder()

    def generate(self, analysis_id: UUID) -> DeepSeekDiagnosis:
        if self._storage.load_result(analysis_id) is None:
            raise DiagnosisServiceError("analysis not found", status_code=404)
        safe_prompt_pack = self._storage.load_safe_prompt_pack(analysis_id)
        if safe_prompt_pack is None:
            raise DiagnosisServiceError("analysis safe prompt not found", status_code=404)
        safe_prompt_pack = validate_safe_prompt_pack(safe_prompt_pack)

        client = self._client or self._build_client()
        result = client.create_json_completion(
            messages=self._prompt_builder.build_messages(safe_prompt_pack),
            user_id=f"analysis_{str(analysis_id).replace('-', '')}",
            max_tokens=self._effective_settings().max_tokens,
        )
        try:
            diagnosis = DeepSeekDiagnosis.model_validate_json(result.content)
        except ValidationError as exc:
            raise DiagnosisServiceError("diagnosis provider returned invalid json", status_code=502) from exc
        try:
            diagnosis = validate_deepseek_diagnosis(diagnosis, safe_prompt_pack)
        except ValueError as exc:
            raise DiagnosisServiceError("diagnosis output failed validation", status_code=422) from exc
        self._storage.save_deepseek_diagnosis(analysis_id, diagnosis, self._build_meta(result))
        return diagnosis

    def get(self, analysis_id: UUID) -> DeepSeekDiagnosis | None:
        return self._storage.load_deepseek_diagnosis(analysis_id)

    def _build_client(self) -> DeepSeekClient:
        settings = self._effective_settings()
        if not settings.api_key:
            raise DiagnosisServiceError("diagnosis provider not configured", status_code=503)
        return build_llm_client(settings)

    def _build_meta(self, result: DeepSeekCompletionResult) -> dict[str, object]:
        settings = self._effective_settings()
        return {
            "provider": settings.provider,
            "model": result.model,
            "base_url": settings.base_url,
            "request_hash": result.request_hash,
            "response_hash": result.response_hash,
            "finish_reason": result.finish_reason,
            "usage": result.usage,
            "latency_ms": result.latency_ms,
            "retry_count": result.retry_count,
            "created_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        }

    def _effective_settings(self):
        if self._provider_store is not None:
            return self._provider_store.get_effective()
        return self._settings.to_provider_settings()
