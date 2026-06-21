import json
from pathlib import Path

from apps.api.app.diagnosis.models import (
    AssetDraft,
    DeepSeekDiagnosis,
    DiagnosisIssue,
    DiagnosisScoreBreakdown,
    DiagnosisUnknown,
    PriorityAction,
)
from apps.api.app.diagnosis.validator import validate_deepseek_diagnosis
from apps.api.app.methods.models import (
    RetrievedMethodChunk,
    RetrievedMethodPack,
    RetrievalQuery,
    StrategyPlan,
    StrategyStep,
)
from apps.api.app.page_evidence.models import PublicReadinessScore, PublicStructuredDataProfile, RuleCheck
from apps.api.app.safe_prompt.models import (
    SafeEvidenceExcerpt,
    SafePrimaryEntity,
    SafeProfileFacts,
    SafePromptPack,
    SafePromptSafetyPolicy,
)


ROOT_DIR = Path(__file__).resolve().parents[3]


def test_deepseek_diagnosis_validator_accepts_bound_output() -> None:
    safe_pack = _safe_prompt_pack()
    diagnosis = _diagnosis()

    validated = validate_deepseek_diagnosis(diagnosis, safe_pack)

    assert validated.geo_score == 64
    assert validated.issues[0].evidence_refs == ["content_blocks[0]"]
    assert validated.priority_actions[0].method_refs == ["chunk_geo_claim_evidence_pair_001"]


def test_deepseek_diagnosis_validator_rejects_unknown_method_ref() -> None:
    safe_pack = _safe_prompt_pack()
    diagnosis = _diagnosis().model_copy(
        update={
            "issues": [
                _diagnosis().issues[0].model_copy(update={"method_refs": ["chunk_unknown_001"]})
            ]
        }
    )

    try:
        validate_deepseek_diagnosis(diagnosis, safe_pack)
    except ValueError as exc:
        assert "unknown method_refs" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("Expected unknown method_ref to fail validation")


def test_deepseek_diagnosis_validator_rejects_unsupported_claim_as_supported_fact() -> None:
    safe_pack = _safe_prompt_pack()
    diagnosis = _diagnosis().model_copy(
        update={
            "issues": [
                _diagnosis().issues[0].model_copy(update={"factual_status": "supported"})
            ]
        }
    )

    try:
        validate_deepseek_diagnosis(diagnosis, safe_pack)
    except ValueError as exc:
        assert "unsupported claim" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("Expected unsupported claim assertion to fail validation")


