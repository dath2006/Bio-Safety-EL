"""CCP determinator node — evaluates hazards using Codex decision tree."""

import json
import re
from typing import List

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from sqlalchemy.ext.asyncio import AsyncSession

from llm import get_chat_model, has_llm
from models.state import HACCPState, CCPCandidate, CCP
from tools.decision_tree import CodexAssessment, evaluate_codex_tree

CCP_DETERMINATION_SYSTEM_PROMPT = """You are an expert food safety engineer specializing in HACCP and FSSAI Schedule 4 compliance.

Your task is to evaluate a list of identified hazards using the Codex 2020 CCP Decision Tree questions to determine which hazards require Critical Control Points (CCPs).

For each hazard, answer the following questions:
1. q1_has_control (boolean): Do control measures exist at this step or subsequent steps for this hazard?
2. q1_sub_necessary (boolean or null): If q1 is No: Is control at this step necessary for safety?
3. q2_designed_to_prevent (boolean): Is the step specifically designed to eliminate or reduce the likely occurrence of this hazard to an acceptable level?
4. q3_contamination_possible (boolean): Could contamination with this hazard occur in excess of acceptable levels or increase to unacceptable levels?
5. q4_subsequent_step_prevents (boolean): Will a subsequent step eliminate this hazard or reduce its likely occurrence to an acceptable level?

Provide a detailed 'reasoning' string for your answers.
Return ONLY a valid JSON array of assessment objects matching the schema.

JSON schema per assessment:
{
  "hazard_name": "string",
  "process_step": "string",
  "q1_has_control": true|false,
  "q1_sub_necessary": true|false|null,
  "q2_designed_to_prevent": true|false,
  "q3_contamination_possible": true|false,
  "q4_subsequent_step_prevents": true|false,
  "reasoning": "string"
}
"""


async def ccp_determinator(
    state: HACCPState,
    db_session: AsyncSession | None = None,
) -> dict:
    """
    Evaluate all confirmed hazards using Codex decision tree questions.
    Returns candidate CCPs and sets up initial approved CCPs.
    """
    hazards = state.get("hazards_identified", [])
    product_category = state.get("product_category", "general")
    
    if not hazards:
        return {
            "ccp_candidates": [],
            "ccps_approved": [],
            "ccps_user_approved": False,
            "current_stage": "ccp_review",
            "awaiting_human_input": True,
            "messages": [
                AIMessage(content="No hazards found to evaluate for CCPs. Please add hazards first.")
            ]
        }

    assessments: List[dict] = []
    
    if has_llm():
        try:
            llm = get_chat_model(temperature=0.1)
            hazards_text = json.dumps([
                {
                    "name": h.get("name"),
                    "category": h.get("category"),
                    "process_step": h.get("process_step"),
                    "rpn": h.get("rpn", h.get("likelihood", 3) * h.get("severity", 3)),
                    "recommended_control": h.get("recommended_control")
                }
                for h in hazards
            ], indent=2)
            
            user_prompt = (
                f"Product category: {product_category}\n\n"
                f"Identify CCPs for the following hazards:\n{hazards_text}\n\n"
                f"Evaluate each using the decision tree. Return a JSON array."
            )
            
            response = await llm.ainvoke([
                SystemMessage(content=CCP_DETERMINATION_SYSTEM_PROMPT),
                HumanMessage(content=user_prompt),
            ])
            assessments = _parse_assessments_json(response.content)
            # If LLM returned something we couldn't parse, use rule-based fallback
            if not assessments:
                assessments = _fallback_ccp_assessments(hazards)
        except Exception as exc:
            # Fallback on network/API failure
            assessments = _fallback_ccp_assessments(hazards)
    else:
        assessments = _fallback_ccp_assessments(hazards)

    # Programmatically process the assessments through our Codex decision tree logic
    candidates: List[dict] = []
    approved_initial: List[dict] = []
    
    for item in assessments:
        try:
            assessment = CodexAssessment(**item)
            is_ccp, path, reasoning = evaluate_codex_tree(assessment)
            
            candidate = CCPCandidate(
                hazard_name=assessment.hazard_name,
                process_step=assessment.process_step,
                is_ccp=is_ccp,
                confidence=0.85 if has_llm() else 0.5,
                decision_tree_path=path,
                reasoning=reasoning
            )
            candidates.append(candidate.model_dump())
            
            # If evaluated as a CCP, add to the initial approved list
            if is_ccp:
                ccp_rec = CCP(
                    hazard_name=assessment.hazard_name,
                    process_step=assessment.process_step,
                    decision_tree_path=path,
                    user_override=False,
                    override_justification=None
                )
                approved_initial.append(ccp_rec.model_dump())
        except Exception:
            continue

    summary_text = _format_ccp_summary(candidates, approved_initial)

    return {
        "ccp_candidates": candidates,
        "ccps_approved": approved_initial,
        "ccps_user_approved": False,
        "current_stage": "ccp_review",
        "awaiting_human_input": True,
        "messages": [
            AIMessage(content=summary_text)
        ]
    }


