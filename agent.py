#!/usr/bin/env python3
"""
RSS Digest Agent — Main Runner
Usage: python agent.py [--config feeds.yaml] [--output ./output]
"""

import argparse
import os
import time
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from core.llm import get_llm
from mcp.fetch_rss import fetch_all_feeds
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
    articles, _seen = fetch_all_feeds(args.config)

    if not articles:
        print("💤 No new articles today. Try again later.")
        return

    # Step 2: Summarize with llama3.2:3b
    llm = get_llm()
    max_words = int(os.getenv("SUMMARY_MAX_WORDS", 80))
    summarized = summarize_batch(articles, llm, max_words)

    if not summarized:
        print("❌ All articles failed to summarize. Check Ollama is running.")
        return

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
