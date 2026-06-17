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
    kind: Literal["json-ld"]
    data: dict[str, Any] | list[Any]
    evidence_ref: str


class ContentBlock(BaseModel):
    evidence_ref: str
    text: str
    source_tag: str


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


class RuleCheckInputs(BaseModel):
    word_count: int
    cjk_char_count: int
    substance_score: int
    content_block_count: int
    heading_count: int
    has_json_ld: bool


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
    storage: StorageEvidence


class RuleCheck(BaseModel):
    rule_id: str
    severity: Literal["low", "medium", "high"]
    status: Literal["passed", "failed", "warning"]
    finding: str
    evidence_refs: list[str] = Field(default_factory=list)
    recommendation: str | None = None


class AnalysisResult(BaseModel):
    id: UUID
    input_url: str
    status: Literal["completed", "failed"]
    language: str
    error_code: str | None = None
    page_evidence: PageEvidencePack | None = None
    rule_checks: list[RuleCheck] = Field(default_factory=list)
    snapshot_dir: str | None = None
