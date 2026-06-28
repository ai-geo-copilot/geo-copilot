from __future__ import annotations

import os
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import delete, text

from apps.api.app.auth import AuthenticatedUser
from apps.api.app.conversations.service import ConversationService
from apps.api.app.db import SqlAlchemyProviderConfigRepository, create_sqlalchemy_engine
from apps.api.app.db.sqlalchemy_store import provider_configs_table, users_table
from apps.api.app.diagnosis.service import DiagnosisService
from apps.api.app.llm.deepseek_client import DeepSeekCompletionResult
from apps.api.app.llm.provider_store import ProviderConfigRequest, ProviderConfigStore
from apps.api.app.llm.secrets import AesGcmSecretCipher
from apps.api.app.llm.settings import LLMProviderSettings
from apps.api.app.page_evidence.storage import SnapshotStorage
from apps.api.tests.test_conversations import _turn, _write_conversation_base_snapshot
from apps.api.tests.test_diagnosis_service import _write_minimal_analysis_snapshot
from apps.api.tests.test_diagnosis_validator import _diagnosis, _safe_prompt_pack


def _integration_database_url() -> str:
    value = os.environ.get("GEO_POSTGRES_INTEGRATION_URL") or ""
    if not value:
        pytest.skip("Set GEO_POSTGRES_INTEGRATION_URL to run PostgreSQL integration tests.")
    return value


class _FakeDiagnosisClient:
    def __init__(self, expected_max_tokens: int) -> None:
        self.expected_max_tokens = expected_max_tokens
        self.calls = 0

    def create_json_completion(self, *, messages, user_id, max_tokens):
        self.calls += 1
        assert max_tokens == self.expected_max_tokens
        assert user_id.startswith("analysis_")
        return DeepSeekCompletionResult(
            content=_diagnosis().model_dump_json(),
            model="integration-fake-model",
            finish_reason="stop",
            usage={"total_tokens": 10},
            latency_ms=12,
            retry_count=0,
            request_hash="sha256:req",
            response_hash="sha256:res",
        )


class _FakeConversationClient:
    def __init__(self, expected_max_tokens: int, analysis_id) -> None:
        self.expected_max_tokens = expected_max_tokens
        self.analysis_id = analysis_id
        self.calls = 0

    def create_text_completion(self, *, messages, user_id, max_tokens):
        self.calls += 1
        assert max_tokens == self.expected_max_tokens
        assert user_id.startswith("analysis_")
        return DeepSeekCompletionResult(
            content=_turn(self.analysis_id).model_dump_json(),
            model="integration-fake-model",
            finish_reason="stop",
            usage={"total_tokens": 10},
            latency_ms=12,
            retry_count=0,
            request_hash="sha256:req",
            response_hash="sha256:res",
        )


def test_provider_config_postgres_migration_and_service_roundtrip(tmp_path: Path) -> None:
    database_url = _integration_database_url()
    engine = create_sqlalchemy_engine(database_url)
    migration_sql = (
        Path(__file__).resolve().parents[3] / "infra" / "migrations" / "0004_provider_config_runtime_settings.sql"
    ).read_text(encoding="utf-8")
    user = AuthenticatedUser(
        user_id=uuid4(),
        email=f"provider-integration-{uuid4().hex[:10]}@example.com",
        display_name="Provider Integration",
    )
    repository = SqlAlchemyProviderConfigRepository(engine)
    store = ProviderConfigStore(
        LLMProviderSettings(
            provider="deepseek",
            api_key="",
            model="deepseek-v4-flash",
            base_url="https://api.deepseek.com",
        ),
        repository=repository,
        cipher=AesGcmSecretCipher(b"C" * 32),
    )
    diagnosis_analysis_id = uuid4()
    conversation_analysis_id = uuid4()
    diagnosis_client = _FakeDiagnosisClient(expected_max_tokens=3456)
    conversation_client = _FakeConversationClient(expected_max_tokens=3456, analysis_id=conversation_analysis_id)
    diagnosis_storage = SnapshotStorage(root_dir=tmp_path / "diagnosis-snapshots")
    conversation_storage = SnapshotStorage(root_dir=tmp_path / "conversation-snapshots")
    diagnosis_service = DiagnosisService(storage=diagnosis_storage, client=diagnosis_client, provider_store=store)
    conversation_service = ConversationService(
        storage=conversation_storage,
        client=conversation_client,
        provider_store=store,
    )

    with engine.begin() as connection:
        for statement in migration_sql.split(";"):
            sql = statement.strip()
            if sql:
                connection.execute(text(sql))
    try:
        store.set_override(
            ProviderConfigRequest(
                provider="openai_compatible",
                api_key="sk-postgres-integration-secret",
                model="gpt-compatible",
                base_url="https://example.invalid/v1",
                timeout_seconds=33.0,
                max_retries=1,
                max_tokens=3456,
            ),
            user=user,
        )
        persisted = repository.get_active(user.user_id)

        _write_minimal_analysis_snapshot(diagnosis_storage, diagnosis_analysis_id)
        (diagnosis_storage.get_snapshot_dir(diagnosis_analysis_id) / "safe_prompt_pack.json").write_text(
            _safe_prompt_pack().model_dump_json(),
            encoding="utf-8",
        )
        diagnosis = diagnosis_service.generate(diagnosis_analysis_id, user)

        _write_conversation_base_snapshot(conversation_storage, conversation_analysis_id)
        turn = conversation_service.create_turn(conversation_analysis_id, {"message": "先改哪里？"}, user)
    finally:
        with engine.begin() as connection:
            connection.execute(delete(provider_configs_table).where(provider_configs_table.c.user_id == user.user_id))
            connection.execute(delete(users_table).where(users_table.c.id == user.user_id))

    assert persisted is not None
    assert persisted.model == "gpt-compatible"
    assert persisted.max_tokens == 3456
    assert "sk-postgres-integration-secret" not in persisted.api_key_ciphertext
    assert diagnosis.geo_score == 64
    assert diagnosis_client.calls == 1
    assert turn.intent == "prioritize_actions"
    assert conversation_client.calls == 1
