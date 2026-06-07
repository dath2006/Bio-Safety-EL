"""Regulatory web search tool for FSSAI and Codex Alimentarius updates.

Uses httpx to fetch from public regulatory sources.
Optionally integrates Tavily Search API if TAVILY_API_KEY is set in .env.
"""
from __future__ import annotations

import os
import asyncio
import logging
from typing import Any

import httpx
from langchain_core.tools import tool

logger = logging.getLogger(__name__)

FSSAI_SOURCES = [
    "https://fssai.gov.in/cms/recent-updates.php",
    "https://fssai.gov.in/cms/circulars.php",
    "https://fssai.gov.in/cms/order.php",
]

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")


async def _tavily_search(query: str, max_results: int = 5) -> list[dict]:
    """Run a Tavily search if API key is available."""
    if not TAVILY_API_KEY:
        return []
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": TAVILY_API_KEY,
                    "query": query,
                    "search_depth": "basic",
                    "max_results": max_results,
                    "include_domains": ["fssai.gov.in", "codexalimentarius.net", "who.int"],
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("results", [])
    except Exception as exc:
        logger.warning("Tavily search failed: %s", exc)
        return []


async def _httpx_scrape(url: str, timeout: int = 10) -> str:
    """Fetch page text content via plain HTTP."""
    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            resp = await client.get(url, headers={"User-Agent": "HACCP-AI-Monitor/1.0"})
            resp.raise_for_status()
            # Return first 3000 chars — enough for headline/summary extraction
            return resp.text[:3000]
    except Exception as exc:
        logger.warning("Failed to scrape %s: %s", url, exc)
        return ""


async def search_regulatory_updates(query: str) -> list[dict[str, str]]:
    """
    Search for FSSAI regulatory updates.

    Returns a list of dicts with 'title', 'url', and 'snippet' keys.
    Tries Tavily first (if key available), falls back to direct HTTP scraping.
    """
    # 1. Try Tavily first
    tavily_results = await _tavily_search(query)
    if tavily_results:
        return [
            {
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "snippet": r.get("content", "")[:500],
            }
            for r in tavily_results
        ]

    # 2. Fallback: scrape known FSSAI pages
    results: list[dict[str, str]] = []
    tasks = [_httpx_scrape(url) for url in FSSAI_SOURCES]
    pages = await asyncio.gather(*tasks, return_exceptions=True)

    for url, content in zip(FSSAI_SOURCES, pages):
        if isinstance(content, str) and content.strip():
            # Look for lines mentioning the query keywords
            lines = content.splitlines()
            relevant = [
                l.strip()
                for l in lines
                if any(kw.lower() in l.lower() for kw in query.split()[:4])
            ][:5]
            if relevant:
                results.append(
                    {
                        "title": f"FSSAI Update from {url}",
                        "url": url,
                        "snippet": " ".join(relevant)[:500],
                    }
                )

    if not results:
        # Return a synthetic entry to tell the agent no live data was found
        results.append(
            {
                "title": "No live updates found",
                "url": "https://fssai.gov.in",
                "snippet": (
                    "Could not retrieve live FSSAI regulatory updates at this time. "
                    "Recommend checking fssai.gov.in manually for recent circulars."
                ),
            }
        )

    return results


@tool
async def fssai_regulatory_search(query: str) -> str:
    """
    Search for FSSAI and Codex regulatory updates matching the given query.

    Args:
        query: Natural language description of what regulatory change to look for.
               Example: 'FSSAI dairy pasteurization temperature limits amendment 2024'

    Returns:
        Formatted string of matching regulatory updates with source URLs.
    """
    results = await search_regulatory_updates(query)
    if not results:
        return "No regulatory updates found for the query."

    formatted = []
    for i, r in enumerate(results, 1):
        formatted.append(
            f"{i}. **{r['title']}**\n"
            f"   URL: {r['url']}\n"
            f"   Summary: {r['snippet']}\n"
        )
    return "\n".join(formatted)


__all__ = ["fssai_regulatory_search", "search_regulatory_updates"]
