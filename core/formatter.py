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
