from __future__ import annotations

from collections import OrderedDict
from collections.abc import Iterable
import re
from urllib.parse import urlparse

from .content_blocks import ContentMetrics
from .models import (
    AnswerUnitCandidate,
    BoilerplateMetrics,
    ClaimCandidate,
    ContentBlock,
    ContentOutlineItem,
    EvidenceCandidate,
    ExtractionWarning,
    GeoSignals,
    MetadataEvidence,
    PrimaryEntityCandidate,
    SafetyFlag,
    StatisticCandidate,
    StructureEvidence,
    StructuredDataEvidence,
    StructuredDataProfile,
)
from .structured_data import collect_structured_type_refs, iter_structured_data_items

_DEFINITION_PATTERNS = (r"\bis\b", r"refers to", r"defined as", r"是什么", r"是一种", r"指的是")
_COMPARISON_PATTERNS = (r"\bvs\b", r"compare", r"comparison", r"alternative", r"对比", r"比较")
_DOCS_PATTERNS = (r"how to", r"guide", r"docs", r"\bapi\b", r"steps", r"tutorial", r"教程", r"指南", r"步骤")
_CLAIM_PATTERNS = (r"\bbest\b", r"\bfastest\b", r"leading", r"领先", r"唯一", r"保证", r"提升", r"降低", r"支持", r"兼容")
_SOURCE_HINT_PATTERNS = (r"according to", r"source", r"report", r"study", r"benchmark", r"citation", r"来源", r"研究")
_NUMERIC_PATTERN = re.compile(r"(\d[\d,]*(?:\.\d+)?%?|\$\d[\d,]*(?:\.\d+)?)")


def build_geo_signals(
    *,
    base_url: str,
    metadata: MetadataEvidence,
    structure: StructureEvidence,
    content_blocks: list[ContentBlock],
    structured_data: StructuredDataEvidence,
    content_metrics: ContentMetrics,
    extraction_warnings: list[ExtractionWarning],
) -> GeoSignals:
    type_refs = collect_structured_type_refs(structured_data)
    page_type_hint, page_type_refs = _detect_page_type(
        base_url=base_url,
        metadata=metadata,
        structure=structure,
        content_metrics=content_metrics,
        type_refs=type_refs,
    )
    evidence_candidates = _build_evidence_candidates(structure, structured_data, content_blocks)
    statistics = _build_statistics(content_blocks, structure)
    claim_candidates = _build_claim_candidates(content_blocks, evidence_candidates, statistics)

    return GeoSignals(
        page_type_hint=page_type_hint,
        page_type_hint_evidence_refs=page_type_refs,
        primary_entity_candidates=_build_primary_entities(base_url, metadata, structure, type_refs, structured_data, page_type_hint),
        content_outline=_build_content_outline(structure),
        answer_unit_candidates=_build_answer_units(content_blocks, structure),
        claim_candidates=claim_candidates,
        evidence_candidates=evidence_candidates,
        statistics=statistics,
        structured_data_profile=_build_structured_data_profile(metadata, structure, content_blocks, structured_data, type_refs),
        boilerplate_metrics=BoilerplateMetrics(
            content_block_count=content_metrics.content_block_count,
            word_count=content_metrics.word_count,
            cjk_char_count=content_metrics.cjk_char_count,
            substance_score=content_metrics.substance_score,
            main_content_confidence=content_metrics.main_content_confidence,
            boilerplate_ratio=content_metrics.boilerplate_ratio,
            first_screen_summary_present=content_metrics.first_screen_summary_present,
            evidence_refs=content_metrics.evidence_refs,
        ),
        safety_flags=_build_safety_flags(extraction_warnings),
    )


def _detect_page_type(
    *,
    base_url: str,
    metadata: MetadataEvidence,
    structure: StructureEvidence,
    content_metrics: ContentMetrics,
    type_refs: list[tuple[str, str]],
) -> tuple[str, list[str]]:
    lowered_types = [(value.casefold(), ref) for value, ref in type_refs]
    for value, ref in lowered_types:
        if value in {"article", "newsarticle", "blogposting", "report"}:
            return "article", [ref]
        if value == "product":
            return "product", [ref]

    title = metadata.title.value or ""
    heading_text = " ".join(heading.text for heading in structure.headings)
    combined = f"{title} {heading_text}".casefold()

    if _matches_any(combined, _COMPARISON_PATTERNS):
        refs = [metadata.title.evidence_ref]
        refs.extend(heading.evidence_ref for heading in structure.headings[:2])
        return "comparison", refs
    if _matches_any(combined, _DOCS_PATTERNS):
        refs = [metadata.title.evidence_ref]
        refs.extend(heading.evidence_ref for heading in structure.headings[:2])
        return "docs", refs

    parsed_url = urlparse(base_url)
    if parsed_url.path in {"", "/"} and content_metrics.content_block_count <= 2 and len(structure.links) >= 2:
        return "home", [metadata.title.evidence_ref] if metadata.title.value else []
    if content_metrics.content_block_count:
        refs = [metadata.title.evidence_ref] if metadata.title.value else []
        refs.extend(block.evidence_ref for block in [])
        return "landing", refs
    return "unknown", []


