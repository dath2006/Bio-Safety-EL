"""Plan validator node — verifies compliance with FSSAI Schedule 4 rules."""

from langchain_core.messages import AIMessage
from models.state import HACCPState


async def plan_validator(state: HACCPState) -> dict:
    """
    Validate the entire generated plan against FSSAI Schedule 4 requirements.
    Calculates compliance score and logs any gaps.
    """
    gaps = []
    score = 100
    
    # 1. Intake
    if not state.get("business_name"):
        gaps.append("Missing business organization name")
        score -= 10
    if not state.get("process_steps") or len(state["process_steps"]) < 2:
        gaps.append("Process flow must contain at least 2 steps")
        score -= 10
        
    # 2. Principle 1: Hazards
    if not state.get("hazards_identified"):
        gaps.append("No hazards identified in the hazard register")
        score -= 15
    elif not state.get("hazards_user_confirmed"):
        gaps.append("Hazard analysis has not been confirmed by the user")
        score -= 10
        
    # 3. Principle 2: CCPs
    if not state.get("ccps_approved") and state.get("hazards_identified"):
        gaps.append("No CCPs have been designated/approved in the plan")
        score -= 15
        
    # 4. Principle 3: Limits
    ccp_keys = [f"{c['process_step']} - {c['hazard_name']}" for c in state.get("ccps_approved", [])]
    limits = state.get("critical_limits", {})
    
    missing_limits = 0
    for key in ccp_keys:
        if key not in limits:
            missing_limits += 1
            
    if missing_limits > 0:
        gaps.append(f"Missing critical limits for {missing_limits} CCP(s)")
        score -= (missing_limits * 5)
        
    # 5. Principle 4: Monitoring
    procedures = state.get("monitoring_procedures", [])
    monitored_keys = [p["ccp_hazard"] for p in procedures]
    missing_monitoring = sum(1 for key in ccp_keys if key not in monitored_keys)
    if missing_monitoring > 0:
        gaps.append(f"Missing monitoring procedures for {missing_monitoring} CCP(s)")
        score -= (missing_monitoring * 5)
        
    # 6. Principle 5: Corrective Actions
    actions = state.get("corrective_actions", [])
    action_keys = [a["ccp_hazard"] for a in actions]
    missing_actions = sum(1 for key in ccp_keys if key not in action_keys)
    if missing_actions > 0:
        gaps.append(f"Missing corrective action plans for {missing_actions} CCP(s)")
        score -= (missing_actions * 5)
        
    # 7. Principle 6 & 7: Verification & Records
    if not state.get("verification_schedule"):
        gaps.append("Missing verification schedule and internal audit intervals")
        score -= 10
    if not state.get("records_generated"):
        gaps.append("Missing record-keeping template checklists")
        score -= 10

    score = max(0, score)

    summary_lines = ["## FSSAI Schedule 4 Compliance Audit\n"]
    summary_lines.append(f"**Compliance Score**: `{score}%` \n")
    
    if gaps:
        summary_lines.append("### Identified Gaps:\n")
        for g in gaps:
            summary_lines.append(f"  - ⚠️ {g}")
    else:
        summary_lines.append("🎉 **Congratulations! The plan meets all FSSAI Schedule 4 regulatory criteria and is ready for report compilation.**")

    return {
        "current_stage": "report_generator",
        "messages": [
            AIMessage(content="\n".join(summary_lines))
        ]
    }
