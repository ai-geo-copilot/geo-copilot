from __future__ import annotations

from .models import ContentBlock


def build_clean_markdown(blocks: list[ContentBlock]) -> str:
    return "\n\n".join(block.text for block in blocks if block.text.strip())
