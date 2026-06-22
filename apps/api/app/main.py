from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .conversations.service import ConversationService
from .diagnosis.service import DiagnosisService
from .llm.provider_store import ProviderConfigStore
from .llm.settings import DeepSeekSettings
from .page_evidence.service import PageEvidenceService
from .routers import analyses, health, llm


@asynccontextmanager
async def lifespan(app: FastAPI):
    service = PageEvidenceService()
    provider_store = ProviderConfigStore(DeepSeekSettings.from_env().to_provider_settings())
    app.state.page_evidence_service = service
    app.state.provider_config_store = provider_store
    app.state.diagnosis_service = DiagnosisService(storage=service.storage, provider_store=provider_store)
    app.state.conversation_service = ConversationService(storage=service.storage, provider_store=provider_store)
    try:
        yield
    finally:
        service.close()


app = FastAPI(
    title="GEO Copilot API",
    version="0.1.0",
    description="Single-URL GEO analysis API scaffold.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(analyses.router, prefix="/api")
app.include_router(llm.router, prefix="/api")
