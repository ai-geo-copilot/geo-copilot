import json
from pathlib import Path

from apps.api.app.page_evidence.models import PageContentProfile


SCHEMA_PATH = Path(__file__).resolve().parents[3] / "packages" / "contracts" / "schemas" / "page-content-profile.schema.json"


def test_page_content_profile_schema_matches_model() -> None:
    expected = PageContentProfile.model_json_schema()
    expected["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    expected["$id"] = "https://geo-copilot.local/schemas/page-content-profile.schema.json"

    actual = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

    assert actual == expected
