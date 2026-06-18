from __future__ import annotations

from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field


class EvidenceValue(BaseModel):
    value: str | None = None
    evidence_ref: str


class RedirectHop(BaseModel):
    from_url: str
    to_url: str
    status_code: int


class FetchedResource(BaseModel):
    url: str
    status_code: int | None = None
    reachable: bool
    status: Literal["present", "missing", "forbidden", "redirect", "server_error", "request_failed"]
    error_code: str | None = None
    evidence_ref: str


class FetchInfo(BaseModel):
    final_url: str
    status_code: int
    content_type: str
    elapsed_ms: int
    html_sha256: str
    redirect_chain: list[RedirectHop] = Field(default_factory=list)


class HeadingEvidence(BaseModel):
    level: int
    text: str
    evidence_ref: str


class LinkEvidence(BaseModel):
    href: str
    text: str | None = None
    rel: list[str] = Field(default_factory=list)
    evidence_ref: str


class ImageEvidence(BaseModel):
    src: str
    alt: str | None = None
    evidence_ref: str


class TableEvidence(BaseModel):
    text: str
    evidence_ref: str


class StructuredDataItem(BaseModel):
    kind: Literal["json-ld", "microdata", "opengraph", "microformat", "rdfa", "dublincore"]
    data: dict[str, Any] | list[Any]
    evidence_ref: str


class ContentBlock(BaseModel):
    evidence_ref: str
    text: str
    source_tag: str


class ExtractionWarning(BaseModel):
    code: str
    message: str
    evidence_ref: str
    snippet_hash: str | None = None


class MetadataEvidence(BaseModel):
    title: EvidenceValue
    description: EvidenceValue
    canonical: EvidenceValue
    lang: EvidenceValue


class CrawlAccessEvidence(BaseModel):
    robots_txt: FetchedResource
    sitemap_xml: FetchedResource
    llms_txt: FetchedResource
    llms_full_txt: FetchedResource


class StructureEvidence(BaseModel):
    headings: list[HeadingEvidence] = Field(default_factory=list)
    links: list[LinkEvidence] = Field(default_factory=list)
    images: list[ImageEvidence] = Field(default_factory=list)
    tables: list[TableEvidence] = Field(default_factory=list)


class StructuredDataEvidence(BaseModel):
    json_ld: list[StructuredDataItem] = Field(default_factory=list)
    microdata: list[StructuredDataItem] = Field(default_factory=list)
    opengraph: list[StructuredDataItem] = Field(default_factory=list)
    microformat: list[StructuredDataItem] = Field(default_factory=list)
    rdfa: list[StructuredDataItem] = Field(default_factory=list)
    dublincore: list[StructuredDataItem] = Field(default_factory=list)


class RuleCheckInputs(BaseModel):
    word_count: int
    cjk_char_count: int
    substance_score: int
    content_block_count: int
    heading_count: int
    has_json_ld: bool


class ExtractionInfo(BaseModel):
    parser: Literal["selectolax"] = "selectolax"
    structured_data_parser: Literal["extruct"] = "extruct"
    main_content_extractor: Literal["trafilatura"] = "trafilatura"
    clean_markdown_sha256: str = ""
    warnings: list[ExtractionWarning] = Field(default_factory=list)


class PrimaryEntityCandidate(BaseModel):
    evidence_ref: str
    name: str
    entity_type: Literal["Product", "Organization", "Article", "WebPage", "Unknown"]
    confidence: float
    evidence_refs: list[str] = Field(default_factory=list)


class ContentOutlineItem(BaseModel):
    evidence_ref: str
    heading: str
    level: int
    section_type: Literal["definition", "evidence", "comparison", "procedure", "faq", "generic"]
    evidence_refs: list[str] = Field(default_factory=list)


class AnswerUnitCandidate(BaseModel):
    evidence_ref: str
    unit_type: Literal["definition", "fact", "statistic", "comparison", "procedure", "faq", "quote", "claim", "unknown"]
    text: str
    support_refs: list[str] = Field(default_factory=list)
    source_tag: str
    confidence: float


class ClaimCandidate(BaseModel):
    evidence_ref: str
    text: str
    claim_type: Literal["feature", "benefit", "statistic", "comparison", "pricing", "guarantee", "generic"]
    needs_support: bool
    nearby_evidence_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)


class EvidenceCandidate(BaseModel):
    evidence_ref: str
    text: str
    evidence_type: Literal["source_link", "statistic", "table", "quote", "schema", "benchmark", "generic"]
    source_url: str | None = None
    support_label: Literal["full", "partial", "none", "unknown"] = "unknown"
    evidence_refs: list[str] = Field(default_factory=list)


class StatisticCandidate(BaseModel):
    evidence_ref: str
    value_text: str
    source_url: str | None = None
    has_source: bool = False
    evidence_refs: list[str] = Field(default_factory=list)


class StructuredDataProfile(BaseModel):
    evidence_ref: str = "geo_signals.structured_data_profile"
    types_detected: list[str] = Field(default_factory=list)
    primary_type: str | None = None
    property_completeness: float = 0.0
    visible_alignment: Literal["good", "partial", "poor", "unknown"] = "unknown"
    missing_recommended_properties: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)


class BoilerplateMetrics(BaseModel):
    evidence_ref: str = "geo_signals.boilerplate_metrics"
    content_block_count: int = 0
    word_count: int = 0
    cjk_char_count: int = 0
    substance_score: int = 0
    main_content_confidence: float = 0.0
    boilerplate_ratio: float = 1.0
    first_screen_summary_present: bool = False
    evidence_refs: list[str] = Field(default_factory=list)


