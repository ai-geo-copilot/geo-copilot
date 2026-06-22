from __future__ import annotations

import json
from pathlib import Path
from uuid import UUID

from apps.api.app.methods.models import RetrievedMethodPack, StrategyPlan
from apps.api.app.diagnosis.models import DeepSeekDiagnosis
from apps.api.app.safe_prompt.models import SafePromptPack

from .models import AnalysisResult, PageContentProfile, PageEvidencePack, RuleCheck


class SnapshotStorage:
    def __init__(self, root_dir: Path | None = None) -> None:
        self._root_dir = root_dir or Path(__file__).resolve().parents[4] / "data" / "analyses"

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
