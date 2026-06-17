from pathlib import Path

import httpx

from apps.api.app.page_evidence.fetcher import PageFetcher
from apps.api.app.page_evidence.service import PageEvidenceService
from apps.api.app.page_evidence.storage import SnapshotStorage


def _resolver(_: str) -> list[str]:
    return ["93.184.216.34"]


def test_page_evidence_service_builds_snapshot_and_rule_checks(tmp_path: Path) -> None:
    html = """
    <html lang="en">
      <head>
        <title>Example Article</title>
        <meta name="description" content="Helpful summary." />
        <link rel="canonical" href="https://example.com/article" />
        <script type="application/ld+json">
          {"@context":"https://schema.org","@type":"Article","headline":"Example Article"}
        </script>
      </head>
      <body>
        <h1>Example Article</h1>
        <p>This page explains how GEO analysis can inspect title tags and page structure.</p>
        <p>It also provides enough body copy to exceed the low-content threshold for the baseline checks.</p>
        <a href="/more">Read more</a>
        <img src="/hero.png" alt="Hero image" />
      </body>
    </html>
    """

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/":
            return httpx.Response(
                200,
                headers={"content-type": "text/html; charset=utf-8"},
                text=html,
                request=request,
            )
        return httpx.Response(404, text="missing", request=request)

    client = httpx.Client(transport=httpx.MockTransport(handler), timeout=2.0)
    service = PageEvidenceService(
        fetcher=PageFetcher(client=client, resolver=_resolver),
        storage=SnapshotStorage(root_dir=tmp_path),
        resolver=_resolver,
    )

    result = service.analyze("https://example.com", "zh-CN")

    assert result.status == "completed"
    assert result.page_evidence is not None
    assert result.page_evidence.metadata.title.value == "Example Article"
    assert result.page_evidence.metadata.description.value == "Helpful summary."
    assert result.page_evidence.rule_check_inputs.has_json_ld is True
    assert any(check.rule_id == "metadata.title_present" and check.status == "passed" for check in result.rule_checks)
    assert any(check.rule_id == "structure.single_h1" and check.status == "passed" for check in result.rule_checks)
    assert Path(result.snapshot_dir or "").exists()
    assert (Path(result.snapshot_dir or "") / "raw.html").exists()
    assert (Path(result.snapshot_dir or "") / "analysis.json").exists()


def test_page_evidence_service_returns_failed_result_for_unsafe_url(tmp_path: Path) -> None:
    service = PageEvidenceService(storage=SnapshotStorage(root_dir=tmp_path), resolver=lambda _: ["127.0.0.1"])

    result = service.analyze_safe("http://localhost/test", "zh-CN")

    assert result.status == "failed"
    assert result.error_code == "unsafe_url"
