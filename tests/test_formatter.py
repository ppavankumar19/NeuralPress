from core.formatter import (
    group_by_category,
    format_article_block,
    format_category_section,
    format_digest_header,
    format_digest_footer,
)

SAMPLE_ARTICLES = [
    {
        "title": "AI Advances",
        "feed_name": "TechCrunch",
        "published": "2025-06-01",
        "link": "https://example.com/1",
        "summary": "AI is advancing fast.",
        "category": "Technology",
    },
    {
        "title": "Climate Summit",
        "feed_name": "BBC",
        "published": "2025-06-01",
        "link": "https://example.com/2",
        "summary": "Leaders meet on climate.",
        "category": "World News",
    },
    {
        "title": "New Chip Released",
        "feed_name": "Ars Technica",
        "published": "2025-06-01",
        "link": "https://example.com/3",
        "summary": "New chip released.",
        "category": "Technology",
    },
]


def test_group_by_category():
    grouped = group_by_category(SAMPLE_ARTICLES)
    assert "Technology" in grouped
    assert "World News" in grouped
    assert len(grouped["Technology"]) == 2
    assert len(grouped["World News"]) == 1


def test_group_by_category_preserves_order():
    grouped = group_by_category(SAMPLE_ARTICLES)
    assert list(grouped.keys())[0] == "Technology"


def test_format_article_block_contains_title():
    block = format_article_block(SAMPLE_ARTICLES[0])
    assert "AI Advances" in block
    assert "https://example.com/1" in block
    assert "TechCrunch" in block


def test_format_article_block_uses_summary():
    block = format_article_block(SAMPLE_ARTICLES[0])
    assert "AI is advancing fast." in block


def test_format_article_block_falls_back_to_description():
    article = {
        "title": "Fallback Test",
        "feed_name": "Feed",
        "published": "2025-06-01",
        "link": "https://example.com/x",
        "description": "Fallback description text here.",
        "category": "General",
    }
    block = format_article_block(article)
    assert "Fallback description text here." in block


def test_format_digest_header():
    header = format_digest_header("Sunday, June 1 2025", 10, 3)
    assert "Daily Brief" in header
    assert "10 articles" in header
    assert "3 feeds" in header


def test_format_digest_footer():
    footer = format_digest_footer("llama3.2:3b", 120.0, 10, 2)
    assert "llama3.2:3b" in footer
    assert "10" in footer
    assert "2" in footer


def test_format_category_section_contains_icon():
    section = format_category_section("Technology", SAMPLE_ARTICLES[:1])
    assert "💻" in section
    assert "Technology" in section


def test_format_category_section_unknown_category():
    section = format_category_section("Gaming", SAMPLE_ARTICLES[:1])
    assert "Gaming" in section
    assert "📌" in section
