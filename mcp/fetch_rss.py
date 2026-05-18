import hashlib
import json
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
    return " ".join(BeautifulSoup(text, "html.parser").get_text(separator=" ").split())


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
    pruned = {}
    for k, v in cache.items():
        try:
            ts = datetime.fromisoformat(v)
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            if ts > cutoff:
                pruned[k] = v
        except (ValueError, TypeError):
            pass  # Drop malformed entries
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

    print("🔍 Fetching feeds...")
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
