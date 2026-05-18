# 🛠️ Implementation Guide

**Project:** Local News / RSS Digest Agent
**Platform:** Ubuntu 22.04 / 24.04
**Models:** `llama3.2:3b` (summarization) via Ollama

---

## Step 0 — Environment Setup

### 0.1 System dependencies

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3.11 python3.11-venv python3-pip curl git
```

### 0.2 Verify Ollama & model

```bash
ollama list
# Should show: llama3.2:3b

# If not pulled yet:
ollama pull llama3.2:3b

# Start Ollama (if not running)
ollama serve &
```

### 0.3 Create project & virtual environment

```bash
mkdir rss-digest-agent && cd rss-digest-agent

python3.11 -m venv venv
source venv/bin/activate

pip install --upgrade pip
pip install langchain==0.3.* langchain-community==0.3.* langchain-ollama==0.2.* \
            feedparser httpx pyyaml python-dotenv streamlit \
            beautifulsoup4 pytest
```

### 0.4 Create folder structure

```bash
mkdir -p mcp core ui data output logs tests/fixtures
touch agent.py .env feeds.yaml
touch mcp/__init__.py mcp/fetch_rss.py mcp/summarize.py mcp/save_digest.py
touch core/__init__.py core/llm.py core/agent_chain.py core/formatter.py
touch ui/app.py
touch tests/__init__.py tests/test_fetch_rss.py tests/test_summarize.py tests/test_formatter.py
```

### 0.5 Create `.env`

```bash
cat > .env << 'EOF'
OLLAMA_BASE_URL=http://localhost:11434
LLM_MODEL=llama3.2:3b
LLM_TEMPERATURE=0.2
FEEDS_CONFIG=./feeds.yaml
OUTPUT_DIR=./output
CACHE_FILE=./data/seen_articles.json
SUMMARY_MAX_WORDS=80
MAX_ARTICLES_PER_RUN=20
CACHE_RETENTION_DAYS=30
EOF
```

### 0.6 Create `feeds.yaml`

```bash
cat > feeds.yaml << 'EOF'
settings:
  max_articles_per_run: 20
  summary_max_words: 80
  output_dir: ./output
  cache_file: ./data/seen_articles.json
  cache_retention_days: 30

feeds:
  - name: "Hacker News"
    url: "https://news.ycombinator.com/rss"
    category: "Technology"
    max_articles: 5
    enabled: true

  - name: "TechCrunch"
    url: "https://techcrunch.com/feed/"
    category: "Technology"
    max_articles: 4
    enabled: true

  - name: "BBC World News"
    url: "http://feeds.bbci.co.uk/news/world/rss.xml"
    category: "World News"
    max_articles: 4
    enabled: true

  - name: "The Batch - DeepLearning.AI"
    url: "https://www.deeplearning.ai/the-batch/feed/"
    category: "AI / ML"
    max_articles: 3
    enabled: true

  - name: "NASA News"
    url: "https://www.nasa.gov/news-release/feed/"
    category: "Science"
    max_articles: 2
    enabled: true

  - name: "NDTV Top Stories"
    url: "https://feeds.feedburner.com/ndtvnews-top-stories"
    category: "India"
    max_articles: 4
    enabled: true
EOF
```

---

## Step 1 — MCP Tool: Fetch RSS

### `mcp/fetch_rss.py`

```python
import hashlib
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import feedparser
import yaml
from bs4 import BeautifulSoup


def _article_id(url: str) -> str:
    """Generate a short unique ID from a URL."""
    return hashlib.sha256(url.encode()).hexdigest()[:16]


def _strip_html(text: str) -> str:
    """Remove HTML tags from text."""
    if not text:
        return ""
    return BeautifulSoup(text, "html.parser").get_text(separator=" ").strip()


def load_config(config_path: str) -> dict:
    """Load feeds.yaml config."""
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def load_seen_cache(cache_path: str) -> dict:
    """Load seen article IDs from JSON cache. Returns empty dict if not found."""
    if not Path(cache_path).exists():
        return {}
    with open(cache_path, "r") as f:
        return json.load(f)


