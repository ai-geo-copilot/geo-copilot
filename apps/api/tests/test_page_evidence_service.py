from pathlib import Path
import socket

import httpx

from apps.api.app.page_evidence.fetcher import PageFetcher
from apps.api.app.page_evidence.service import PageEvidenceService
from apps.api.app.page_evidence.storage import SnapshotStorage
from apps.api.app.page_evidence.url_safety import validate_public_url


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
    assert result.page_evidence.rule_check_inputs.substance_score >= result.page_evidence.rule_check_inputs.word_count
    assert any(check.rule_id == "metadata.title_present" and check.status == "passed" for check in result.rule_checks)
    assert any(check.rule_id == "structure.single_h1" and check.status == "passed" for check in result.rule_checks)
    assert any(check.rule_id == "content.minimum_substance" and check.status == "warning" for check in result.rule_checks)
    assert Path(result.snapshot_dir or "").exists()
    assert (Path(result.snapshot_dir or "") / "raw.html").exists()
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


def test_page_evidence_service_counts_cjk_substance(tmp_path: Path) -> None:
    html = """
    <html lang="zh-CN">
      <head>
        <title>中文页面</title>
        <meta name="description" content="中文摘要" />
        <link rel="canonical" href="https://example.com/zh" />
      </head>
      <body>
        <h1>中文标题</h1>
        <p>这是一个用于验证中文内容计数的页面。这里包含足够多的中文字符用于内容质量判断。</p>
        <p>继续补充一些中文文本，确保 substance score 不是依赖空格分词。</p>
      </body>
    </html>
    """

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/":
            return httpx.Response(200, headers={"content-type": "text/html; charset=utf-8"}, text=html, request=request)
        return httpx.Response(404, text="missing", request=request)

    service = PageEvidenceService(
        fetcher=PageFetcher(client=httpx.Client(transport=httpx.MockTransport(handler)), resolver=_resolver),
        storage=SnapshotStorage(root_dir=tmp_path),
        resolver=_resolver,
    )

    result = service.analyze("https://example.com", "zh-CN")

    assert result.page_evidence is not None
    assert result.page_evidence.rule_check_inputs.word_count > 0
    assert result.page_evidence.rule_check_inputs.cjk_char_count > 0
    assert result.page_evidence.rule_check_inputs.substance_score == result.page_evidence.rule_check_inputs.cjk_char_count