def _parse_assessments_json(content: str) -> List[dict]:
    """Parse JSON array of Codex assessments from LLM content."""
    # Strip markdown fenced code blocks (```json ... ``` or ``` ... ```)
    stripped = re.sub(r"```(?:json)?\s*", "", content).strip()

    for text in (stripped, content):
        try:
            data = json.loads(text)
            if isinstance(data, list):
                return data
            if isinstance(data, dict) and "assessments" in data:
                return data["assessments"]
        except json.JSONDecodeError:
            pass

        match = re.search(r"\[[\s\S]*\]", text)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass

    return []


def _fallback_ccp_assessments(hazards: List[dict]) -> List[dict]:
    """Generate default Codex assessments when LLM is unavailable or returns bad JSON.
    
    Logic mirrors the Codex 2020 CCP Decision Tree:
    - Biological hazards at thermal-kill steps (pasteurisation, cooking, etc.) → CCP
    - Biological hazards at upstream steps (reception, storage) → NOT a CCP *if* a
      downstream thermal step exists that will control them
    - Biological hazards with no downstream thermal step → CCP (control must happen here)
    - Chemical/physical hazards → evaluated purely on severity and control availability
    """
    # Collect all unique process step names present in the hazard list
    all_steps = {h.get("process_step", "").lower() for h in hazards}
    thermal_keywords = ("pasteur", "cook", "heat", "steril", "kill", "bake", "fry", "roast", "boil")
    process_has_thermal_kill = any(
        any(kw in step for kw in thermal_keywords) for step in all_steps
    )

    assessments = []
    for h in hazards:
        name_lower = h.get("name", "").lower()
        step_lower = h.get("process_step", "").lower()
        category = h.get("category", "biological")
        severity = int(h.get("severity", 3))

        # Is THIS specific step a thermal-kill step?
        is_thermal_kill = any(kw in step_lower for kw in thermal_keywords)

        if category == "biological" and is_thermal_kill:
            # Step specifically designed to eliminate pathogens → CCP
            assessments.append({
                "hazard_name": h.get("name"),
                "process_step": h.get("process_step"),
                "q1_has_control": True,
                "q1_sub_necessary": None,
                "q2_designed_to_prevent": True,
                "q3_contamination_possible": True,
                "q4_subsequent_step_prevents": False,
                "reasoning": (
                    f"Step '{h.get('process_step')}' involves thermal treatment specifically "
                    f"designed to destroy pathogens including {h.get('name')}. Classified as CCP."
                )
            })
        elif category == "biological" and not is_thermal_kill:
            # Upstream step: if a thermal-kill step exists later it will control the hazard
            q4_subsequent = process_has_thermal_kill
            assessments.append({
                "hazard_name": h.get("name"),
                "process_step": h.get("process_step"),
                "q1_has_control": True,
                "q1_sub_necessary": None,
                "q2_designed_to_prevent": False,
                "q3_contamination_possible": True,
                "q4_subsequent_step_prevents": q4_subsequent,
                "reasoning": (
                    f"Step '{h.get('process_step')}' is not specifically a thermal-kill step. "
                    + (
                        "A downstream thermal-kill CCP will control this hazard."
                        if q4_subsequent
                        else "No subsequent thermal step exists; this step must be a CCP."
                    )
                )
            })
        else:
            # Chemical / physical hazard — mark as CCP only if severity is high and no alternative control
            is_ccp_candidate = severity >= 4
            assessments.append({
                "hazard_name": h.get("name"),
                "process_step": h.get("process_step"),
                "q1_has_control": True,
                "q1_sub_necessary": None,
                "q2_designed_to_prevent": is_ccp_candidate,
                "q3_contamination_possible": True,
                "q4_subsequent_step_prevents": not is_ccp_candidate,
                "reasoning": (
                    f"{category.title()} hazard '{h.get('name')}' at step '{h.get('process_step')}'. "
                    + (
                        "High severity requires dedicated CCP control at this step."
                        if is_ccp_candidate
                        else "Controlled by GMP/SOP; not classified as CCP."
                    )
                )
            })

    return assessments


def _format_ccp_summary(candidates: List[dict], approved: List[dict]) -> str:
    """Format the candidate CCP evaluation for the chat window."""
    lines = ["## CCP Determination (Codex 2020 Tree)\n"]
    lines.append(f"Evaluated {len(candidates)} hazards against the Codex decision tree.\n")
    
    if approved:
        lines.append("### Recommended Critical Control Points (CCPs):\n")
        for i, c in enumerate(approved, 1):
            lines.append(
                f"**{i}. {c['process_step']} — {c['hazard_name']}**\n"
                f"  - Decision Path: {' -> '.join(c['decision_tree_path'])}\n"
            )
    else:
        lines.append("*No candidate CCPs were automatically identified. All hazards are controlled by subsequent steps or standard GMPs/SOPs.*\n")

    lines.append("\n*Awaiting your review and approval. You can override any recommendation with justification.*")
    return "\n".join(lines)
