"""Verification planner node — establishes verification schedules."""

import json
import re

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from sqlalchemy.ext.asyncio import AsyncSession

from llm import get_chat_model, has_llm
from models.state import HACCPState, VerificationSchedule

VERIFICATION_PLANNER_SYSTEM_PROMPT = """You are an expert food safety engineer specializing in FSSAI Schedule 4 compliance.

Your task is to establish a verification schedule and audit checklist (Principle 6 of HACCP) to ensure the food safety plan is implemented effectively.

Design a verification schedule specifying:
1. review_interval: How often the entire plan is reviewed (e.g. quarterly, semi-annually, annually)
2. audit_checklist: A list of key audit verification activities (e.g. check sensor calibrations, review CCP logs, audit operator training)
3. sign_off_responsibility: Who signs off on the verification reviews (e.g. Food Safety Manager, Operations Director)

Return ONLY a valid JSON object matching the VerificationSchedule schema.

JSON schema:
{
  "review_interval": "string",
  "audit_checklist": ["string", "string", ...],
  "sign_off_responsibility": "string"
}
"""


async def verification_planner(
    state: HACCPState,
    db_session: AsyncSession | None = None,
) -> dict:
    """
    Design verification protocols and audit checklist.
    """
    ccps = state.get("ccps_approved", [])
    product_category = state.get("product_category", "general")
    
    schedule_data = {}
    
    if has_llm():
        try:
            llm = get_chat_model(temperature=0.1)
            ccp_names = ", ".join([f"'{c['process_step']} - {c['hazard_name']}'" for c in ccps])
            user_prompt = (
                f"Product category: {product_category}\n"
                f"CCPs: [{ccp_names}]\n\n"
                f"Design FSSAI-compliant verification checks and sign-off rules. Return a JSON object."
            )
            
            response = await llm.ainvoke([
                SystemMessage(content=VERIFICATION_PLANNER_SYSTEM_PROMPT),
                HumanMessage(content=user_prompt),
            ])
            schedule_data = _parse_schedule_json(response.content)
        except Exception:
            schedule_data = _fallback_schedule()
    else:
        schedule_data = _fallback_schedule()

    # Normalize to VerificationSchedule model
    record = VerificationSchedule(
        review_interval=schedule_data.get("review_interval", "semi-annually"),
        audit_checklist=schedule_data.get("audit_checklist", []),
        sign_off_responsibility=schedule_data.get("sign_off_responsibility", "Food Safety Manager")
    )
    
    summary_text = _format_schedule_summary(record)

    return {
        "verification_schedule": record.model_dump(),
        "current_stage": "record_generator",
        "messages": [
            AIMessage(content=summary_text)
        ]
    }


def _parse_schedule_json(content: str) -> dict:
    """Parse JSON dict of verification schedule from LLM response."""
    try:
        data = json.loads(content)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{[\s\S]*\}", content)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    return {}


def _fallback_schedule() -> dict:
    """Generate default verification schedule when LLM is unavailable."""
    return {
        "review_interval": "semi-annually",
        "audit_checklist": [
            "Verify that weekly calibration of all CCP sensors and thermometers is performed and logged",
            "Perform monthly reviews of CCP monitoring sheets and corrective action records",
            "Conduct an internal audit of all GMP/SOP hygiene protocols at least twice a year",
            "Conduct microbiological testing of finished product batches to validate CCP effectiveness",
            "Check that annual food safety training for handlers is conducted and logged"
        ],
        "sign_off_responsibility": "Food Safety Management Representative (MR)"
    }


def _format_schedule_summary(schedule: VerificationSchedule) -> str:
    """Format verification schedule for chat display."""
    lines = ["## Verification & Audit Schedule (P6)\n"]
    lines.append(f"Established verification intervals and audit items:\n")
    lines.append(f"  - **Review Interval**: {schedule.review_interval}")
    lines.append(f"  - **Sign-off Officer**: {schedule.sign_off_responsibility}\n")
    
    lines.append("### Verification Checklist items:\n")
    for item in schedule.audit_checklist:
        lines.append(f"  - [ ] {item}")
        
    return "\n".join(lines)
