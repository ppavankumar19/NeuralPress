import json
import pytest
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import patch, MagicMock

from mcp.fetch_rss import _article_id, _strip_html, load_seen_cache, save_seen_cache


def _recent_ts():
    """Return an ISO timestamp from 1 day ago (always within retention window)."""
    return (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()


def test_article_id_is_consistent():
    url = "https://example.com/article/1"
    assert _article_id(url) == _article_id(url)
    assert len(_article_id(url)) == 16


def test_article_id_differs_for_different_urls():
    assert _article_id("https://a.com/1") != _article_id("https://a.com/2")


def test_strip_html():
    html = "<p>Hello <b>World</b></p>"
    assert _strip_html(html) == "Hello World"


def test_strip_html_no_tags():
    assert _strip_html("Plain text") == "Plain text"


def test_strip_html_empty():
    assert _strip_html("") == ""
    assert _strip_html(None) == ""


def test_seen_cache_roundtrip(tmp_path):
    cache_file = str(tmp_path / "seen.json")
    cache = {"abc123": _recent_ts()}
    save_seen_cache(cache, cache_file)
    loaded = load_seen_cache(cache_file)
    assert "abc123" in loaded


def test_load_seen_cache_missing_file(tmp_path):
    result = load_seen_cache(str(tmp_path / "nonexistent.json"))
    assert result == {}


def test_save_seen_cache_prunes_old_entries(tmp_path):
    cache_file = str(tmp_path / "seen.json")
    cache = {
        "old_entry": "2020-01-01T00:00:00+00:00",
        "new_entry": _recent_ts(),
    }
    save_seen_cache(cache, cache_file, retention_days=30)
    loaded = load_seen_cache(cache_file)
    assert "old_entry" not in loaded
    assert "new_entry" in loaded


def test_fetch_single_feed_skips_seen(tmp_path):
    """Articles already in seen cache should be skipped."""
    from mcp.fetch_rss import _article_id, fetch_single_feed
    import feedparser

    url = "https://example.com/article/1"
    seen = {_article_id(url): "2025-06-01T07:00:00+00:00"}

    mock_entry = MagicMock()
    mock_entry.get = lambda key, default="": {
        "link": url,
        "title": "Test",
        "summary": "Test description",
        "published": "2025-06-01",
    }.get(key, default)

    mock_parsed = MagicMock()
    mock_parsed.entries = [mock_entry]

    with patch("feedparser.parse", return_value=mock_parsed):
        feed_config = {"name": "Test", "url": url, "category": "Technology"}
        articles = fetch_single_feed(feed_config, seen, max_articles=5)

    assert articles == []
