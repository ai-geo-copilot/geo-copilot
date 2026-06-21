from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field, HttpUrl

from ..methods.models import RetrievedMethodPack, StrategyPlan
from ..page_evidence.service import PageEvidenceService
from ..page_evidence.models import AnalysisResult, PageEvidencePack, PublicPageContentProfile, RuleCheck
from ..page_evidence.page_content_profile import build_public_page_content_profile

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
    page_content_profile: PublicPageContentProfile | None = None
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
    return AnalysisResponse(
        id=result.id,
        input_url=result.input_url,
        status=result.status,
        language=result.language,
        error_code=result.error_code,
        page_evidence=result.page_evidence,
        page_content_profile=(
            None
            if result.page_content_profile is None
            else build_public_page_content_profile(result.page_content_profile)
        ),
        rule_checks=result.rule_checks,
        snapshot_dir=result.snapshot_dir,
    )


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


@router.get("/{analysis_id}/methods", response_model=RetrievedMethodPack)
def get_analysis_methods(
    analysis_id: UUID,
    service: PageEvidenceService = Depends(get_analysis_service),
) -> RetrievedMethodPack:
    retrieved_methods = service.get_retrieved_methods(analysis_id)
    if retrieved_methods is None:
        raise HTTPException(status_code=404, detail="analysis methods not found")
    return retrieved_methods


@router.get("/{analysis_id}/strategy", response_model=StrategyPlan)
def get_analysis_strategy(
    analysis_id: UUID,
    service: PageEvidenceService = Depends(get_analysis_service),
) -> StrategyPlan:
    strategy_plan = service.get_strategy_plan(analysis_id)
    if strategy_plan is None:
        raise HTTPException(status_code=404, detail="analysis strategy not found")
    return strategy_plan


@router.post("/{analysis_id}/messages", response_model=FollowUpResponse)
def create_follow_up(analysis_id: UUID, payload: FollowUpRequest) -> FollowUpResponse:
    if not payload.message.strip():
        raise HTTPException(status_code=422, detail="message cannot be blank")
    return FollowUpResponse(
        analysis_id=analysis_id,
        status="failed",
        error_code="analysis_not_ready",
    )
