from __future__ import annotations

from collections import OrderedDict

from .models import (
    PageContentProfile,
    PageEvidencePack,
    PublicPageContentProfile,
    PublicPrimaryEntity,
    PublicReadinessScore,
    PublicStructuredDataProfile,
    ReadinessScore,
)


def build_page_content_profile(pack: PageEvidencePack) -> PageContentProfile:
    geo_signals = pack.geo_signals

    selection_readiness = _build_selection_readiness(pack)
    absorption_readiness = _build_absorption_readiness(pack)

    return PageContentProfile(
        input_url=pack.input_url,
        normalized_url=pack.normalized_url,
        page_type=geo_signals.page_type_hint,
        page_type_evidence_refs=geo_signals.page_type_hint_evidence_refs,
        primary_entity_candidates=[item.model_copy(deep=True) for item in geo_signals.primary_entity_candidates],
        content_outline=[item.model_copy(deep=True) for item in geo_signals.content_outline],
        answer_units=[item.model_copy(deep=True) for item in geo_signals.answer_unit_candidates],
        claim_candidates=[item.model_copy(deep=True) for item in geo_signals.claim_candidates],
        evidence_candidates=[item.model_copy(deep=True) for item in geo_signals.evidence_candidates],
        statistics=[item.model_copy(deep=True) for item in geo_signals.statistics],
        structured_data_profile=geo_signals.structured_data_profile.model_copy(deep=True),
        boilerplate_metrics=geo_signals.boilerplate_metrics.model_copy(deep=True),
        prompt_injection_risk=_highest_risk(geo_signals.safety_flags),
        safety_flags=[item.model_copy(deep=True) for item in geo_signals.safety_flags],
        selection_readiness=selection_readiness,
        absorption_readiness=absorption_readiness,
        content_gaps=_build_content_gaps(pack),
    )


def build_public_page_content_profile(profile: PageContentProfile) -> PublicPageContentProfile:
    primary_entity = profile.primary_entity_candidates[0] if profile.primary_entity_candidates else None
    return PublicPageContentProfile(
        page_type=profile.page_type,
        page_type_evidence_refs=list(profile.page_type_evidence_refs),
        primary_entity=(
            None
            if primary_entity is None
            else PublicPrimaryEntity(
                name=primary_entity.name,
                entity_type=primary_entity.entity_type,
                confidence=primary_entity.confidence,
                evidence_refs=list(primary_entity.evidence_refs),
            )
        ),
        selection_readiness=PublicReadinessScore(
            score=profile.selection_readiness.score,
            status=profile.selection_readiness.status,
            evidence_refs=list(profile.selection_readiness.evidence_refs),
        ),
        absorption_readiness=PublicReadinessScore(
            score=profile.absorption_readiness.score,
            status=profile.absorption_readiness.status,
            evidence_refs=list(profile.absorption_readiness.evidence_refs),
        ),
        prompt_injection_risk=profile.prompt_injection_risk,
        structured_data=PublicStructuredDataProfile(
            primary_type=profile.structured_data_profile.primary_type,
            visible_alignment=profile.structured_data_profile.visible_alignment,
            evidence_refs=list(profile.structured_data_profile.evidence_refs),
        ),
    )


def _build_selection_readiness(pack: PageEvidencePack) -> ReadinessScore:
    reasons: list[str] = []
    evidence_refs: list[str] = []
    score = 0.0

    if pack.metadata.title.value:
        score += 0.15
        reasons.append("title_present")
        evidence_refs.append(pack.metadata.title.evidence_ref)
    if pack.metadata.canonical.value:
        score += 0.1
        reasons.append("canonical_present")
        evidence_refs.append(pack.metadata.canonical.evidence_ref)
    if pack.metadata.lang.value:
        score += 0.1
        reasons.append("lang_present")
        evidence_refs.append(pack.metadata.lang.evidence_ref)
    if pack.geo_signals.primary_entity_candidates:
        score += 0.25
        reasons.append("primary_entity_detected")
        evidence_refs.extend(pack.geo_signals.primary_entity_candidates[0].evidence_refs)
    if pack.geo_signals.structured_data_profile.types_detected:
        score += 0.2
        reasons.append("structured_data_detected")
        evidence_refs.extend(pack.geo_signals.structured_data_profile.evidence_refs)
    if pack.geo_signals.structured_data_profile.visible_alignment in {"good", "partial"}:
        score += 0.1
        reasons.append(f"structured_data_alignment_{pack.geo_signals.structured_data_profile.visible_alignment}")
        evidence_refs.append(pack.geo_signals.structured_data_profile.evidence_ref)
    if any(heading.level == 1 for heading in pack.structure.headings):
        score += 0.1
        reasons.append("h1_present")
        evidence_refs.extend(heading.evidence_ref for heading in pack.structure.headings if heading.level == 1)

    score = round(min(score, 1.0), 3)
    return ReadinessScore(
        evidence_ref="page_content_profile.selection_readiness",
        score=score,
        status=_status_for_score(score),
        reasons=reasons,
        evidence_refs=_dedupe(evidence_refs),
    )