def _build_primary_entities(
    base_url: str,
    metadata: MetadataEvidence,
    structure: StructureEvidence,
    type_refs: list[tuple[str, str]],
    structured_data: StructuredDataEvidence,
    page_type_hint: str,
) -> list[PrimaryEntityCandidate]:
    candidates: list[PrimaryEntityCandidate] = []
    seen: set[str] = set()

    def append(name: str | None, entity_type: str, confidence: float, evidence_refs: list[str]) -> None:
        if not name:
            return
        key = name.casefold()
        if key in seen:
            return
        seen.add(key)
        candidates.append(
            PrimaryEntityCandidate(
                evidence_ref=f"geo_signals.primary_entity_candidates[{len(candidates)}]",
                name=name,
                entity_type=entity_type,  # type: ignore[arg-type]
                confidence=confidence,
                evidence_refs=evidence_refs,
            )
        )

    for item in iter_structured_data_items(structured_data):
        value = _get_primary_schema_label(item.data)
        if isinstance(value, str) and value.strip():
            append(
                value.strip(),
                _entity_type_for(page_type_hint, type_refs),
                0.95,
                [item.evidence_ref],
            )

    h1 = next((heading for heading in structure.headings if heading.level == 1), None)
    if h1 is not None:
        append(h1.text, _entity_type_for(page_type_hint, type_refs), 0.85, [h1.evidence_ref])
    append(metadata.title.value, "WebPage", 0.75, [metadata.title.evidence_ref])

    slug = urlparse(base_url).path.rstrip("/").rsplit("/", 1)[-1].replace("-", " ").strip()
    if slug:
        append(slug.title(), "Unknown", 0.55, [metadata.canonical.evidence_ref])

    return candidates


def _build_content_outline(structure: StructureEvidence) -> list[ContentOutlineItem]:
    outline: list[ContentOutlineItem] = []
    for heading in structure.headings:
        outline.append(
            ContentOutlineItem(
                evidence_ref=f"geo_signals.content_outline[{len(outline)}]",
                heading=heading.text,
                level=heading.level,
                section_type=_classify_section_type(heading.text),
                evidence_refs=[heading.evidence_ref],
            )
        )
    return outline


def _build_answer_units(content_blocks: list[ContentBlock], structure: StructureEvidence) -> list[AnswerUnitCandidate]:
    candidates: list[AnswerUnitCandidate] = []
    for block in content_blocks:
        unit_type = _classify_answer_unit(block.text, block.source_tag)
        if unit_type == "unknown":
            continue
        candidates.append(
            AnswerUnitCandidate(
                evidence_ref=f"geo_signals.answer_unit_candidates[{len(candidates)}]",
                unit_type=unit_type,
                text=block.text,
                support_refs=[block.evidence_ref],
                source_tag=block.source_tag,
                confidence=_confidence_for_unit(unit_type),
            )
        )
    for table in structure.tables:
        candidates.append(
            AnswerUnitCandidate(
                evidence_ref=f"geo_signals.answer_unit_candidates[{len(candidates)}]",
                unit_type="comparison" if _matches_any(table.text.casefold(), _COMPARISON_PATTERNS) or " vs " in table.text.casefold() else "statistic",
                text=table.text,
                support_refs=[table.evidence_ref],
                source_tag="table",
                confidence=0.82,
            )
        )
    return candidates