def save_seen_cache(cache: dict, cache_path: str, retention_days: int = 30) -> None:
    """Save updated cache, pruning old entries."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
    pruned = {
        k: v for k, v in cache.items()
        if datetime.fromisoformat(v).replace(tzinfo=timezone.utc) > cutoff
    }
    Path(cache_path).parent.mkdir(parents=True, exist_ok=True)
    with open(cache_path, "w") as f:
        json.dump(pruned, f, indent=2)


def fetch_single_feed(feed_config: dict, seen: dict, max_articles: int) -> list[dict]:
    """Fetch and parse one RSS feed. Returns list of fresh article dicts."""
    articles = []
    try:
        parsed = feedparser.parse(feed_config["url"])
        entries = parsed.entries[:max_articles]

        for entry in entries:
            url = entry.get("link", "")
            if not url:
                continue

            article_id = _article_id(url)
            if article_id in seen:
                continue  # Already processed

            description = _strip_html(
                entry.get("summary", "") or entry.get("description", "")
            )
            if not description:
                description = entry.get("title", "")

            articles.append({
                "id": article_id,
                "title": entry.get("title", "No title"),
                "description": description[:1500],  # Trim for LLM
                "link": url,
                "published": entry.get("published", datetime.now().isoformat()),
                "feed_name": feed_config["name"],
                "category": feed_config.get("category", "General"),
            })

    except Exception as e:
        print(f"  ⚠️  Failed to fetch '{feed_config['name']}': {e}")

    return articles


def fetch_all_feeds(config_path: str) -> tuple[list[dict], dict]:
    """
    Fetch all enabled feeds from config.
    Returns (fresh_articles, seen_cache).
    """
    config = load_config(config_path)
    settings = config.get("settings", {})
    cache_path = settings.get("cache_file", "./data/seen_articles.json")
    global_max = settings.get("max_articles_per_run", 20)

    seen = load_seen_cache(cache_path)
    all_articles = []

    print(f"🔍 Fetching feeds...")
    for feed in config.get("feeds", []):
        if not feed.get("enabled", True):
            continue
        feed_max = feed.get("max_articles", 5)
        articles = fetch_single_feed(feed, seen, feed_max)
        print(f"  📡 {feed['name']}: {len(articles)} new articles")
        all_articles.extend(articles)

    # Respect global max
    all_articles = all_articles[:global_max]
    print(f"\n📊 Total fresh articles: {len(all_articles)}")

    return all_articles, seen
```

---

## Step 2 — MCP Tool: Summarize

### `mcp/summarize.py`

```python
import time


SUMMARIZE_PROMPT = """You are a concise news summarizer. 
Summarize the following article in {max_words} words or less.
Be factual, neutral, and informative. Do not add any opinions.
Do not start with "This article" — begin directly with the key information.

Title: {title}

Content: {description}

Summary:"""


def summarize_article(article: dict, llm, max_words: int = 80) -> str:
    """
    Summarize a single article using the Ollama LLM.
    Returns summary string, or empty string on failure.
    """
    prompt = SUMMARIZE_PROMPT.format(
        max_words=max_words,
        title=article["title"],
        description=article["description"],
    )
    try:
        response = llm.invoke(prompt)
        return response.strip()
    except Exception as e:
        print(f"    ⚠️  Summarization failed for '{article['title']}': {e}")
        return ""


def summarize_batch(articles: list[dict], llm, max_words: int = 80) -> list[dict]:
    """
    Summarize all articles. Attaches 'summary' key to each article dict.
    Articles where summarization fails are skipped (not included in output).
    """
    summarized = []
    total = len(articles)

    print(f"\n🤖 Summarizing {total} articles with llama3.2:3b...")

    for i, article in enumerate(articles, 1):
        print(f"  [{i}/{total}] {article['title'][:60]}...")
        start = time.time()
        summary = summarize_article(article, llm, max_words)
        elapsed = round(time.time() - start, 1)

        if summary:
            article["summary"] = summary
            summarized.append(article)
            print(f"    ✅ Done in {elapsed}s")
        else:
            print(f"    ❌ Skipped")

    print(f"\n✅ Summarized: {len(summarized)}/{total} articles")
    return summarized
```

---

## Step 3 — MCP Tool: Save Digest

### `mcp/save_digest.py`

```python
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from core.formatter import (
    format_digest_header,
    format_category_section,
    format_digest_footer,
    group_by_category,
)


def save_digest(
    articles: list[dict],
    output_dir: str,
    model_name: str,
    stats: dict,
) -> str:
    """
    Format and write the daily digest markdown file.
    Returns the output file path.
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    today = datetime.now().strftime("%Y-%m-%d")
    filename = f"daily_brief_{today}.md"
    filepath = os.path.join(output_dir, filename)

    grouped = group_by_category(articles)

    lines = []
    lines.append(format_digest_header(
        date=datetime.now().strftime("%A, %B %d %Y"),
        article_count=len(articles),
        feed_count=len(set(a["feed_name"] for a in articles)),
    ))

    for category, cat_articles in grouped.items():
        lines.append(format_category_section(category, cat_articles))

    lines.append(format_digest_footer(
        model=model_name,
        elapsed=stats.get("elapsed", 0),
        processed=stats.get("processed", 0),
        skipped=stats.get("skipped", 0),
    ))

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return filepath


