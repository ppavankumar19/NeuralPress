# 🔧 Technical Specification

**Project:** Local News / RSS Digest Agent
**Platform:** Ubuntu 22.04 / 24.04
**Version:** 1.0

---

## 1. What Is RSS?

**RSS (Really Simple Syndication)** is a standard XML format used by websites to publish a live list of their latest articles. Each feed is a URL that returns structured XML containing article titles, descriptions, links and timestamps. No scraping, no authentication — just a `GET` request to a public URL.

```xml
<rss version="2.0">
  <channel>
    <title>Hacker News</title>
    <item>
      <title>Ask HN: Best local LLMs in 2026?</title>
      <link>https://news.ycombinator.com/item?id=...</link>
      <description>Discussion about running LLMs offline...</description>
      <pubDate>Sun, 18 May 2026 07:00:00 GMT</pubDate>
    </item>
  </channel>
</rss>
```

**Why RSS?** Every major publisher provides one. It is machine-readable, standardised (RSS 2.0 and Atom 1.0), requires no API key, and `feedparser` handles all edge cases and encoding quirks.

---

## 2. System Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                        agent.py (Orchestrator)                   │
│                       Fixed Pipeline (v1.0)                      │
└────────┬──────────────────┬────────────────────────┬─────────────┘
         │                  │                        │
         ▼                  ▼                        ▼
┌─────────────────┐ ┌──────────────────┐ ┌───────────────────────┐
│  MCP Tool 1     │ │  MCP Tool 2      │ │  MCP Tool 3           │
│  fetch_rss      │ │  summarize_      │ │  save_digest          │
│                 │ │  article         │ │                       │
│ • Parse feeds   │ │ • Trim text      │ │ • Format markdown     │
│ • Deduplicate   │ │ • Build prompt   │ │ • Group by category   │
│ • Return list   │ │ • Call Ollama    │ │ • Write .md file      │
│   of articles   │ │ • Return summary │ │ • Update seen cache   │
└────────┬────────┘ └────────┬─────────┘ └───────────────────────┘
         │                   │
         ▼                   ▼
┌─────────────────┐  ┌────────────────────────┐
│  feeds.yaml     │  │  Ollama (localhost:     │
│  (user config)  │  │  11434)                │
│                 │  │  llama3.2:3b           │
└─────────────────┘  └────────────────────────┘
         │
         ▼
┌─────────────────┐
│  seen_articles  │
│  .json (cache)  │
└─────────────────┘
                               ▼
                    ┌──────────────────────────┐
                    │  output/                 │
                    │  daily_brief_2025-06-01  │
                    │  .md                     │
                    └──────────────────────────┘
```

---

## 2. Technology Stack

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| LLM Runtime | Ollama | Latest | Run llama3.2:3b locally |
| LLM Model | llama3.2:3b | — | Article summarization |
| Agent Framework | LangChain | 0.3.x | Tool-using agent loop |
| RSS Parsing | feedparser | 6.x | Parse RSS 2.0 + Atom 1.0 |
| HTTP Client | httpx | 0.27.x | Async feed fetching |
| Config Format | PyYAML | 6.x | feeds.yaml parsing |
| Dedup Cache | JSON file | — | Seen article URL tracking |
| UI (optional) | Flask + HTML/CSS/JS | 3.x | Digest browser (responsive web app) |
| Scheduler | cron (Ubuntu) | — | Daily automation |
| Language | Python | 3.12 | Core language |
| Testing | pytest | 8.x | Unit tests |

---

## 3. Configuration Files

### `feeds.yaml` Schema

```yaml
settings:
  max_articles_per_run: 20       # Global cap across all feeds
  summary_max_words: 80          # Per-article summary length
  output_dir: ./output
  cache_file: ./data/seen_articles.json
  cache_retention_days: 30

