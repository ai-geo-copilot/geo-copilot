import json
from pathlib import Path

from apps.api.app.page_evidence.models import PageEvidencePack


SCHEMA_PATH = Path(__file__).resolve().parents[3] / "packages" / "contracts" / "schemas" / "page-evidence-pack.schema.json"


def test_page_evidence_pack_schema_matches_model() -> None:
    expected = PageEvidencePack.model_json_schema()
    expected["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    expected["$id"] = "https://geo-copilot.local/schemas/page-evidence-pack.schema.json"

    actual = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

    assert actual == expected