def _build_claim_candidates(
    content_blocks: list[ContentBlock],
    evidence_candidates: list[EvidenceCandidate],
    statistics: list[StatisticCandidate],
) -> list[ClaimCandidate]:
    candidates: list[ClaimCandidate] = []
    evidence_refs = [candidate.evidence_ref for candidate in evidence_candidates]
    statistic_sources = {stat.evidence_ref: stat for stat in statistics}
    for block in content_blocks:
        text = block.text
        if not _is_claim_candidate(text):
            continue
        nearby_refs: list[str] = []
        if _matches_any(text.casefold(), _SOURCE_HINT_PATTERNS):
            nearby_refs.append(block.evidence_ref)
        if block.evidence_ref in statistic_sources and statistic_sources[block.evidence_ref].has_source:
            nearby_refs.append(statistic_sources[block.evidence_ref].evidence_ref)
        if _matches_any(text.casefold(), _COMPARISON_PATTERNS):
            nearby_refs.extend(ref for ref in evidence_refs if ref not in nearby_refs)
        candidates.append(
            ClaimCandidate(
                evidence_ref=f"geo_signals.claim_candidates[{len(candidates)}]",
                text=text,
                claim_type=_classify_claim_type(text),
                needs_support=True,
                nearby_evidence_refs=nearby_refs,
                evidence_refs=[block.evidence_ref],
            )
        )
    return candidates


def _build_evidence_candidates(
    structure: StructureEvidence,
    structured_data: StructuredDataEvidence,
    content_blocks: list[ContentBlock],
) -> list[EvidenceCandidate]:
    candidates: list[EvidenceCandidate] = []
    for link in structure.links:
        if not link.text:
            continue
        candidates.append(
            EvidenceCandidate(
                evidence_ref=f"geo_signals.evidence_candidates[{len(candidates)}]",
                text=link.text,
                evidence_type="source_link",
                source_url=link.href,
                support_label="unknown",
                evidence_refs=[link.evidence_ref],
            )
        )
    for table in structure.tables:
        candidates.append(
            EvidenceCandidate(
                evidence_ref=f"geo_signals.evidence_candidates[{len(candidates)}]",
                text=table.text,
                evidence_type="table",
                support_label="partial" if _NUMERIC_PATTERN.search(table.text) else "unknown",
                evidence_refs=[table.evidence_ref],
            )
        )
    for block in content_blocks:
        if block.source_tag != "blockquote":
            continue
        candidates.append(
            EvidenceCandidate(
                evidence_ref=f"geo_signals.evidence_candidates[{len(candidates)}]",
                text=block.text,
                evidence_type="quote",
                support_label="partial",
                evidence_refs=[block.evidence_ref],
            )
        )
    for item in iter_structured_data_items(structured_data):
        candidates.append(
            EvidenceCandidate(
                evidence_ref=f"geo_signals.evidence_candidates[{len(candidates)}]",
                text=_summarize_schema_item(item.data),
                evidence_type="schema",
                support_label="unknown",
                evidence_refs=[item.evidence_ref],
            )
        )
    return candidates


def _build_statistics(content_blocks: list[ContentBlock], structure: StructureEvidence) -> list[StatisticCandidate]:
    statistics: list[StatisticCandidate] = []
    for index, block in enumerate(content_blocks):
        if not _NUMERIC_PATTERN.search(block.text):
            continue
        support_refs = [block.evidence_ref]
        has_source = _matches_any(block.text.casefold(), _SOURCE_HINT_PATTERNS)
        if not has_source:
            for offset in (-1, 1):
                nearby_index = index + offset
                if nearby_index < 0 or nearby_index >= len(content_blocks):
                    continue
                nearby_block = content_blocks[nearby_index]
                if _matches_any(nearby_block.text.casefold(), _SOURCE_HINT_PATTERNS):
                    has_source = True
                    support_refs.append(nearby_block.evidence_ref)
                    break
        statistics.append(
            StatisticCandidate(
                evidence_ref=block.evidence_ref,
                value_text=block.text,
                has_source=has_source,
                evidence_refs=support_refs,
            )
        )
    for table in structure.tables:
        if not _NUMERIC_PATTERN.search(table.text):
            continue
        statistics.append(
            StatisticCandidate(
                evidence_ref=table.evidence_ref,
                value_text=table.text,
                has_source=False,
                evidence_refs=[table.evidence_ref],
            )
        )
    return statistics


