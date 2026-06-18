from __future__ import annotations

from .models import PageContentProfile, PageEvidencePack, RuleCheck
from .page_content_profile import build_page_content_profile


def build_rule_checks(pack: PageEvidencePack, profile: PageContentProfile | None = None) -> list[RuleCheck]:
    findings: list[RuleCheck] = []
    profile = profile or build_page_content_profile(pack)

    _append_metadata_check(findings, pack, "title", pack.metadata.title.value, "high")
    _append_metadata_check(findings, pack, "description", pack.metadata.description.value, "medium")
    _append_metadata_check(findings, pack, "canonical", pack.metadata.canonical.value, "medium")
    _append_metadata_check(findings, pack, "lang", pack.metadata.lang.value, "medium")

    h1_refs = [heading.evidence_ref for heading in pack.structure.headings if heading.level == 1]
    findings.append(
        RuleCheck(
            rule_id="structure.h1_missing_or_multiple",
            severity="high",
            status="passed" if len(h1_refs) == 1 else "failed",
            finding="Exactly one H1 heading was found." if len(h1_refs) == 1 else f"Expected exactly one H1 heading, found {len(h1_refs)}.",
            failure_type="structure_blocker",
            evidence_refs=h1_refs or [heading.evidence_ref for heading in pack.structure.headings[:3]],
            recommendation=None if len(h1_refs) == 1 else "Keep exactly one primary H1 heading on the page.",
        )
    )

    hierarchy_refs = [heading.evidence_ref for heading in pack.structure.headings]
    hierarchy_valid = _is_heading_hierarchy_valid(pack)
    findings.append(
        RuleCheck(
            rule_id="structure.heading_hierarchy_invalid",
            severity="medium",
            status="passed" if hierarchy_valid else "failed",
            finding="Heading hierarchy is consistent." if hierarchy_valid else "Heading levels skip or reset in a way that weakens page structure.",
            failure_type="structure_blocker",
            evidence_refs=hierarchy_refs,
            recommendation=None if hierarchy_valid else "Use a sequential heading hierarchy without skipped levels.",
        )
    )

    substance_status = "passed"
    if pack.rule_check_inputs.substance_score < 50:
        substance_status = "failed"
    elif pack.rule_check_inputs.substance_score < 150:
        substance_status = "warning"
    findings.append(
        RuleCheck(
            rule_id="content.minimum_substance_low",
            severity="medium",
            status=substance_status,
            finding=(
                "Detected content substance score "
                f"{pack.rule_check_inputs.substance_score} "
                f"(words={pack.rule_check_inputs.word_count}, cjk_chars={pack.rule_check_inputs.cjk_char_count})."
            ),
            failure_type="absorption_blocker",
            evidence_refs=pack.geo_signals.boilerplate_metrics.evidence_refs,
            recommendation=None if substance_status == "passed" else "Add more substantive, page-specific content with verifiable facts.",
        )
    )

    confidence_ok = pack.geo_signals.boilerplate_metrics.main_content_confidence >= 0.5
    findings.append(
        RuleCheck(
            rule_id="content.main_content_confidence_low",
            severity="high",
            status="passed" if confidence_ok else "failed",
            finding=(
                "Main content confidence is "
                f"{pack.geo_signals.boilerplate_metrics.main_content_confidence:.3f}."
            ),
            failure_type="absorption_blocker",
            evidence_refs=[pack.geo_signals.boilerplate_metrics.evidence_ref],
            recommendation=None if confidence_ok else "Reduce boilerplate and strengthen the visible main content.",
        )
    )

    needs_definition = pack.geo_signals.page_type_hint != "home"
    has_definition = any(candidate.unit_type == "definition" for candidate in pack.geo_signals.answer_unit_candidates)
    findings.append(
        RuleCheck(
            rule_id="content.definition_unit_missing",
            severity="high",
            status="passed" if has_definition or not needs_definition else "failed",
            finding="A definition-like answer unit is present." if has_definition else "No clear definition-like answer unit was found.",
            failure_type="absorption_blocker",
            evidence_refs=pack.geo_signals.page_type_hint_evidence_refs or pack.geo_signals.boilerplate_metrics.evidence_refs,
            recommendation=None if has_definition or not needs_definition else "Add a concise definition or summary block near the top of the page.",
        )
    )
    findings.append(_build_readiness_rule(profile, "selection"))
    findings.append(_build_readiness_rule(profile, "absorption"))

    unsupported_claims = [claim for claim in pack.geo_signals.claim_candidates if claim.needs_support and not claim.nearby_evidence_refs]
    findings.append(
        RuleCheck(
            rule_id="content.claim_without_evidence",
            severity="high",
            status="passed" if not unsupported_claims else "failed",
            finding="Claims have nearby supporting evidence." if not unsupported_claims else f"Found {len(unsupported_claims)} claim candidate(s) without nearby support.",
            failure_type="claim_evidence_blocker",
            evidence_refs=[claim.evidence_ref for claim in unsupported_claims] or [claim.evidence_ref for claim in pack.geo_signals.claim_candidates[:3]],
            recommendation=None if not unsupported_claims else "Place citations, tables, or source links next to claims that require support.",
        )
    )

    unsupported_statistics = [stat for stat in pack.geo_signals.statistics if not stat.has_source]
    findings.append(
        RuleCheck(
            rule_id="content.numeric_claim_without_source",
            severity="high",
            status="passed" if not unsupported_statistics else "failed",
            finding="Numeric claims have source cues." if not unsupported_statistics else f"Found {len(unsupported_statistics)} numeric claim candidate(s) without a visible source cue.",
            failure_type="claim_evidence_blocker",
            evidence_refs=[stat.evidence_ref for stat in unsupported_statistics] or [stat.evidence_ref for stat in pack.geo_signals.statistics[:3]],
            recommendation=None if not unsupported_statistics else "Add dates, source labels, or citations next to numeric claims.",
        )
    )

    structured_items_present = bool(pack.geo_signals.structured_data_profile.types_detected)
    needs_schema = pack.geo_signals.page_type_hint in {"article", "product", "docs"}
    findings.append(
        RuleCheck(
            rule_id="schema.structured_data_missing",
            severity="medium",
            status="passed" if structured_items_present or not needs_schema else "failed",
            finding="Relevant structured data is present." if structured_items_present else "No structured data was detected for a page type that usually benefits from it.",
            failure_type="selection_blocker",
            evidence_refs=pack.geo_signals.structured_data_profile.evidence_refs or [pack.geo_signals.structured_data_profile.evidence_ref],
            recommendation=None if structured_items_present or not needs_schema else "Add structured data that matches the page type and visible content.",
        )
    )

    alignment_poor = pack.geo_signals.structured_data_profile.visible_alignment == "poor"
    findings.append(
        RuleCheck(
            rule_id="schema.visible_alignment_poor",
            severity="high",
            status="failed" if alignment_poor else "passed",
            finding="Structured data matches visible page content." if not alignment_poor else "Structured data claims are not well aligned with visible page content.",
            failure_type="schema_blocker",
            evidence_refs=[pack.geo_signals.structured_data_profile.evidence_ref],
            recommendation=None if not alignment_poor else "Align schema properties with facts users can actually see on the page.",
        )
    )

    product_incomplete = (
        pack.geo_signals.page_type_hint == "product"
        and (
            bool(pack.geo_signals.structured_data_profile.missing_recommended_properties)
            or pack.geo_signals.structured_data_profile.visible_alignment == "poor"
        )
    )
    findings.append(
        RuleCheck(
            rule_id="schema.product_incomplete",
            severity="medium",
            status="warning" if product_incomplete else "passed",
            finding="Product schema signals look complete." if not product_incomplete else "Product schema is missing recommended fields or signals.",
            failure_type="schema_blocker",
            evidence_refs=[pack.geo_signals.structured_data_profile.evidence_ref],
            recommendation=None if not product_incomplete else "Add name, offers, and rating or review inputs where they are truly present.",
        )
    )

    article_incomplete = pack.geo_signals.page_type_hint == "article" and bool(pack.geo_signals.structured_data_profile.missing_recommended_properties)
    findings.append(
        RuleCheck(
            rule_id="schema.article_incomplete",
            severity="medium",
            status="warning" if article_incomplete else "passed",
            finding="Article schema signals look complete." if not article_incomplete else "Article schema is missing recommended fields or signals.",
            failure_type="schema_blocker",
            evidence_refs=[pack.geo_signals.structured_data_profile.evidence_ref],
            recommendation=None if not article_incomplete else "Add headline, date, author, and image signals where they are truly present.",
        )
    )

    findings.append(
        RuleCheck(
            rule_id="safety.prompt_injection_suspected",
            severity="high",
            status="failed" if pack.geo_signals.safety_flags else "passed",
            finding="No suspicious AI-directed instructions were detected." if not pack.geo_signals.safety_flags else f"Detected {len(pack.geo_signals.safety_flags)} suspicious AI-directed instruction signal(s).",
            failure_type="safety_blocker",
            evidence_refs=[flag.evidence_ref for flag in pack.geo_signals.safety_flags],
            recommendation=None if not pack.geo_signals.safety_flags else "Remove hidden or non-user-facing AI instructions from comments, metadata, and hidden text.",
        )
    )

    return findings


