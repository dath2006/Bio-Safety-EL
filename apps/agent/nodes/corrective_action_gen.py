"""Corrective Action generator node — designs corrective actions for CCP deviations."""

import json
import re
from typing import List

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from sqlalchemy.ext.asyncio import AsyncSession

from llm import get_chat_model, has_llm
from models.state import HACCPState, CorrectiveAction

CORRECTIVE_ACTION_GEN_SYSTEM_PROMPT = """You are an expert food safety engineer specializing in FSSAI Schedule 4 compliance.

Your task is to design a corrective action procedure for each approved Critical Control Point (CCP) to be triggered when critical limits are breached.

For each CCP, specify:
1. ccp_hazard: The unique CCP key string in the format "{process_step} - {hazard_name}"
2. trigger_condition: The exact deviation trigger (e.g. Temperature drops below 72°C)
3. immediate_action: What must be done immediately to secure the product (e.g. divert flow, quarantine batch, return to cook)
4. root_cause_procedure: How to investigate and resolve the cause (e.g. check steam valve, calibrate probe)
5. personnel: Who is responsible for implementing the corrective actions (e.g. Quality Supervisor, Plant Maintenance Engineer)

Return ONLY a valid JSON array of corrective action objects matching the CorrectiveAction schema.

JSON schema per object:
{
  "ccp_hazard": "string",
  "trigger_condition": "string",
  "immediate_action": "string",
  "root_cause_procedure": "string",
  "personnel": "string"
}
"""


async def corrective_action_gen(
    state: HACCPState,
    db_session: AsyncSession | None = None,
) -> dict:
    """
    Design corrective actions for all approved CCPs.
    """
    ccps = state.get("ccps_approved", [])
    limits = state.get("critical_limits", {})
    product_category = state.get("product_category", "general")
    
    if not ccps:
        return {
            "corrective_actions": [],
            "current_stage": "verification_planner",
            "messages": [
                AIMessage(content="No CCPs available to design corrective actions.")
            ]
        }

    actions: List[dict] = []
    
    if has_llm():
        try:
            llm = get_chat_model(temperature=0.1)
            ccp_limits_text = json.dumps([
                {
                    "ccp_key": f"{ccp['process_step']} - {ccp['hazard_name']}",
                    "limits": limits.get(f"{ccp['process_step']} - {ccp['hazard_name']}", {})
                }
                for ccp in ccps
            ], indent=2)
            
            user_prompt = (
                f"Product category: {product_category}\n"
                f"CCPs & Limits:\n{ccp_limits_text}\n\n"
                f"Design FSSAI-compliant corrective actions for each CCP. Return a JSON array."
            )
            
            response = await llm.ainvoke([
                SystemMessage(content=CORRECTIVE_ACTION_GEN_SYSTEM_PROMPT),
                HumanMessage(content=user_prompt),
            ])
            actions = _parse_actions_json(response.content)
        except Exception:
            actions = _fallback_actions(ccps)
    else:
        actions = _fallback_actions(ccps)

    # Normalize to CorrectiveAction models
    normalized_actions: List[dict] = []
    for ccp in ccps:
        ccp_key = f"{ccp['process_step']} - {ccp['hazard_name']}"
        action_data = next((a for a in actions if a.get("ccp_hazard") == ccp_key), None)
        
        if not action_data:
            action_data = next((a for a in actions if ccp['process_step'] in a.get("ccp_hazard", "")), {})

        record = CorrectiveAction(
            ccp_hazard=ccp_key,
            trigger_condition=action_data.get("trigger_condition", "Critical limit parameter breached"),
            immediate_action=action_data.get("immediate_action", "Isolate product, halt line, notify manager"),
            root_cause_procedure=action_data.get("root_cause_procedure", "Check calibrations, investigate process log"),
            personnel=action_data.get("personnel", "Quality Supervisor")
        )
        normalized_actions.append(record.model_dump())

    summary_text = _format_actions_summary(normalized_actions)

    return {
        "corrective_actions": normalized_actions,
        "current_stage": "verification_planner",
        "messages": [
            AIMessage(content=summary_text)
        ]
    }


def _parse_actions_json(content: str) -> List[dict]:
    """Parse JSON array of corrective actions from LLM response."""
    try:
        data = json.loads(content)
        if isinstance(data, list):
            return data
    except json.JSONDecodeError:
        pass

    match = re.search(r"\[[\s\S]*\]", content)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    return []


def _fallback_actions(ccps: list) -> List[dict]:
    """Generate default corrective actions when LLM is unavailable."""
    actions = []
    for ccp in ccps:
        ccp_key = f"{ccp['process_step']} - {ccp['hazard_name']}"
        step_lower = ccp['process_step'].lower()
        
        if "pasteur" in step_lower:
            actions.append({
                "ccp_hazard": ccp_key,
                "trigger_condition": "Pasteurizer temperature drops below critical limits (e.g. <72°C)",
                "immediate_action": "Flow diversion valve auto-diverts product; hold and quarantine raw milk batch; adjust steam pressure",
                "root_cause_procedure": "Check steam control valve and piping; calibrate temperature probes and record chart",
                "personnel": "Shift Pasteurizer Operator & Maintenance Engineer"
            })
        elif "cook" in step_lower or "heat" in step_lower or "bake" in step_lower:
            actions.append({
                "ccp_hazard": ccp_key,
                "trigger_condition": "Core product temperature drops below critical limits (e.g. <74°C)",
                "immediate_action": "Halt batch output; return product to cook cycle; quarantine affected units until compliance is verified",
                "root_cause_procedure": "Inspect equipment heating elements; verify internal core temperature probe calibration",
                "personnel": "Cooking Supervisor / Production Chef"
            })
        elif "cool" in step_lower or "refrigerat" in step_lower or "storage" in step_lower:
            actions.append({
                "ccp_hazard": ccp_key,
                "trigger_condition": "Chill room/storage temperature rises above critical limit (e.g. >4°C)",
                "immediate_action": "Transfer raw materials to auxiliary cold storage; verify room temperature seal; check log timing",
                "root_cause_procedure": "Inspect cold storage refrigeration compressor; check evaporator units for ice blockages; check door seals",
                "personnel": "Cold Storage Supervisor & Maintenance Engineer"
            })
        else:
            actions.append({
                "ccp_hazard": ccp_key,
                "trigger_condition": "Parameter value falls out of acceptable critical ranges",
                "immediate_action": "Isolate product batch and label clearly; pause production flow; notify QA supervisor",
                "root_cause_procedure": "Review process logs; check calibration of testing equipment; investigate batch formulation",
                "personnel": "Shift Production Supervisor & QA Officer"
            })
            
    return actions


def _format_actions_summary(actions: List[dict]) -> str:
    """Format corrective actions for chat display."""
    lines = ["## Corrective Action Protocols (P5)\n"]
    lines.append("Formulated FSSAI-compliant deviation procedures for all CCPs:\n")
    
    for i, a in enumerate(actions, 1):
        lines.append(
            f"**{i}. {a['ccp_hazard']}**\n"
            f"  - **Deviation Trigger**: {a['trigger_condition']}\n"
            f"  - **Immediate Action**: {a['immediate_action']}\n"
            f"  - **Root Cause Procedure**: {a['root_cause_procedure']}\n"
            f"  - **Responsible Personnel**: {a['personnel']}\n"
        )
        
    return "\n".join(lines)
