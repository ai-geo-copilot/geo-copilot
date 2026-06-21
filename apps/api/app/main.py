from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .page_evidence.service import PageEvidenceService
from .routers import analyses, health


@asynccontextmanager
async def lifespan(app: FastAPI):
    service = PageEvidenceService()
    app.state.page_evidence_service = service
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
