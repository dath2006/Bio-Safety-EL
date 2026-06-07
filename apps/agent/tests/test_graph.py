"""Tests for LangGraph HACCP orchestrator (Phase 1 nodes)."""

import pytest

from graphs.haccp_graph import build_haccp_graph, create_initial_state
from nodes.intake import intake_processor


@pytest.mark.asyncio
async def test_intake_processor_valid():
    state = create_initial_state("plan-1")
    state["business_name"] = "Test Dairy"
    state["product_category"] = "dairy_pasteurized"
    state["process_steps"] = ["Reception", "Pasteurization", "Packaging"]

    result = await intake_processor(state)
    assert result["current_stage"] == "hazard_analysis"
    assert result["awaiting_human_input"] is False


@pytest.mark.asyncio
async def test_intake_processor_missing_data():
    state = create_initial_state("plan-2")
    result = await intake_processor(state)
    assert result["awaiting_human_input"] is True
    assert result["current_stage"] == "intake"


@pytest.mark.asyncio
async def test_graph_intake_only_invalid():
    """Graph should stop at intake when data is incomplete."""
    graph = build_haccp_graph(db_session=None)
    state = create_initial_state("plan-3")
    state["business_name"] = ""  # invalid

    result = await graph.ainvoke(state, {"configurable": {"thread_id": "plan-3"}})
    assert result["current_stage"] == "intake"
    assert result.get("hazards_identified", []) == []
