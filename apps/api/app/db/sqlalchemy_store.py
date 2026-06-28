from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, CheckConstraint, DateTime, Float, ForeignKey, Integer, MetaData, String, Table, Text, UniqueConstraint, Uuid, create_engine, select
from sqlalchemy.engine import Engine
from sqlalchemy.sql.schema import Column
from sqlalchemy.types import JSON

from apps.api.app.page_evidence.models import AnalysisResult
from apps.api.app.page_evidence.storage import SnapshotStorage
from apps.api.app.auth import AuthenticatedUser
from apps.api.app.llm.provider_store import ProviderConfigRepository, StoredProviderConfig
from apps.api.app.llm.settings import LLMProviderSettings

from .models import AnalysisRecord, JobRecord

metadata = MetaData()

users_table = Table(
    "users",
    metadata,
    Column("id", Uuid(as_uuid=True), primary_key=True),
    Column("email", Text, nullable=False, unique=True),
    Column("display_name", Text, nullable=True),
    Column("is_active", Boolean, nullable=False, default=True),
    Column("created_at", DateTime(timezone=True), nullable=False, default=lambda: datetime.now().astimezone()),
    Column("updated_at", DateTime(timezone=True), nullable=False, default=lambda: datetime.now().astimezone()),
)

workspaces_table = Table(
    "workspaces",
    metadata,
    Column("id", Uuid(as_uuid=True), primary_key=True),
    Column("name", Text, nullable=False),
    Column("owner_id", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False, default=lambda: datetime.now().astimezone()),
)

projects_table = Table(
    "projects",
    metadata,
    Column("id", Uuid(as_uuid=True), primary_key=True),
    Column("workspace_id", Uuid(as_uuid=True), ForeignKey("workspaces.id"), nullable=False, index=True),
    Column("name", Text, nullable=False),
    Column("site_url", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False, default=lambda: datetime.now().astimezone()),
)

analyses_table = Table(
    "analyses",
    metadata,
    Column("id", Uuid(as_uuid=True), primary_key=True),
    Column("project_id", Uuid(as_uuid=True), ForeignKey("projects.id"), nullable=True, index=True),
    Column("source_type", String(32), nullable=False, default="url"),
    Column("input_url", Text, nullable=False),
    Column("final_url", Text, nullable=True),
    Column("status", String(32), nullable=False),
    Column("language", String(16), nullable=False),
    Column("snapshot_uri", Text, nullable=True),
    Column("input_context", JSON, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False, default=lambda: datetime.now().astimezone()),
    Column("completed_at", DateTime(timezone=True), nullable=True),
    Column("error_code", Text, nullable=True),
)

jobs_table = Table(
    "jobs",
    metadata,
    Column("id", Uuid(as_uuid=True), primary_key=True),
    Column("analysis_id", Uuid(as_uuid=True), ForeignKey("analyses.id"), nullable=False, index=True),
    Column("type", String(32), nullable=False),
    Column("status", String(32), nullable=False, index=True),
    Column("attempts", Integer, nullable=False, default=0),
    Column("input_hash", Text, nullable=True),
    Column("artifact_refs", JSON, nullable=False, default=list),
    Column("error_code", Text, nullable=True),
    Column("trace_id", Text, nullable=True),
    Column("started_at", DateTime(timezone=True), nullable=True),
    Column("finished_at", DateTime(timezone=True), nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False, default=lambda: datetime.now().astimezone()),
)

