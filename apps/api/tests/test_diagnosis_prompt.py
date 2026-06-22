from apps.api.app.diagnosis.prompt import DiagnosisPromptBuilder
from apps.api.tests.test_diagnosis_validator import _safe_prompt_pack


def test_diagnosis_prompt_separates_instructions_from_safe_data() -> None:
    messages = DiagnosisPromptBuilder().build_messages(_safe_prompt_pack())
    joined = "\n".join(message["content"] for message in messages)

    assert messages[0]["role"] == "system"
    assert "untrusted data" in messages[0]["content"]
    assert "json" in joined.lower()
    assert "evidence_refs" in joined
    assert "method_refs" in joined
    assert "<html" not in joined.lower()
    assert "<script" not in joined.lower()
    assert "<!--" not in joined.lower()