def _build_structured_data_profile(
    metadata: MetadataEvidence,
    structure: StructureEvidence,
    content_blocks: list[ContentBlock],
    structured_data: StructuredDataEvidence,
    type_refs: list[tuple[str, str]],
) -> StructuredDataProfile:
    types_detected = list(OrderedDict.fromkeys(type_name for type_name, _ in type_refs))
    evidence_refs = list(OrderedDict.fromkeys(ref for _, ref in type_refs))
    primary_type = types_detected[0] if types_detected else None

    required_fields: list[str]
    if primary_type == "Article":
        required_fields = ["headline", "datePublished", "author", "image"]
    elif primary_type == "Product":
        required_fields = ["name", "offers", "aggregateRating"]
    else:
        required_fields = ["name", "description", "url"]

    available_fields = {
        field_name
        for item in iter_structured_data_items(structured_data)
        for field_name in _flatten_property_keys(item.data)
    }
    matched_required = [field_name for field_name in required_fields if field_name in available_fields]
    property_completeness = round(len(matched_required) / len(required_fields), 3) if required_fields else 0.0
    missing = [field_name for field_name in required_fields if field_name not in available_fields]

    visible_text = " ".join(
        part
        for part in [
            metadata.title.value or "",
            " ".join(heading.text for heading in structure.headings),
            " ".join(block.text for block in content_blocks),
        ]
        if part
    )
    visible_alignment = _compute_visible_alignment(visible_text, structured_data, primary_type)

    return StructuredDataProfile(
        types_detected=types_detected,
        primary_type=primary_type,
        property_completeness=property_completeness,
        visible_alignment=visible_alignment,
        missing_recommended_properties=missing,
        evidence_refs=evidence_refs,
    )


def _build_safety_flags(extraction_warnings: list[ExtractionWarning]) -> list[SafetyFlag]:
    flags: list[SafetyFlag] = []
    for warning in extraction_warnings:
        if warning.code not in {
            "html_comment_instruction",
            "metadata_instruction",
            "hidden_text_instruction",
        }:
            continue
        flags.append(
            SafetyFlag(
                evidence_ref=f"geo_signals.safety_flags[{len(flags)}]",
                flag_type=warning.code,  # type: ignore[arg-type]
                risk_level="high",
                snippet_hash=warning.snippet_hash or "",
                evidence_refs=[warning.evidence_ref],
            )
        )
    return flags


def _classify_section_type(text: str) -> str:
    lowered = text.casefold()
    if _matches_any(lowered, _DEFINITION_PATTERNS):
        return "definition"
    if _matches_any(lowered, _COMPARISON_PATTERNS):
        return "comparison"
    if _matches_any(lowered, _DOCS_PATTERNS):
        return "procedure"
    if "faq" in lowered or "q&a" in lowered:
        return "faq"
    if "evidence" in lowered or "benchmark" in lowered or "proof" in lowered:
        return "evidence"
    return "generic"


def _classify_answer_unit(text: str, source_tag: str) -> str:
    lowered = text.casefold()
    if source_tag == "blockquote":
        return "quote"
    if _matches_any(lowered, _DEFINITION_PATTERNS):
        return "definition"
    if source_tag == "li" and (_matches_any(lowered, _DOCS_PATTERNS) or re.match(r"^(step\s*\d*|\d+[\).:])", lowered)):
        return "procedure"
    if _NUMERIC_PATTERN.search(text):
        return "statistic"
    if _matches_any(lowered, _COMPARISON_PATTERNS):
        return "comparison"
    if "?" in text or lowered.startswith("q:"):
        return "faq"
    if _is_claim_candidate(text):
        return "claim"
    if len(text.split()) >= 8:
        return "fact"
    return "unknown"


def _confidence_for_unit(unit_type: str) -> float:
    return {
        "definition": 0.9,
        "statistic": 0.88,
        "comparison": 0.85,
        "procedure": 0.84,
        "faq": 0.78,
        "quote": 0.82,
        "claim": 0.76,
        "fact": 0.7,
    }.get(unit_type, 0.55)


def _classify_claim_type(text: str) -> str:
    lowered = text.casefold()
    if _NUMERIC_PATTERN.search(text):
        return "statistic"
    if "price" in lowered or "$" in text or "usd" in lowered:
        return "pricing"
    if _matches_any(lowered, _COMPARISON_PATTERNS):
        return "comparison"
    if "guarantee" in lowered or "保证" in lowered:
        return "guarantee"
    if "support" in lowered or "compatible" in lowered or "兼容" in lowered:
        return "feature"
    if "improve" in lowered or "reduce" in lowered or "提升" in lowered or "降低" in lowered:
        return "benefit"
    return "generic"


def _is_claim_candidate(text: str) -> bool:
    lowered = text.casefold()
    return bool(_NUMERIC_PATTERN.search(text) or _matches_any(lowered, _CLAIM_PATTERNS) or _matches_any(lowered, _SOURCE_HINT_PATTERNS))