def _append_metadata_check(
    findings: list[RuleCheck],
    pack: PageEvidencePack,
    field_name: str,
    value: str | None,
    severity: str,
) -> None:
    present = bool(value and value.strip())
    findings.append(
        RuleCheck(
            rule_id=f"metadata.{field_name}_missing",
            severity=severity,  # type: ignore[arg-type]
            status="passed" if present else "failed",
            finding=f"{field_name} is present." if present else f"{field_name} is missing.",
            failure_type="selection_blocker",
            evidence_refs=[getattr(pack.metadata, field_name).evidence_ref],
            recommendation=None if present else f"Add a {field_name} value that reflects visible page content.",
        )
    )


def _is_heading_hierarchy_valid(pack: PageEvidencePack) -> bool:
    previous_level: int | None = None
    for heading in pack.structure.headings:
        if previous_level is not None and heading.level > previous_level + 1:
            return False
        previous_level = heading.level
    return True


def _build_readiness_rule(profile: PageContentProfile, readiness_type: str) -> RuleCheck:
    readiness = profile.selection_readiness if readiness_type == "selection" else profile.absorption_readiness
    gap_refs = profile.page_type_evidence_refs if readiness_type == "selection" else profile.boilerplate_metrics.evidence_refs
    related_gaps = _related_gaps(profile, readiness_type)
    status = "passed"
    if readiness.status == "weak":
        status = "failed"
    elif readiness.status == "mixed":
        status = "warning"

    gap_suffix = ""
    if related_gaps:
        gap_suffix = " Gaps: " + ", ".join(related_gaps) + "."

    recommendation = None
    if status != "passed":
        recommendation = (
            "Strengthen selection signals with clearer metadata, entity cues, and aligned schema."
            if readiness_type == "selection"
            else "Strengthen answer-ready content with clearer definitions, evidence, and visible main content."
        )

    return RuleCheck(
        rule_id=f"{readiness_type}.readiness_low",
        severity="medium" if readiness_type == "selection" else "high",
        status=status,  # type: ignore[arg-type]
        finding=(
            f"{readiness_type.capitalize()} readiness score is {readiness.score:.3f} "
            f"({readiness.status}).{gap_suffix}"
        ),
        failure_type=f"{readiness_type}_blocker",
        evidence_refs=readiness.evidence_refs or gap_refs or [readiness.evidence_ref],
        recommendation=recommendation,
    )


def _related_gaps(profile: PageContentProfile, readiness_type: str) -> list[str]:
    if readiness_type == "selection":
        relevant = {
            "primary_entity_unclear",
            "structured_data_missing_for_page_type",
        }
    else:
        relevant = {
            "definition_unit_missing",
            "unsupported_claims_present",
            "main_content_confidence_low",
            "prompt_injection_risk_present",
        }
    return [gap for gap in profile.content_gaps if gap in relevant]
