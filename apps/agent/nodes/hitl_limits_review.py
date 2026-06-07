"""HITL Limits Review node — processes user validation for critical limits."""

from langchain_core.messages import AIMessage
from models.state import HACCPState


async def hitl_limits_review(state: HACCPState) -> dict:
    """
    Process the user decision from the critical limits review gate.
    If approved or modified, update limits and proceed to monitoring design.
    """
    decision = state.get("human_decision")
    
    if decision and decision.get("gate") == "limits_review":
        action = decision.get("action")
        payload = decision.get("payload", {})
        limits = payload.get("critical_limits", {})
        justification = decision.get("justification", "")
        
        if action in ("approve", "modify"):
            # Mark all confirmed limits as validated
            validated_limits = {}
            for ccp_key, limit_data in limits.items():
                limit_data["user_validated"] = True
                validated_limits[ccp_key] = limit_data
                
            log_msg = f"Critical limits validated by user. Justification: {justification}" if justification else "Critical limits validated by user."
            return {
                "critical_limits": validated_limits,
                "awaiting_human_input": False,
                "current_stage": "monitoring_designer",
                "human_decision": None,
                "messages": [
                    AIMessage(content=log_msg)
                ]
            }
        elif action == "reanalyze":
            return {
                "awaiting_human_input": False,
                "current_stage": "limit_fetching",
                "human_decision": None,
                "messages": [
                    AIMessage(content="User requested critical limits re-evaluation. Routing back.")
                ]
            }
            
    # Default fallback: keep state paused
    return {
        "awaiting_human_input": True,
        "current_stage": "limits_review"
    }
