"""Monitoring designer node — designs monitoring procedures for CCPs."""

import json
import re
from typing import List

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from sqlalchemy.ext.asyncio import AsyncSession

from llm import get_chat_model, has_llm
from models.state import HACCPState, MonitoringProcedure

MONITORING_DESIGNER_SYSTEM_PROMPT = """You are an expert food safety engineer specializing in FSSAI Schedule 4 compliance.

Your task is to design a monitoring procedure for each approved Critical Control Point (CCP) and its validated critical limit.

For each CCP, specify:
1. ccp_hazard: The unique CCP key string in the format "{process_step} - {hazard_name}"
2. method: How it will be monitored (e.g. continuous recorder, manual thermometer probe, pH meter)
3. frequency: How often monitoring occurs (e.g. continuous, every batch, hourly, twice daily)
4. responsible_person: Who is responsible (e.g. Pasteurizer Operator, Quality Assurance Inspector, Kitchen Supervisor)
5. record_format: The log/sheet where records are documented (e.g. Pasteurization Temp Log Chart, Daily Chill Room Sheet)

Return ONLY a valid JSON array of monitoring objects matching the MonitoringProcedure schema.

JSON schema per object:
{
  "ccp_hazard": "string",
  "method": "string",
  "frequency": "string",
  "responsible_person": "string",
  "record_format": "string"
}
"""


async def monitoring_designer(
    state: HACCPState,
    db_session: AsyncSession | None = None,
) -> dict:
    """
    Design monitoring protocols for all approved CCPs.
    """
    ccps = state.get("ccps_approved", [])
    limits = state.get("critical_limits", {})
    product_category = state.get("product_category", "general")
    
    if not ccps:
        return {
            "monitoring_procedures": [],
            "current_stage": "corrective_action_gen",
            "messages": [
                AIMessage(content="No CCPs available to design monitoring procedures.")
            ]
        }

    procedures: List[dict] = []
    
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
                f"Design FSSAI-compliant monitoring procedures for each CCP. Return a JSON array."
            )
            
            response = await llm.ainvoke([
                SystemMessage(content=MONITORING_DESIGNER_SYSTEM_PROMPT),
                HumanMessage(content=user_prompt),
            ])
            procedures = _parse_procedures_json(response.content)
        except Exception:
            procedures = _fallback_procedures(ccps)
    else:
        procedures = _fallback_procedures(ccps)

    # Normalize to MonitoringProcedure models
    normalized_procedures: List[dict] = []
    for ccp in ccps:
        ccp_key = f"{ccp['process_step']} - {ccp['hazard_name']}"
        proc_data = next((p for p in procedures if p.get("ccp_hazard") == ccp_key), None)
        
        if not proc_data:
            # Try fuzzy match
            proc_data = next((p for p in procedures if ccp['process_step'] in p.get("ccp_hazard", "")), {})

        record = MonitoringProcedure(
            ccp_hazard=ccp_key,
            method=proc_data.get("method", "Check and log parameters"),
            frequency=proc_data.get("frequency", "Every batch"),
            responsible_person=proc_data.get("responsible_person", "Quality QC Officer"),
            record_format=proc_data.get("record_format", "CCP Parameter Log Sheet")
        )
        normalized_procedures.append(record.model_dump())

    summary_text = _format_monitoring_summary(normalized_procedures)

    return {
        "monitoring_procedures": normalized_procedures,
        "current_stage": "corrective_action_gen",
        "messages": [
            AIMessage(content=summary_text)
        ]
    }


def _parse_procedures_json(content: str) -> List[dict]:
    """Parse JSON array of monitoring procedures from LLM response."""
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


def _fallback_procedures(ccps: list) -> List[dict]:
    """Generate default monitoring procedures when LLM is unavailable."""
    procedures = []
    for ccp in ccps:
        ccp_key = f"{ccp['process_step']} - {ccp['hazard_name']}"
        step_lower = ccp['process_step'].lower()
        
        if "pasteur" in step_lower:
            procedures.append({
                "ccp_hazard": ccp_key,
                "method": "Continuous digital thermometer recording with flow diversion valve checking",
                "frequency": "Continuous automatically; logged manually every 2 hours",
                "responsible_person": "Pasteurizer Operator",
                "record_format": "HTST Pasteurization Log Sheet"
            })
        elif "cook" in step_lower or "heat" in step_lower or "bake" in step_lower:
            procedures.append({
                "ccp_hazard": ccp_key,
                "method": "Calibrated dial/probe thermometer checks inserted into the center of the core product",
                "frequency": "Every batch at final completion",
                "responsible_person": "Production Chef / Kitchen Supervisor",
                "record_format": "Cooking Core Temperature Log Sheet"
            })
        elif "cool" in step_lower or "refrigerat" in step_lower or "storage" in step_lower:
            procedures.append({
                "ccp_hazard": ccp_key,
                "method": "Visual inspection of cold-room digital display and automated SCADA graph logs",
                "frequency": "Twice daily (every morning and evening shifts)",
                "responsible_person": "Cold Storage Supervisor",
                "record_format": "Daily Refrigerator Temperature Sheet"
            })
        else:
            procedures.append({
                "ccp_hazard": ccp_key,
                "method": "Visual and manual parameter testing per SOP",
                "frequency": "Every batch",
                "responsible_person": "Quality Control Inspector",
                "record_format": "GMP Parameter Inspection Log"
            })
            
    return procedures


def _format_monitoring_summary(procedures: List[dict]) -> str:
    """Format monitoring procedures for chat display."""
    lines = ["## CCP Monitoring Procedures (P4)\n"]
    lines.append("Designed FSSAI-compliant monitoring protocols for all active CCPs:\n")
    
    for i, p in enumerate(procedures, 1):
        lines.append(
            f"**{i}. {p['ccp_hazard']}**\n"
            f"  - **Method**: {p['method']}\n"
            f"  - **Frequency**: {p['frequency']}\n"
            f"  - **Responsibility**: {p['responsible_person']}\n"
            f"  - **Record Sheet**: *{p['record_format']}*\n"
        )
        
    return "\n".join(lines)
