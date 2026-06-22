from pathlib import Path
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from apps.api.app.conversations.models import CopilotTurn
from apps.api.app.conversations.context import build_conversation_safe_pack
from apps.api.app.conversations.prompt import CopilotPromptBuilder
from apps.api.app.conversations.service import ConversationService, ConversationServiceError
from apps.api.app.llm.deepseek_client import DeepSeekCompletionResult
from apps.api.app.llm.settings import DeepSeekSettings
from apps.api.app.main import app
from apps.api.app.page_evidence.storage import SnapshotStorage
from apps.api.app.page_input.models import PageInputContext
from apps.api.app.routers.analyses import get_analysis_service, get_conversation_service, get_diagnosis_service
from apps.api.tests.test_contract import _StubDiagnosisService, _StubService
from apps.api.tests.test_diagnosis_service import _write_minimal_analysis_snapshot
from apps.api.tests.test_diagnosis_validator import _diagnosis, _safe_prompt_pack


class _FakeClient:
    def __init__(self, content: str) -> None:
        self.content = content
        self.calls = 0

    def create_json_completion(self, *, messages, user_id, max_tokens):
        self.calls += 1
        assert "ConversationSafePack" in messages[1]["content"]
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


def test_conversation_service_generates_validates_and_saves_turn(tmp_path: Path) -> None:
    storage = SnapshotStorage(root_dir=tmp_path)
    analysis_id = uuid4()
    _write_conversation_base_snapshot(storage, analysis_id)
    turn = _turn(analysis_id)
    fake_client = _FakeClient(turn.model_dump_json())
    service = ConversationService(
        storage=storage,
        client=fake_client,
        settings=DeepSeekSettings(api_key="unused"),
    )

    result = service.create_turn(
        analysis_id,
        {
            "message": "我是 B2B SaaS，目标词是 AI sales assistant，先改哪里？",
            "turn_user_context": {
                "business_type": "b2b_saas",
                "target_keywords": ["AI sales assistant"],
            },
        },
    )

    assert result.intent == "prioritize_actions"
    assert fake_client.calls == 1
    history = storage.load_conversation_history(analysis_id)
    assert len(history.messages) == 2
    assert history.messages[0].role == "user"
    assert history.turns[0].turn_id == turn.turn_id
    snapshot_dir = storage.get_snapshot_dir(analysis_id) / "conversations" / "default" / "turns"
    assert (snapshot_dir / "000001_user.json").exists()
    assert (snapshot_dir / "000001_assistant.json").exists()
    assert (snapshot_dir / "000001_assistant.meta.json").exists()


def test_conversation_service_rejects_unknown_refs_without_saving(tmp_path: Path) -> None:
    storage = SnapshotStorage(root_dir=tmp_path)
    analysis_id = uuid4()
    _write_conversation_base_snapshot(storage, analysis_id)
    invalid_turn = _turn(analysis_id).model_copy(update={"evidence_refs": ["unknown.ref"]})
    service = ConversationService(
        storage=storage,
        client=_FakeClient(invalid_turn.model_dump_json()),
        settings=DeepSeekSettings(api_key="unused"),
    )

    try:
        service.create_turn(analysis_id, {"message": "先改哪里？"})
    except ConversationServiceError as exc:
        assert exc.status_code == 422
        assert str(exc) == "copilot output failed validation"
    else:  # pragma: no cover
        raise AssertionError("Expected validator failure")
    assert not (storage.get_snapshot_dir(analysis_id) / "conversations").exists()


def test_conversation_service_missing_safe_prompt_does_not_call_client(tmp_path: Path) -> None:
    storage = SnapshotStorage(root_dir=tmp_path)
    analysis_id = uuid4()
    _write_minimal_analysis_snapshot(storage, analysis_id)
    storage.save_input_context(
        analysis_id,
        PageInputContext(source_type="url", input_url="https://example.com/page", language="zh-CN"),
    )
    fake_client = _FakeClient(_turn(analysis_id).model_dump_json())
    service = ConversationService(storage=storage, client=fake_client, settings=DeepSeekSettings(api_key="unused"))

    try:
        service.create_turn(analysis_id, {"message": "解释一下页面识别"})
    except ConversationServiceError as exc:
        assert exc.status_code == 404
        assert str(exc) == "analysis safe prompt not found"
    else:  # pragma: no cover
        raise AssertionError("Expected missing safe prompt failure")
    assert fake_client.calls == 0


