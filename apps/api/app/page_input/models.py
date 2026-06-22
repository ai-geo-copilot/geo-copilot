from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class PageInputContext(BaseModel):
    context_version: Literal["page-input-context-v0"] = "page-input-context-v0"
    source_type: Literal["url", "uploaded_html", "pasted_html", "pasted_markdown"]
    input_url: str | None = None
    declared_url: str | None = None
    upload_filename: str | None = None
    upload_sha256: str | None = None
    language: str
    business_type: str | None = None
    target_keywords: list[str] = Field(default_factory=list)
    target_audience: str | None = None
    conversion_goal: str | None = None
    market: str | None = None
    brand_facts: list[str] = Field(default_factory=list)
    forbidden_claims: list[str] = Field(default_factory=list)
