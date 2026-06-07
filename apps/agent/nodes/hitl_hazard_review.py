"""HITL Hazard Review node — processes user overrides for identified hazards."""

from langchain_core.messages import AIMessage
from models.state import HACCPState


async def hitl_hazard_review(state: HACCPState) -> dict:
    """
    Process the user decision from the hazard review gate.
    If approved or modified, update hazards list and proceed.
    """
    decision = state.get("human_decision")
    
    if decision and decision.get("gate") == "hazard_review":
        action = decision.get("action")
        payload = decision.get("payload", {})
        hazards = payload.get("hazards", [])
        justification = decision.get("justification", "")
        
        if action in ("approve", "modify"):
            # Add a log message regarding the user decision
            log_msg = f"Hazard analysis approved by user. Justification: {justification}" if justification else "Hazard analysis approved by user."
            return {
                "hazards_identified": hazards,
                "hazards_user_confirmed": True,
                "awaiting_human_input": False,
                "current_stage": "ccp_determination",
                "human_decision": None,
                "messages": [
                    AIMessage(content=log_msg)
                ]
            }
        elif action == "reanalyze":
            return {
                "hazards_user_confirmed": False,
                "awaiting_human_input": False,
                "current_stage": "intake",
                "human_decision": None,
                "messages": [
                    AIMessage(content="User requested hazard re-analysis. Routing back to intake.")
                ]
            }
            
    # Default fallback: keep state paused
    return {
        "awaiting_human_input": True,
        "current_stage": "hazard_review"
    }