feeds:
  - name: "TechCrunch"
    url: "https://techcrunch.com/feed/"
    category: "Technology"
    max_articles: 5
    enabled: true

  - name: "Hacker News"
    url: "https://news.ycombinator.com/rss"
    category: "Technology"
    max_articles: 5
    enabled: true

  - name: "BBC World News"
    url: "http://feeds.bbci.co.uk/news/world/rss.xml"
    category: "World News"
    max_articles: 5
    enabled: true

  - name: "The Batch (DeepLearning.AI)"
    url: "https://www.deeplearning.ai/the-batch/feed/"
    category: "AI / ML"
    max_articles: 3
    enabled: true

  - name: "NASA News"
    url: "https://www.nasa.gov/news-release/feed/"
    category: "Science"
    max_articles: 3
    enabled: true

  - name: "NDTV India"
    url: "https://feeds.feedburner.com/ndtvnews-top-stories"
    category: "India"
    max_articles: 4
    enabled: true
```

### `.env` File

```env
# Ollama
OLLAMA_BASE_URL=http://localhost:11434
LLM_MODEL=llama3.2:3b
LLM_TEMPERATURE=0.2

# Paths
FEEDS_CONFIG=./feeds.yaml
OUTPUT_DIR=./output
CACHE_FILE=./data/seen_articles.json

# Digest
SUMMARY_MAX_WORDS=80
MAX_ARTICLES_PER_RUN=20
CACHE_RETENTION_DAYS=30
```

---

## 4. Module Specifications

### 4.1 `mcp/fetch_rss.py` — MCP Tool: `fetch_rss`

**Responsibility:** Fetch all enabled RSS feeds, parse articles, filter against seen-cache, return fresh articles list.

**Dependencies:** `feedparser`, `httpx`, `PyYAML`

**Article object schema:**
```python
{
  "id": "sha256-of-url",          # Unique dedup key
  "title": "string",
  "description": "string",        # RSS description / summary field (plain text)
  "link": "https://...",
  "published": "2025-06-01T07:00:00Z",
  "feed_name": "TechCrunch",
  "category": "Technology",
}
```

**Interface:**
```python
def fetch_all_feeds(config_path: str) -> list[dict]:
    """
    Load feeds.yaml, fetch each enabled feed,
    filter seen articles, return fresh article list.
    """

def fetch_single_feed(feed: dict) -> list[dict]:
    """Fetch and parse one RSS feed. Returns list of article dicts."""

def is_seen(article_id: str, cache: dict) -> bool:
    """Check if article URL hash exists in seen cache."""

def load_seen_cache(cache_path: str) -> dict:
    """Load seen article IDs from JSON file."""
```

**Error handling:**
- Feed fetch timeout → skip feed, log warning
- Malformed XML → `feedparser` handles gracefully
- Empty feed → return empty list for that feed

---

### 4.2 `mcp/summarize.py` — MCP Tool: `summarize_article`

**Responsibility:** Take a single article dict, build a prompt, call Ollama, return clean summary string.

**Prompt Template:**
```
You are a news summarizer. Summarize the following article in {max_words} words or less.
Be factual, concise, and neutral. Do not add opinions or information not in the article.
Do not start with "This article..." — start directly with the key point.

Article Title: {title}
Article Content: {description}

Summary:
```

**Interface:**
```python
def summarize_article(article: dict, llm, max_words: int = 80) -> str:
    """
    Call Ollama LLM to summarize article description.
    Returns summary string or empty string on failure.
    """

def summarize_batch(articles: list[dict], llm, max_words: int = 80) -> list[dict]:
    """
    Summarize all articles, attaching 'summary' key to each.
    Skips articles where summarization fails.
    """
```

**Input trimming:**
- Truncate `description` to max 1500 characters before sending to LLM
- Strip HTML tags from description before processing

---

### 4.3 `mcp/save_digest.py` — MCP Tool: `save_digest`

**Responsibility:** Format all summarized articles into markdown, write daily brief file, update seen-articles cache.

**Output filename format:** `daily_brief_YYYY-MM-DD.md`

**Markdown structure:**
```
# 📰 Daily Brief — {Day}, {Date}
Generated at {time} | Model: {model} | {N} articles from {M} feeds

---
## {Category 1}
### {Article Title}
*Source: {feed_name} — {date}*
{summary}
📎 [Read full article]({link})

---
## {Category 2}
...

