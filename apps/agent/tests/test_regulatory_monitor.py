"""Tests for the Regulatory Monitoring Agent (RegMonitorGraph)."""
from __future__ import annotations

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestSearchRegulatoryUpdates:
    """Tests for the web search tool."""

    @pytest.mark.asyncio
    async def test_returns_list_of_dicts(self):
        """search_regulatory_updates should return a list of dicts."""
        from tools.web_search import search_regulatory_updates

        with patch("tools.web_search._httpx_scrape", new=AsyncMock(return_value="")):
            result = await search_regulatory_updates("FSSAI dairy standards")
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_no_results_returns_fallback(self):
        """When no pages return content, a fallback synthetic entry is returned."""
        from tools.web_search import search_regulatory_updates

        with patch("tools.web_search._httpx_scrape", new=AsyncMock(return_value="")):
            result = await search_regulatory_updates("dairy pasteurization")
        assert len(result) >= 1
        assert "url" in result[0]
        assert "title" in result[0]
        assert "snippet" in result[0]

    @pytest.mark.asyncio
    async def test_tavily_fallback_when_no_key(self):
        """When no Tavily key, Tavily search returns empty list."""
        from tools.web_search import _tavily_search

        with patch("tools.web_search.TAVILY_API_KEY", ""):
            result = await _tavily_search("FSSAI update")
        assert result == []

    @pytest.mark.asyncio
    async def test_scrape_returns_string(self):
        """_httpx_scrape should return a string even on error."""
        from tools.web_search import _httpx_scrape

        # Test with an invalid URL — should not raise
        result = await _httpx_scrape("http://invalid-domain-that-does-not-exist.xyz", timeout=3)
        assert isinstance(result, str)


class TestRegMonitorGraph:
    """Tests for the RegMonitorGraph LangGraph agent."""

    def _make_mock_results(self):
        return [
            {
                "title": "FSSAI Update: Revised Dairy Standards 2024",
                "url": "https://fssai.gov.in/test",
                "snippet": "FSSAI has revised pasteurization requirements amendment dairy milk temperature limits.",
            }
        ]

    @pytest.mark.asyncio
    async def test_run_monitor_returns_list(self):
        """run_regulatory_monitor should return a list."""
        from graphs.reg_monitor import run_regulatory_monitor

        with patch(
            "graphs.reg_monitor._fetch_regulatory_updates",
            new=AsyncMock(return_value={"search_results": self._make_mock_results()}),
        ):
            result = await run_regulatory_monitor(
                plan_id="test-plan-id",
                business_name="Test Dairy Co.",
                product_category="dairy_pasteurized",
                plan_sections=["Pasteurization CCP: temperature 72°C for 15 seconds"],
            )
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_state_has_required_keys(self):
        """RegMonitorState must have all required keys."""
        from graphs.reg_monitor import RegMonitorState

        state: RegMonitorState = {
            "plan_id": "test-id",
            "business_name": "Test Co.",
            "product_category": "dairy",
            "plan_sections": [],
            "search_results": [],
            "detected_changes": [],
            "alerts_to_create": [],
            "error": None,
        }
        assert state["plan_id"] == "test-id"
        assert state["error"] is None

    def test_keyword_analysis_detects_relevant_results(self):
        """_keyword_analysis should flag regulatory-keyword-containing results."""
        from graphs.reg_monitor import _keyword_analysis

        results = [
            {
                "title": "FSSAI Amendment 2024",
                "url": "https://fssai.gov.in",
                "snippet": "FSSAI schedule 4 revised amendment updated dairy pasteurization critical limit",
            },
            {
                "title": "Food Recipe Blog",
                "url": "https://foodblog.com",
                "snippet": "How to make butter chicken at home — a delicious recipe",
            },
        ]
        detected, alerts = _keyword_analysis(results, ["Pasteurization CCP"], "dairy")
        assert len(detected) >= 1
        assert any(d["url"] == "https://fssai.gov.in" for d in detected)

    def test_infer_affected_sections_maps_keywords(self):
        """_infer_affected_sections should map temperature text to correct sections."""
        from graphs.reg_monitor import _infer_affected_sections

        text = "revised critical limit for pasteurization temperature monitoring"
        sections = _infer_affected_sections(text, [])
        assert len(sections) > 0
        assert any("Limit" in s or "Monitoring" in s or "CCP" in s for s in sections)

    def test_infer_affected_sections_fallback(self):
        """Unknown text should return General Compliance."""
        from graphs.reg_monitor import _infer_affected_sections

        sections = _infer_affected_sections("unrelated text with no keywords", [])
        assert sections == ["General Compliance"]

    @pytest.mark.asyncio
    async def test_graph_builds_without_error(self):
        """build_reg_monitor_graph should compile without error."""
        from graphs.reg_monitor import build_reg_monitor_graph

        graph = build_reg_monitor_graph()
        assert graph is not None
