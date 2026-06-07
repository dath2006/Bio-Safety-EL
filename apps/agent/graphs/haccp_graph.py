"""HACCPOrchestratorGraph — Phase 2: Complete 12-node graph with HITL interrupts."""

from functools import partial
from langgraph.graph import END, StateGraph
from langgraph.checkpoint.memory import MemorySaver

from models.state import HACCPState, create_initial_state

# Import all node functions
from nodes.intake import intake_processor
from nodes.hazard_analyzer import hazard_analyzer
from nodes.hitl_hazard_review import hitl_hazard_review
from nodes.ccp_determinator import ccp_determinator
from nodes.hitl_ccp_review import hitl_ccp_review
from nodes.limit_fetcher import limit_fetcher
from nodes.hitl_limits_review import hitl_limits_review
from nodes.monitoring_designer import monitoring_designer
from nodes.corrective_action_gen import corrective_action_gen
from nodes.verification_planner import verification_planner
from nodes.record_generator import record_generator
from nodes.plan_validator import plan_validator
from nodes.report_generator import report_generator


# --- Conditional Routing Functions ---

def _route_after_intake(state: HACCPState) -> str:
    if state.get("awaiting_human_input"):
        return "end"
    return "hazard_analyzer"


def _route_after_hazard_review(state: HACCPState) -> str:
    if state.get("hazards_user_confirmed", False):
        return "ccp_determinator"
    return "intake_processor"


def _route_after_ccp_review(state: HACCPState) -> str:
    if state.get("ccps_user_approved", False):
        return "critical_limit_fetcher"
    return "ccp_determinator"


def _route_after_limits_review(state: HACCPState) -> str:
    limits = state.get("critical_limits", {})
    if not limits:
        return "critical_limit_fetcher"
    all_validated = all(l.get("user_validated", False) for l in limits.values())
    if all_validated:
        return "monitoring_designer"
    return "critical_limit_fetcher"


# --- Graph Builder ---

def build_haccp_graph(db_session=None, checkpointer=None):
    """
    Build the complete Phase 2 12-node HACCP orchestrator graph with HITL interrupts.
    Pass a checkpointer to enable durable persistence (AsyncPostgresSaver recommended).
    Falls back to in-memory MemorySaver when no checkpointer is provided.
    """
    graph = StateGraph(HACCPState)

    hazard_node = partial(hazard_analyzer, db_session=db_session)
    ccp_node = partial(ccp_determinator, db_session=db_session)
    limits_node = partial(limit_fetcher, db_session=db_session)

    graph.add_node("intake_processor", intake_processor)
    graph.add_node("hazard_analyzer", hazard_node)
    graph.add_node("hitl_hazard_review", hitl_hazard_review)
    graph.add_node("ccp_determinator", ccp_node)
    graph.add_node("hitl_ccp_review", hitl_ccp_review)
    graph.add_node("critical_limit_fetcher", limits_node)
    graph.add_node("hitl_limits_review", hitl_limits_review)
    graph.add_node("monitoring_designer", monitoring_designer)
    graph.add_node("corrective_action_gen", corrective_action_gen)
    graph.add_node("verification_planner", verification_planner)
    graph.add_node("record_generator", record_generator)
    graph.add_node("plan_validator", plan_validator)
    graph.add_node("report_generator", report_generator)

    graph.set_entry_point("intake_processor")

    graph.add_conditional_edges(
        "intake_processor",
        _route_after_intake,
        {"hazard_analyzer": "hazard_analyzer", "end": END},
    )
    graph.add_edge("hazard_analyzer", "hitl_hazard_review")
    graph.add_conditional_edges(
        "hitl_hazard_review",
        _route_after_hazard_review,
        {"ccp_determinator": "ccp_determinator", "intake_processor": "intake_processor"},
    )
    graph.add_edge("ccp_determinator", "hitl_ccp_review")
    graph.add_conditional_edges(
        "hitl_ccp_review",
        _route_after_ccp_review,
        {"critical_limit_fetcher": "critical_limit_fetcher", "ccp_determinator": "ccp_determinator"},
    )
    graph.add_edge("critical_limit_fetcher", "hitl_limits_review")
    graph.add_conditional_edges(
        "hitl_limits_review",
        _route_after_limits_review,
        {"monitoring_designer": "monitoring_designer", "critical_limit_fetcher": "critical_limit_fetcher"},
    )
    graph.add_edge("monitoring_designer", "corrective_action_gen")
    graph.add_edge("corrective_action_gen", "verification_planner")
    graph.add_edge("verification_planner", "record_generator")
    graph.add_edge("record_generator", "plan_validator")
    graph.add_edge("plan_validator", "report_generator")
    graph.add_edge("report_generator", END)

    active_checkpointer = checkpointer if checkpointer is not None else MemorySaver()

    return graph.compile(
        checkpointer=active_checkpointer,
        interrupt_before=["hitl_hazard_review", "hitl_ccp_review", "hitl_limits_review"]
    )


def create_plan_graph(db_session=None, checkpointer=None):
    """Alias for build_haccp_graph."""
    return build_haccp_graph(db_session, checkpointer)


__all__ = ["build_haccp_graph", "create_plan_graph", "create_initial_state"]
