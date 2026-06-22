from pathlib import Path
from uuid import uuid4

from apps.api.app.diagnosis.service import DiagnosisService, DiagnosisServiceError, DeepSeekSettings
from apps.api.app.llm.deepseek_client import DeepSeekCompletionResult
from apps.api.app.page_evidence.storage import SnapshotStorage
from apps.api.tests.test_diagnosis_validator import _diagnosis, _safe_prompt_pack


class _FakeClient:
    def __init__(self, content: str) -> None:
        self.content = content
        self.calls = 0

    def create_json_completion(self, *, messages, user_id, max_tokens):
        self.calls += 1
        assert "json" in messages[0]["content"].lower()
        assert "<script" not in messages[1]["content"].lower()
        assert user_id.startswith("analysis_")
        return DeepSeekCompletionResult(
            content=self.content,
            model="deepseek-v4-flash",
            finish_reason="stop",
            usage={"total_tokens": 10},
            latency_ms=12,
            retry_count=0,
            request_hash="sha256:req",
            response_hash="sha256:res",
        )


def test_diagnosis_service_generates_validates_and_saves_snapshot(tmp_path: Path) -> None:
    storage = SnapshotStorage(root_dir=tmp_path)
    analysis_id = uuid4()
    _write_minimal_analysis_snapshot(storage, analysis_id)
    safe_pack = _safe_prompt_pack()
    (storage.get_snapshot_dir(analysis_id) / "safe_prompt_pack.json").write_text(
        safe_pack.model_dump_json(),
        encoding="utf-8",
    )
    fake_client = _FakeClient(_diagnosis().model_dump_json())
    service = DiagnosisService(
        storage=storage,
        client=fake_client,
        settings=DeepSeekSettings(api_key="unused"),
    )

    diagnosis = service.generate(analysis_id)

    assert diagnosis.geo_score == 64
    assert fake_client.calls == 1
    assert (storage.get_snapshot_dir(analysis_id) / "deepseek_diagnosis.json").exists()
    assert (storage.get_snapshot_dir(analysis_id) / "deepseek_diagnosis_meta.json").exists()
    assert storage.load_deepseek_diagnosis(analysis_id).geo_score == 64


def test_diagnosis_service_rejects_invalid_model_output_without_saving(tmp_path: Path) -> None:
    storage = SnapshotStorage(root_dir=tmp_path)
    analysis_id = uuid4()
    _write_minimal_analysis_snapshot(storage, analysis_id)
    (storage.get_snapshot_dir(analysis_id) / "safe_prompt_pack.json").write_text(
        _safe_prompt_pack().model_dump_json(),
        encoding="utf-8",
    )
    invalid = _diagnosis().model_copy(
        update={"issues": [_diagnosis().issues[0].model_copy(update={"method_refs": ["unknown_method"]})]}
    )
    service = DiagnosisService(
        storage=storage,
        client=_FakeClient(invalid.model_dump_json()),
        settings=DeepSeekSettings(api_key="unused"),
    )

    try:
        service.generate(analysis_id)
    except DiagnosisServiceError as exc:
        assert exc.status_code == 422
    else:  # pragma: no cover
        raise AssertionError("Expected validator failure")
    assert not (storage.get_snapshot_dir(analysis_id) / "deepseek_diagnosis.json").exists()


def test_diagnosis_service_missing_safe_prompt_does_not_call_client(tmp_path: Path) -> None:
    storage = SnapshotStorage(root_dir=tmp_path)
    analysis_id = uuid4()
    _write_minimal_analysis_snapshot(storage, analysis_id)
    fake_client = _FakeClient(_diagnosis().model_dump_json())
    service = DiagnosisService(storage=storage, client=fake_client, settings=DeepSeekSettings(api_key="unused"))

    try:
        service.generate(analysis_id)
    except DiagnosisServiceError as exc:
        assert exc.status_code == 404
        assert str(exc) == "analysis safe prompt not found"
    else:  # pragma: no cover
        raise AssertionError("Expected missing safe prompt failure")
    assert fake_client.calls == 0


def _write_minimal_analysis_snapshot(storage: SnapshotStorage, analysis_id) -> None:
    snapshot_dir = storage.get_snapshot_dir(analysis_id)
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    (snapshot_dir / "analysis.json").write_text(
        (
            '{"id":"%s","input_url":"https://example.com/page","status":"completed",'
            '"language":"zh-CN","error_code":null,"page_evidence":null,'
            '"page_content_profile":null,"rule_checks":[],"snapshot_dir":"%s"}'
        )
        % (analysis_id, str(snapshot_dir).replace("\\", "\\\\")),
        encoding="utf-8",
    )