def _build_absorption_readiness(pack: PageEvidencePack) -> ReadinessScore:
    reasons: list[str] = []
    evidence_refs: list[str] = []
    score = 0.0

    has_definition = any(item.unit_type == "definition" for item in pack.geo_signals.answer_unit_candidates)
    has_comparison = any(item.unit_type == "comparison" for item in pack.geo_signals.answer_unit_candidates)
    has_procedure = any(item.unit_type == "procedure" for item in pack.geo_signals.answer_unit_candidates)
    has_statistics = bool(pack.geo_signals.statistics)
    supported_claims = [
        claim for claim in pack.geo_signals.claim_candidates if (not claim.needs_support) or claim.nearby_evidence_refs
    ]

    confidence = pack.geo_signals.boilerplate_metrics.main_content_confidence
    if confidence >= 0.7:
        score += 0.3
        reasons.append("main_content_confidence_high")
    elif confidence >= 0.5:
        score += 0.2
        reasons.append("main_content_confidence_adequate")
    elif confidence > 0:
        score += 0.1
        reasons.append("main_content_confidence_low")
    evidence_refs.append(pack.geo_signals.boilerplate_metrics.evidence_ref)
    evidence_refs.extend(pack.geo_signals.boilerplate_metrics.evidence_refs)

    if has_definition:
        score += 0.2
        reasons.append("definition_unit_present")
        evidence_refs.extend(item.evidence_ref for item in pack.geo_signals.answer_unit_candidates if item.unit_type == "definition")
    if has_comparison:
        score += 0.1
        reasons.append("comparison_unit_present")
        evidence_refs.extend(item.evidence_ref for item in pack.geo_signals.answer_unit_candidates if item.unit_type == "comparison")
    if has_procedure:
        score += 0.1
        reasons.append("procedure_unit_present")
        evidence_refs.extend(item.evidence_ref for item in pack.geo_signals.answer_unit_candidates if item.unit_type == "procedure")
    if has_statistics:
        score += 0.1
        reasons.append("statistics_present")
        evidence_refs.extend(item.evidence_ref for item in pack.geo_signals.statistics[:3])
    if supported_claims:
        score += 0.2
        reasons.append("supported_claim_present")
        evidence_refs.extend(item.evidence_ref for item in supported_claims[:3])

    score = round(min(score, 1.0), 3)
    return ReadinessScore(
        evidence_ref="page_content_profile.absorption_readiness",
        score=score,
        status=_status_for_score(score),
        reasons=reasons,
        evidence_refs=_dedupe(evidence_refs),
    )


def _build_content_gaps(pack: PageEvidencePack) -> list[str]:
    gaps: list[str] = []
    if not pack.geo_signals.primary_entity_candidates:
        gaps.append("primary_entity_unclear")
    if pack.geo_signals.page_type_hint != "home" and not any(
        item.unit_type == "definition" for item in pack.geo_signals.answer_unit_candidates
    ):
        gaps.append("definition_unit_missing")
    if any(claim.needs_support and not claim.nearby_evidence_refs for claim in pack.geo_signals.claim_candidates):
        gaps.append("unsupported_claims_present")
    if pack.geo_signals.page_type_hint in {"article", "product", "docs"} and not pack.geo_signals.structured_data_profile.types_detected:
        gaps.append("structured_data_missing_for_page_type")
    if pack.geo_signals.boilerplate_metrics.main_content_confidence < 0.5:
        gaps.append("main_content_confidence_low")
    if pack.geo_signals.safety_flags:
        gaps.append("prompt_injection_risk_present")
    return gaps


def _highest_risk(flags: list) -> str:
    if any(flag.risk_level == "high" for flag in flags):
        return "high"
    if any(flag.risk_level == "medium" for flag in flags):
        return "medium"
    return "low"


def _status_for_score(score: float) -> str:
    if score >= 0.7:
        return "strong"
    if score >= 0.4:
        return "mixed"
    return "weak"


def _dedupe(values: list[str]) -> list[str]:
    return list(OrderedDict.fromkeys(value for value in values if value))