def update_seen_cache(articles: list[dict], cache_path: str, retention_days: int = 30) -> None:
    """Mark all articles as seen in the JSON cache."""
    from mcp.fetch_rss import load_seen_cache, save_seen_cache
    cache = load_seen_cache(cache_path)
    now = datetime.now(timezone.utc).isoformat()
    for article in articles:
        cache[article["id"]] = now
    save_seen_cache(cache, cache_path, retention_days)
```

---

## Step 4 — Formatter

### `core/formatter.py`

```python
from datetime import datetime


def group_by_category(articles: list[dict]) -> dict:
    """Group article list by category, preserving order of first appearance."""
    grouped = {}
    for article in articles:
        cat = article.get("category", "General")
        grouped.setdefault(cat, []).append(article)
    return grouped


def format_digest_header(date: str, article_count: int, feed_count: int) -> str:
    time_str = datetime.now().strftime("%I:%M %p")
    return (
        f"# 📰 Daily Brief — {date}\n"
        f"*Generated at {time_str} | {article_count} articles from {feed_count} feeds*\n\n"
        f"---\n"
    )


def format_article_block(article: dict) -> str:
    summary = article.get("summary", article.get("description", "")[:200])
    return (
        f"### {article['title']}\n"
        f"*{article['feed_name']} — {article.get('published', '')[:10]}*\n\n"
        f"{summary}\n\n"
        f"📎 [Read full article]({article['link']})\n"
    )


def format_category_section(category: str, articles: list[dict]) -> str:
    category_icons = {
        "Technology": "💻",
        "World News": "🌍",
        "AI / ML": "🤖",
        "Science": "🔬",
        "India": "🇮🇳",
        "Business": "💼",
        "Health": "🏥",
        "Sports": "⚽",
        "General": "📋",
    }
    icon = category_icons.get(category, "📌")
    lines = [f"## {icon} {category}\n"]
    for article in articles:
        lines.append(format_article_block(article))
        lines.append("---\n")
    return "\n".join(lines)


def format_digest_footer(model: str, elapsed: float, processed: int, skipped: int) -> str:
    return (
        f"\n---\n"
        f"*🤖 Generated locally by RSS Digest Agent*  \n"
        f"*Model: `{model}` | Time: {elapsed:.0f}s | "
        f"Processed: {processed} | Skipped: {skipped}*\n"
    )
```

---

## Step 5 — LLM Wrapper

### `core/llm.py`

```python
import os
from langchain_ollama import OllamaLLM


def get_llm(model_name: str = None, temperature: float = None) -> OllamaLLM:
    """Return configured local Ollama LLM."""
    model = model_name or os.getenv("LLM_MODEL", "llama3.2:3b")
    temp = (
        temperature
        if temperature is not None
        else float(os.getenv("LLM_TEMPERATURE", 0.2))
    )
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    return OllamaLLM(model=model, temperature=temp, base_url=base_url)
```

---

## Step 6 — Main Agent

### `agent.py`

```python
#!/usr/bin/env python3
"""
RSS Digest Agent — Main Runner
Usage: python agent.py [--config feeds.yaml]
"""

