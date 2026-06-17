from pathlib import Path

from apps.api.app.page_evidence.parser import parse_html


FIXTURES_DIR = Path(__file__).parent / "fixtures" / "html"


def test_parse_html_uses_selectolax_for_dom_extraction() -> None:
    html = (FIXTURES_DIR / "selectolax_article.html").read_text(encoding="utf-8")

    parsed = parse_html(html, "https://example.com/base")

    assert parsed.metadata.title.value == "Selectolax Example Page"
    assert parsed.metadata.description.value == "Selectolax parser example summary."
    assert parsed.metadata.canonical.value == "https://example.com/articles/selectolax-example"
    assert parsed.metadata.lang.value == "en"
    assert [heading.text for heading in parsed.structure.headings] == [
        "Selectolax Example Page",
        "Why DOM extraction matters",
    ]
    assert parsed.structure.links[0].href == "https://example.com/articles/selectolax-example"
    assert parsed.structure.links[0].rel == ["canonical"]
    anchor_links = [link for link in parsed.structure.links if link.text]
    assert anchor_links[0].text == "Navigation Link"
    assert anchor_links[0].href == "https://example.com/nav"
    assert anchor_links[-1].text == "Read more"
    assert parsed.structure.images[0].alt == "Hero image"
    assert parsed.structure.tables[0].text == "Field Value Parser Selectolax"
    assert [block.source_tag for block in parsed.content_blocks] == ["p", "blockquote", "li", "li"]
    assert parsed.clean_markdown.startswith("# Selectolax Example Page")
    assert "Evidence-first parsing keeps the downstream rule engine honest." in parsed.clean_markdown
    assert parsed.structured_data.json_ld[0].data["@type"] == "Article"
    assert parsed.structured_data.opengraph[0].kind == "opengraph"
    assert parsed.structured_data.dublincore[0].kind == "dublincore"
    assert parsed.structured_data.microdata == []


def test_parse_html_ignores_empty_selectolax_blocks() -> None:
    html = """
    <html lang="zh-CN">
      <head><title>中文测试</title></head>
      <body>
        <p> </p>
        <p>第一段内容</p>
        <li>第二段内容</li>
      </body>
    </html>
    """

    parsed = parse_html(html, "https://example.com")

    assert [block.text for block in parsed.content_blocks] == ["第一段内容", "第二段内容"]
    assert "第一段内容" in parsed.clean_markdown


def test_parse_html_collects_extraction_warnings_for_suspicious_instructions() -> None:
    html = (FIXTURES_DIR / "prompt_injection_hidden_comment.html").read_text(encoding="utf-8")

    parsed = parse_html(html, "https://example.com/injected")

    assert [warning.code for warning in parsed.extraction_warnings] == [
        "metadata_instruction",
        "html_comment_instruction",
        "hidden_text_instruction",
    ]
    assert all(warning.evidence_ref.startswith("extraction.warnings[") for warning in parsed.extraction_warnings)
