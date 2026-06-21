import json
from pathlib import Path
import socket

import httpx

from apps.api.app.page_evidence.fetcher import PageFetcher
from apps.api.app.page_evidence.service import PageEvidenceService
from apps.api.app.page_evidence.storage import SnapshotStorage
from apps.api.app.page_evidence.url_safety import validate_public_url


FIXTURES_DIR = Path(__file__).parent / "fixtures" / "html"


def _resolver(_: str) -> list[str]:
    return ["93.184.216.34"]


def _read_fixture(name: str) -> str:
    return (FIXTURES_DIR / name).read_text(encoding="utf-8")


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
    assert result.page_evidence.rule_check_inputs.substance_score >= result.page_evidence.rule_check_inputs.word_count
    assert result.page_evidence.extraction.parser == "selectolax"
    assert result.page_evidence.geo_signals.page_type_hint == "article"
    assert result.page_content_profile is not None
    assert result.page_content_profile.page_type == "article"
    assert any(check.rule_id == "metadata.title_missing" and check.status == "passed" for check in result.rule_checks)
    assert any(check.rule_id == "structure.h1_missing_or_multiple" and check.status == "passed" for check in result.rule_checks)
    assert any(
        check.rule_id == "content.minimum_substance_low" and check.status in {"warning", "failed", "passed"}
        for check in result.rule_checks
    )
    assert Path(result.snapshot_dir or "").exists()
    assert (Path(result.snapshot_dir or "") / "raw.html").exists()
    assert (Path(result.snapshot_dir or "") / "page_content_profile.json").exists()
    assert (Path(result.snapshot_dir or "") / "retrieved_methods.json").exists()
    assert (Path(result.snapshot_dir or "") / "strategy_plan.json").exists()
    assert (Path(result.snapshot_dir or "") / "safe_prompt_pack.json").exists()
    assert (Path(result.snapshot_dir or "") / "analysis.json").exists()
    assert result.page_evidence.crawl_access.robots_txt.status == "missing"


def test_page_evidence_service_returns_failed_result_for_unsafe_url(tmp_path: Path) -> None:
    service = PageEvidenceService(storage=SnapshotStorage(root_dir=tmp_path), resolver=lambda _: ["127.0.0.1"])

    result = service.analyze_safe("http://localhost/test", "zh-CN")

    assert result.status == "failed"
    assert result.error_code == "unsafe_url"


def test_validate_public_url_returns_dns_error_for_resolution_failure() -> None:
    def failing_resolver(_: str) -> list[str]:
        raise socket.gaierror("lookup failed")

    try:
        validate_public_url("https://example.com", resolver=failing_resolver)
    except Exception as exc:  # pragma: no cover - assertion follows immediately
        assert getattr(exc, "error_code", None) == "dns_resolution_failed"
    else:  # pragma: no cover
        raise AssertionError("Expected DNS resolution failure")


def test_fetcher_rejects_non_html_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, headers={"content-type": "application/json"}, text="{}", request=request)

    fetcher = PageFetcher(client=httpx.Client(transport=httpx.MockTransport(handler)), resolver=_resolver)

    try:
        fetcher.fetch_html("https://example.com")
    except Exception as exc:  # pragma: no cover - assertion follows immediately
        assert getattr(exc, "error_code", None) == "non_html_response"
    else:  # pragma: no cover
        raise AssertionError("Expected non-html response error")


def test_fetcher_rejects_large_response_body() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            headers={"content-type": "text/html"},
            text="<html><body>" + ("a" * 300) + "</body></html>",
            request=request,
        )

    fetcher = PageFetcher(
        client=httpx.Client(transport=httpx.MockTransport(handler)),
        resolver=_resolver,
        max_bytes=100,
    )

    try:
        fetcher.fetch_html("https://example.com")
    except Exception as exc:  # pragma: no cover - assertion follows immediately
        assert getattr(exc, "error_code", None) == "fetch_failed"
    else:  # pragma: no cover
        raise AssertionError("Expected fetch failure for oversized body")


def test_fetcher_rejects_large_response_body_from_content_length_header() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            headers={"content-type": "text/html", "content-length": "1000"},
            text="<html><body>small body</body></html>",
            request=request,
        )

    fetcher = PageFetcher(
        client=httpx.Client(transport=httpx.MockTransport(handler)),
        resolver=_resolver,
        max_bytes=100,
    )

    try:
        fetcher.fetch_html("https://example.com")
    except Exception as exc:  # pragma: no cover - assertion follows immediately
        assert getattr(exc, "error_code", None) == "fetch_failed"
    else:  # pragma: no cover
        raise AssertionError("Expected fetch failure for oversized content-length header")


