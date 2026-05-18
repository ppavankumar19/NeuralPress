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
