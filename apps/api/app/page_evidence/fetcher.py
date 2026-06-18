from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import hashlib
import threading
import time
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse

import httpx

from .errors import FetchError, NonHtmlResponseError, PageEvidenceError
from .models import FetchInfo, FetchedResource, RedirectHop
from .url_safety import Resolver, validate_public_url


@dataclass
class FetchResult:
    fetch_info: FetchInfo
    html: str


class PageFetcher:
    def __init__(
        self,
        client: httpx.Client | None = None,
        *,
        timeout_seconds: float = 10.0,
        max_redirects: int = 5,
        max_bytes: int = 1_000_000,
        max_auxiliary_workers: int = 4,
        resolver: Resolver | None = None,
    ) -> None:
        self._client = client or httpx.Client(
            timeout=timeout_seconds,
            trust_env=False,
            limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
        )
        self._owns_client = client is None
        self._timeout_seconds = timeout_seconds
        self._max_redirects = max_redirects
        self._max_bytes = max_bytes
        self._max_auxiliary_workers = max(1, max_auxiliary_workers)
        self._resolver = resolver
        self._validated_url_cache: dict[str, str] = {}
        self._validated_url_cache_lock = threading.Lock()

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def validate_public_url(self, url: str) -> str:
        return self._validate_public_url_cached(url)

    def fetch_html(self, url: str) -> FetchResult:
        current_url = self._validate_public_url_cached(url)
        redirects: list[RedirectHop] = []
        started = time.perf_counter()

        for _ in range(self._max_redirects + 1):
            try:
                with self._client.stream("GET", current_url, follow_redirects=False) as response:
                    if 300 <= response.status_code < 400:
                        location = response.headers.get("location")
                        if not location:
                            raise FetchError("Redirect response missing location header.")
                        next_url = self._validate_public_url_cached(
                            urljoin(current_url, location),
                        )
                        redirects.append(
                            RedirectHop(
                                from_url=current_url,
                                to_url=next_url,
                                status_code=response.status_code,
                            )
                        )
                        current_url = next_url
                        continue

                    content_type = response.headers.get("content-type", "")
                    if "text/html" not in content_type and "application/xhtml+xml" not in content_type:
                        raise NonHtmlResponseError(f"Unsupported content type: {content_type or 'unknown'}")
                    if _content_length_exceeds_limit(response.headers.get("content-length"), self._max_bytes):
                        raise FetchError("Response body exceeded the size limit.")

                    chunks: list[bytes] = []
                    total_bytes = 0
                    for chunk in response.iter_bytes():
                        total_bytes += len(chunk)
                        if total_bytes > self._max_bytes:
                            raise FetchError("Response body exceeded the size limit.")
                        chunks.append(chunk)

                    html_bytes = b"".join(chunks)
                    encoding = response.encoding or "utf-8"
                    elapsed_ms = int((time.perf_counter() - started) * 1000)
                    html_sha256 = hashlib.sha256(html_bytes).hexdigest()
                    return FetchResult(
                        fetch_info=FetchInfo(
                            final_url=str(response.url),
                            status_code=response.status_code,
                            content_type=content_type,
                            elapsed_ms=elapsed_ms,
                            html_sha256=html_sha256,
                            redirect_chain=redirects,
                        ),
                        html=html_bytes.decode(encoding, errors="replace"),
                    )
            except httpx.TimeoutException as exc:
                raise FetchError("Request timed out.") from exc
            except httpx.HTTPError as exc:
                raise FetchError("HTTP request failed.") from exc

        raise FetchError("Too many redirects.")

    def fetch_auxiliary(self, page_url: str, path: str, evidence_ref: str) -> FetchedResource:
        resource_url = self._build_auxiliary_url(page_url, path)
        return self._fetch_auxiliary_resource(resource_url, evidence_ref)

    def fetch_auxiliary_bundle(self, page_url: str, resources: list[tuple[str, str]]) -> dict[str, FetchedResource]:
        if not resources:
            return {}

        jobs = [
            (evidence_ref, self._build_auxiliary_url(page_url, path))
            for path, evidence_ref in resources
        ]
        if len(jobs) == 1:
            evidence_ref, resource_url = jobs[0]
            return {evidence_ref: self._fetch_auxiliary_resource(resource_url, evidence_ref)}

        max_workers = min(self._max_auxiliary_workers, len(jobs))
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                evidence_ref: executor.submit(self._fetch_auxiliary_resource, resource_url, evidence_ref)
                for evidence_ref, resource_url in jobs
            }
        return {
            evidence_ref: future.result()
            for evidence_ref, future in futures.items()
        }

    def _fetch_auxiliary_resource(self, resource_url: str, evidence_ref: str) -> FetchedResource:
        try:
            response = self._client.get(resource_url, follow_redirects=False, timeout=self._timeout_seconds)
        except httpx.TimeoutException:
            return FetchedResource(
                url=resource_url,
                reachable=False,
                status="request_failed",
                error_code="request_failed",
                evidence_ref=evidence_ref,
            )
        except (PageEvidenceError, httpx.HTTPError):
            return FetchedResource(
                url=resource_url,
                reachable=False,
                status="request_failed",
                error_code="request_failed",
                evidence_ref=evidence_ref,
            )

        status_code = response.status_code
        if status_code == 200:
            status_name = "present"
            reachable = True
            error_code = None
        elif status_code == 403:
            status_name = "forbidden"
            reachable = False
            error_code = "forbidden"
        elif status_code == 404:
            status_name = "missing"
            reachable = False
            error_code = "not_found"
        elif 300 <= status_code < 400:
            status_name = "redirect"
            reachable = False
            error_code = "redirect_not_followed"
        elif status_code >= 500:
            status_name = "server_error"
            reachable = False
            error_code = "server_error"
        else:
            status_name = "request_failed"
            reachable = False
            error_code = "unexpected_status"

        return FetchedResource(
            url=resource_url,
            status_code=status_code,
            reachable=reachable,
            status=status_name,
            error_code=error_code,
            evidence_ref=evidence_ref,
        )

    def _validate_public_url_cached(self, url: str) -> str:
        with self._validated_url_cache_lock:
            cached = self._validated_url_cache.get(url)
        if cached is not None:
            return cached

        validated = validate_public_url(url, resolver=self._resolver)
        with self._validated_url_cache_lock:
            self._validated_url_cache[url] = validated
        return validated

    def _build_auxiliary_url(self, page_url: str, path: str) -> str:
        safe_page_url = self._validate_public_url_cached(page_url)
        resource_url = urljoin(safe_page_url, path)
        if _origin_changed(safe_page_url, resource_url):
            return self._validate_public_url_cached(resource_url)
        return resource_url


def _origin_changed(base_url: str, candidate_url: str) -> bool:
    return (
        urlparse(base_url).scheme,
        urlparse(base_url).hostname,
        urlparse(base_url).port,
    ) != (
        urlparse(candidate_url).scheme,
        urlparse(candidate_url).hostname,
        urlparse(candidate_url).port,
    )


def _content_length_exceeds_limit(content_length: str | None, max_bytes: int) -> bool:
    if content_length is None:
        return False
    try:
        parsed_length = int(content_length)
    except ValueError:
        return False
    return parsed_length > max_bytes
