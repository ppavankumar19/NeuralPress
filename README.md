# 📰 NeuralPress — Local RSS Digest Agent

> Fetch RSS feeds, summarize with `llama3.2:3b` via Ollama, and wake up to a clean daily brief — fully offline, zero subscriptions, zero cloud.

![Python](https://img.shields.io/badge/Python-3.12+-blue?logo=python)
![Ollama](https://img.shields.io/badge/Ollama-llama3.2:3b-black)
![MCP](https://img.shields.io/badge/MCP-Model%20Context%20Protocol-purple)
![LangChain](https://img.shields.io/badge/LangChain-0.3-green)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

---

## What Is This?

A **local AI-powered news agent** that:

1. Fetches articles from your chosen RSS feeds every morning
2. Uses `llama3.2:3b` (via Ollama) to summarize each article
3. Groups summaries by topic/category
4. Saves a clean `daily_brief_YYYY-MM-DD.md` to your `output/` folder
5. Serves a beautiful web UI at `localhost:5000` to browse past digests

No cloud. No API keys. No tracking. Just your news, summarized your way.

---

## What Is RSS?

**RSS (Really Simple Syndication)** is a standard web format that websites use to publish their latest content in a machine-readable way.

Instead of visiting 10 different news sites every morning to check for new articles, each website exposes an RSS **feed** — a structured XML file that lists their latest articles with titles, summaries, links, and timestamps. Your app just fetches those XML files and gets all the new content in one place.

### What a raw RSS feed looks like

```xml
<rss version="2.0">
  <channel>
    <title>TechCrunch</title>
    <item>
      <title>OpenAI Releases New Model</title>
      <link>https://techcrunch.com/2026/05/18/openai-...</link>
      <description>OpenAI has announced...</description>
      <pubDate>Sun, 18 May 2026 07:00:00 GMT</pubDate>
    </item>
  </channel>
</rss>
```

Every major news site — BBC, TechCrunch, NASA, Hacker News — publishes one of these files and keeps it updated automatically whenever they post something new.

### How NeuralPress uses RSS

```
feeds.yaml      →  lists the RSS feed URLs you care about
feedparser      →  fetches and parses the XML for you
fetch_rss.py    →  extracts title + description from each item
summarize.py    →  sends the description to llama3.2:3b
save_digest.py  →  writes the final daily_brief.md
```

RSS is the **input source** of the entire pipeline — it's how the agent discovers articles and gets their content, without scraping, logging in, or paying for any API.

---

## System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| OS | Ubuntu 22.04 | Ubuntu 24.04 LTS |
| RAM | 8 GB | 16 GB |
| Ollama Model | llama3.2:3b | llama3.2:3b |
| Python | 3.10+ | 3.12 |
| Internet | Required (RSS fetch) | Required |
| Storage | 2 GB (model) | 5 GB |

---

## Quick Start

### 1. Make sure Ollama is running

```bash
ollama serve &
ollama list   # should show llama3.2:3b

# If not pulled yet:
ollama pull llama3.2:3b
```

### 2. Setup

```bash
cd NeuralPress
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure your feeds

```bash
# Edit feeds.yaml with your preferred RSS sources
nano feeds.yaml
```

### 4. Run the agent

```bash
python agent.py
# Digest saved to ./output/daily_brief_2026-05-18.md
```

### 5. Open the web UI

```bash
python ui/server.py
# Open http://localhost:5000
```

### 6. Schedule daily at 7 AM (optional)

```bash
crontab -e
# Add:
0 7 * * * cd /home/pavankumar19/NeuralPress && venv/bin/python agent.py >> logs/cron.log 2>&1
```

---

## Process Flow

```
┌─────────────────────────────────────────────────────────────┐
│                        feeds.yaml                           │
│         (RSS feed URLs, categories, settings)               │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│               MCP Tool 1: fetch_rss.py                      │
│                                                             │
│  1. Read feeds.yaml                                         │
│  2. For each enabled feed:                                  │
│     - feedparser.parse(url)  →  fetch XML from internet     │
│     - Strip HTML from descriptions                          │
│     - SHA-256 each article URL → check seen_articles.json   │
│     - Skip if already seen (deduplication)                  │
│  3. Truncate descriptions to 1500 chars                     │
│  4. Return list of fresh article dicts                      │
└──────────────────────────┬──────────────────────────────────┘
                           │
                    [articles list]
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│               MCP Tool 2: summarize.py                      │
│                                                             │
│  For each article:                                          │
│  1. Build prompt with title + description                   │
│  2. llm.invoke(prompt)  →  Ollama (llama3.2:3b)            │
│  3. Get back ~80-word summary                               │
│  4. Attach summary to article dict                          │
│  5. If fails → skip article, continue                       │
└──────────────────────────┬──────────────────────────────────┘
                           │
                  [summarized articles]
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│               MCP Tool 3: save_digest.py                    │
│                                                             │
│  1. Group articles by category                              │
│  2. Render markdown (header + sections + footer)            │
│  3. Write  output/daily_brief_YYYY-MM-DD.md                 │
│  4. Update seen_articles.json  (mark all as seen)           │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                      ui/server.py                           │
│                    Flask web server                         │
│                                                             │
│  GET /api/digests        →  list all digest dates           │
│  GET /api/digest/<date>  →  return markdown content         │
│  POST /api/run           →  trigger agent.py manually       │
│                                                             │
│  Serves static/index.html  →  http://localhost:5000         │
└─────────────────────────────────────────────────────────────┘
```

**Data stores touched along the way:**

```
data/seen_articles.json   <->  fetch_rss.py (read) + save_digest.py (write)
output/daily_brief_*.md    <-  save_digest.py (write) + ui/server.py (read)
feeds.yaml                 <-  fetch_rss.py (read only)
.env                       <-  agent.py (load at startup)
```

**Scheduler (optional):**

```
cron (7 AM daily)
    └──► python agent.py  (runs Tools 1 → 2 → 3 in sequence)
```

---

## Project Structure

```
NeuralPress/
├── agent.py                  # Main agent entry point
├── feeds.yaml                # Your RSS feed list (edit this)
├── feeds.example.yaml        # Example feed config
├── requirements.txt
├── .env / .env.example
│
├── mcp/                      # MCP Tool Layer
│   ├── __init__.py
│   ├── fetch_rss.py          # MCP Tool 1: fetch & parse RSS feeds
│   ├── summarize.py          # MCP Tool 2: summarize article via Ollama
│   └── save_digest.py        # MCP Tool 3: write digest markdown file
│
├── core/
│   ├── __init__.py
│   ├── llm.py                # Ollama LLM wrapper
│   └── formatter.py          # Markdown digest formatter
│
├── ui/
│   ├── server.py             # Flask API server
│   └── static/
│       └── index.html        # Web UI (CSS + JS inlined)
│
├── output/                   # Daily brief .md files saved here
├── data/                     # seen_articles.json cache
├── logs/                     # Cron logs
└── tests/                    # Unit tests (28 tests)
    ├── test_fetch_rss.py
    ├── test_summarize.py
    ├── test_formatter.py
    ├── test_save_digest.py
    └── fixtures/
```

---

## What Is MCP?

**MCP (Model Context Protocol)** is an open standard introduced by Anthropic that defines how AI models interact with external tools, data sources, and capabilities in a structured, composable way.

Think of MCP as a **universal plugin interface for AI**. Instead of an LLM having monolithic capabilities baked in, MCP lets you define discrete, well-scoped *tools* — each with a clear input/output contract — that the model (or an agent) can call on demand.

### Core Idea

```
AI Agent
   │
   ├──calls──► MCP Tool 1: fetch_rss(config_path) → articles[]
   ├──calls──► MCP Tool 2: summarize_article(article, llm) → summary
   └──calls──► MCP Tool 3: save_digest(articles, output_dir) → file_path
```

Each tool is:
- **Isolated** — it does one thing and does it well
- **Testable** — you can unit-test it without running the whole agent
- **Composable** — tools can be combined in any order or pipeline
- **Portable** — the same tool can be used by different agents or models

---

## How MCP Is Used in This Project

This project implements the MCP pattern with **3 custom tools**, each in its own module under `mcp/`.

### Tool 1 — `fetch_rss` (`mcp/fetch_rss.py`)

**What it does:** Reads `feeds.yaml`, fetches every enabled RSS/Atom feed, strips HTML from descriptions, deduplicates against the seen-articles cache, and returns a clean list of fresh article dicts.

**Input:** `config_path` (path to `feeds.yaml`)
**Output:** `list[dict]` — fresh articles with `id`, `title`, `description`, `link`, `published`, `feed_name`, `category`

```python
# How it's called in agent.py
articles, seen_cache = fetch_all_feeds("./feeds.yaml")
```

**Key behaviors:**
- Each article gets a SHA-256 ID from its URL — used for deduplication
- HTML tags are stripped from descriptions before they reach the LLM
- Descriptions are truncated to 1500 chars to stay within model context
- If a feed is down or slow, it's skipped with a warning — the rest continue

---

### Tool 2 — `summarize_article` (`mcp/summarize.py`)

**What it does:** Takes one article dict, builds a prompt, calls `llama3.2:3b` via Ollama, and returns a clean summary string.

**Input:** `article: dict`, `llm`, `max_words: int`
**Output:** `str` — a 60–100 word summary

```python
# How it's called in agent.py
summarized_articles = summarize_batch(articles, llm, max_words=80)
```

**The prompt:**

```
You are a concise news summarizer.
Summarize the following article in {max_words} words or less.
Be factual, neutral, and informative. Do not add any opinions.
Do not start with "This article" — begin directly with the key information.

Title: {title}
Content: {description}

Summary:
```

**Key behaviors:**
- Failure on one article does not stop the batch — it's skipped and logged
- LLM temperature is set to `0.2` to keep summaries factual and consistent

---

### Tool 3 — `save_digest` (`mcp/save_digest.py`)

**What it does:** Takes all summarized articles, groups them by category, renders them into a structured markdown file, writes it to `output/`, and updates the seen-articles cache so these articles aren't re-processed tomorrow.

**Input:** `articles: list[dict]`, `output_dir`, `model_name`, `stats: dict`
**Output:** `str` — path to the written `.md` file

```python
# How it's called in agent.py
output_path = save_digest(articles, "./output", "llama3.2:3b", stats)
update_seen_cache(articles, cache_path, retention_days=30)
```

---

## Why MCP? (vs. just writing functions)

You could write `fetch()`, `summarize()`, `save()` as plain functions. Here's why MCP-style tooling is better for an agent architecture:

| Plain Functions | MCP Tools |
|----------------|-----------|
| Tightly coupled to caller | Self-contained, no caller dependency |
| Hard to swap or mock | Easy to mock in tests, easy to swap |
| Agent can't reason about them | Agent can inspect tool name + description |
| Scaling to more tools = spaghetti | Each tool is a clean, isolated unit |
| Debugging requires tracing the whole chain | Each tool has a clear I/O contract to inspect |

In this project, the agent follows a **fixed pipeline** (fetch → summarize → save) rather than a free-form ReAct loop. This is intentional for v1.0 — a 3B model doesn't need to reason about which tool to call next; the sequence is always the same. The MCP structure still pays off by keeping each step isolated, testable, and easy to extend.

In a future version, you could swap out `summarize_article` for a different model, add a `filter_articles` tool between fetch and summarize, or wire the same tools into a fully autonomous agent with zero changes to the tool code itself.

---

## Web UI

The UI is a plain **HTML + CSS + JavaScript** app served by a lightweight **Flask** server.

```bash
python ui/server.py
# Open http://localhost:5000
```

### API Endpoints (provided by `ui/server.py`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/digests` | List all available digest dates |
| `GET` | `/api/digest/<date>` | Get full markdown content for a date |
| `POST` | `/api/run` | Trigger `agent.py` to generate today's digest |

### Why HTML/CSS/JS instead of Streamlit?

| Streamlit | HTML/CSS/JS + Flask |
|-----------|---------------------|
| Entire page rerenders on each interaction | Smooth partial updates, no flicker |
| Limited styling control | Full CSS control |
| ~200ms lag on every widget click | Instant JS interactions |
| Requires Python process for UI | Static assets, clear separation |
| Can't build custom layouts easily | Any layout you want |
| Heavy dependency (~50MB) | Flask is ~1MB |

---

## Configuration

### `feeds.yaml`

```yaml
settings:
  max_articles_per_run: 20     # Global cap across all feeds
  summary_max_words: 80        # Per-article summary length
  output_dir: ./output
  cache_file: ./data/seen_articles.json
  cache_retention_days: 30

feeds:
  - name: "Hacker News"
    url: "https://news.ycombinator.com/rss"
    category: "Technology"
    max_articles: 5
    enabled: true
```

### `.env`

```env
OLLAMA_BASE_URL=http://localhost:11434
LLM_MODEL=llama3.2:3b
LLM_TEMPERATURE=0.2
SUMMARY_MAX_WORDS=80
MAX_ARTICLES_PER_RUN=20
CACHE_RETENTION_DAYS=30
```

---

## Running Tests

```bash
pytest tests/ -v
# 28 tests, all should pass
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `Connection refused` to Ollama | Run `ollama serve` in a terminal |
| Empty summaries | Run `ollama list` — model must be pulled |
| Feed returns no articles | Feed may be down; check URL in browser |
| `feedparser` import error | `pip install feedparser` |
| Cron job not running | Check `cat logs/cron.log`; verify venv path |
| Very slow (CPU only) | Normal — llama3.2:3b takes ~10s/article on CPU |
| Duplicate articles appearing | Verify `CACHE_FILE` path is consistent between runs |

---

## License

MIT © 2026
