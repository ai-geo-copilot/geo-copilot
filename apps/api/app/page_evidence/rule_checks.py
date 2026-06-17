from __future__ import annotations

from .models import PageEvidencePack, RuleCheck


def build_rule_checks(pack: PageEvidencePack) -> list[RuleCheck]:
    findings: list[RuleCheck] = []

    _append_required_metadata(findings, "title", pack.metadata.title.value, "metadata.title")
    _append_required_metadata(
        findings,
        "description",
        pack.metadata.description.value,
        "metadata.description",
    )
    _append_required_metadata(
        findings,
        "canonical",
        pack.metadata.canonical.value,
        "metadata.canonical",
    )
    _append_required_metadata(findings, "lang", pack.metadata.lang.value, "metadata.lang")

    h1_refs = [heading.evidence_ref for heading in pack.structure.headings if heading.level == 1]
    findings.append(
        RuleCheck(
            rule_id="structure.single_h1",
            severity="medium",
            status="passed" if len(h1_refs) == 1 else "failed",
            finding="Exactly one H1 was found." if len(h1_refs) == 1 else f"Expected one H1, found {len(h1_refs)}.",
            evidence_refs=h1_refs,
            recommendation=None if len(h1_refs) == 1 else "Add a single clear H1 heading.",
        )
    )

    has_json_ld = bool(pack.structured_data.json_ld)
    findings.append(
        RuleCheck(
            rule_id="structured_data.json_ld_present",
            severity="low",
            status="passed" if has_json_ld else "warning",
            finding="JSON-LD structured data is present." if has_json_ld else "No JSON-LD structured data was found.",
            evidence_refs=[item.evidence_ref for item in pack.structured_data.json_ld],
            recommendation=None if has_json_ld else "Add relevant structured data where appropriate.",
        )
    )

    enough_content = pack.rule_check_inputs.substance_score >= 150
    findings.append(
        RuleCheck(
            rule_id="content.minimum_substance",
            severity="medium",
            status="passed" if enough_content else "warning",
            finding=(
                "Detected content substance score "
                f"{pack.rule_check_inputs.substance_score} "
                f"(words={pack.rule_check_inputs.word_count}, cjk_chars={pack.rule_check_inputs.cjk_char_count})."
            ),
            evidence_refs=[block.evidence_ref for block in pack.content_blocks[:3]],
            recommendation=None if enough_content else "Add more substantive page content.",
        )
    )
    return findings


def _append_required_metadata(
    findings: list[RuleCheck],
    field_name: str,
    value: str | None,
    evidence_ref: str,
) -> None:
    present = bool(value and value.strip())
    findings.append(
        RuleCheck(
            rule_id=f"metadata.{field_name}_present",
            severity="high" if field_name in {"title", "description"} else "medium",
            status="passed" if present else "failed",
            finding=f"{field_name} is present." if present else f"{field_name} is missing.",
            evidence_refs=[evidence_ref],
            recommendation=None if present else f"Add a {field_name} value.",
        )
    )
