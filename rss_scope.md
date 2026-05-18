# 🗺️ Project Scope

**Project:** Local News / RSS Digest Agent
**Platform:** Ubuntu (local machine)
**Stack:** Ollama (llama3.2:3b) + MCP Tools + LangChain + Flask + HTML/CSS/JS
**Version:** 1.0

---

## 📡 What Is RSS?

**RSS (Really Simple Syndication)** is a standard XML format that news websites use to publish new articles automatically. Instead of scraping pages, the agent simply fetches each feed URL — a structured file that lists article titles, descriptions, links and timestamps — and processes the content directly.

```
BBC World News  →  http://feeds.bbci.co.uk/news/world/rss.xml
TechCrunch      →  https://techcrunch.com/feed/
Hacker News     →  https://news.ycombinator.com/rss
```

RSS is the **zero-cost, zero-login input source** for the entire pipeline.

---

## 🎯 Project Goal

Build a **locally running, automated news digest agent** that:
1. Reads RSS/Atom feeds from user-configured sources
2. Uses `llama3.2:3b` via MCP tools to summarize each article
3. Groups and formats summaries into a clean daily markdown brief
4. Runs on a cron schedule (every morning) with zero manual intervention
5. Optionally serves a browser-based UI to read past digests

---

## ✅ In Scope

### Core Agent Functionality
- [x] Fetch articles from RSS/Atom feeds (user-configured YAML list)
- [x] Parse article title, description, link, publish date
- [x] Deduplicate articles seen in previous runs
- [x] Summarize each article using `llama3.2:3b` via Ollama
- [x] Group summaries by feed category (Tech, World, AI, etc.)
- [x] Write formatted `daily_brief_YYYY-MM-DD.md` to output folder
- [x] Run as a standalone Python script (no UI required)
- [x] Schedule via cron job on Ubuntu

### MCP Tool Layer
- [x] `fetch_rss` tool — structured fetch + parse of RSS/Atom XML
- [x] `summarize_article` tool — send article body to Ollama, return summary
- [x] `save_digest` tool — write markdown output to disk

### Feed Management
- [x] `feeds.yaml` config file — user edits to add/remove/categorize feeds
- [x] Support RSS 2.0 and Atom 1.0 formats
- [x] Per-feed configurable: max articles, enabled/disabled flag
- [x] Global max articles per run (default: 20)

### Digest Output
- [x] Markdown format with headers, source links, timestamps
- [x] One file per day, saved to `./output/`
- [x] Summary word limit configurable (default: 80 words per article)
- [x] Footer with stats (articles processed, model used, time taken)

### Optional UI
- [x] Flask + HTML/CSS/JS web app to browse and read past daily briefs
- [x] Date list sidebar to select past digests
- [x] Category filter pills with horizontal scroll
- [x] Dark / light theme toggle
- [x] Responsive layout (desktop, tablet, mobile)

### Reliability
- [x] Skip articles that fail to fetch (timeout, 404)
- [x] Skip articles where summarization fails
- [x] Log errors without crashing the full run
- [x] Seen-articles cache to avoid re-summarizing old news

---

## ❌ Out of Scope (v1.0)

| Feature | Reason |
|---------|--------|
| Email delivery of digest | v2.0 feature |
| Scraping full article body (beyond RSS description) | Needs browser/scraping stack |
| Multi-language summarization | Model limitation at 3B |
| Sentiment analysis / scoring | Future enhancement |
| Push notifications | Out of scope for local app |
| Authentication / multi-user | Single-user local tool |
| Cloud deployment | Intentionally local |
| Podcast / video feed support | Different pipeline needed |
| Fine-tuning on news style | Separate project |
| Real-time feed watching | Cron-based is sufficient for v1 |

---

## 📦 Deliverables

| Deliverable | Description |
|------------|-------------|
| `agent.py` | Main runnable agent script |
| `mcp/` | Three MCP tool modules |
| `core/` | LLM wrapper + markdown formatter |
| `feeds.yaml` | User-configurable feed list |
| `ui/server.py` | Flask API server |
| `ui/static/index.html` | Responsive web UI (HTML + CSS + JS) |
| `output/` | Daily brief markdown files |
| `README.md` | Setup and usage guide |
| `.env.example` | Config template |
| `requirements.txt` | Python dependencies |
| `tests/` | Unit tests for all tools |

---

## 🏁 Milestones

### Phase 1 — Feed Fetching (Days 1–2)
- [x] `feeds.yaml` schema defined
- [x] `fetch_rss` MCP tool working
- [x] Deduplication cache working
- [x] CLI test: print fetched article titles

### Phase 2 — Summarization (Days 3–4)
- [x] `summarize_article` MCP tool working with Ollama
- [x] Prompt tuned for concise, clean summaries
- [x] Batch summarization with progress logging

### Phase 3 — Agent + Output (Days 5–6)
- [x] Fixed pipeline orchestrating all 3 MCP tools
- [x] `save_digest` tool writing formatted markdown
- [x] `agent.py` end-to-end working

### Phase 4 — Polish (Days 7–8)
- [x] Flask + HTML/CSS/JS responsive web UI
- [x] Cron setup documented
- [x] 28 unit tests passing
- [x] README finalized with MCP and RSS documentation

---

## 📐 Success Criteria

1. Running `python agent.py` produces a valid `daily_brief_YYYY-MM-DD.md` in under **5 minutes**.
2. Each article summary is **60–100 words**, accurate, and not hallucinated.
3. Duplicate articles from previous days are **not re-summarized**.
4. The script **does not crash** if 1–2 feeds are down or slow.
5. Cron job runs silently at 7 AM daily without manual input.
6. All unit tests pass (`pytest tests/`).

---

## ⚠️ Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| llama3.2:3b gives poor summaries | Medium | High | Tune prompt, limit article length input |
| RSS feed returns malformed XML | High | Low | Use `feedparser` which handles edge cases |
| Ollama slow on CPU (no GPU) | High | Medium | Limit articles per run (max 20), async batching |
| Feed returns 403/rate limit | Medium | Low | Skip with warning, retry on next run |
| Seen-articles cache grows too large | Low | Low | Prune entries older than 30 days |

---

## 🔮 Future Scope (v2.0)

- Email delivery (send digest to yourself via `msmtp`)
- Full article scraping (BeautifulSoup + Playwright)
- Keyword filtering (only summarize articles matching your interests)
- Importance scoring (rank articles by relevance to you)
- Voice readout using local TTS (Piper / Coqui)
- Integration with Personal Second Brain (RAG project)
- Weekly summary of summaries
