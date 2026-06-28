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
from apps.api.app.llm.provider_store import ProviderConfigRequest, ProviderConfigStore
from apps.api.app.llm.secrets import AesGcmSecretCipher
from apps.api.app.llm.settings import DeepSeekSettings
from apps.api.app.page_evidence.storage import SnapshotStorage
from apps.api.tests.test_conversations import _write_conversation_base_snapshot
from apps.api.tests.test_diagnosis_service import _write_minimal_analysis_snapshot
from apps.api.tests.test_diagnosis_validator import _safe_prompt_pack


def _require_real_smoke_flag() -> None:
    if os.environ.get("GEO_REAL_PROVIDER_SMOKE") != "1":
        pytest.skip("Set GEO_REAL_PROVIDER_SMOKE=1 to run the real provider smoke test.")


def _require_postgres_url() -> str:
    value = os.environ.get("GEO_POSTGRES_INTEGRATION_URL") or ""
    if not value:
        pytest.skip("Set GEO_POSTGRES_INTEGRATION_URL to run the real provider smoke test.")
    return value


def test_real_provider_roundtrip_with_persisted_postgres_config(tmp_path: Path) -> None:
    _require_real_smoke_flag()
    database_url = _require_postgres_url()
    deepseek = DeepSeekSettings.from_env()
    if not deepseek.api_key:
        pytest.skip("DeepSeek API key is not configured.")

    engine = create_sqlalchemy_engine(database_url)
    migration_sql = (
        Path(__file__).resolve().parents[3] / "infra" / "migrations" / "0004_provider_config_runtime_settings.sql"
    ).read_text(encoding="utf-8")
    repository = SqlAlchemyProviderConfigRepository(engine)
    store = ProviderConfigStore(
        deepseek.to_provider_settings(),
        repository=repository,
        cipher=AesGcmSecretCipher(b"E" * 32),
    )
    user = AuthenticatedUser(
        user_id=uuid4(),
        email=f"real-provider-smoke-{uuid4().hex[:10]}@example.com",
        display_name="Real Provider Smoke",
    )
    diagnosis_analysis_id = uuid4()
    conversation_analysis_id = uuid4()
    diagnosis_storage = SnapshotStorage(root_dir=tmp_path / "diagnosis-snapshots")
    conversation_storage = SnapshotStorage(root_dir=tmp_path / "conversation-snapshots")
    diagnosis_service = DiagnosisService(storage=diagnosis_storage, provider_store=store)
    conversation_service = ConversationService(storage=conversation_storage, provider_store=store)

    with engine.begin() as connection:
        for statement in migration_sql.split(";"):
            sql = statement.strip()
            if sql:
                connection.execute(text(sql))

    try:
        store.set_override(
            ProviderConfigRequest(
                provider="deepseek",
                api_key=deepseek.api_key,
                model=deepseek.model,
                base_url=deepseek.base_url,
                timeout_seconds=deepseek.timeout_seconds,
                max_retries=deepseek.max_retries,
                max_tokens=min(deepseek.max_tokens, 1024),
            ),
            user=user,
        )

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

    assert 0 <= diagnosis.geo_score <= 100
    assert diagnosis.executive_summary.strip()
    assert turn.answer.strip()
