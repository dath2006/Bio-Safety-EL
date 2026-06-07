"""HITL CCP Review node — processes user overrides and approves CCP list."""

from langchain_core.messages import AIMessage
from models.state import HACCPState


async def hitl_ccp_review(state: HACCPState) -> dict:
    """
    Process the user decision from the CCP review gate.
    If approved or modified, update approved CCPs list and proceed to critical limits.
    """
    decision = state.get("human_decision")
    
    if decision and decision.get("gate") == "ccp_review":
        action = decision.get("action")
        payload = decision.get("payload", {})
        ccps = payload.get("ccps", [])
        justification = decision.get("justification", "")
        
        if action in ("approve", "modify"):
            # If user approved without modification, payload.ccps may be empty.
            # Fall back to the AI-computed ccps_approved already in state.
            if not ccps:
                ccps = state.get("ccps_approved", [])

            overrides_count = sum(1 for c in ccps if c.get("user_override", False))
            log_msg = f"CCP configuration approved by user. Justification: {justification}" if justification else "CCP configuration approved by user."
            if overrides_count > 0:
                log_msg += f" (Contains {overrides_count} custom override(s))"

            return {
                "ccps_approved": ccps,
                "ccps_user_approved": True,
                "awaiting_human_input": False,
                "current_stage": "limit_fetching",
                "human_decision": None,
                "messages": [
                    AIMessage(content=log_msg)
                ]
            }
        elif action == "reanalyze":
            return {
                "ccps_user_approved": False,
                "awaiting_human_input": False,
                "current_stage": "ccp_determination",
                "human_decision": None,
                "messages": [
                    AIMessage(content="User requested CCP re-evaluation. Routing back to determination stage.")
                ]
            }
            
    # Default fallback: keep state paused
    return {
        "awaiting_human_input": True,
        "current_stage": "ccp_review"
    }