conversation_threads_table = Table(
    "conversation_threads",
    metadata,
    Column("id", Uuid(as_uuid=True), primary_key=True),
    Column("analysis_id", Uuid(as_uuid=True), ForeignKey("analyses.id"), nullable=False, index=True),
    Column("user_id", Uuid(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True),
    Column("title", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False, default=lambda: datetime.now().astimezone()),
    Column("updated_at", DateTime(timezone=True), nullable=False, default=lambda: datetime.now().astimezone()),
)

messages_table = Table(
    "messages",
    metadata,
    Column("id", Uuid(as_uuid=True), primary_key=True),
    Column("thread_id", Uuid(as_uuid=True), ForeignKey("conversation_threads.id"), nullable=False, index=True),
    Column("sequence", Integer, nullable=False),
    Column("role", String(16), nullable=False),
    Column("content", Text, nullable=False),
    Column("turn_json", JSON, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False, default=lambda: datetime.now().astimezone()),
    CheckConstraint("sequence >= 0", name="ck_messages_sequence_nonnegative"),
    CheckConstraint("role IN ('user', 'assistant', 'system')", name="ck_messages_role"),
    UniqueConstraint("thread_id", "sequence", name="uq_messages_thread_sequence"),
)

provider_configs_table = Table(
    "provider_configs",
    metadata,
    Column("id", Uuid(as_uuid=True), primary_key=True),
    Column("user_id", Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True),
    Column("provider", String(32), nullable=False),
    Column("base_url", Text, nullable=False),
    Column("model", Text, nullable=False),
    Column("timeout_seconds", Float, nullable=False, default=60.0),
    Column("max_retries", Integer, nullable=False, default=2),
    Column("max_tokens", Integer, nullable=False, default=4096),
    Column("api_key_ciphertext", Text, nullable=False),
    Column("is_active", Boolean, nullable=False, default=True),
    Column("created_at", DateTime(timezone=True), nullable=False, default=lambda: datetime.now().astimezone()),
    Column("updated_at", DateTime(timezone=True), nullable=False, default=lambda: datetime.now().astimezone()),
    UniqueConstraint("user_id", "provider", name="uq_provider_configs_user_provider"),
)


def create_sqlalchemy_engine(database_url: str) -> Engine:
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    return create_engine(database_url, future=True, connect_args=connect_args)


class SqlAlchemyAnalysisRepository:
    """Database analysis index with snapshot-backed artifact loading."""

    def __init__(self, engine: Engine, storage: SnapshotStorage) -> None:
        self._engine = engine
        self._storage = storage

    def create_schema(self) -> None:
        metadata.create_all(self._engine)

    def save_record(self, record: AnalysisRecord) -> None:
        values = {
            "id": record.analysis_id,
            "input_url": record.input_url,
            "status": record.status,
            "language": record.language,
            "snapshot_uri": record.snapshot_dir,
            "input_context": None if record.input_context is None else record.input_context.model_dump(mode="json"),
            "completed_at": datetime.now().astimezone() if record.status == "completed" else None,
            "error_code": record.error_code,
        }
        with self._engine.begin() as connection:
            existing = connection.execute(
                select(analyses_table.c.id).where(analyses_table.c.id == values["id"])
            ).first()
            if existing is None:
                connection.execute(analyses_table.insert().values(**values))
            else:
                connection.execute(
                    analyses_table.update().where(analyses_table.c.id == values["id"]).values(**values)
                )

    def get_result(self, analysis_id: UUID) -> AnalysisResult | None:
        if self.get_record(analysis_id) is None:
            return None
        return self._storage.load_result(analysis_id)

    def get_record(self, analysis_id: UUID) -> AnalysisRecord | None:
        with self._engine.begin() as connection:
            row = connection.execute(
                select(analyses_table).where(analyses_table.c.id == analysis_id)
            ).mappings().first()
        if row is None:
            return None
        return AnalysisRecord(
            analysis_id=row["id"],
            input_url=row["input_url"],
            status=row["status"],
            language=row["language"],
            error_code=row["error_code"],
            snapshot_dir=row["snapshot_uri"],
            input_context=row["input_context"],
        )


class SqlAlchemyJobRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def create_schema(self) -> None:
        metadata.create_all(self._engine)

    def save(self, job: JobRecord) -> None:
        values = {
            "id": job.job_id,
            "analysis_id": job.analysis_id,
            "type": job.job_type,
            "status": job.status,
            "attempts": job.attempts,
            "input_hash": job.input_hash,
            "artifact_refs": job.artifact_refs,
            "error_code": job.error_code,
            "trace_id": job.trace_id,
            "started_at": job.started_at,
            "finished_at": job.finished_at,
        }
        with self._engine.begin() as connection:
            existing = connection.execute(select(jobs_table.c.id).where(jobs_table.c.id == values["id"])).first()
            if existing is None:
                connection.execute(jobs_table.insert().values(**values))
            else:
                connection.execute(jobs_table.update().where(jobs_table.c.id == values["id"]).values(**values))

    def get(self, analysis_id: UUID, job_id: UUID) -> JobRecord | None:
        with self._engine.begin() as connection:
            row = connection.execute(
                select(jobs_table).where(
                    jobs_table.c.analysis_id == analysis_id,
                    jobs_table.c.id == job_id,
                )
            ).mappings().first()
        return None if row is None else _job_from_row(row)

    def list_for_analysis(self, analysis_id: UUID) -> list[JobRecord]:
        with self._engine.begin() as connection:
            rows = connection.execute(
                select(jobs_table).where(jobs_table.c.analysis_id == analysis_id).order_by(jobs_table.c.id)
            ).mappings().all()
        return [_job_from_row(row) for row in rows]

    def claim_next(self, job_type: str) -> JobRecord | None:
        with self._engine.begin() as connection:
            query = (
                select(jobs_table)
                .where(jobs_table.c.type == job_type, jobs_table.c.status.in_(("queued", "retrying")))
                .order_by(jobs_table.c.created_at, jobs_table.c.id)
                .limit(1)
            )
            if self._engine.dialect.name == "postgresql":
                query = query.with_for_update(skip_locked=True)
            row = connection.execute(query).mappings().first()
            if row is None:
                return None
            now = datetime.now().astimezone()
            connection.execute(
                jobs_table.update()
                .where(
                    jobs_table.c.id == row["id"],
                    jobs_table.c.status.in_(("queued", "retrying")),
                )
                .values(status="running", attempts=row["attempts"] + 1, started_at=now, finished_at=None)
            )
            claimed = dict(row)
            claimed.update(status="running", attempts=row["attempts"] + 1, started_at=now, finished_at=None)
        return _job_from_row(claimed)

    def recover_stale(self, job_type: str, started_before: datetime, max_attempts: int) -> list[JobRecord]:
        recovered: list[JobRecord] = []
        with self._engine.begin() as connection:
            query = select(jobs_table).where(
                jobs_table.c.type == job_type,
                jobs_table.c.status == "running",
                jobs_table.c.started_at < started_before,
            )
            if self._engine.dialect.name == "postgresql":
                query = query.with_for_update(skip_locked=True)
            rows = connection.execute(query).mappings().all()
            now = datetime.now().astimezone()
            for row in rows:
                terminal = row["attempts"] >= max_attempts
                values = {
                    "status": "failed" if terminal else "retrying",
                    "error_code": "worker_lease_expired",
                    "finished_at": now if terminal else None,
                }
                connection.execute(jobs_table.update().where(jobs_table.c.id == row["id"]).values(**values))
                recovered.append(_job_from_row({**dict(row), **values}))
        return recovered


class SqlAlchemyProviderConfigRepository(ProviderConfigRepository):
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def create_schema(self) -> None:
        metadata.create_all(self._engine)

    def save_active(
        self,
        user: AuthenticatedUser,
        settings: LLMProviderSettings,
        *,
        api_key_ciphertext: str,
    ) -> None:
        now = datetime.now().astimezone()
        values = {
            "user_id": user.user_id,
            "provider": settings.provider,
            "base_url": settings.base_url,
            "model": settings.model,
            "timeout_seconds": settings.timeout_seconds,
            "max_retries": settings.max_retries,
            "max_tokens": settings.max_tokens,
            "api_key_ciphertext": api_key_ciphertext,
            "is_active": True,
            "updated_at": now,
        }
        with self._engine.begin() as connection:
            self._upsert_user(connection, user, now)
            connection.execute(
                provider_configs_table.update()
                .where(provider_configs_table.c.user_id == user.user_id)
                .values(is_active=False, updated_at=now)
            )
            existing = connection.execute(
                select(provider_configs_table.c.id).where(
                    provider_configs_table.c.user_id == user.user_id,
                    provider_configs_table.c.provider == settings.provider,
                )
            ).first()
            if existing is None:
                connection.execute(provider_configs_table.insert().values(id=uuid4(), created_at=now, **values))
            else:
                connection.execute(
                    provider_configs_table.update()
                    .where(provider_configs_table.c.id == existing[0])
                    .values(**values)
                )

    def get_active(self, user_id: UUID) -> StoredProviderConfig | None:
        with self._engine.begin() as connection:
            row = connection.execute(
                select(provider_configs_table)
                .where(
                    provider_configs_table.c.user_id == user_id,
                    provider_configs_table.c.is_active.is_(True),
                )
                .order_by(provider_configs_table.c.updated_at.desc(), provider_configs_table.c.id.desc())
            ).mappings().first()
        if row is None:
            return None
        return StoredProviderConfig(
            user_id=row["user_id"],
            provider=row["provider"],
            api_key_ciphertext=row["api_key_ciphertext"],
            model=row["model"],
            base_url=row["base_url"],
            timeout_seconds=float(row["timeout_seconds"]),
            max_retries=row["max_retries"],
            max_tokens=row["max_tokens"],
            is_active=row["is_active"],
        )

    def clear_active(self, user_id: UUID) -> None:
        now = datetime.now().astimezone()
        with self._engine.begin() as connection:
            connection.execute(
                provider_configs_table.update()
                .where(
                    provider_configs_table.c.user_id == user_id,
                    provider_configs_table.c.is_active.is_(True),
                )
                .values(is_active=False, updated_at=now)
            )

    def _upsert_user(self, connection, user: AuthenticatedUser, now: datetime) -> None:
        existing = connection.execute(select(users_table.c.id).where(users_table.c.id == user.user_id)).first()
        values = {
            "email": user.email,
            "display_name": user.display_name,
            "is_active": True,
            "updated_at": now,
        }
        if existing is None:
            connection.execute(users_table.insert().values(id=user.user_id, created_at=now, **values))
        else:
            connection.execute(users_table.update().where(users_table.c.id == user.user_id).values(**values))


def _job_from_row(row) -> JobRecord:
    return JobRecord(
        job_id=row["id"],
        analysis_id=row["analysis_id"],
        job_type=row["type"],
        status=row["status"],
        attempts=row["attempts"],
        input_hash=row["input_hash"],
        artifact_refs=list(row["artifact_refs"] or []),
        error_code=row["error_code"],
        trace_id=row["trace_id"],
        started_at=row["started_at"],
        finished_at=row["finished_at"],
    )