---
*Generated locally by RSS Digest Agent using llama3.2:3b*
*Total time: {elapsed}s | Articles processed: {N} | Skipped: {S}*
```

**Interface:**
```python
def save_digest(articles: list[dict], output_dir: str, model_name: str, stats: dict) -> str:
    """
    Format articles into markdown grouped by category.
    Write to output_dir/daily_brief_YYYY-MM-DD.md.
    Returns the output file path.
    """

def update_seen_cache(articles: list[dict], cache_path: str, retention_days: int = 30) -> None:
    """
    Add article IDs to seen cache JSON.
    Prune entries older than retention_days.
    """

def group_by_category(articles: list[dict]) -> dict[str, list[dict]]:
    """Return articles grouped by their category field."""
```

---

### 4.4 `core/llm.py`

```python
import os
from langchain_ollama import OllamaLLM

def get_llm(model_name: str = None, temperature: float = None) -> OllamaLLM:
    model = model_name or os.getenv("LLM_MODEL", "llama3.2:3b")
    temp = temperature if temperature is not None else float(os.getenv("LLM_TEMPERATURE", 0.2))
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    return OllamaLLM(model=model, temperature=temp, base_url=base_url)
```

---

### 4.5 `core/formatter.py`

**Responsibility:** Pure markdown formatting helpers (used by `save_digest`).

```python
def format_article_block(article: dict) -> str:
    """Render one article as a markdown block."""

def format_category_section(category: str, articles: list[dict]) -> str:
    """Render a full category section with header and articles."""

def format_digest_header(date: str, article_count: int, feed_count: int) -> str:
    """Render the top header of the digest."""

def format_digest_footer(model: str, elapsed: float, processed: int, skipped: int) -> str:
    """Render the bottom stats footer."""
```

---

### 4.6 `agent.py` — Main Entry Point

```python
"""
RSS Digest Agent — Main Runner
Usage: python agent.py [--config feeds.yaml] [--output ./output]
"""
```

**Flow:**
```
1. Load .env and feeds.yaml
2. Initialize Ollama LLM
3. fetch_all_feeds() → fresh articles list
4. If no new articles → log "Nothing new today" and exit
5. summarize_batch() → articles with summaries
6. save_digest() → write markdown file
7. update_seen_cache() → mark articles as processed
8. Print: "✅ Digest saved to ./output/daily_brief_2025-06-01.md"
```

---

## 5. Seen-Articles Cache Format

**File:** `./data/seen_articles.json`

```json
{
  "a3f4c9...": "2025-06-01T07:00:00",
  "b8d2e1...": "2025-05-31T07:00:00",
  "...": "..."
}
```

- Key: SHA-256 of article URL (first 16 chars)
- Value: ISO timestamp when first seen
- Pruned: entries older than `CACHE_RETENTION_DAYS` on each run

---

## 6. Performance Targets

| Metric | Target |
|--------|--------|
| Total run time (20 articles, CPU) | < 5 minutes |
| Per-article summarization time | < 15 seconds |
| Feed fetch timeout | 10 seconds per feed |
| Max description fed to LLM | 1500 characters |
| Output file size | < 50 KB |

---

## 7. Cron Setup (Ubuntu)

```bash
# Edit crontab
crontab -e

# Run every day at 7:00 AM
0 7 * * * cd /home/pavankumar19/NeuralPress && \
  /home/pavankumar19/NeuralPress/venv/bin/python agent.py \
  >> /home/pavankumar19/NeuralPress/logs/cron.log 2>&1
```

Create logs directory:
```bash
mkdir -p logs
```

---

## 8. Testing Plan

```
tests/
├── test_fetch_rss.py        # Feed parsing, dedup, cache logic
├── test_summarize.py        # Prompt building, LLM call mock
├── test_formatter.py        # Markdown output format
├── test_save_digest.py      # File writing + cache update
└── fixtures/
    ├── sample_feed.xml      # Mock RSS XML
    └── sample_articles.json # Mock article list
```

---

## 9. Dependencies (`requirements.txt`)

```
langchain==0.3.*
langchain-community==0.3.*
langchain-ollama==0.2.*
feedparser==6.*
httpx==0.27.*
pyyaml==6.*
python-dotenv==1.0.*
flask==3.*
beautifulsoup4==4.*
pytest==8.*
```
