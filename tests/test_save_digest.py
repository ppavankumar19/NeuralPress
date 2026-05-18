import os
import json
from pathlib import Path
from datetime import datetime

import pytest

from mcp.save_digest import save_digest, update_seen_cache

SAMPLE_ARTICLES = [
    {
        "id": "abc1234567890123",
        "title": "AI Advances",
        "feed_name": "TechCrunch",
        "published": "2025-06-01",
        "link": "https://example.com/1",
        "summary": "AI is advancing fast.",
        "category": "Technology",
    },
    {
        "id": "def4567890123456",
        "title": "Climate Summit",
        "feed_name": "BBC",
        "published": "2025-06-01",
        "link": "https://example.com/2",
        "summary": "Leaders meet on climate.",
        "category": "World News",
    },
]


def test_save_digest_creates_file(tmp_path):
    stats = {"elapsed": 42.0, "processed": 2, "skipped": 0}
    path = save_digest(SAMPLE_ARTICLES, str(tmp_path), "llama3.2:3b", stats)
    assert Path(path).exists()


def test_save_digest_filename_format(tmp_path):
    stats = {"elapsed": 10.0, "processed": 2, "skipped": 0}
    path = save_digest(SAMPLE_ARTICLES, str(tmp_path), "llama3.2:3b", stats)
    today = datetime.now().strftime("%Y-%m-%d")
    assert f"daily_brief_{today}.md" in path


def test_save_digest_content(tmp_path):
    stats = {"elapsed": 10.0, "processed": 2, "skipped": 0}
    path = save_digest(SAMPLE_ARTICLES, str(tmp_path), "llama3.2:3b", stats)
    content = Path(path).read_text(encoding="utf-8")
    assert "Daily Brief" in content
    assert "AI Advances" in content
    assert "Climate Summit" in content
    assert "llama3.2:3b" in content


def test_update_seen_cache(tmp_path):
    cache_file = str(tmp_path / "data" / "seen.json")
    update_seen_cache(SAMPLE_ARTICLES, cache_file)
    with open(cache_file) as f:
        cache = json.load(f)
    assert "abc1234567890123" in cache
    assert "def4567890123456" in cache