def test_deepseek_diagnosis_schema_matches_model() -> None:
    expected = DeepSeekDiagnosis.model_json_schema()
    expected["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    expected["$id"] = "https://geo-copilot.local/schemas/deepseek-diagnosis.schema.json"
    actual = json.loads(
        (ROOT_DIR / "packages" / "contracts" / "schemas" / "deepseek-diagnosis.schema.json").read_text(
            encoding="utf-8"
        )
    )

    assert actual == expected


def _safe_prompt_pack() -> SafePromptPack:
    return SafePromptPack(
        input_url="https://example.com/page",
        normalized_url="https://example.com/page",
        facts=SafeProfileFacts(
            page_type="article",
            page_type_evidence_refs=["geo_signals.page_type_hint"],
            primary_entity=SafePrimaryEntity(
                name="Example",
                entity_type="Article",
                confidence=0.9,
                evidence_refs=["metadata.title"],
            ),
            selection_readiness=PublicReadinessScore(
                score=0.8,
                status="strong",
                evidence_refs=["metadata.title"],
            ),
            absorption_readiness=PublicReadinessScore(
                score=0.4,
                status="mixed",
                evidence_refs=["content_blocks[0]"],
            ),
            prompt_injection_risk="low",
            structured_data=PublicStructuredDataProfile(
                primary_type="Article",
                visible_alignment="good",
                evidence_refs=["structured_data.json_ld[0]"],
            ),
            content_gaps=["unsupported_claims_present"],
        ),
        rule_checks=[
            RuleCheck(
                rule_id="content.claim_without_evidence",
                severity="high",
                status="failed",
                finding="Found unsupported claims.",
                failure_type="claim_evidence_blocker",
                evidence_refs=["content_blocks[0]"],
            )
        ],
        retrieved_methods=RetrievedMethodPack(
            compiled_method_pack_version="method-pack-v0",
            retrieval_query=RetrievalQuery(
                page_type="article",
                failed_rule_ids=["content.claim_without_evidence"],
                warning_rule_ids=[],
                failure_types=["claim_evidence_blocker"],
            ),
            chunks=[
                RetrievedMethodChunk(
                    method_ref="chunk_geo_claim_evidence_pair_001",
                    title="Claim Evidence Pairing",
                    text="Pair claims with nearby evidence.",
                    why_selected="Selected because content.claim_without_evidence failed.",
                    matched_rule_ids=["content.claim_without_evidence"],
                    matched_failure_types=["claim_evidence_blocker"],
                    matched_evidence_refs=["content_blocks[0]"],
                    strategy_group="claim_evidence_strengthening",
                    expected_artifacts=["claim_evidence_patch"],
                    guardrails=["Unsupported claims must remain unknown or be removed."],
                    score=155,
                )
            ],
        ),
        strategy_plan=StrategyPlan(
            strategy_steps=[
                StrategyStep(
                    step_id="strategy_step_001",
                    strategy_group="claim_evidence_strengthening",
                    rank=50,
                    method_refs=["chunk_geo_claim_evidence_pair_001"],
                    rule_ids=["content.claim_without_evidence"],
                    failure_types=["claim_evidence_blocker"],
                    evidence_refs=["content_blocks[0]"],
                    why_now="Claim evidence is missing.",
                    expected_artifacts=["claim_evidence_patch"],
                    validator_requirements=["Every recommendation must include evidence_refs and method_refs."],
                )
            ]
        ),
        evidence_excerpts=[
            SafeEvidenceExcerpt(
                evidence_ref="content_blocks[0]",
                text="Example claim without nearby source.",
                source="content_block",
            )
        ],
        safety_policy=SafePromptSafetyPolicy(
            forbidden_inputs=["raw_html", "full_clean_markdown"],
            required_bindings=["issues must cite evidence_refs"],
            unknown_handling=["unsupported claims remain unknown"],
        ),
    )


def _diagnosis() -> DeepSeekDiagnosis:
    return DeepSeekDiagnosis(
        geo_score=64,
        score_breakdown=DiagnosisScoreBreakdown(
            selection=80,
            absorption=55,
            claim_evidence=35,
            structure=80,
            schema_alignment=75,
            safety=100,
        ),
        executive_summary="The page has usable selection signals but unsupported claims need evidence.",
        issues=[
            DiagnosisIssue(
                issue_id="issue_001",
                title="Unsupported claim lacks nearby evidence",
                severity="high",
                rule_ids=["content.claim_without_evidence"],
                failure_types=["claim_evidence_blocker"],
                evidence_refs=["content_blocks[0]"],
                method_refs=["chunk_geo_claim_evidence_pair_001"],
                factual_status="unknown",
                explanation="The claim should remain unknown until supporting evidence is added.",
            )
        ],
        priority_actions=[
            PriorityAction(
                action_id="action_001",
                title="Request source evidence for the claim",
                priority="P0",
                issue_ids=["issue_001"],
                evidence_refs=["content_blocks[0]"],
                method_refs=["chunk_geo_claim_evidence_pair_001"],
                action_type="request_evidence",
                expected_artifacts=["claim_evidence_patch"],
                rationale="Unsupported claims require a nearby citation or source.",
            )
        ],
        asset_drafts=[
            AssetDraft(
                asset_id="asset_001",
                asset_type="claim_evidence_patch",
                evidence_refs=["content_blocks[0]"],
                method_refs=["chunk_geo_claim_evidence_pair_001"],
                draft_text=None,
                unknown_fields=["supporting_source_url"],
                guardrails=["Do not invent source URLs."],
            )
        ],
        unknowns=[
            DiagnosisUnknown(
                unknown_id="unknown_001",
                question="What source supports the claim?",
                reason="No nearby source was found in the page evidence.",
                evidence_refs=["content_blocks[0]"],
                related_issue_ids=["issue_001"],
            )
        ],
    )
