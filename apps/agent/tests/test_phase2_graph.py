"""Integration tests for Phase 2 complete graph flow and human-in-the-loop gates."""

import pytest
from graphs.haccp_graph import build_haccp_graph, create_initial_state


@pytest.mark.asyncio
async def test_full_phase2_graph_flow():
    """
    Test the entire 12-node graph from intake to completion,
    simulating human decisions at each of the 3 interrupt gates.
    """
    # 1. Compile graph (db_session is None for test keyword RAG fallback)
    graph = build_haccp_graph(db_session=None)
    
    plan_id = "test-plan-12345"
    config = {"configurable": {"thread_id": plan_id}}
    
    # 2. Intake step
    state = create_initial_state(plan_id=plan_id)
    state["business_name"] = "Test Pasteurization Facility"
    state["product_category"] = "dairy_pasteurized"
    state["process_steps"] = ["Reception", "Pasteurization", "Cooling", "Packaging"]
    
    # Start graph run (should pause at hitl_hazard_review)
    result = await graph.ainvoke(state, config)
    
    assert result["current_stage"] == "hazard_review"
    assert result["awaiting_human_input"] is True
    assert len(result["hazards_identified"]) > 0
    
    # 3. Simulate Hazard Review Gate Approval
    hazards = result["hazards_identified"]
    decision_hazard = {
        "gate": "hazard_review",
        "action": "approve",
        "payload": {"hazards": hazards},
        "justification": "Verified all biological and physical hazards"
    }
    
    # Resume by updating decision and calling ainvoke
    graph.update_state(config, {"human_decision": decision_hazard})
    result = await graph.ainvoke(None, config)
    
    assert result["current_stage"] == "ccp_review"
    assert result["awaiting_human_input"] is True
    assert len(result["ccp_candidates"]) > 0
    assert len(result["ccps_approved"]) > 0
    
    # 4. Simulate CCP Review Gate Approval
    ccps = result["ccps_approved"]
    decision_ccp = {
        "gate": "ccp_review",
        "action": "approve",
        "payload": {"ccps": ccps},
        "justification": "Approved pasteurizer as CCP-1"
    }
    
    graph.update_state(config, {"human_decision": decision_ccp})
    result = await graph.ainvoke(None, config)
    
    assert result["current_stage"] == "limits_review"
    assert result["awaiting_human_input"] is True
    assert len(result["critical_limits"]) > 0
    
    # 5. Simulate Limits Review Gate Approval
    limits = result["critical_limits"]
    decision_limits = {
        "gate": "limits_review",
        "action": "approve",
        "payload": {"critical_limits": limits},
        "justification": "Validated minimum 72C temp limits"
    }
    
    graph.update_state(config, {"human_decision": decision_limits})
    result = await graph.ainvoke(None, config)
    
    # 6. Verify all subsequent auto nodes executed to completion
    assert result["current_stage"] == "completed"
    assert result["awaiting_human_input"] is False
    assert len(result["monitoring_procedures"]) > 0
    assert len(result["corrective_actions"]) > 0
    assert len(result["verification_schedule"]["audit_checklist"]) > 0
    assert len(result["records_generated"]) > 0