import argparse
import os
import time
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from core.llm import get_llm
from mcp.fetch_rss import fetch_all_feeds, save_seen_cache
from mcp.summarize import summarize_batch
from mcp.save_digest import save_digest, update_seen_cache


def main():
    parser = argparse.ArgumentParser(description="RSS Digest Agent")
    parser.add_argument("--config", default=os.getenv("FEEDS_CONFIG", "./feeds.yaml"))
    parser.add_argument("--output", default=os.getenv("OUTPUT_DIR", "./output"))
    args = parser.parse_args()

    start_time = time.time()
    print("🗞️  RSS Digest Agent starting...\n")

    # Step 1: Fetch fresh articles
    articles, seen_cache = fetch_all_feeds(args.config)

    if not articles:
        print("💤 No new articles today. Try again later.")
        return

    # Step 2: Summarize with llama3.2:3b
    llm = get_llm()
    max_words = int(os.getenv("SUMMARY_MAX_WORDS", 80))
    summarized = summarize_batch(articles, llm, max_words)

    skipped = len(articles) - len(summarized)
    elapsed = round(time.time() - start_time, 1)

    # Step 3: Save digest
    stats = {
        "elapsed": elapsed,
        "processed": len(summarized),
        "skipped": skipped,
    }
    output_path = save_digest(
        articles=summarized,
        output_dir=args.output,
        model_name=os.getenv("LLM_MODEL", "llama3.2:3b"),
        stats=stats,
    )

    # Step 4: Update seen cache
    cache_path = os.getenv("CACHE_FILE", "./data/seen_articles.json")
    retention = int(os.getenv("CACHE_RETENTION_DAYS", 30))
    update_seen_cache(summarized, cache_path, retention)

    print(f"\n{'='*50}")
    print(f"✅ Digest saved: {output_path}")
    print(f"📊 Articles: {len(summarized)} processed, {skipped} skipped")
    print(f"⏱️  Total time: {elapsed}s")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
```

---

## Step 7 — Optional Streamlit UI

### `ui/app.py`

```python
import os
import glob
from pathlib import Path
from datetime import datetime

import streamlit as st
from dotenv import load_dotenv
load_dotenv()

OUTPUT_DIR = os.getenv("OUTPUT_DIR", "./output")

st.set_page_config(
    page_title="📰 Daily Digest",
    page_icon="📰",
    layout="wide",
)

st.title("📰 Daily News Digest")
st.caption("Locally generated with llama3.2:3b via Ollama")

# Find all digest files
digest_files = sorted(
    glob.glob(os.path.join(OUTPUT_DIR, "daily_brief_*.md")),
    reverse=True,
)

if not digest_files:
    st.info("No digests found yet. Run `python agent.py` to generate your first digest.")
    st.code("python agent.py")
else:
    # Date picker from available files
    dates = [Path(f).stem.replace("daily_brief_", "") for f in digest_files]
    selected_date = st.selectbox("📅 Select Date", dates)

    selected_file = os.path.join(OUTPUT_DIR, f"daily_brief_{selected_date}.md")

    col1, col2 = st.columns([3, 1])

    with col2:
        if st.button("🔄 Generate Today's Digest"):
            with st.spinner("Running agent..."):
                os.system("python agent.py")
            st.rerun()

    with col1:
        with open(selected_file, "r", encoding="utf-8") as f:
            content = f.read()
        st.markdown(content)
```

---

## Step 8 — Tests

### `tests/test_fetch_rss.py`

```python
import json
import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from mcp.fetch_rss import _article_id, _strip_html, load_seen_cache, save_seen_cache


def test_article_id_is_consistent():
    url = "https://example.com/article/1"
    assert _article_id(url) == _article_id(url)
    assert len(_article_id(url)) == 16


def test_strip_html():
    html = "<p>Hello <b>World</b></p>"
    assert _strip_html(html) == "Hello World"


def test_strip_html_empty():
    assert _strip_html("") == ""
    assert _strip_html(None) == ""


