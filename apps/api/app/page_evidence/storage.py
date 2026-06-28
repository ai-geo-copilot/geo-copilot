from __future__ import annotations

import json
import os
from pathlib import Path
from uuid import UUID

from apps.api.app.conversations.models import (
    ConversationHistory,
    ConversationMessage,
    ConversationMessageRequest,
    CopilotTurn,
)
from apps.api.app.methods.models import RetrievedMethodPack, StrategyPlan
from apps.api.app.diagnosis.models import DeepSeekDiagnosis
from apps.api.app.page_input.models import PageInputContext
from apps.api.app.safe_prompt.models import SafePromptPack

from .models import AnalysisResult, PageContentProfile, PageEvidencePack, RuleCheck


class SnapshotStorage:
    def __init__(self, root_dir: Path | None = None) -> None:
        self._root_dir = root_dir or Path(__file__).resolve().parents[4] / "data" / "analyses"

    @property
    def root_dir(self) -> Path:
        return self._root_dir

    def get_snapshot_dir(self, analysis_id: UUID) -> Path:
        return self._root_dir / str(analysis_id)

    def save(
        self,
        analysis_id: UUID,
        html: str,
        clean_markdown: str,
        pack: PageEvidencePack,
        profile: PageContentProfile,
        rule_checks: list[RuleCheck],
        result: AnalysisResult,
        retrieved_methods: RetrievedMethodPack | None = None,
        strategy_plan: StrategyPlan | None = None,
        safe_prompt_pack: SafePromptPack | None = None,
        input_context: PageInputContext | None = None,
    ) -> str:
        snapshot_dir = self.get_snapshot_dir(analysis_id)
        snapshot_dir.mkdir(parents=True, exist_ok=True)
        (snapshot_dir / "raw.html").write_text(html, encoding="utf-8")
        (snapshot_dir / "clean.md").write_text(clean_markdown, encoding="utf-8")
        (snapshot_dir / "evidence.json").write_text(
            json.dumps(pack.model_dump(mode="json"), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        (snapshot_dir / "page_content_profile.json").write_text(
            json.dumps(profile.model_dump(mode="json"), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        (snapshot_dir / "rule_checks.json").write_text(
            json.dumps([item.model_dump(mode="json") for item in rule_checks], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        if retrieved_methods is not None:
            (snapshot_dir / "retrieved_methods.json").write_text(
                json.dumps(retrieved_methods.model_dump(mode="json"), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        if strategy_plan is not None:
            (snapshot_dir / "strategy_plan.json").write_text(
                json.dumps(strategy_plan.model_dump(mode="json"), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        if safe_prompt_pack is not None:
            (snapshot_dir / "safe_prompt_pack.json").write_text(
                json.dumps(safe_prompt_pack.model_dump(mode="json"), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        if input_context is not None:
            self.save_input_context(analysis_id, input_context)
        (snapshot_dir / "analysis.json").write_text(
            result.model_dump_json(indent=2),
            encoding="utf-8",
        )
        return str(snapshot_dir)

    def load_result(self, analysis_id: UUID) -> AnalysisResult | None:
        snapshot_dir = self._root_dir / str(analysis_id)
        analysis_file = snapshot_dir / "analysis.json"
        if not analysis_file.exists():
            return None
        return AnalysisResult.model_validate_json(analysis_file.read_text(encoding="utf-8"))

    def save_input_context(self, analysis_id: UUID, input_context: PageInputContext) -> None:
        snapshot_dir = self.get_snapshot_dir(analysis_id)
        snapshot_dir.mkdir(parents=True, exist_ok=True)
        (snapshot_dir / "input_context.json").write_text(
            json.dumps(input_context.model_dump(mode="json"), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def load_input_context(self, analysis_id: UUID) -> PageInputContext | None:
        context_file = self._root_dir / str(analysis_id) / "input_context.json"
        if not context_file.exists():
            return None
        return PageInputContext.model_validate_json(context_file.read_text(encoding="utf-8"))

    def load_retrieved_methods(self, analysis_id: UUID) -> RetrievedMethodPack | None:
        methods_file = self._root_dir / str(analysis_id) / "retrieved_methods.json"
        if not methods_file.exists():
            return None
        return RetrievedMethodPack.model_validate_json(methods_file.read_text(encoding="utf-8"))

    def load_strategy_plan(self, analysis_id: UUID) -> StrategyPlan | None:
        strategy_file = self._root_dir / str(analysis_id) / "strategy_plan.json"
        if not strategy_file.exists():
            return None
        return StrategyPlan.model_validate_json(strategy_file.read_text(encoding="utf-8"))

    def load_safe_prompt_pack(self, analysis_id: UUID) -> SafePromptPack | None:
        safe_prompt_file = self._root_dir / str(analysis_id) / "safe_prompt_pack.json"
        if not safe_prompt_file.exists():
            return None
        return SafePromptPack.model_validate_json(safe_prompt_file.read_text(encoding="utf-8"))

    def save_deepseek_diagnosis(
        self,
        analysis_id: UUID,
        diagnosis: DeepSeekDiagnosis,
        metadata: dict[str, object],
    ) -> None:
        snapshot_dir = self.get_snapshot_dir(analysis_id)
        snapshot_dir.mkdir(parents=True, exist_ok=True)
        (snapshot_dir / "deepseek_diagnosis.json").write_text(
            json.dumps(diagnosis.model_dump(mode="json"), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        (snapshot_dir / "deepseek_diagnosis_meta.json").write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def load_deepseek_diagnosis(self, analysis_id: UUID) -> DeepSeekDiagnosis | None:
        diagnosis_file = self._root_dir / str(analysis_id) / "deepseek_diagnosis.json"
        if not diagnosis_file.exists():
            return None
        return DeepSeekDiagnosis.model_validate_json(diagnosis_file.read_text(encoding="utf-8"))

    def save_copilot_turn(
        self,
        analysis_id: UUID,
        request: ConversationMessageRequest,
        turn: CopilotTurn,
        metadata: dict[str, object],
    ) -> None:
        conversation_dir = self.get_snapshot_dir(analysis_id) / "conversations" / "default"
        turns_dir = conversation_dir / "turns"
        turns_dir.mkdir(parents=True, exist_ok=True)
        turn_number = self._next_turn_number(turns_dir)
        user_payload = {
            "role": "user",
            "content": request.message,
            "turn_user_context": (
                None if request.turn_user_context is None else request.turn_user_context.model_dump(mode="json")
            ),
            "intent": request.intent,
        }
        self._atomic_write_json(turns_dir / f"{turn_number:06d}_user.json", user_payload)
        self._atomic_write_json(turns_dir / f"{turn_number:06d}_assistant.json", turn.model_dump(mode="json"))
        self._atomic_write_json(turns_dir / f"{turn_number:06d}_assistant.meta.json", metadata)
        self._atomic_write_json(
            conversation_dir / "conversation.json",
            {
                "analysis_id": str(analysis_id),
                "conversation_id": "default",
                "turn_count": turn_number,
                "updated_at": metadata.get("created_at"),
            },
        )

    def load_conversation_history(self, analysis_id: UUID) -> ConversationHistory:
        turns_dir = self.get_snapshot_dir(analysis_id) / "conversations" / "default" / "turns"
        if not turns_dir.exists():
            return ConversationHistory(analysis_id=analysis_id)
        messages: list[ConversationMessage] = []
        turns: list[CopilotTurn] = []
        for path in sorted(turns_dir.glob("*_user.json")):
            payload = json.loads(path.read_text(encoding="utf-8"))
            content = payload.get("content")
            if isinstance(content, str):
                messages.append(ConversationMessage(role="user", content=content))
            assistant_path = path.with_name(path.name.replace("_user.json", "_assistant.json"))
            if assistant_path.exists():
                turn = CopilotTurn.model_validate_json(assistant_path.read_text(encoding="utf-8"))
                turns.append(turn)
                messages.append(ConversationMessage(role="assistant", content=turn.answer))
        return ConversationHistory(analysis_id=analysis_id, messages=messages, turns=turns)

    def _next_turn_number(self, turns_dir: Path) -> int:
        existing = []
        for path in turns_dir.glob("*_assistant.json"):
            try:
                existing.append(int(path.name.split("_", 1)[0]))
            except ValueError:
                continue
        return max(existing, default=0) + 1

    def _atomic_write_json(self, path: Path, payload: dict[str, object]) -> None:
        temp_path = path.with_suffix(path.suffix + ".tmp")
        temp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(temp_path, path)
