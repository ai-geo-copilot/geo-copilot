from contextlib import asynccontextmanager
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .auth import AuthenticatedUserResolver
from .conversations.service import ConversationService
from .conversations.repository import SnapshotConversationRepository, SqlAlchemyConversationRepository
from .db import (
    SnapshotAnalysisRepository,
    SnapshotJobRepository,
    SqlAlchemyAnalysisRepository,
    SqlAlchemyJobRepository,
    SqlAlchemyProviderConfigRepository,
    create_sqlalchemy_engine,
)
from .diagnosis.service import DiagnosisService
from .llm.provider_store import ProviderConfigStore
from .llm.secrets import AesGcmSecretCipher, ProviderSecretSettings
from .llm.settings import DeepSeekSettings
from .jobs.service import JobService
from .page_evidence.service import PageEvidenceService
from .page_evidence.storage import SnapshotStorage
from .routers import analyses, health, llm


@asynccontextmanager
async def lifespan(app: FastAPI):
    database_url = _load_database_url()
    storage = SnapshotStorage()
    provider_repository = None
    if database_url:
        engine = create_sqlalchemy_engine(database_url)
        analysis_repository = SqlAlchemyAnalysisRepository(engine, storage)
        job_repository = SqlAlchemyJobRepository(engine)
        provider_repository = SqlAlchemyProviderConfigRepository(engine)
        analysis_repository.create_schema()
        conversation_repository = SqlAlchemyConversationRepository(engine, storage)
        app.state.database_engine = engine
    else:
        analysis_repository = SnapshotAnalysisRepository(storage)
        job_repository = SnapshotJobRepository(storage)
        conversation_repository = SnapshotConversationRepository(storage)
    service = PageEvidenceService(
        storage=storage,
        analysis_repository=analysis_repository,
        job_repository=job_repository,
    )
    job_service = JobService(analysis_repository, job_repository)
    secret_settings = ProviderSecretSettings.from_env()
    provider_store = ProviderConfigStore(
        DeepSeekSettings.from_env().to_provider_settings(),
        repository=provider_repository,
        cipher=None if secret_settings is None else AesGcmSecretCipher(secret_settings.master_key),
    )
    app.state.page_evidence_service = service
    app.state.job_service = job_service
    app.state.provider_config_store = provider_store
    app.state.user_identity_resolver = AuthenticatedUserResolver.from_env()
    app.state.diagnosis_service = DiagnosisService(storage=service.storage, provider_store=provider_store)
    app.state.conversation_service = ConversationService(
        storage=service.storage,
        provider_store=provider_store,
        repository=conversation_repository,
    )
    try:
        yield
    finally:
        service.close()


def _load_database_url() -> str | None:
    value = os.getenv("DATABASE_URL")
    if value:
        return value
    if os.getenv("GEO_DISABLE_DOTENV_DATABASE") == "1":
        return None
    env_path = Path(".env")
    if not env_path.exists():
        return None
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, raw_value = line.split("=", 1)
        if key.strip() == "DATABASE_URL":
            return raw_value.strip().strip('"').strip("'") or None
    return None


app = FastAPI(
    title="GEO Copilot API",
    version="0.1.0",
    description="Single-URL GEO analysis API scaffold.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(analyses.router, prefix="/api")
app.include_router(llm.router, prefix="/api")
