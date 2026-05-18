# 📰 NeuralPress — Local RSS Digest Agent
> Fetch RSS feeds, summarize with `llama3.2:3b` via MCP tools, and wake up to a clean daily brief — fully offline, zero subscriptions.

![Python](https://img.shields.io/badge/Python-3.12+-blue?logo=python)
![Ollama](https://img.shields.io/badge/Ollama-llama3.2:3b-black)
![MCP](https://img.shields.io/badge/MCP-Model%20Context%20Protocol-purple)
![LangChain](https://img.shields.io/badge/LangChain-0.3-green)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

---

## 📡 What Is RSS?

**RSS (Really Simple Syndication)** is a standard web format that websites use to publish their latest content in a machine-readable way.

Instead of visiting 10 different news sites every morning, each website exposes an RSS **feed** — a structured XML file listing their latest articles with titles, summaries, links, and timestamps. This app fetches those XML files and gets all the new content in one place.

```xml
<rss version="2.0">
  <channel>
    <title>TechCrunch</title>
    <item>
      <title>OpenAI Releases New Model</title>
      <link>https://techcrunch.com/...</link>
      <description>OpenAI has announced...</description>
      <pubDate>Sun, 18 May 2026 07:00:00 GMT</pubDate>
    </item>
  </channel>
</rss>
```

RSS is the **input source** of the entire pipeline — no scraping, no logins, no paid APIs.

---

## ✨ What Is This?

A **local AI-powered news agent** that:
1. Fetches articles from your chosen RSS feeds every morning
2. Uses `llama3.2:3b` (via Ollama) to summarize each article
3. Groups summaries by topic/category
4. Saves a clean `daily_brief_YYYY-MM-DD.md` to your `output/` folder
5. Optionally serves a responsive web UI at `localhost:5000`

No cloud. No API keys. No tracking. Just your news, summarized your way.

---

## 🖥️ System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| OS | Ubuntu 22.04 | Ubuntu 24.04 LTS |
| RAM | 8 GB | 16 GB |
| Ollama Model | llama3.2:3b | llama3.2:3b |
| Python | 3.10+ | 3.11 |
| Internet | Required (RSS fetch) | Required |
| Storage | 2 GB (model) | 5 GB |

---

## 🚀 Quick Start

### 1. Make sure Ollama is running

```bash
ollama serve &
ollama list   # should show llama3.2:3b
```

### 2. Clone & Setup

```bash
git clone git@github.com:ppavankumar19/NeuralPress.git
cd NeuralPress

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure your feeds

```bash
cp feeds.example.yaml feeds.yaml
# Edit feeds.yaml with your preferred RSS sources
```

### 4. Run manually

```bash
python agent.py
# Digest saved to ~/daily_brief_2025-06-01.md
```

### 5. (Optional) Open the web UI

```bash
python ui/server.py
# Open http://localhost:5000
```

### 6. (Optional) Schedule daily at 7 AM

```bash
crontab -e
# Add this line:
0 7 * * * /path/to/rss-digest-agent/venv/bin/python /path/to/rss-digest-agent/agent.py
```

---

## 📁 Project Structure

```
rss-digest-agent/
├── agent.py                  # Main agent entry point
├── feeds.yaml                # Your RSS feed list (you edit this)
├── feeds.example.yaml        # Example feed config
├── requirements.txt
├── .env
├── .env.example
│
├── mcp/
│   ├── __init__.py
│   ├── fetch_rss.py          # MCP Tool: fetch & parse RSS feeds
│   ├── summarize.py          # MCP Tool: summarize article via Ollama
│   └── save_digest.py        # MCP Tool: write digest markdown file
│
├── core/
│   ├── __init__.py
│   ├── llm.py                # Ollama LLM wrapper
│   └── formatter.py          # Markdown digest formatter
│
├── ui/
│   ├── server.py             # Flask API server
│   └── static/
│       └── index.html        # Web UI (HTML + CSS + JS, single file)
│
├── output/
│   └── .gitkeep              # Daily briefs saved here
│
└── tests/
    ├── test_fetch_rss.py
    ├── test_summarize.py
    ├── test_formatter.py
    └── test_save_digest.py
```

---

## 📰 Sample Output (`daily_brief_2025-06-01.md`)

```markdown
# 📰 Daily Brief — Sunday, June 1 2025
Generated at 07:00 AM | Model: llama3.2:3b | 12 articles from 4 feeds

---

## 🌍 World News
### India Signs New Climate Agreement
*Source: BBC World — Jun 1, 2025*
India and 30 other nations signed a landmark climate deal focusing on
renewable energy targets by 2035. The agreement includes $50B in funding...
📎 [Read full article](https://bbc.com/...)

---

## 💻 Technology
### New Open-Source LLM Released by Mistral
*Source: TechCrunch — Jun 1, 2025*
Mistral AI released a new 12B parameter model outperforming GPT-4o on
several benchmarks, available under Apache 2.0 license...

---
*Digest generated locally by RSS Digest Agent using llama3.2:3b*
```

---

## 📡 Default Feed Categories

| Category | Example Sources |
|----------|----------------|
| 🌍 World News | BBC, Reuters, Al Jazeera |
| 💻 Technology | TechCrunch, Hacker News, Ars Technica |
| 🤖 AI / ML | Towards Data Science, The Batch, Import AI |
| 🇮🇳 India | NDTV, The Hindu, Times of India |
| 🔬 Science | NASA, Nature, New Scientist |

---

## ⚙️ MCP Tools Used

| Tool | What It Does |
|------|-------------|
| `fetch_rss` | Fetches and parses RSS/Atom feed XML |
| `summarize_article` | Sends article text to llama3.2 for summarization |
| `save_digest` | Writes final markdown digest to output folder |

---

## 🛠️ Contributing

PRs welcome. Open an issue first for major changes.

---

## 📄 License

MIT © 2026
