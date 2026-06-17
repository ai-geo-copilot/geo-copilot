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
