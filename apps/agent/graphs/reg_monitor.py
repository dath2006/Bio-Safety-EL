"""
RegMonitorGraph — Regulatory Monitoring LangGraph Agent (Phase 3)

Searches for FSSAI and Codex regulatory updates and compares them
against stored HACCP plan sections to generate ComplianceAlert records.
"""
from __future__ import annotations

import logging
import os
from typing import Any, Optional, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph

from tools.web_search import search_regulatory_updates

logger = logging.getLogger(__name__)

# ─── State ───────────────────────────────────────────────────────────────────

class RegMonitorState(TypedDict):
    """State for the regulatory monitoring agent."""
    plan_id: str
    business_name: str
    product_category: str
    # Sections of the current plan to diff against
    plan_sections: list[str]
    # Raw search results from FSSAI/Codex
    search_results: list[dict[str, str]]
    # Detected regulatory changes (each is a dict with title, url, snippet)
    detected_changes: list[dict[str, str]]
    # Alerts to persist
    alerts_to_create: list[dict[str, Any]]
    # Control
    error: Optional[str]


# ─── Nodes ───────────────────────────────────────────────────────────────────

SEARCH_QUERIES = [
    "FSSAI food safety regulation amendment 2024 2025 2026",
    "FSSAI schedule 4 update circular order",
    "Codex Alimentarius food hygiene standard revision",
    "FSSAI inspection checklist revised guidelines",
    "FSSAI microbiological standards dairy RTE update",
]


async def _fetch_regulatory_updates(state: RegMonitorState) -> dict:
    """Node: search regulatory sources for updates."""
    category = state.get("product_category", "general")

    # Build category-specific query
    category_queries = {
        "dairy": "FSSAI dairy pasteurization milk standards amendment",
        "dairy_pasteurized": "FSSAI dairy pasteurization milk standards amendment",
        "rte": "FSSAI ready-to-eat meals microbiological standards update",
        "meat": "FSSAI meat poultry slaughter standards amendment",
        "seafood": "FSSAI fish seafood aquaculture standards update",
        "street_food": "FSSAI street food vendor hygiene guidelines update",
        "cold_chain": "FSSAI cold storage temperature requirements amendment",
        "catering": "FSSAI catering food service standards update",
        "beverages": "FSSAI beverages water standards amendment",
    }

    queries = [
        category_queries.get(category, SEARCH_QUERIES[0]),
        SEARCH_QUERIES[1],  # Generic schedule 4
        SEARCH_QUERIES[4],  # Microbiological
    ]

    all_results: list[dict] = []
    for q in queries:
        try:
            results = await search_regulatory_updates(q)
            all_results.extend(results)
        except Exception as exc:
            logger.warning("Search failed for query '%s': %s", q, exc)

    # Deduplicate by URL
    seen_urls: set[str] = set()
    unique_results: list[dict] = []
    for r in all_results:
        url = r.get("url", "")
        if url not in seen_urls:
            seen_urls.add(url)
            unique_results.append(r)

    return {"search_results": unique_results[:10]}


async def _analyze_changes(state: RegMonitorState) -> dict:
    """Node: compare search results against plan sections using LLM or keyword analysis."""
    search_results = state.get("search_results", [])
    plan_sections = state.get("plan_sections", [])
    product_category = state.get("product_category", "general")

    if not search_results:
        return {"detected_changes": [], "alerts_to_create": []}

    detected_changes: list[dict] = []
    alerts: list[dict] = []

    # Try LLM-based analysis
    try:
        from llm import get_chat_model, has_llm

        if has_llm() and plan_sections:
            llm = get_chat_model(temperature=0.1)
            plan_context = "\n".join(plan_sections[:5])
            search_context = "\n\n".join(
                f"[{r['title']}] ({r['url']})\n{r['snippet']}"
                for r in search_results[:5]
            )

            system_prompt = (
                "You are a food safety compliance analyst. You will analyze whether recent regulatory updates "
                "from FSSAI or Codex Alimentarius are relevant to the given HACCP plan.\n\n"
                "For each relevant update, output a JSON-like summary: "
                "{'regulatory_source': '...', 'change_summary': '...', 'affected_sections': [...], 'is_relevant': true/false}\n"
                "If not relevant, skip it."
            )

            response = await llm.ainvoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=(
                    f"Product Category: {product_category}\n\n"
                    f"Current Plan Sections:\n{plan_context}\n\n"
                    f"Recent Regulatory Updates:\n{search_context}\n\n"
                    "Identify which updates are relevant to this HACCP plan and summarize the impact."
                )),
            ])

            content = response.content
            # Parse a simple check — if LLM found anything relevant
            if "relevant" in content.lower() and "true" in content.lower():
                for result in search_results[:3]:
                    if result.get("title") != "No live updates found":
                        alerts.append({
                            "regulatory_source": "FSSAI",
                            "change_summary": result.get("snippet", "Regulatory update detected.")[:300],
                            "affected_sections": _infer_affected_sections(result.get("snippet", ""), plan_sections),
                            "status": "active",
                        })
                        detected_changes.append(result)
        else:
            # Keyword-based fallback
            detected_changes, alerts = _keyword_analysis(search_results, plan_sections, product_category)

    except Exception as exc:
        logger.warning("LLM analysis failed, using keyword fallback: %s", exc)
        detected_changes, alerts = _keyword_analysis(search_results, plan_sections, product_category)

    return {"detected_changes": detected_changes, "alerts_to_create": alerts}


