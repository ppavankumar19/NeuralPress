from unittest.mock import MagicMock

from mcp.summarize import summarize_article, summarize_batch, SUMMARIZE_PROMPT


SAMPLE_ARTICLE = {
    "id": "abc123",
    "title": "AI Advances Rapidly",
    "description": "Artificial intelligence is advancing at an unprecedented pace across multiple domains.",
    "link": "https://example.com/1",
    "published": "2025-06-01",
    "feed_name": "TechCrunch",
    "category": "Technology",
}


def test_summarize_article_success():
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = "  AI is advancing rapidly across many domains.  "
    result = summarize_article(SAMPLE_ARTICLE, mock_llm, max_words=80)
    assert result == "AI is advancing rapidly across many domains."
    assert mock_llm.invoke.called


def test_summarize_article_prompt_contains_title():
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = "Summary."
    summarize_article(SAMPLE_ARTICLE, mock_llm, max_words=80)
    call_args = mock_llm.invoke.call_args[0][0]
    assert "AI Advances Rapidly" in call_args


def test_summarize_article_failure_returns_empty():
    mock_llm = MagicMock()
    mock_llm.invoke.side_effect = Exception("Connection refused")
    result = summarize_article(SAMPLE_ARTICLE, mock_llm)
    assert result == ""


def test_summarize_batch_attaches_summary():
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = "Brief summary."
    articles = [dict(SAMPLE_ARTICLE)]
    result = summarize_batch(articles, mock_llm)
    assert len(result) == 1
    assert result[0]["summary"] == "Brief summary."


def test_summarize_batch_skips_failed():
    mock_llm = MagicMock()
    mock_llm.invoke.side_effect = [Exception("Fail"), "Good summary."]
    articles = [
        dict(SAMPLE_ARTICLE),
        {**SAMPLE_ARTICLE, "id": "def456", "title": "Second Article"},
    ]
    result = summarize_batch(articles, mock_llm)
    assert len(result) == 1
    assert result[0]["title"] == "Second Article"


def test_summarize_batch_empty_input():
    mock_llm = MagicMock()
    result = summarize_batch([], mock_llm)
    assert result == []
    mock_llm.invoke.assert_not_called()
