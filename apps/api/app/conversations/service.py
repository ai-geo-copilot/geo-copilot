from __future__ import annotations

import json
from datetime import UTC, datetime
from uuid import UUID, uuid4

from pydantic import ValidationError

from apps.api.app.llm.deepseek_client import DeepSeekClient, DeepSeekCompletionResult, build_llm_client
from apps.api.app.llm.provider_store import ProviderConfigStore
from apps.api.app.llm.settings import DeepSeekSettings
from apps.api.app.page_evidence.storage import SnapshotStorage

from .context import build_conversation_safe_pack
from .models import ConversationHistory, ConversationMessageRequest, ConversationSafePack, CopilotTurn
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
        provider_store: ProviderConfigStore | None = None,
        prompt_builder: CopilotPromptBuilder | None = None,
    ) -> None:
        self._storage = storage
        self._client = client
        self._settings = settings or DeepSeekSettings.from_env()
        self._provider_store = provider_store
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
            max_tokens=self._effective_settings().max_tokens,
        )
        try:
            turn = CopilotTurn.model_validate_json(result.content)
        except ValidationError as exc:
            turn = self._wrap_plain_text_turn(safe_pack, result.content)
        turn = self._normalize_turn(turn, safe_pack)
        try:
            turn = validate_copilot_turn(turn, safe_pack)
        except ValueError as exc:
            turn = self._repair_invalid_turn(turn, safe_pack, str(exc))
            turn = validate_copilot_turn(turn, safe_pack)
        self._storage.save_copilot_turn(analysis_id, request, turn, self._build_meta(result))
        return turn

    def get_history(self, analysis_id: UUID) -> ConversationHistory:
        if self._storage.load_result(analysis_id) is None:
            raise ConversationServiceError("analysis not found", status_code=404)
        return self._storage.load_conversation_history(analysis_id)

    def _build_client(self) -> DeepSeekClient:
        settings = self._effective_settings()
        if not settings.api_key:
            raise ConversationServiceError("copilot provider not configured", status_code=503)
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

    def _wrap_plain_text_turn(self, safe_pack: ConversationSafePack, content: str) -> CopilotTurn:
        answer = content.strip()
        if not answer:
            raise ConversationServiceError("copilot provider returned empty content", status_code=502)
        nested_turn = _parse_nested_turn(answer)
        if nested_turn is not None:
            return nested_turn.model_copy(
                update={
                    "analysis_id": safe_pack.analysis_id,
                    "validator_warnings": [
                        *nested_turn.validator_warnings,
                        "provider_returned_nested_json_unwrapped",
                    ],
                }
            )
        evidence_refs = _refs_mentioned_in_text(answer, safe_pack.known_evidence_refs)
        method_refs = _refs_mentioned_in_text(answer, safe_pack.known_method_refs)
        intent = "prioritize_actions" if evidence_refs and method_refs else "ask_unknown"
        return CopilotTurn(
            turn_id=uuid4(),
            analysis_id=safe_pack.analysis_id,
            intent=intent,
            answer=answer[:8000],
            evidence_refs=evidence_refs,
            method_refs=method_refs,
            follow_up_suggestions=[
                "继续展开具体改法",
                "把建议整理成可执行清单",
                "生成页面文案草案",
            ],
            validator_warnings=["provider_returned_non_json_wrapped"],
        )

    def _normalize_turn(self, turn: CopilotTurn, safe_pack: ConversationSafePack) -> CopilotTurn:
        nested_turn = _parse_nested_turn(turn.answer)
        if nested_turn is None:
            return turn
        return nested_turn.model_copy(
            update={
                "turn_id": turn.turn_id,
                "analysis_id": safe_pack.analysis_id,
                "validator_warnings": [
                    *turn.validator_warnings,
                    *nested_turn.validator_warnings,
                    "answer_contained_nested_json_unwrapped",
                ],
            }
        )

    def _repair_invalid_turn(self, turn: CopilotTurn, safe_pack: ConversationSafePack, reason: str) -> CopilotTurn:
        evidence_refs = _known_refs_only(turn.evidence_refs, safe_pack.known_evidence_refs)
        method_refs = _known_refs_only(turn.method_refs, safe_pack.known_method_refs)
        asset_drafts = []
        for draft in turn.asset_drafts:
            next_evidence_refs = _known_refs_only(draft.evidence_refs, safe_pack.known_evidence_refs)
            next_method_refs = _known_refs_only(draft.method_refs, safe_pack.known_method_refs)
            if next_evidence_refs and next_method_refs:
                asset_drafts.append(
                    draft.model_copy(
                        update={
                            "evidence_refs": next_evidence_refs,
                            "method_refs": next_method_refs,
                        }
                    )
                )
        intent = turn.intent
        if not evidence_refs or (intent in {"prioritize_actions", "compare_options"} and not method_refs):
            intent = "ask_unknown"
            method_refs = []
            asset_drafts = []
        warnings = [
            *turn.validator_warnings,
            f"provider_output_repaired_after_validation_failure: {reason}",
        ]
        return turn.model_copy(
            update={
                "intent": intent,
                "evidence_refs": evidence_refs,
                "method_refs": method_refs,
                "asset_drafts": asset_drafts,
                "validator_warnings": warnings,
            }
        )


def _refs_mentioned_in_text(text: str, known_refs: list[str]) -> list[str]:
    return [ref for ref in known_refs if ref and ref in text]


def _known_refs_only(refs: list[str], known_refs: list[str]) -> list[str]:
    known = set(known_refs)
    return [ref for ref in refs if ref in known]


def _parse_nested_turn(text: str) -> CopilotTurn | None:
    stripped = text.strip()
    if not stripped.startswith("{"):
        return None
    try:
        payload = json.loads(stripped)
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict) or "answer" not in payload:
        return None
    try:
        return CopilotTurn.model_validate(payload)
    except ValidationError:
        return None
