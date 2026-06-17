from __future__ import annotations

import json
from pathlib import Path
from uuid import UUID

from .models import AnalysisResult, PageEvidencePack, RuleCheck


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
        rule_checks: list[RuleCheck],
        result: AnalysisResult,
    ) -> str:
        snapshot_dir = self.get_snapshot_dir(analysis_id)
        snapshot_dir.mkdir(parents=True, exist_ok=True)
        (snapshot_dir / "raw.html").write_text(html, encoding="utf-8")
        (snapshot_dir / "clean.md").write_text(clean_markdown, encoding="utf-8")
        (snapshot_dir / "evidence.json").write_text(
            json.dumps(pack.model_dump(mode="json"), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        (snapshot_dir / "rule_checks.json").write_text(
            json.dumps([item.model_dump(mode="json") for item in rule_checks], ensure_ascii=False, indent=2),
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
