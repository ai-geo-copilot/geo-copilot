from fastapi.testclient import TestClient

from apps.api.app.main import app
from apps.api.app.page_evidence.models import (
    AnalysisResult,
    CrawlAccessEvidence,
    EvidenceValue,
    FetchInfo,
    FetchedResource,
    MetadataEvidence,
    PageEvidencePack,
    RuleCheck,
    RuleCheckInputs,
    StorageEvidence,
    StructureEvidence,
    StructuredDataEvidence,
)
from apps.api.app.routers.analyses import get_analysis_service


client = TestClient(app)


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
                    robots_txt=FetchedResource(url=f"{url}/robots.txt", status_code=404, reachable=True, error_code=None, evidence_ref="crawl_access.robots_txt"),
                    sitemap_xml=FetchedResource(url=f"{url}/sitemap.xml", status_code=404, reachable=True, error_code=None, evidence_ref="crawl_access.sitemap_xml"),
                    llms_txt=FetchedResource(url=f"{url}/llms.txt", status_code=404, reachable=True, error_code=None, evidence_ref="crawl_access.llms_txt"),
                    llms_full_txt=FetchedResource(url=f"{url}/llms-full.txt", status_code=404, reachable=True, error_code=None, evidence_ref="crawl_access.llms_full_txt"),
                ),
                structure=StructureEvidence(),
                structured_data=StructuredDataEvidence(),
                content_blocks=[],
                rule_check_inputs=RuleCheckInputs(
                    word_count=0,
                    content_block_count=0,
                    heading_count=0,
                    has_json_ld=False,
                ),
                storage=StorageEvidence(
                    analysis_id="11111111-1111-1111-1111-111111111111",
                    snapshot_dir="data/analyses/11111111-1111-1111-1111-111111111111",
                ),
            ),
            rule_checks=[
                RuleCheck(
                    rule_id="metadata.title_present",
                    severity="high",
                    status="passed",
                    finding="title is present.",
                    evidence_refs=["metadata.title"],
                )
            ],
            snapshot_dir="data/analyses/11111111-1111-1111-1111-111111111111",
        )

    def get_result(self, analysis_id):
        return self.analyze_safe("https://example.com/", "zh-CN")


app.dependency_overrides[get_analysis_service] = _StubService


def test_health_check() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_analysis_returns_completed_contract() -> None:
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
    assert body["rule_checks"][0]["rule_id"] == "metadata.title_present"
