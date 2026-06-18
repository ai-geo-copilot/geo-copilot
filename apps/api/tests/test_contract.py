from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from apps.api.app.main import app
from apps.api.app.page_evidence.models import (
    AnalysisResult,
    CrawlAccessEvidence,
    EvidenceValue,
    ExtractionInfo,
    FetchInfo,
    FetchedResource,
    GeoSignals,
    MetadataEvidence,
    PageContentProfile,
    PageEvidencePack,
    ReadinessScore,
    RuleCheck,
    RuleCheckInputs,
    StorageEvidence,
    StructureEvidence,
    StructuredDataEvidence,
)
from apps.api.app.routers.analyses import get_analysis_service


class _StubService:
    def analyze_safe(self, url: str, language: str) -> AnalysisResult:
        return AnalysisResult(
            id="11111111-1111-1111-1111-111111111111",
            input_url=url,
            status="completed",
            language=language,
            page_evidence=PageEvidencePack(
                input_url=url,
                normalized_url=url,
                fetch=FetchInfo(
                    final_url=url,
                    status_code=200,
                    content_type="text/html",
                    elapsed_ms=12,
                    html_sha256="abc123",
                    redirect_chain=[],
                ),
                metadata=MetadataEvidence(
                    title=EvidenceValue(value="Example", evidence_ref="metadata.title"),
                    description=EvidenceValue(value="Summary", evidence_ref="metadata.description"),
                    canonical=EvidenceValue(value=url, evidence_ref="metadata.canonical"),
                    lang=EvidenceValue(value="en", evidence_ref="metadata.lang"),
                ),
                crawl_access=CrawlAccessEvidence(
                    robots_txt=FetchedResource(url=f"{url}/robots.txt", status_code=404, reachable=False, status="missing", error_code="not_found", evidence_ref="crawl_access.robots_txt"),
                    sitemap_xml=FetchedResource(url=f"{url}/sitemap.xml", status_code=404, reachable=False, status="missing", error_code="not_found", evidence_ref="crawl_access.sitemap_xml"),
                    llms_txt=FetchedResource(url=f"{url}/llms.txt", status_code=404, reachable=False, status="missing", error_code="not_found", evidence_ref="crawl_access.llms_txt"),
                    llms_full_txt=FetchedResource(url=f"{url}/llms-full.txt", status_code=404, reachable=False, status="missing", error_code="not_found", evidence_ref="crawl_access.llms_full_txt"),
                ),
                structure=StructureEvidence(),
                structured_data=StructuredDataEvidence(
                    json_ld=[],
                    microdata=[],
                    opengraph=[],
                    microformat=[],
                    rdfa=[],
                    dublincore=[],
                ),
                content_blocks=[],
                rule_check_inputs=RuleCheckInputs(
                    word_count=0,
                    cjk_char_count=0,
                    substance_score=0,
                    content_block_count=0,
                    heading_count=0,
                    has_json_ld=False,
                ),
                extraction=ExtractionInfo(clean_markdown_sha256="abc123"),
                geo_signals=GeoSignals(),
                storage=StorageEvidence(
                    analysis_id="11111111-1111-1111-1111-111111111111",
                    snapshot_dir="data/analyses/11111111-1111-1111-1111-111111111111",
                ),
            ),
            page_content_profile=PageContentProfile(
                input_url=url,
                normalized_url=url,
                page_type="article",
                page_type_evidence_refs=["structured_data.json_ld[0]"],
                primary_entity_candidates=[],
                content_outline=[],
                answer_units=[],
                claim_candidates=[],
                evidence_candidates=[],
                statistics=[],
                structured_data_profile={
                    "primary_type": "Article",
                    "visible_alignment": "good",
                    "evidence_refs": ["structured_data.json_ld[0]"],
                },
                boilerplate_metrics={
                    "content_block_count": 0,
                    "word_count": 0,
                    "cjk_char_count": 0,
                    "substance_score": 0,
                    "main_content_confidence": 0.0,
                    "boilerplate_ratio": 1.0,
                    "first_screen_summary_present": False,
                    "evidence_refs": [],
                },
                prompt_injection_risk="low",
                safety_flags=[],
                selection_readiness=ReadinessScore(
                    evidence_ref="page_content_profile.selection_readiness",
                    score=1.0,
                    status="strong",
                    reasons=["title_present"],
                    evidence_refs=["metadata.title"],
                ),
                absorption_readiness=ReadinessScore(
                    evidence_ref="page_content_profile.absorption_readiness",
                    score=0.7,
                    status="strong",
                    reasons=["definition_unit_present"],
                    evidence_refs=["geo_signals.answer_unit_candidates[0]"],
                ),
                content_gaps=[],
            ),
            rule_checks=[
                RuleCheck(
                    rule_id="metadata.title_missing",
                    severity="high",
                    status="passed",
                    finding="title is present.",
                    failure_type="selection_blocker",
                    evidence_refs=["metadata.title"],
                )
            ],
            snapshot_dir="data/analyses/11111111-1111-1111-1111-111111111111",
        )

    def get_result(self, analysis_id):
        return self.analyze_safe("https://example.com/", "zh-CN")


@pytest.fixture
def client() -> Iterator[TestClient]:
    app.dependency_overrides[get_analysis_service] = lambda request=None: _StubService()
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()


def test_lifespan_registers_page_evidence_service() -> None:
    with TestClient(app) as client:
        assert hasattr(client.app.state, "page_evidence_service")


def test_health_check(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_analysis_returns_completed_contract(client: TestClient) -> None:
    response = client.post(
        "/api/analyses",
        json={"url": "https://example.com", "language": "zh-CN"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["input_url"] == "https://example.com/"
    assert body["status"] == "completed"
    assert body["language"] == "zh-CN"
    assert body["error_code"] is None
    assert body["page_evidence"]["metadata"]["title"]["value"] == "Example"
    assert body["page_evidence"]["extraction"]["parser"] == "selectolax"
    assert body["page_evidence"]["geo_signals"]["page_type_hint"] == "unknown"
    assert body["page_content_profile"]["profile_version"] == "v1-minimal-public"
    assert body["page_content_profile"]["page_type"] == "article"
    assert body["page_content_profile"]["selection_readiness"]["status"] == "strong"
    assert body["page_content_profile"]["structured_data"]["primary_type"] == "Article"
    assert body["rule_checks"][0]["rule_id"] == "metadata.title_missing"


def test_get_analysis_returns_minimal_public_page_content_profile(client: TestClient) -> None:
    response = client.get("/api/analyses/11111111-1111-1111-1111-111111111111")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert body["snapshot_dir"] == "data/analyses/11111111-1111-1111-1111-111111111111"
    assert body["page_content_profile"]["absorption_readiness"]["score"] == 0.7
    assert "content_gaps" not in body["page_content_profile"]
    assert "answer_units" not in body["page_content_profile"]
