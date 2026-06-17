from __future__ import annotations

import re
from urllib.parse import urljoin

from selectolax.lexbor import LexborHTMLParser
import trafilatura

from .content_blocks import build_clean_markdown
from .models import (
    ContentBlock,
    EvidenceValue,
    HeadingEvidence,
    ImageEvidence,
    LinkEvidence,
    MetadataEvidence,
    StructureEvidence,
    TableEvidence,
)
from .structured_data import parse_structured_data

_CONTENT_BLOCK_SELECTOR = "p, li, blockquote"
_HEADING_SELECTOR = "h1, h2, h3, h4, h5, h6"


def _normalize_text(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = re.sub(r"\s+", " ", value).strip()
    return normalized or None


def _first_attr(tree: LexborHTMLParser, selector: str, attribute: str) -> str | None:
    node = tree.css_first(selector)
    if node is None:
        return None
    return _normalize_text(node.attributes.get(attribute))


class ParsedPage:
    def __init__(
        self,
        *,
        metadata: MetadataEvidence,
        structure: StructureEvidence,
        content_blocks: list[ContentBlock],
        clean_markdown: str,
        structured_data,
    ) -> None:
        self.metadata = metadata
        self.structure = structure
        self.content_blocks = content_blocks
        self.clean_markdown = clean_markdown
        self.structured_data = structured_data


def parse_html(html: str, base_url: str) -> ParsedPage:
    tree = LexborHTMLParser(html)

    title_node = tree.css_first("title")
    title = _normalize_text(title_node.text()) if title_node is not None else None
    description = (
        _first_attr(tree, 'meta[name="description"]', "content")
        or _first_attr(tree, 'meta[property="og:description"]', "content")
    )
    canonical_href = _first_attr(tree, 'link[rel="canonical"]', "href")
    canonical = urljoin(base_url, canonical_href) if canonical_href else None
    html_node = tree.css_first("html")
    lang = _normalize_text(html_node.attributes.get("lang")) if html_node is not None else None

    headings: list[HeadingEvidence] = []
    for index, node in enumerate(tree.css(_HEADING_SELECTOR)):
        text = _normalize_text(node.text(separator=" ", strip=True))
        if not text:
            continue
        headings.append(
            HeadingEvidence(
                level=int(node.tag[1]),
                text=text,
                evidence_ref=f"structure.headings[{len(headings)}]",
            )
        )

    links: list[LinkEvidence] = []
    for node in tree.css("link[href]"):
        href = node.attributes.get("href")
        if not href:
            continue
        rel = _normalize_text(node.attributes.get("rel"))
        links.append(
            LinkEvidence(
                href=urljoin(base_url, href),
                text=None,
                rel=rel.split() if rel else [],
                evidence_ref=f"structure.links[{len(links)}]",
            )
        )
    for node in tree.css("a[href]"):
        href = node.attributes.get("href")
        if not href:
            continue
        links.append(
            LinkEvidence(
                href=urljoin(base_url, href),
                text=_normalize_text(node.text(separator=" ", strip=True)),
                rel=[],
                evidence_ref=f"structure.links[{len(links)}]",
            )
        )

    images: list[ImageEvidence] = []
    for node in tree.css("img[src]"):
        src = node.attributes.get("src")
        if not src:
            continue
        images.append(
            ImageEvidence(
                src=urljoin(base_url, src),
                alt=_normalize_text(node.attributes.get("alt")),
                evidence_ref=f"structure.images[{len(images)}]",
            )
        )

    tables: list[TableEvidence] = []
    for node in tree.css("table"):
        text = _normalize_text(node.text(separator=" ", strip=True))
        if not text:
            continue
        tables.append(TableEvidence(text=text, evidence_ref=f"structure.tables[{len(tables)}]"))

    content_blocks: list[ContentBlock] = []
    for node in tree.css(_CONTENT_BLOCK_SELECTOR):
        text = _normalize_text(node.text(separator=" ", strip=True))
        if not text:
            continue
        content_blocks.append(
            ContentBlock(
                evidence_ref=f"content_blocks[{len(content_blocks)}]",
                text=text,
                source_tag=node.tag,
            )
        )

    clean_markdown = trafilatura.extract(
        html,
        url=base_url,
        output_format="markdown",
        include_tables=True,
        include_formatting=True,
        include_links=False,
        include_images=False,
        target_language=lang,
    )
    if clean_markdown is None:
        clean_markdown = build_clean_markdown(content_blocks)

    metadata = MetadataEvidence(
        title=EvidenceValue(value=title, evidence_ref="metadata.title"),
        description=EvidenceValue(value=description, evidence_ref="metadata.description"),
        canonical=EvidenceValue(value=canonical, evidence_ref="metadata.canonical"),
        lang=EvidenceValue(value=lang, evidence_ref="metadata.lang"),
    )
    structure = StructureEvidence(
        headings=headings,
        links=links,
        images=images,
        tables=tables,
    )
    return ParsedPage(
        metadata=metadata,
        structure=structure,
        content_blocks=content_blocks,
        clean_markdown=clean_markdown.strip(),
        structured_data=parse_structured_data(html, base_url),
    )
