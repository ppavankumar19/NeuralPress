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
