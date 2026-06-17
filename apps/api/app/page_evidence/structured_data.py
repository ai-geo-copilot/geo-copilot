from __future__ import annotations

from typing import Any

import extruct
from w3lib.html import get_base_url

from .models import StructuredDataEvidence, StructuredDataItem


_STRUCTURED_KINDS = (
    "json-ld",
    "microdata",
    "opengraph",
    "microformat",
    "rdfa",
    "dublincore",
)


def parse_structured_data(html: str, base_url: str) -> StructuredDataEvidence:
    extracted = extruct.extract(
        html,
        base_url=get_base_url(html, base_url),
        uniform=True,
    )
    buckets: dict[str, list[StructuredDataItem]] = {kind: [] for kind in _STRUCTURED_KINDS}

    for kind in _STRUCTURED_KINDS:
        for index, item in enumerate(extracted.get(kind, [])):
            data = item if isinstance(item, (dict, list)) else {"value": item}
            buckets[kind].append(
                StructuredDataItem(
                    kind=kind,
                    data=data,
                    evidence_ref=f"structured_data.{kind.replace('-', '_')}[{index}]",
                )
            )

    return StructuredDataEvidence(
        json_ld=buckets["json-ld"],
        microdata=buckets["microdata"],
        opengraph=buckets["opengraph"],
        microformat=buckets["microformat"],
        rdfa=buckets["rdfa"],
        dublincore=buckets["dublincore"],
    )


def iter_structured_data_items(structured_data: StructuredDataEvidence) -> list[StructuredDataItem]:
    return [
        *structured_data.json_ld,
        *structured_data.microdata,
        *structured_data.opengraph,
        *structured_data.microformat,
        *structured_data.rdfa,
        *structured_data.dublincore,
    ]


def collect_structured_type_refs(structured_data: StructuredDataEvidence) -> list[tuple[str, str]]:
    type_refs: list[tuple[str, str]] = []
    for item in iter_structured_data_items(structured_data):
        for value in _extract_type_values(item.data):
            normalized = _normalize_type_name(value)
            if normalized:
                type_refs.append((normalized, item.evidence_ref))
    return type_refs


def _extract_type_values(data: dict[str, Any] | list[Any]) -> list[str]:
    if isinstance(data, list):
        values: list[str] = []
        for entry in data:
            if isinstance(entry, (dict, list)):
                values.extend(_extract_type_values(entry))
        return values
    if not isinstance(data, dict):
        return []

    values: list[str] = []
    for key in ("@type", "type", "og:type"):
        raw_value = data.get(key)
        if isinstance(raw_value, list):
            values.extend(str(value) for value in raw_value)
        elif raw_value is not None:
            values.append(str(raw_value))
    properties = data.get("properties")
    if isinstance(properties, dict):
        values.extend(_extract_type_values(properties))
    return values


def _normalize_type_name(value: str) -> str:
    if not value:
        return ""
    normalized = value.rsplit("/", 1)[-1].rsplit("#", 1)[-1]
    return normalized.strip()
