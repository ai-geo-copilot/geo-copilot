from typing import Annotated
from uuid import UUID
import hashlib
from pathlib import PurePath

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from pydantic import BaseModel, Field, HttpUrl

from ..diagnosis.models import DeepSeekDiagnosis
from ..diagnosis.service import DiagnosisService, DiagnosisServiceError
from ..llm.errors import DeepSeekAuthError, DeepSeekBillingError, DeepSeekInvalidResponseError, DeepSeekUnavailableError
from ..methods.models import RetrievedMethodPack, StrategyPlan
from ..page_input.models import PageInputContext
from ..page_evidence.service import PageEvidenceService
from ..page_evidence.models import AnalysisResult, PageEvidencePack, PublicPageContentProfile, RuleCheck
from ..page_evidence.page_content_profile import build_public_page_content_profile

router = APIRouter(prefix="/analyses", tags=["analyses"])

UPLOAD_MAX_BYTES = 2_000_000
UPLOAD_ALLOWED_EXTENSIONS = {".html", ".htm", ".txt", ".md"}
UPLOAD_ALLOWED_CONTENT_TYPES = {
    "text/html",
    "text/plain",
    "text/markdown",
    "application/octet-stream",
}

def get_analysis_service(request: Request) -> PageEvidenceService:
    return request.app.state.page_evidence_service


def get_diagnosis_service(request: Request) -> DiagnosisService:
    return request.app.state.diagnosis_service


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
    url = str(payload.url)
    input_context = PageInputContext(
        source_type="url",
        input_url=url,
        language=payload.language,
        business_type=payload.business_type,
        target_keywords=payload.target_keywords,
    )
    return _to_response(service.analyze_safe(url, payload.language, input_context))


@router.post("/uploads", response_model=AnalysisResponse, status_code=status.HTTP_200_OK)
async def create_uploaded_analysis(
    file: Annotated[UploadFile, File()],
    language: Annotated[str, Form(min_length=2, max_length=16)] = "zh-CN",
    declared_url: Annotated[str | None, Form(max_length=2048)] = None,
    business_type: Annotated[str | None, Form(max_length=80)] = None,
    target_keywords: Annotated[list[str] | None, Form(max_length=20)] = None,
    target_audience: Annotated[str | None, Form(max_length=160)] = None,
    conversion_goal: Annotated[str | None, Form(max_length=160)] = None,
    market: Annotated[str | None, Form(max_length=80)] = None,
    brand_facts: Annotated[list[str] | None, Form(max_length=20)] = None,
    forbidden_claims: Annotated[list[str] | None, Form(max_length=20)] = None,
    service: PageEvidenceService = Depends(get_analysis_service),
) -> AnalysisResponse:
    upload_bytes = await _read_upload_bytes(file)
    upload_sha256 = hashlib.sha256(upload_bytes).hexdigest()
    html = _decode_upload(upload_bytes)
    input_context = PageInputContext(
        source_type="uploaded_html",
        declared_url=declared_url,
        upload_filename=file.filename,
        upload_sha256=upload_sha256,
        language=language,
        business_type=business_type,
        target_keywords=target_keywords or [],
        target_audience=target_audience,
        conversion_goal=conversion_goal,
        market=market,
        brand_facts=brand_facts or [],
        forbidden_claims=forbidden_claims or [],
    )
    return _to_response(
        service.analyze_uploaded_html(
            html=html,
            upload_filename=file.filename,
            upload_sha256=upload_sha256,
            language=language,
            input_context=input_context,
            declared_url=declared_url,
        )
    )


@router.get("/{analysis_id}", response_model=AnalysisResponse)
def get_analysis(
    analysis_id: UUID,
    service: PageEvidenceService = Depends(get_analysis_service),
) -> AnalysisResponse:
    result = service.get_result(analysis_id)
    if result is None:
        raise HTTPException(status_code=404, detail="analysis not found")
    return _to_response(result)


async def _read_upload_bytes(file: UploadFile) -> bytes:
    filename = file.filename or ""
    extension = PurePath(filename).suffix.lower()
    if extension not in UPLOAD_ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=422, detail="unsupported upload file extension")

    content_type = (file.content_type or "").split(";", 1)[0].lower()
    if content_type and content_type not in UPLOAD_ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=422, detail="unsupported upload content type")

    data = await file.read(UPLOAD_MAX_BYTES + 1)
    if len(data) > UPLOAD_MAX_BYTES:
        raise HTTPException(status_code=413, detail="upload file too large")
    if not data.strip():
        raise HTTPException(status_code=422, detail="upload file cannot be empty")
    return data


def _decode_upload(upload_bytes: bytes) -> str:
    try:
        return upload_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=422, detail="upload file must be utf-8 text") from exc


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


@router.post("/{analysis_id}/diagnosis", response_model=DeepSeekDiagnosis)
def create_analysis_diagnosis(
    analysis_id: UUID,
    service: DiagnosisService = Depends(get_diagnosis_service),
) -> DeepSeekDiagnosis:
    try:
        return service.generate(analysis_id)
    except DiagnosisServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    except DeepSeekAuthError as exc:
        raise HTTPException(status_code=502, detail="diagnosis provider auth failed") from exc
    except DeepSeekBillingError as exc:
        raise HTTPException(status_code=502, detail="diagnosis provider billing unavailable") from exc
    except DeepSeekInvalidResponseError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except DeepSeekUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/{analysis_id}/diagnosis", response_model=DeepSeekDiagnosis)
def get_analysis_diagnosis(
    analysis_id: UUID,
    service: DiagnosisService = Depends(get_diagnosis_service),
) -> DeepSeekDiagnosis:
    diagnosis = service.get(analysis_id)
    if diagnosis is None:
        raise HTTPException(status_code=404, detail="analysis diagnosis not found")
    return diagnosis


@router.post("/{analysis_id}/messages", response_model=FollowUpResponse)
def create_follow_up(analysis_id: UUID, payload: FollowUpRequest) -> FollowUpResponse:
    if not payload.message.strip():
        raise HTTPException(status_code=422, detail="message cannot be blank")
    return FollowUpResponse(
        analysis_id=analysis_id,
        status="failed",
        error_code="analysis_not_ready",
    )
