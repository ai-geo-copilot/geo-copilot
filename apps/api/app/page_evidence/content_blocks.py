from __future__ import annotations

from dataclasses import dataclass, field
import re

from .models import RuleCheckInputs, StructuredDataEvidence, StructureEvidence
from .models import ContentBlock


def build_clean_markdown(blocks: list[ContentBlock]) -> str:
    return "\n\n".join(block.text for block in blocks if block.text.strip())


@dataclass(slots=True)
class ContentMetrics:
    content_block_count: int
    word_count: int
    cjk_char_count: int
    substance_score: int
    main_content_confidence: float
    boilerplate_ratio: float
    first_screen_summary_present: bool
    evidence_refs: list[str] = field(default_factory=list)

    def to_rule_check_inputs(self, structured_data: StructuredDataEvidence) -> RuleCheckInputs:
        return RuleCheckInputs(
            word_count=self.word_count,
            cjk_char_count=self.cjk_char_count,
            substance_score=self.substance_score,
            content_block_count=self.content_block_count,
            heading_count=0,
            has_json_ld=bool(structured_data.json_ld),
        )


def analyze_content_blocks(blocks: list[ContentBlock], structure: StructureEvidence) -> ContentMetrics:
    block_text = "\n".join(block.text for block in blocks)
    word_count = len(re.findall(r"\b\w+\b", block_text, flags=re.UNICODE))
    cjk_char_count = len(re.findall(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]", block_text))
    substance_score = max(word_count, cjk_char_count)
    content_block_count = len(blocks)
    short_blocks = sum(1 for block in blocks if len(block.text.split()) <= 6 and len(block.text) <= 48)
    boilerplate_ratio = round(short_blocks / content_block_count, 3) if content_block_count else 1.0
    first_screen_summary_present = any(
        len(block.text.split()) >= 12 or len(re.findall(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]", block.text)) >= 24
        for block in blocks[:2]
    )

    confidence = 0.0
    if content_block_count >= 2:
        confidence += 0.25
    if substance_score >= 120:
        confidence += 0.35
    elif substance_score >= 60:
        confidence += 0.2
    if first_screen_summary_present:
        confidence += 0.2
    if any(heading.level == 1 for heading in structure.headings):
        confidence += 0.1
    confidence -= boilerplate_ratio * 0.2
    main_content_confidence = round(min(1.0, max(0.0, confidence)), 3)

    evidence_refs = [block.evidence_ref for block in blocks[:3]]
    if structure.headings:
        evidence_refs.append(structure.headings[0].evidence_ref)

    return ContentMetrics(
        content_block_count=content_block_count,
        word_count=word_count,
        cjk_char_count=cjk_char_count,
        substance_score=substance_score,
        main_content_confidence=main_content_confidence,
        boilerplate_ratio=boilerplate_ratio,
        first_screen_summary_present=first_screen_summary_present,
        evidence_refs=evidence_refs,
    )
