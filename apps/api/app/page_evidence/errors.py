class PageEvidenceError(Exception):
    error_code = "page_evidence_error"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class UnsafeUrlError(PageEvidenceError):
    error_code = "unsafe_url"


class DnsResolutionError(PageEvidenceError):
    error_code = "dns_resolution_failed"


class FetchError(PageEvidenceError):
    error_code = "fetch_failed"


class NonHtmlResponseError(PageEvidenceError):
    error_code = "non_html_response"