def test_copilot_prompt_uses_safe_context_only(tmp_path: Path) -> None:
    storage = SnapshotStorage(root_dir=tmp_path)
    analysis_id = uuid4()
    _write_conversation_base_snapshot(storage, analysis_id)
    service = ConversationService(
        storage=storage,
        client=_FakeClient(_turn(analysis_id).model_dump_json()),
        settings=DeepSeekSettings(api_key="unused"),
    )
    service.create_turn(analysis_id, {"message": "解释一下页面识别"})
    history = storage.load_conversation_history(analysis_id)
    safe_pack = _safe_prompt_pack()
    prompt = CopilotPromptBuilder().build_messages(
        build_conversation_safe_pack(
            analysis_id=analysis_id,
            input_context=storage.load_input_context(analysis_id),
            safe_prompt_pack=safe_pack,
            user_message="解释一下页面识别",
            recent_messages=history.messages,
            diagnosis=_diagnosis(),
        )
    )
    prompt_text = prompt[1]["content"].lower()

    assert "diagnosis-compact-summary-v0" in prompt_text
    assert "<html" not in prompt_text
    assert "<script" not in prompt_text
    assert "<!--" not in prompt_text


def test_messages_api_creates_and_reads_history(tmp_path: Path) -> None:
    storage = SnapshotStorage(root_dir=tmp_path)
    analysis_id = UUID("11111111-1111-1111-1111-111111111111")
    _write_conversation_base_snapshot(storage, analysis_id)
    conversation_service = ConversationService(
        storage=storage,
        client=_FakeClient(_turn(analysis_id).model_dump_json()),
        settings=DeepSeekSettings(api_key="unused"),
    )
    app.dependency_overrides[get_analysis_service] = lambda request=None: _StubService()
    app.dependency_overrides[get_diagnosis_service] = lambda request=None: _StubDiagnosisService()
    app.dependency_overrides[get_conversation_service] = lambda request=None: conversation_service
    try:
        with TestClient(app) as client:
            post_response = client.post(
                f"/api/analyses/{analysis_id}/messages",
                json={
                    "message": "先改哪里？",
                    "turn_user_context": {"business_type": "b2b_saas"},
                },
            )
            get_response = client.get(f"/api/analyses/{analysis_id}/messages")
    finally:
        app.dependency_overrides.clear()

    assert post_response.status_code == 200
    assert post_response.json()["turn_version"] == "geo-copilot-turn-v0"
    assert get_response.status_code == 200
    assert len(get_response.json()["messages"]) == 2
    assert get_response.json()["turns"][0]["intent"] == "prioritize_actions"


def _write_conversation_base_snapshot(storage: SnapshotStorage, analysis_id) -> None:
    _write_minimal_analysis_snapshot(storage, analysis_id)
    storage.save_input_context(
        analysis_id,
        PageInputContext(
            source_type="url",
            input_url="https://example.com/page",
            language="zh-CN",
            business_type="b2b_saas",
            target_keywords=["AI sales assistant"],
        ),
    )
    snapshot_dir = storage.get_snapshot_dir(analysis_id)
    (snapshot_dir / "safe_prompt_pack.json").write_text(
        _safe_prompt_pack().model_dump_json(),
        encoding="utf-8",
    )
    storage.save_deepseek_diagnosis(analysis_id, _diagnosis(), {"created_at": "2026-06-22T00:00:00Z"})


def _turn(analysis_id) -> CopilotTurn:
    safe_pack = _safe_prompt_pack()
    evidence_ref = safe_pack.evidence_excerpts[0].evidence_ref
    method_ref = safe_pack.retrieved_methods.chunks[0].method_ref
    return CopilotTurn(
        turn_id=uuid4(),
        analysis_id=analysis_id,
        intent="prioritize_actions",
        answer="先补强首屏定义块，并把建议绑定到现有页面证据。",
        evidence_refs=[evidence_ref],
        method_refs=[method_ref],
        follow_up_suggestions=["要不要生成一个首屏定义块？"],
    )
