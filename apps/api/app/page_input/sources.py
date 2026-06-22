from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, Field

from apps.api.app.page_evidence.models import FetchInfo


class FetchedUrlSource(BaseModel):
    source_type: Literal["url"] = "url"
    input_url: str
    normalized_url: str
    html: str
    fetch_info: FetchInfo


class UploadedHtmlSource(BaseModel):
    source_type: Literal["uploaded_html"] = "uploaded_html"
    declared_url: str | None = None
    upload_filename: str | None = None
    upload_sha256: str
    html: str


class PastedHtmlSource(BaseModel):
    source_type: Literal["pasted_html"] = "pasted_html"
    declared_url: str | None = None
    html: str


PageInputSource = Annotated[
    FetchedUrlSource | UploadedHtmlSource | PastedHtmlSource,
    Field(discriminator="source_type"),
]
