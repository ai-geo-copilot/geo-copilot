from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field, HttpUrl

from ..page_evidence import PageEvidenceService
from ..page_evidence.models import AnalysisResult, PageEvidencePack, RuleCheck

router = APIRouter(prefix="/analyses", tags=["analyses"])

def get_analysis_service(request: Request) -> PageEvidenceService:
    return request.app.state.page_evidence_service


class AnalysisCreateRequest(BaseModel):
    url: HttpUrl
    language: str = Field(default="zh-CN", min_length=2, max_length=16)
    business_type: str | None = Field(default=None, max_length=80)
    target_keywords: list[str] = Field(default_factory=list, max_length=20)


class AnalysisResponse(BaseModel):
    id: UUID
    input_url: str
    status: str
    language: str
    error_code: str | None = None
    page_evidence: PageEvidencePack | None = None
    rule_checks: list[RuleCheck] = Field(default_factory=list)
    snapshot_dir: str | None = None


class FollowUpRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)


class FollowUpResponse(BaseModel):
    analysis_id: UUID
    status: str
    answer: str | None = None
    error_code: str | None = None


def _to_response(result: AnalysisResult) -> AnalysisResponse:
    return AnalysisResponse(**result.model_dump())


@router.post("", response_model=AnalysisResponse, status_code=status.HTTP_200_OK)
def create_analysis(
    payload: AnalysisCreateRequest,
    service: PageEvidenceService = Depends(get_analysis_service),
) -> AnalysisResponse:
    return _to_response(service.analyze_safe(str(payload.url), payload.language))


@router.get("/{analysis_id}", response_model=AnalysisResponse)
def get_analysis(
    analysis_id: UUID,
    service: PageEvidenceService = Depends(get_analysis_service),
) -> AnalysisResponse:
    result = service.get_result(analysis_id)
    if result is None:
        raise HTTPException(status_code=404, detail="analysis not found")
    return _to_response(result)


@router.post("/{analysis_id}/messages", response_model=FollowUpResponse)
def create_follow_up(analysis_id: UUID, payload: FollowUpRequest) -> FollowUpResponse:
    if not payload.message.strip():
        raise HTTPException(status_code=422, detail="message cannot be blank")
    return FollowUpResponse(
        analysis_id=analysis_id,
        status="failed",
        error_code="analysis_not_ready",
    )
