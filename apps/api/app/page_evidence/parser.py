from __future__ import annotations

from html.parser import HTMLParser
from urllib.parse import urljoin

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
from .structured_data import parse_json_ld


class _EvidenceHtmlParser(HTMLParser):
    def __init__(self, base_url: str) -> None:
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.lang: str | None = None
        self.title_parts: list[str] = []
        self.title = ""
        self.description: str | None = None
        self.canonical: str | None = None
        self.headings: list[HeadingEvidence] = []
        self.links: list[LinkEvidence] = []
        self.images: list[ImageEvidence] = []
        self.tables: list[str] = []
        self.content_blocks: list[ContentBlock] = []
        self.json_ld_scripts: list[str] = []

        self._current_title = False
        self._current_heading_level: int | None = None
        self._current_heading_text: list[str] = []
        self._current_block_tag: str | None = None
        self._current_block_text: list[str] = []
        self._current_table = False
        self._current_table_text: list[str] = []
        self._current_script_json_ld = False
        self._current_script_text: list[str] = []
        self._heading_index = 0
        self._link_index = 0
        self._image_index = 0
        self._table_index = 0
        self._block_index = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = dict(attrs)
        if tag == "html":
            self.lang = (attr_map.get("lang") or self.lang or "").strip() or None
        elif tag == "title":
            self._current_title = True
        elif tag == "meta":
            name = (attr_map.get("name") or attr_map.get("property") or "").lower()
            if name in {"description", "og:description"} and not self.description:
                self.description = (attr_map.get("content") or "").strip() or None
        elif tag == "link":
            rel = (attr_map.get("rel") or "").lower().split()
            href = attr_map.get("href")
            if href:
                if "canonical" in rel and not self.canonical:
                    self.canonical = urljoin(self.base_url, href)
                self.links.append(
                    LinkEvidence(
                        href=urljoin(self.base_url, href),
                        text=None,
                        rel=rel,
                        evidence_ref=f"structure.links[{self._link_index}]",
                    )
                )
                self._link_index += 1
        elif tag == "a":
            href = attr_map.get("href")
            if href:
                self.links.append(
                    LinkEvidence(
                        href=urljoin(self.base_url, href),
                        text=None,
                        rel=[],
                        evidence_ref=f"structure.links[{self._link_index}]",
                    )
                )
                self._link_index += 1
        elif tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self._current_heading_level = int(tag[1])
            self._current_heading_text = []
        elif tag == "img":
            src = attr_map.get("src")
            if src:
                self.images.append(
                    ImageEvidence(
                        src=urljoin(self.base_url, src),
                        alt=(attr_map.get("alt") or "").strip() or None,
                        evidence_ref=f"structure.images[{self._image_index}]",
                    )
                )
                self._image_index += 1
        elif tag == "table":
            self._current_table = True
            self._current_table_text = []
        elif tag in {"p", "li", "blockquote"}:
            self._current_block_tag = tag
            self._current_block_text = []
        elif tag == "script" and (attr_map.get("type") or "").lower() == "application/ld+json":
            self._current_script_json_ld = True
            self._current_script_text = []

    def handle_data(self, data: str) -> None:
        text = data.strip()
        if not text:
            return
        if self._current_title:
            self.title_parts.append(text)
        if self._current_heading_level is not None:
            self._current_heading_text.append(text)
        if self._current_block_tag is not None:
            self._current_block_text.append(text)
        if self._current_table:
            self._current_table_text.append(text)
        if self._current_script_json_ld:
            self._current_script_text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._current_title = False
            self.title = " ".join(self.title_parts).strip()
        elif tag in {"h1", "h2", "h3", "h4", "h5", "h6"} and self._current_heading_level is not None:
            text = " ".join(self._current_heading_text).strip()
            if text:
                self.headings.append(
                    HeadingEvidence(
                        level=self._current_heading_level,
                        text=text,
                        evidence_ref=f"structure.headings[{self._heading_index}]",
                    )
                )
                self._heading_index += 1
            self._current_heading_level = None
            self._current_heading_text = []
        elif tag == "table" and self._current_table:
            text = " ".join(self._current_table_text).strip()
            if text:
                self.tables.append(text)
                self._table_index += 1
            self._current_table = False
            self._current_table_text = []
        elif tag == self._current_block_tag and self._current_block_tag is not None:
            text = " ".join(self._current_block_text).strip()
            if text:
                self.content_blocks.append(
                    ContentBlock(
                        evidence_ref=f"content_blocks[{self._block_index}]",
                        text=text,
                        source_tag=self._current_block_tag,
                    )
                )
                self._block_index += 1
            self._current_block_tag = None
            self._current_block_text = []
        elif tag == "script" and self._current_script_json_ld:
            content = "".join(self._current_script_text).strip()
            if content:
                self.json_ld_scripts.append(content)
            self._current_script_json_ld = False
            self._current_script_text = []


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
    parser = _EvidenceHtmlParser(base_url)
    parser.feed(html)
    metadata = MetadataEvidence(
        title=EvidenceValue(value=parser.title or None, evidence_ref="metadata.title"),
        description=EvidenceValue(value=parser.description, evidence_ref="metadata.description"),
        canonical=EvidenceValue(value=parser.canonical, evidence_ref="metadata.canonical"),
        lang=EvidenceValue(value=parser.lang, evidence_ref="metadata.lang"),
    )
    structure = StructureEvidence(
        headings=parser.headings,
        links=parser.links,
        images=parser.images,
        tables=[
            TableEvidence(text=text, evidence_ref=f"structure.tables[{index}]")
            for index, text in enumerate(parser.tables)
        ],
    )
    content_blocks = parser.content_blocks
    return ParsedPage(
        metadata=metadata,
        structure=StructureEvidence.model_validate(structure),
        content_blocks=content_blocks,
        clean_markdown=build_clean_markdown(content_blocks),
        structured_data=parse_json_ld(parser.json_ld_scripts),
    )
