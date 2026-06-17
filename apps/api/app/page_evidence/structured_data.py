from __future__ import annotations

import json
from typing import Any

from .models import StructuredDataEvidence, StructuredDataItem


def parse_json_ld(script_contents: list[str]) -> StructuredDataEvidence:
    items: list[StructuredDataItem] = []
    for index, content in enumerate(script_contents):
        try:
            parsed: dict[str, Any] | list[Any] = json.loads(content)
        except json.JSONDecodeError:
            continue
        items.append(
            StructuredDataItem(
                kind="json-ld",
                data=parsed,
                evidence_ref=f"structured_data.json_ld[{index}]",
            )
        )
    return StructuredDataEvidence(json_ld=items)
