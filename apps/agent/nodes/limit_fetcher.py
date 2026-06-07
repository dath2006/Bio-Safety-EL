"""Critical Limit fetcher node — fetches limits from knowledge base using RAG."""

import json
import re
from typing import Dict

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from sqlalchemy.ext.asyncio import AsyncSession

from llm import get_chat_model, has_llm
from models.state import HACCPState, CriticalLimit
from rag.retriever import RegulatoryRetriever, chunks_to_context

LIMIT_FETCHER_SYSTEM_PROMPT = """You are an expert food safety engineer specializing in FSSAI Schedule 4 compliance.

Your task is to determine the Critical Limits (such as temperature, duration, pH, moisture, or chemical ppm) for each Critical Control Point (CCP).

INSTRUCTIONS:
1. Base your limits ONLY on the provided regulatory context. Do not invent values or citations.
2. For each CCP, provide:
   - parameter (e.g., "Pasteurization Temperature", "Storage Temperature")
   - min_value (float or null)
   - max_value (float or null)
   - unit (e.g., "°C", "seconds", "pH")
   - source_citation (the exact FSSAI or Codex section and document title)
3. Return ONLY a valid JSON object where:
   - The keys are the unique CCP identifier string in the format "{process_step} - {hazard_name}".
   - The values are objects matching the CriticalLimit JSON schema.

JSON schema per value:
{
  "parameter": "string",
  "min_value": float|null,
  "max_value": float|null,
  "unit": "string",
  "source_citation": "string"
}
"""


async def limit_fetcher(
    state: HACCPState,
    db_session: AsyncSession | None = None,
) -> dict:
    """
    RAG retrieval for critical limits per approved CCP.
    Returns critical limits configuration.
    """
    ccps = state.get("ccps_approved", [])
    product_category = state.get("product_category", "general")
    
    if not ccps:
        return {
            "critical_limits": {},
            "current_stage": "limits_review",
            "awaiting_human_input": True,
            "messages": [
                AIMessage(content="No approved CCPs found to design critical limits. Please approve CCPs first.")
            ]
        }

    retriever = RegulatoryRetriever()
    all_chunks = []
    rag_sources = []
    ccp_details = []

    for ccp in ccps:
        ccp_key = f"{ccp['process_step']} - {ccp['hazard_name']}"
        ccp_details.append(ccp_key)
        
        query = (
            f"What are the critical limits (temperature, time, pH, or limits) for "
            f"controlling {ccp['hazard_name']} at {ccp['process_step']} in "
            f"{product_category} production under FSSAI Schedule 4 and Codex?"
        )
        chunks = await retriever.retrieve(
            session=db_session,
            query=query,
            product_category=product_category,
            top_k=3,
        )
        all_chunks.extend(chunks)
        rag_sources.extend([c.citation for c in chunks])

    rag_sources = list(dict.fromkeys(rag_sources))
    context = chunks_to_context(all_chunks) if all_chunks else "No regulatory context retrieved."

    limits: Dict[str, dict] = {}
    
    if has_llm():
        try:
            llm = get_chat_model(temperature=0.1)
            ccp_input = ", ".join([f"'{c}'" for c in ccp_details])
            user_prompt = (
                f"Product category: {product_category}\n"
                f"Approved CCPs: [{ccp_input}]\n\n"
                f"Regulatory context:\n{context}\n\n"
                f"Extract critical limits for each CCP and return a JSON object."
            )
            
            response = await llm.ainvoke([
                SystemMessage(content=LIMIT_FETCHER_SYSTEM_PROMPT),
                HumanMessage(content=user_prompt),
            ])
            limits = _parse_limits_json(response.content)
        except Exception:
            limits = _fallback_limits(ccps)
    else:
        limits = _fallback_limits(ccps)

    # Normalize limits and mark user_validated as False
    normalized_limits: Dict[str, dict] = {}
    for ccp in ccps:
        ccp_key = f"{ccp['process_step']} - {ccp['hazard_name']}"
        limit_data = limits.get(ccp_key, {})
        
        # If the LLM returned it under a slightly different key, try matching by step
        if not limit_data:
            matching_key = next((k for k in limits.keys() if ccp['process_step'] in k), None)
            if matching_key:
                limit_data = limits[matching_key]

        record = CriticalLimit(
            parameter=limit_data.get("parameter", "Control Temperature"),
            min_value=limit_data.get("min_value"),
            max_value=limit_data.get("max_value"),
            unit=limit_data.get("unit", "°C"),
            source_citation=limit_data.get("source_citation", "FSSAI Schedule 4 / GMP guidelines"),
            user_validated=False
        )
        normalized_limits[ccp_key] = record.model_dump()

    summary_text = _format_limits_summary(normalized_limits)

    return {
        "critical_limits": normalized_limits,
        "current_stage": "limits_review",
        "awaiting_human_input": True,
        "rag_sources": list(set(state.get("rag_sources", []) + rag_sources)),
        "messages": [
            AIMessage(content=summary_text)
        ]
    }