def _keyword_analysis(
    search_results: list[dict],
    plan_sections: list[str],
    product_category: str,
) -> tuple[list[dict], list[dict]]:
    """Keyword-based fallback for change detection."""
    RELEVANCE_KEYWORDS = [
        "amendment", "revised", "updated", "circular", "order", "notification",
        "schedule 4", "critical limit", "microbiological", "HACCP", "pasteurization",
    ]
    CATEGORY_KEYWORDS = {
        "dairy": ["milk", "dairy", "pasteurization", "UHT"],
        "rte": ["ready-to-eat", "RTE", "meal"],
        "meat": ["meat", "poultry", "slaughter"],
        "seafood": ["fish", "seafood", "aquaculture"],
        "street_food": ["street food", "vendor"],
        "cold_chain": ["cold storage", "temperature", "frozen"],
    }
    category_kws = CATEGORY_KEYWORDS.get(product_category, ["food safety", "FSSAI"])

    detected: list[dict] = []
    alerts: list[dict] = []

    for result in search_results:
        if result.get("title") == "No live updates found":
            continue
        snippet = (result.get("snippet", "") + " " + result.get("title", "")).lower()
        is_relevant = any(kw.lower() in snippet for kw in RELEVANCE_KEYWORDS)
        is_category = any(kw.lower() in snippet for kw in category_kws)

        if is_relevant or is_category:
            detected.append(result)
            source = "FSSAI" if "fssai" in result.get("url", "").lower() else "Codex"
            alerts.append({
                "regulatory_source": source,
                "change_summary": result.get("snippet", "Regulatory update detected.")[:300],
                "affected_sections": _infer_affected_sections(snippet, plan_sections),
                "status": "active",
            })

    return detected, alerts


def _infer_affected_sections(text: str, plan_sections: list[str]) -> list[str]:
    """Infer which plan sections may be affected by a regulatory update."""
    SECTION_KEYWORDS = {
        "Pasteurization CCP": ["pasteurization", "temperature", "thermal"],
        "Critical Limits": ["critical limit", "temperature", "pH", "Aw"],
        "Monitoring Procedures": ["monitoring", "frequency", "record"],
        "Corrective Actions": ["corrective action", "deviation", "recall"],
        "Verification Schedule": ["verification", "audit", "inspection"],
        "Hazard Analysis": ["hazard", "pathogen", "Salmonella", "Listeria"],
        "Biological Hazards": ["microbiological", "pathogen", "bacteria", "virus"],
        "Chemical Hazards": ["pesticide", "chemical", "additive"],
    }
    affected: list[str] = []
    text_lower = text.lower()
    for section, keywords in SECTION_KEYWORDS.items():
        if any(kw.lower() in text_lower for kw in keywords):
            affected.append(section)

    return affected[:3] if affected else ["General Compliance"]


async def _persist_alerts(state: RegMonitorState) -> dict:
    """Node: persist generated alerts to DB (called externally when db_session is available)."""
    # Actual DB persistence is handled by the caller (reg_monitor_task.py)
    # This node just validates and normalizes the alerts
    alerts = state.get("alerts_to_create", [])
    normalized = []
    for alert in alerts:
        normalized.append({
            "regulatory_source": alert.get("regulatory_source", "FSSAI"),
            "change_summary": alert.get("change_summary", "")[:500],
            "affected_sections": alert.get("affected_sections", ["General Compliance"]),
            "status": alert.get("status", "active"),
        })
    return {"alerts_to_create": normalized}


# ─── Graph Builder ────────────────────────────────────────────────────────────

def build_reg_monitor_graph():
    """Build the regulatory monitoring LangGraph agent."""
    graph = StateGraph(RegMonitorState)

    graph.add_node("fetch_updates", _fetch_regulatory_updates)
    graph.add_node("analyze_changes", _analyze_changes)
    graph.add_node("persist_alerts", _persist_alerts)

    graph.set_entry_point("fetch_updates")
    graph.add_edge("fetch_updates", "analyze_changes")
    graph.add_edge("analyze_changes", "persist_alerts")
    graph.add_edge("persist_alerts", END)

    return graph.compile()


async def run_regulatory_monitor(
    plan_id: str,
    business_name: str,
    product_category: str,
    plan_sections: list[str],
) -> list[dict[str, Any]]:
    """
    Run the regulatory monitoring agent for a given plan.

    Returns a list of alert dicts to be persisted to the DB.
    """
    graph = build_reg_monitor_graph()

    initial_state: RegMonitorState = {
        "plan_id": plan_id,
        "business_name": business_name,
        "product_category": product_category,
        "plan_sections": plan_sections,
        "search_results": [],
        "detected_changes": [],
        "alerts_to_create": [],
        "error": None,
    }

    result = await graph.ainvoke(initial_state)
    return result.get("alerts_to_create", [])


__all__ = ["build_reg_monitor_graph", "run_regulatory_monitor"]
