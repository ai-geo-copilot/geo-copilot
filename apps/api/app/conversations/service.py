from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from pydantic import ValidationError

from apps.api.app.llm.deepseek_client import DeepSeekClient, DeepSeekCompletionResult
from apps.api.app.llm.settings import DeepSeekSettings
from apps.api.app.page_evidence.storage import SnapshotStorage

from .context import build_conversation_safe_pack
from .models import ConversationHistory, ConversationMessageRequest, CopilotTurn
from .prompt import CopilotPromptBuilder
from .validator import validate_copilot_turn


class ConversationServiceError(RuntimeError):
    def __init__(self, message: str, *, status_code: int) -> None:
        super().__init__(message)
        self.status_code = status_code


class ConversationService:
    def __init__(
        self,
        *,
        storage: SnapshotStorage,
        client: DeepSeekClient | None = None,
        settings: DeepSeekSettings | None = None,
        prompt_builder: CopilotPromptBuilder | None = None,
    ) -> None:
        self._storage = storage
        self._client = client
        self._settings = settings or DeepSeekSettings.from_env()
        self._prompt_builder = prompt_builder or CopilotPromptBuilder()

    def create_turn(self, analysis_id: UUID, request: ConversationMessageRequest | dict[str, object]) -> CopilotTurn:
        if not isinstance(request, ConversationMessageRequest):
            request = ConversationMessageRequest.model_validate(request)
        if not request.message.strip():
            raise ConversationServiceError("message cannot be blank", status_code=422)
        if self._storage.load_result(analysis_id) is None:
            raise ConversationServiceError("analysis not found", status_code=404)
        safe_prompt_pack = self._storage.load_safe_prompt_pack(analysis_id)
        if safe_prompt_pack is None:
            raise ConversationServiceError("analysis safe prompt not found", status_code=404)
        input_context = self._storage.load_input_context(analysis_id)
        if input_context is None:
            raise ConversationServiceError("analysis input context not found", status_code=404)

        history = self._storage.load_conversation_history(analysis_id)
        safe_pack = build_conversation_safe_pack(
            analysis_id=analysis_id,
            input_context=input_context,
            safe_prompt_pack=safe_prompt_pack,
            user_message=request.message.strip(),
            recent_messages=history.messages,
            turn_user_context=request.turn_user_context,
            diagnosis=self._storage.load_deepseek_diagnosis(analysis_id),
        )
        client = self._client or self._build_client()
        result = client.create_json_completion(
            messages=self._prompt_builder.build_messages(safe_pack),
            user_id=f"analysis_{str(analysis_id).replace('-', '')}",
            max_tokens=self._settings.max_tokens,
        )
        try:
            turn = CopilotTurn.model_validate_json(result.content)
        except ValidationError as exc:
            raise ConversationServiceError("copilot provider returned invalid json", status_code=502) from exc
        try:
            turn = validate_copilot_turn(turn, safe_pack)
        except ValueError as exc:
            raise ConversationServiceError("copilot output failed validation", status_code=422) from exc
        self._storage.save_copilot_turn(analysis_id, request, turn, self._build_meta(result))
        return turn

    def get_history(self, analysis_id: UUID) -> ConversationHistory:
        if self._storage.load_result(analysis_id) is None:
            raise ConversationServiceError("analysis not found", status_code=404)
        return self._storage.load_conversation_history(analysis_id)

    def _build_client(self) -> DeepSeekClient:
        if not self._settings.api_key:
            raise ConversationServiceError("copilot provider not configured", status_code=503)
        return DeepSeekClient(
            api_key=self._settings.api_key,
            base_url=self._settings.base_url,
            model=self._settings.model,
            timeout_seconds=self._settings.timeout_seconds,
            max_retries=self._settings.max_retries,
        )

    def _build_meta(self, result: DeepSeekCompletionResult) -> dict[str, object]:
        return {
            "provider": "deepseek",
            "model": result.model,
            "base_url": self._settings.base_url,
            "request_hash": result.request_hash,
            "response_hash": result.response_hash,
            "finish_reason": result.finish_reason,
            "usage": result.usage,
            "latency_ms": result.latency_ms,
            "retry_count": result.retry_count,
            "created_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        }