class SafetyFlag(BaseModel):
    evidence_ref: str
    flag_type: Literal[
        "html_comment_instruction",
        "metadata_instruction",
        "hidden_text_instruction",
        "script_style_ignored",
        "suspicious_ai_directive",
    ]
    risk_level: Literal["low", "medium", "high"]
    snippet_hash: str
    evidence_refs: list[str] = Field(default_factory=list)


class GeoSignals(BaseModel):
    page_type_hint: Literal["article", "product", "docs", "landing", "comparison", "home", "unknown"] = "unknown"
    page_type_hint_evidence_refs: list[str] = Field(default_factory=list)
    primary_entity_candidates: list[PrimaryEntityCandidate] = Field(default_factory=list)
    content_outline: list[ContentOutlineItem] = Field(default_factory=list)
    answer_unit_candidates: list[AnswerUnitCandidate] = Field(default_factory=list)
    claim_candidates: list[ClaimCandidate] = Field(default_factory=list)
    evidence_candidates: list[EvidenceCandidate] = Field(default_factory=list)
    statistics: list[StatisticCandidate] = Field(default_factory=list)
    structured_data_profile: StructuredDataProfile = Field(default_factory=StructuredDataProfile)
    boilerplate_metrics: BoilerplateMetrics = Field(default_factory=BoilerplateMetrics)
    safety_flags: list[SafetyFlag] = Field(default_factory=list)


class ReadinessScore(BaseModel):
    evidence_ref: str
    score: float
    status: Literal["strong", "mixed", "weak"]
    reasons: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)


class PageContentProfile(BaseModel):
    source_evidence_pack_version: Literal["v1"] = "v1"
    input_url: str
    normalized_url: str
    page_type: Literal["article", "product", "docs", "landing", "comparison", "home", "unknown"] = "unknown"
    page_type_evidence_refs: list[str] = Field(default_factory=list)
    primary_entity_candidates: list[PrimaryEntityCandidate] = Field(default_factory=list)
    content_outline: list[ContentOutlineItem] = Field(default_factory=list)
    answer_units: list[AnswerUnitCandidate] = Field(default_factory=list)
    claim_candidates: list[ClaimCandidate] = Field(default_factory=list)
    evidence_candidates: list[EvidenceCandidate] = Field(default_factory=list)
    statistics: list[StatisticCandidate] = Field(default_factory=list)
    structured_data_profile: StructuredDataProfile = Field(default_factory=StructuredDataProfile)
    boilerplate_metrics: BoilerplateMetrics = Field(default_factory=BoilerplateMetrics)
    prompt_injection_risk: Literal["low", "medium", "high"] = "low"
    safety_flags: list[SafetyFlag] = Field(default_factory=list)
    selection_readiness: ReadinessScore
    absorption_readiness: ReadinessScore
    content_gaps: list[str] = Field(default_factory=list)


class PublicPrimaryEntity(BaseModel):
    name: str
    entity_type: Literal["Product", "Organization", "Article", "WebPage", "Unknown"]
    confidence: float
    evidence_refs: list[str] = Field(default_factory=list)


class PublicReadinessScore(BaseModel):
    score: float
    status: Literal["strong", "mixed", "weak"]
    evidence_refs: list[str] = Field(default_factory=list)


class PublicStructuredDataProfile(BaseModel):
    primary_type: str | None = None
    visible_alignment: Literal["good", "partial", "poor", "unknown"] = "unknown"
    evidence_refs: list[str] = Field(default_factory=list)


class PublicPageContentProfile(BaseModel):
    profile_version: Literal["v1-minimal-public"] = "v1-minimal-public"
    page_type: Literal["article", "product", "docs", "landing", "comparison", "home", "unknown"] = "unknown"
    page_type_evidence_refs: list[str] = Field(default_factory=list)
    primary_entity: PublicPrimaryEntity | None = None
    selection_readiness: PublicReadinessScore
    absorption_readiness: PublicReadinessScore
    prompt_injection_risk: Literal["low", "medium", "high"] = "low"
    structured_data: PublicStructuredDataProfile = Field(default_factory=PublicStructuredDataProfile)


class StorageEvidence(BaseModel):
    analysis_id: UUID
    snapshot_dir: str


class PageEvidencePack(BaseModel):
    input_url: str
    normalized_url: str
    fetch: FetchInfo
    metadata: MetadataEvidence
    crawl_access: CrawlAccessEvidence
    structure: StructureEvidence
    structured_data: StructuredDataEvidence
    content_blocks: list[ContentBlock] = Field(default_factory=list)
    rule_check_inputs: RuleCheckInputs
    extraction: ExtractionInfo = Field(default_factory=ExtractionInfo)
    geo_signals: GeoSignals = Field(default_factory=GeoSignals)
    storage: StorageEvidence


class RuleCheck(BaseModel):
    rule_id: str
    severity: Literal["low", "medium", "high"]
    status: Literal["passed", "failed", "warning"]
    finding: str
    failure_type: str | None = None
    evidence_refs: list[str] = Field(default_factory=list)
    recommendation: str | None = None


class AnalysisResult(BaseModel):
    id: UUID
    input_url: str
    status: Literal["completed", "failed"]
    language: str
    error_code: str | None = None
    page_evidence: PageEvidencePack | None = None
    page_content_profile: PageContentProfile | None = None
    rule_checks: list[RuleCheck] = Field(default_factory=list)
    snapshot_dir: str | None = None