def test_seen_cache_roundtrip(tmp_path):
    cache_file = str(tmp_path / "seen.json")
    cache = {"abc123": "2025-06-01T07:00:00+00:00"}
    save_seen_cache(cache, cache_file)
    loaded = load_seen_cache(cache_file)
    assert "abc123" in loaded


def test_load_seen_cache_missing_file(tmp_path):
    result = load_seen_cache(str(tmp_path / "nonexistent.json"))
    assert result == {}
```

### `tests/test_formatter.py`

```python
from core.formatter import (
    group_by_category,
    format_article_block,
    format_digest_header,
    format_digest_footer,
)

SAMPLE_ARTICLES = [
    {"title": "AI Advances", "feed_name": "TechCrunch", "published": "2025-06-01",
     "link": "https://example.com/1", "summary": "AI is advancing fast.", "category": "Technology"},
    {"title": "Climate Summit", "feed_name": "BBC", "published": "2025-06-01",
     "link": "https://example.com/2", "summary": "Leaders meet on climate.", "category": "World News"},
    {"title": "New Chip", "feed_name": "Ars Technica", "published": "2025-06-01",
     "link": "https://example.com/3", "summary": "New chip released.", "category": "Technology"},
]


def test_group_by_category():
    grouped = group_by_category(SAMPLE_ARTICLES)
    assert "Technology" in grouped
    assert "World News" in grouped
    assert len(grouped["Technology"]) == 2


def test_format_article_block_contains_title():
    block = format_article_block(SAMPLE_ARTICLES[0])
    assert "AI Advances" in block
    assert "https://example.com/1" in block


def test_format_digest_header():
    header = format_digest_header("Sunday, June 1 2025", 10, 3)
    assert "Daily Brief" in header
    assert "10 articles" in header


def test_format_digest_footer():
    footer = format_digest_footer("llama3.2:3b", 120, 10, 2)
    assert "llama3.2:3b" in footer
    assert "10" in footer
```

---

## Step 9 — Cron Automation

```bash
# Make agent executable
chmod +x agent.py

# Open crontab editor
crontab -e

# Add this line (runs every day at 7:00 AM):
0 7 * * * cd /home/pavankumar19/rss-digest-agent && \
  /home/pavankumar19/rss-digest-agent/venv/bin/python agent.py \
  >> /home/pavankumar19/rss-digest-agent/logs/cron.log 2>&1

# Verify crontab saved
crontab -l
```

---

## Step 10 — Run Everything

```bash
# 1. Make sure Ollama is running
ollama serve &

# 2. Activate venv
source venv/bin/activate

# 3. Run the agent manually
python agent.py

# Expected output:
# 🗞️  RSS Digest Agent starting...
# 🔍 Fetching feeds...
#   📡 Hacker News: 5 new articles
#   📡 TechCrunch: 4 new articles
#   ...
# 🤖 Summarizing 18 articles with llama3.2:3b...
#   [1/18] OpenAI announces new model...  ✅ Done in 8.2s
#   ...
# ✅ Digest saved: ./output/daily_brief_2025-06-01.md

# 4. View in browser (optional)
streamlit run ui/app.py

# 5. Run tests
pytest tests/ -v
```

---

## Quick Validation Checklist

```
[ ] ollama list            → shows llama3.2:3b
[ ] python agent.py        → runs without errors
[ ] output/ folder         → contains daily_brief_YYYY-MM-DD.md
[ ] Open the .md file      → readable summaries with source links
[ ] Run again same day     → "No new articles today" (dedup working)
[ ] pytest tests/ -v       → all tests pass
[ ] streamlit run ui/app.py → UI opens at localhost:8501
[ ] crontab -l             → cron job listed
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `Connection refused` to Ollama | Run `ollama serve` in a terminal |
| Empty summaries | Check `ollama list` — model must be pulled |
| Feed returns no articles | Some feeds may be down; check URL in browser |
| `feedparser` import error | `pip install feedparser` |
| Cron job not running | Check logs: `cat logs/cron.log`; verify venv path |
| Summaries too long | Reduce `SUMMARY_MAX_WORDS` in `.env` |
| Very slow (CPU only) | Normal — llama3.2:3b takes ~10s/article on CPU |
| Duplicate articles appearing | Verify `CACHE_FILE` path is consistent between runs |