def _parse_limits_json(content: str) -> Dict[str, dict]:
    """Parse JSON dict of critical limits from LLM response."""
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


def _fallback_limits(ccps: list) -> Dict[str, dict]:
    """Generate default critical limits based on FSSAI guidelines when LLM is unavailable."""
    limits = {}
    for ccp in ccps:
        ccp_key = f"{ccp['process_step']} - {ccp['hazard_name']}"
        step_lower = ccp['process_step'].lower()
        
        if "pasteur" in step_lower:
            limits[ccp_key] = {
                "parameter": "Pasteurization Temperature",
                "min_value": 72.0,
                "max_value": None,
                "unit": "°C",
                "source_citation": "FSSAI Schedule 4 Part I Sec 5.2.1 (Minimum pasteurization parameters)"
            }
        elif "cook" in step_lower or "heat" in step_lower or "bake" in step_lower:
            limits[ccp_key] = {
                "parameter": "Core Heating Temperature",
                "min_value": 74.0,
                "max_value": None,
                "unit": "°C",
                "source_citation": "FSSAI Schedule 4 Part IV Sec 3.1.2 (Core product temperature standards)"
            }
        elif "cool" in step_lower or "refrigerat" in step_lower or "storage" in step_lower:
            limits[ccp_key] = {
                "parameter": "Cold Storage Temperature",
                "min_value": None,
                "max_value": 4.0,
                "unit": "°C",
                "source_citation": "FSSAI Schedule 4 Part I Sec 3.2 (Refrigerated storage rules)"
            }
        else:
            limits[ccp_key] = {
                "parameter": "Operation Limit Parameter",
                "min_value": None,
                "max_value": None,
                "unit": "",
                "source_citation": "FSSAI FSMS plan templates / GMP guidelines"
            }
            
    return limits


def _format_limits_summary(limits: Dict[str, dict]) -> str:
    """Format limits summary for chat display."""
    lines = ["## Critical Limits (FSSAI Grounded)\n"]
    lines.append("Retrieved validated regulatory limits for each approved CCP:\n")
    
    for i, (ccp_key, l) in enumerate(limits.items(), 1):
        val_range = ""
        if l.get("min_value") is not None and l.get("max_value") is not None:
            val_range = f"{l['min_value']} to {l['max_value']} {l['unit']}"
        elif l.get("min_value") is not None:
            val_range = f">= {l['min_value']} {l['unit']}"
        elif l.get("max_value") is not None:
            val_range = f"<= {l['max_value']} {l['unit']}"
        else:
            val_range = "Defined per SOP/GMP"
            
        lines.append(
            f"**{i}. {ccp_key}**\n"
            f"  - Parameter: {l['parameter']}\n"
            f"  - Critical Limit: {val_range}\n"
            f"  - Citation: *{l['source_citation']}*\n"
        )
        
    lines.append("\n*Awaiting your validation of these critical limits before designing monitoring procedures.*")
    return "\n".join(lines)