def test_fetcher_rejects_too_many_redirects() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            302,
            headers={"location": "/loop"},
            request=request,
        )

    fetcher = PageFetcher(
        client=httpx.Client(transport=httpx.MockTransport(handler)),
        resolver=_resolver,
        max_redirects=1,
    )

    try:
        fetcher.fetch_html("https://example.com")
    except Exception as exc:  # pragma: no cover - assertion follows immediately
        assert getattr(exc, "error_code", None) == "fetch_failed"
    else:  # pragma: no cover
        raise AssertionError("Expected too many redirects failure")


def test_fetcher_rejects_redirect_to_private_ip() -> None:
    def redirect_handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/":
            return httpx.Response(302, headers={"location": "http://10.0.0.1/private"}, request=request)
        return httpx.Response(200, headers={"content-type": "text/html"}, text="<html></html>", request=request)

    fetcher = PageFetcher(
        client=httpx.Client(transport=httpx.MockTransport(redirect_handler)),
        resolver=lambda hostname: ["10.0.0.1"] if hostname == "10.0.0.1" else ["93.184.216.34"],
    )

    try:
        fetcher.fetch_html("https://example.com")
    except Exception as exc:  # pragma: no cover - assertion follows immediately
        assert getattr(exc, "error_code", None) == "unsafe_url"
    else:  # pragma: no cover
        raise AssertionError("Expected unsafe redirect rejection")


def test_page_evidence_service_handles_dns_failures(tmp_path: Path) -> None:
    def failing_resolver(_: str) -> list[str]:
        raise socket.gaierror("lookup failed")

    service = PageEvidenceService(storage=SnapshotStorage(root_dir=tmp_path), resolver=failing_resolver)

    result = service.analyze_safe("https://example.com", "zh-CN")

    assert result.status == "failed"
    assert result.error_code == "dns_resolution_failed"


def test_page_evidence_service_reuses_url_validation_for_main_and_auxiliary_fetches(tmp_path: Path) -> None:
    html = _read_fixture("article_jsonld_good.html")
    page_url = "https://example.com/guides/what-is-geo"
    resolve_calls: list[str] = []

    def counting_resolver(hostname: str) -> list[str]:
        resolve_calls.append(hostname)
        return ["93.184.216.34"]

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/guides/what-is-geo":
            return httpx.Response(200, headers={"content-type": "text/html; charset=utf-8"}, text=html, request=request)
        return httpx.Response(404, text="missing", request=request)

    service = PageEvidenceService(
        fetcher=PageFetcher(client=httpx.Client(transport=httpx.MockTransport(handler)), resolver=counting_resolver),
        storage=SnapshotStorage(root_dir=tmp_path),
        resolver=counting_resolver,
    )

    result = service.analyze(page_url, "zh-CN")

    assert result.status == "completed"
    assert resolve_calls == ["example.com"]


def test_page_evidence_service_counts_cjk_substance(tmp_path: Path) -> None:
    html = _read_fixture("cjk_product_page.html")
    page_url = "https://example.com/zh/products/geo-helper-pro"

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/zh/products/geo-helper-pro":
            return httpx.Response(200, headers={"content-type": "text/html; charset=utf-8"}, text=html, request=request)
        return httpx.Response(404, text="missing", request=request)

    service = PageEvidenceService(
        fetcher=PageFetcher(client=httpx.Client(transport=httpx.MockTransport(handler)), resolver=_resolver),
        storage=SnapshotStorage(root_dir=tmp_path),
        resolver=_resolver,
    )

    result = service.analyze(page_url, "zh-CN")

    assert result.page_evidence is not None
    assert result.page_evidence.rule_check_inputs.cjk_char_count > 0
    assert result.page_evidence.rule_check_inputs.substance_score == result.page_evidence.rule_check_inputs.cjk_char_count
    assert result.page_evidence.geo_signals.page_type_hint == "product"
    assert result.page_content_profile is not None
    assert result.page_content_profile.page_type == "product"
    assert any(check.rule_id == "schema.structured_data_missing" and check.status == "passed" for check in result.rule_checks)


def test_page_evidence_service_supports_cjk_docs_fixture(tmp_path: Path) -> None:
    html = _read_fixture("cjk_docs_howto_page.html")
    page_url = "https://example.com/zh/docs/setup-geo-checks"

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/zh/docs/setup-geo-checks":
            return httpx.Response(200, headers={"content-type": "text/html; charset=utf-8"}, text=html, request=request)
        return httpx.Response(404, text="missing", request=request)

    service = PageEvidenceService(
        fetcher=PageFetcher(client=httpx.Client(transport=httpx.MockTransport(handler)), resolver=_resolver),
        storage=SnapshotStorage(root_dir=tmp_path),
        resolver=_resolver,
    )

    result = service.analyze(page_url, "zh-CN")

    assert result.page_evidence is not None
    assert result.page_evidence.geo_signals.page_type_hint == "docs"
    assert result.page_content_profile is not None
    assert result.page_content_profile.page_type == "docs"
    assert any(check.rule_id == "schema.structured_data_missing" and check.status == "failed" for check in result.rule_checks)