def _compute_visible_alignment(visible_text: str, structured_data: StructuredDataEvidence, primary_type: str | None) -> str:
    if not primary_type:
        return "unknown"
    lowered_visible = visible_text.casefold()
    names: list[str] = []
    prices: list[str] = []
    ratings: list[str] = []
    for item in iter_structured_data_items(structured_data):
        names.extend(_collect_property_values(item.data, {"name", "headline", "title"}))
        prices.extend(_collect_property_values(item.data, {"price"}))
        ratings.extend(_collect_property_values(item.data, {"ratingvalue", "reviewcount"}))

    names = list(OrderedDict.fromkeys(value for value in names if value))
    prices = list(OrderedDict.fromkeys(value for value in prices if value))
    ratings = list(OrderedDict.fromkeys(value for value in ratings if value))

    names_visible = any(name.casefold() in lowered_visible for name in names)
    numeric_values_visible = all(value in visible_text for value in [*prices, *ratings] if value)

    if names and not names_visible:
        return "poor"
    if primary_type == "Product":
        has_product_visibility_cues = any(
            cue in lowered_visible
            for cue in ("price", "pricing", "usd", "review", "reviews", "rating", "rated", "stars", "价格", "定价", "评分", "口碑", "评论")
        )
        has_product_visibility_negation = any(
            cue in lowered_visible
            for cue in ("without visible", "no visible", "missing", "not shown", "未显示", "缺少", "没有")
        )
        if (prices or ratings) and not numeric_values_visible:
            if has_product_visibility_cues and not has_product_visibility_negation:
                return "partial"
            return "poor"
    if names:
        return "good" if (not prices and not ratings) or numeric_values_visible else "partial"
    return "partial"


def _flatten_property_keys(data: object) -> set[str]:
    keys: set[str] = set()
    if isinstance(data, dict):
        for key, value in data.items():
            if key not in {"@context", "@type", "type"}:
                keys.add(key)
            keys.update(_flatten_property_keys(value))
    elif isinstance(data, list):
        for item in data:
            keys.update(_flatten_property_keys(item))
    return keys


def _get_nested_value(data: object, target_key: str) -> object | None:
    if isinstance(data, dict):
        if target_key in data:
            return data[target_key]
        for value in data.values():
            found = _get_nested_value(value, target_key)
            if found is not None:
                return found
    elif isinstance(data, list):
        for item in data:
            found = _get_nested_value(item, target_key)
            if found is not None:
                return found
    return None


def _collect_property_values(data: object, target_keys: set[str]) -> list[str]:
    values: list[str] = []
    if isinstance(data, dict):
        for key, value in data.items():
            normalized_key = _normalize_schema_key(key)
            if normalized_key in target_keys:
                values.extend(_coerce_schema_text_values(value))
            values.extend(_collect_property_values(value, target_keys))
    elif isinstance(data, list):
        for item in data:
            values.extend(_collect_property_values(item, target_keys))
    return values


def _coerce_schema_text_values(value: object) -> list[str]:
    if isinstance(value, str):
        stripped = value.strip()
        return [stripped] if stripped else []
    if isinstance(value, list):
        values: list[str] = []
        for item in value:
            values.extend(_coerce_schema_text_values(item))
        return values
    if isinstance(value, dict):
        if "@value" in value:
            return _coerce_schema_text_values(value.get("@value"))
    return []


def _normalize_schema_key(key: str) -> str:
    candidate = key.rsplit("/", 1)[-1]
    candidate = candidate.rsplit("#", 1)[-1]
    candidate = candidate.rsplit(":", 1)[-1]
    return candidate.casefold()


def _get_primary_schema_label(data: object) -> object | None:
    if isinstance(data, dict):
        for key in ("headline", "name"):
            value = data.get(key)
            if isinstance(value, str) and value.strip():
                return value
        properties = data.get("properties")
        if isinstance(properties, dict):
            for key in ("headline", "name"):
                value = properties.get(key)
                if isinstance(value, str) and value.strip():
                    return value
    return None


def _summarize_schema_item(data: object) -> str:
    name = _get_nested_value(data, "name") or _get_nested_value(data, "headline")
    if isinstance(name, str) and name.strip():
        return name.strip()
    return "Structured data item"


def _entity_type_for(page_type_hint: str, type_refs: Iterable[tuple[str, str]]) -> str:
    lowered_types = {value.casefold() for value, _ in type_refs}
    if "product" in lowered_types or page_type_hint == "product":
        return "Product"
    if "organization" in lowered_types:
        return "Organization"
    if "article" in lowered_types or page_type_hint == "article":
        return "Article"
    if "webpage" in lowered_types:
        return "WebPage"
    return "Unknown"


def _matches_any(text: str, patterns: Iterable[str]) -> bool:
    return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in patterns)
