import logging
import re
from urllib.parse import quote

import requests

logger = logging.getLogger(__name__)

HEADERS = {"User-Agent": "LearnixBot/1.0 (Educational Platform)"}


def _clean_text(text):
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", "", text)
    return " ".join(text.split())


def search_duckduckgo(query, max_topics=4):
    """Fetch instant answers and related topics from DuckDuckGo."""
    results = []
    try:
        resp = requests.get(
            "https://api.duckduckgo.com/",
            params={
                "q": query,
                "format": "json",
                "no_redirect": 1,
                "no_html": 1,
                "skip_disambig": 1,
            },
            headers=HEADERS,
            timeout=8,
        )
        resp.raise_for_status()
        data = resp.json()

        if data.get("Heading"):
            results.append(f"Topic: {data['Heading']}")

        abstract = _clean_text(data.get("AbstractText", ""))
        if abstract:
            source = data.get("AbstractSource", "Web")
            results.append(f"{source}: {abstract}")

        for topic in data.get("RelatedTopics", [])[:max_topics]:
            if isinstance(topic, dict) and topic.get("Text"):
                results.append(_clean_text(topic["Text"]))
            elif isinstance(topic, dict) and "Topics" in topic:
                for sub in topic["Topics"][:2]:
                    if sub.get("Text"):
                        results.append(_clean_text(sub["Text"]))
    except Exception as exc:
        logger.warning("DuckDuckGo search failed: %s", exc)

    return results


def search_wikipedia(query):
    """Fetch a concise Wikipedia summary for educational context."""
    try:
        title = quote(query.strip().replace(" ", "_"))
        resp = requests.get(
            f"https://en.wikipedia.org/api/rest_v1/page/summary/{title}",
            headers=HEADERS,
            timeout=8,
        )
        if resp.status_code != 200:
            # Try search API to resolve title
            search_resp = requests.get(
                "https://en.wikipedia.org/w/api.php",
                params={
                    "action": "opensearch",
                    "search": query,
                    "limit": 1,
                    "format": "json",
                },
                headers=HEADERS,
                timeout=8,
            )
            if search_resp.status_code == 200:
                titles = search_resp.json()
                if len(titles) >= 2 and titles[1]:
                    title = quote(titles[1][0].replace(" ", "_"))
                    resp = requests.get(
                        f"https://en.wikipedia.org/api/rest_v1/page/summary/{title}",
                        headers=HEADERS,
                        timeout=8,
                    )

        if resp.status_code == 200:
            data = resp.json()
            extract = _clean_text(data.get("extract", ""))
            if extract:
                page_title = data.get("title", query)
                return f"Wikipedia ({page_title}): {extract}"
    except Exception as exc:
        logger.warning("Wikipedia search failed: %s", exc)

    return None


def fetch_web_context(query, max_chars=2500):
    """
    Search the web for relevant context to augment Gemini responses.
    Returns a formatted context string or empty string if nothing found.
    """
    if not query or not query.strip():
        return ""

    parts = []
    parts.extend(search_duckduckgo(query))

    wiki = search_wikipedia(query)
    if wiki:
        parts.append(wiki)

    if not parts:
        # Extract key terms for a secondary search
        keywords = re.sub(
            r"\b(what|is|are|the|a|an|explain|tell|me|about|how|does|do|define|describe)\b",
            "",
            query.lower(),
            flags=re.I,
        ).strip()
        if keywords and keywords != query.lower():
            parts.extend(search_duckduckgo(keywords, max_topics=2))

    context = "\n".join(dict.fromkeys(parts))  # dedupe preserving order
    return context[:max_chars]
