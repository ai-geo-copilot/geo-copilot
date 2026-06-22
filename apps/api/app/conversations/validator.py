from __future__ import annotations

from .models import INTENT_ASSET_TYPES, ConversationSafePack, CopilotTurn

_FORBIDDEN_ANSWER_PHRASES = (
    "<html",
    "<script",
    "<style",
    "<!--",
    "guarantee ranking",
    "guaranteed ranking",
    "guarantee ai citation",
    "guaranteed ai citation",
    "保证排名",
    "保证被引用",
)


def validate_copilot_turn(turn: CopilotTurn, pack: ConversationSafePack) -> CopilotTurn:
    if turn.analysis_id != pack.analysis_id:
        raise ValueError("copilot turn analysis_id does not match request")
    if turn.intent not in pack.allowed_intents:
        raise ValueError("copilot turn intent is not allowed")
    _validate_refs("evidence_ref", turn.evidence_refs, pack.known_evidence_refs)
    _validate_refs("method_ref", turn.method_refs, pack.known_method_refs)
    _validate_forbidden_text(turn.answer)

    if _needs_evidence(turn) and not turn.evidence_refs:
        raise ValueError("copilot turn page facts must include evidence_refs")
    if _needs_method(turn) and not turn.method_refs:
        raise ValueError("copilot turn recommendations must include method_refs")

    allowed_asset_types = INTENT_ASSET_TYPES.get(turn.intent, set())
    if not allowed_asset_types and turn.asset_drafts:
        raise ValueError("copilot turn intent does not allow asset drafts")

    for draft in turn.asset_drafts:
        if draft.asset_type not in pack.allowed_asset_types:
            raise ValueError("copilot asset draft type is not allowed")
        if allowed_asset_types and draft.asset_type not in allowed_asset_types:
            raise ValueError("copilot asset draft type does not match intent")
        _validate_refs("asset evidence_ref", draft.evidence_refs, pack.known_evidence_refs)
        _validate_refs("asset method_ref", draft.method_refs, pack.known_method_refs)
        if draft.draft_text:
            _validate_forbidden_text(draft.draft_text)
    for unknown in turn.unknowns:
        _validate_refs("unknown evidence_ref", unknown.evidence_refs, pack.known_evidence_refs)
    return turn


def _validate_refs(label: str, refs: list[str], known_refs: list[str]) -> None:
    known = set(known_refs)
    unknown = [ref for ref in refs if ref not in known]
    if unknown:
        raise ValueError(f"unknown {label}: {unknown[0]}")


def _validate_forbidden_text(text: str) -> None:
    lowered = text.lower()
    for phrase in _FORBIDDEN_ANSWER_PHRASES:
        if phrase in lowered:
            raise ValueError("copilot turn contains forbidden content")


def _needs_evidence(turn: CopilotTurn) -> bool:
    return turn.intent != "ask_unknown" or bool(turn.asset_drafts)


def _needs_method(turn: CopilotTurn) -> bool:
    return turn.intent in {
        "prioritize_actions",
        "draft_metadata",
        "draft_definition_block",
        "draft_faq",
        "draft_json_ld",
        "request_evidence",
        "compare_options",
    }
