from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field, HttpUrl

router = APIRouter(prefix="/analyses", tags=["analyses"])


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


class FollowUpRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)


class FollowUpResponse(BaseModel):
    analysis_id: UUID
    status: str
    answer: str | None = None
    error_code: str | None = None


@router.post("", response_model=AnalysisResponse, status_code=status.HTTP_202_ACCEPTED)
def create_analysis(payload: AnalysisCreateRequest) -> AnalysisResponse:
    return AnalysisResponse(
        id=uuid4(),
        input_url=str(payload.url),
        status="queued",
        language=payload.language,
    )


@router.get("/{analysis_id}", response_model=AnalysisResponse)
def get_analysis(analysis_id: UUID) -> AnalysisResponse:
    return AnalysisResponse(
        id=analysis_id,
        input_url="unknown",
        status="queued",
        language="zh-CN",
    )


@router.post("/{analysis_id}/messages", response_model=FollowUpResponse)
def create_follow_up(analysis_id: UUID, payload: FollowUpRequest) -> FollowUpResponse:
    if not payload.message.strip():
        raise HTTPException(status_code=422, detail="message cannot be blank")
    return FollowUpResponse(
        analysis_id=analysis_id,
        status="failed",
        error_code="analysis_not_ready",
    )