def test_page_evidence_service_snapshot_persists_evidence_and_rule_outputs(tmp_path: Path) -> None:
    html = _read_fixture("opengraph_only_landing.html")
    page_url = "https://example.com/platform/geowidget"

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/platform/geowidget":
            return httpx.Response(200, headers={"content-type": "text/html; charset=utf-8"}, text=html, request=request)
        return httpx.Response(404, text="missing", request=request)

    service = PageEvidenceService(
        fetcher=PageFetcher(client=httpx.Client(transport=httpx.MockTransport(handler)), resolver=_resolver),
        storage=SnapshotStorage(root_dir=tmp_path),
        resolver=_resolver,
    )

    result = service.analyze(page_url, "zh-CN")

    snapshot_dir = Path(result.snapshot_dir or "")
    evidence_payload = json.loads((snapshot_dir / "evidence.json").read_text(encoding="utf-8"))
    profile_payload = json.loads((snapshot_dir / "page_content_profile.json").read_text(encoding="utf-8"))
    rule_payload = json.loads((snapshot_dir / "rule_checks.json").read_text(encoding="utf-8"))
    analysis_payload = json.loads((snapshot_dir / "analysis.json").read_text(encoding="utf-8"))
    retrieved_methods_payload = json.loads((snapshot_dir / "retrieved_methods.json").read_text(encoding="utf-8"))
    strategy_plan_payload = json.loads((snapshot_dir / "strategy_plan.json").read_text(encoding="utf-8"))
    safe_prompt_payload = json.loads((snapshot_dir / "safe_prompt_pack.json").read_text(encoding="utf-8"))

    assert evidence_payload["geo_signals"]["page_type_hint"] == "landing"
    assert profile_payload["page_type"] == "landing"
    assert profile_payload["selection_readiness"]["evidence_ref"] == "page_content_profile.selection_readiness"
    assert evidence_payload["structured_data"]["opengraph"]
    assert evidence_payload["metadata"]["title"]["evidence_ref"] == "metadata.title"
    assert evidence_payload["geo_signals"]["primary_entity_candidates"][0]["evidence_ref"] == "geo_signals.primary_entity_candidates[0]"
    assert analysis_payload["page_evidence"]["storage"]["snapshot_dir"] == str(snapshot_dir)
    assert analysis_payload["page_content_profile"]["page_type"] == "landing"
    assert "retrieved_methods" not in analysis_payload
    assert "strategy_plan" not in analysis_payload
    assert retrieved_methods_payload["selection_mode"] == "deterministic_v0"
    assert strategy_plan_payload["strategy_steps"]
    assert safe_prompt_payload["pack_version"] == "safe-prompt-pack-v0"
    assert "raw_html" in safe_prompt_payload["safety_policy"]["forbidden_inputs"]
    assert any(
        item["rule_id"] == "schema.structured_data_missing"
        and item["status"] == "passed"
        and item["evidence_refs"]
        for item in rule_payload
    )


def test_snapshot_storage_load_result_round_trips_analysis(tmp_path: Path) -> None:
    html = _read_fixture("rdfa_article.html")

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/":
            return httpx.Response(200, headers={"content-type": "text/html; charset=utf-8"}, text=html, request=request)
        return httpx.Response(404, text="missing", request=request)

    storage = SnapshotStorage(root_dir=tmp_path)
    service = PageEvidenceService(
        fetcher=PageFetcher(client=httpx.Client(transport=httpx.MockTransport(handler)), resolver=_resolver),
        storage=storage,
        resolver=_resolver,
    )

    result = service.analyze("https://example.com", "zh-CN")
    reloaded = storage.load_result(result.id)
    reloaded_methods = storage.load_retrieved_methods(result.id)
    reloaded_strategy = storage.load_strategy_plan(result.id)
    reloaded_safe_prompt = storage.load_safe_prompt_pack(result.id)

    assert reloaded is not None
    assert reloaded_methods is not None
    assert reloaded_strategy is not None
    assert reloaded_safe_prompt is not None
    assert reloaded.id == result.id
    assert reloaded.page_evidence is not None
    assert reloaded.page_content_profile is not None
    assert reloaded.page_content_profile.page_type == "article"
    assert reloaded.page_evidence.geo_signals.page_type_hint == "article"
    assert reloaded.page_evidence.structured_data.rdfa
    assert reloaded.rule_checks == result.rule_checks
    assert reloaded_methods.selection_mode == "deterministic_v0"
    assert reloaded_strategy.strategy_steps
    assert reloaded_safe_prompt.pack_version == "safe-prompt-pack-v0"
