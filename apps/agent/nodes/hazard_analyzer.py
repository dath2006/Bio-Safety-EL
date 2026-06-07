"""Hazard analyzer node — RAG-grounded hazard identification."""

import json
import re

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from sqlalchemy.ext.asyncio import AsyncSession

from llm import get_chat_model, has_llm
from models.state import HazardRecord
from rag.retriever import RegulatoryRetriever, chunks_to_context
from models.state import HACCPState

HAZARD_ANALYSIS_SYSTEM_PROMPT = """You are an expert food safety engineer specializing in HACCP and FSSAI Schedule 4 compliance.

Your task is to identify biological, chemical, and physical hazards for each process step in a food production flow.

RULES:
1. Base your analysis ONLY on the provided regulatory context. Do not invent regulatory facts.
2. If the context is insufficient, state uncertainty and assign lower confidence scores.
3. For each hazard, provide: name, category (biological/chemical/physical), process_step, likelihood (1-5), severity (1-5), recommended_control, and ai_confidence (0.0-1.0).
4. Cite the regulatory source for each hazard in the citations array.
5. Return ONLY valid JSON array of hazard objects.

JSON schema per hazard:
{
  "name": "string",
  "category": "biological|chemical|physical",
  "process_step": "string",
  "source_in_process": "string",
  "likelihood": 1-5,
  "severity": 1-5,
  "recommended_control": "string",
  "ai_confidence": 0.0-1.0,
  "citations": ["source citation strings"]
}
"""


async def hazard_analyzer(
    state: HACCPState,
    db_session: AsyncSession | None = None,
) -> dict:
    """
    Perform RAG retrieval per process step and LLM hazard classification.
    Returns identified hazards with citations.
    """
    retriever = RegulatoryRetriever()
    product_category = state.get("product_category", "general")
    process_steps = state.get("process_steps", [])

    all_chunks = []
    rag_sources: list[str] = []

    for step in process_steps:
        query = (
            f"What biological, chemical, and physical hazards are associated with "
            f"'{step}' in {product_category} production per FSSAI and Codex standards?"
        )
        chunks = await retriever.retrieve(
            session=db_session,
            query=query,
            product_category=product_category,
            top_k=3,
        )
        all_chunks.extend(chunks)
        rag_sources.extend([c.citation for c in chunks])

    # Deduplicate sources
    rag_sources = list(dict.fromkeys(rag_sources))
    context = chunks_to_context(all_chunks) if all_chunks else "No regulatory context retrieved."

    process_flow_text = "\n".join(f"{i+1}. {step}" for i, step in enumerate(process_steps))

    user_prompt = f"""Product category: {product_category}
Business: {state.get('business_name', 'N/A')}

Process flow:
{process_flow_text}

Regulatory context:
{context}

Identify all significant hazards for each process step. Return a JSON array."""

    hazards: list[dict] = []
    analysis_message = ""

    if has_llm():
        try:
            llm = get_chat_model(temperature=0.1)
            response = await llm.ainvoke([
                SystemMessage(content=HAZARD_ANALYSIS_SYSTEM_PROMPT),
                HumanMessage(content=user_prompt),
            ])
            analysis_message = response.content
            hazards = _parse_hazards_json(analysis_message)
        except Exception as exc:
            hazards = _fallback_hazard_extraction(all_chunks, process_steps, product_category)
            analysis_message = (
                f"LLM call failed ({exc}). Using RAG-based hazard extraction.\n\n"
                f"Identified {len(hazards)} hazards from regulatory documents."
            )
    else:
        # Fallback: rule-based hazard extraction from RAG chunks when no API key
        hazards = _fallback_hazard_extraction(all_chunks, process_steps, product_category)
        analysis_message = (
            "Hazard analysis completed using RAG retrieval (LLM unavailable — "
            "set OPENROUTER_API_KEY for full AI reasoning).\n\n"
            f"Identified {len(hazards)} hazards from regulatory documents."
        )

    # Normalize and compute RPN
    normalized: list[dict] = []
    for h in hazards:
        record = HazardRecord(
            name=h.get("name", "Unknown hazard"),
            category=h.get("category", "biological"),
            process_step=h.get("process_step", process_steps[0] if process_steps else ""),
            source_in_process=h.get("source_in_process", ""),
            likelihood=int(h.get("likelihood", 3)),
            severity=int(h.get("severity", 3)),
            recommended_control=h.get("recommended_control", ""),
            ai_confidence=float(h.get("ai_confidence", 0.5)),
            citations=h.get("citations", rag_sources[:3]),
        )
        normalized.append(record.model_dump())

    return {
        "hazards_identified": normalized,
        "hazards_user_confirmed": False,
        "current_stage": "hazard_review",
        "awaiting_human_input": True,
        "rag_sources": rag_sources,
        "messages": [
            AIMessage(content=_format_hazard_summary(normalized, analysis_message)),
        ],
    }


def _parse_hazards_json(content: str) -> list[dict]:
    """Extract JSON array from LLM response."""
    # Try direct parse
    try:
        data = json.loads(content)
        if isinstance(data, list):
            return data
        if isinstance(data, dict) and "hazards" in data:
            return data["hazards"]
    except json.JSONDecodeError:
        pass

    # Try to find JSON array in response
    match = re.search(r"\[[\s\S]*\]", content)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    return []


def _fallback_hazard_extraction(chunks, process_steps: list[str], product_category: str = "general") -> list[dict]:
    """Extract hazards from RAG chunks without LLM."""
    hazards: list[dict] = []
    
    # Expanded keywords for Phase 4 multi-product support
    hazard_keywords = {
        "biological": ["pathogen", "bacteria", "microbial", "salmonella", "listeria", "e. coli", "bacillus", "coliform", "staphylococcus"],
        "chemical": ["aflatoxin", "pesticide", "residue", "detergent", "chemical", "antibiotic", "heavy metal", "additive"],
        "physical": ["metal", "glass", "foreign", "physical", "fragment", "bone", "plastic"],
    }

    for chunk in chunks:
        text_lower = chunk.text.lower()
        for category, keywords in hazard_keywords.items():
            if any(kw in text_lower for kw in keywords):
                step = process_steps[0] if process_steps else "General"
                
                # Context-aware step matching
                if "pasteur" in text_lower:
                    step = next((s for s in process_steps if "pasteur" in s.lower()), step)
                elif "cook" in text_lower or "heat" in text_lower:
                    step = next((s for s in process_steps if "cook" in s.lower() or "heat" in s.lower()), step)
                elif "chill" in text_lower or "freez" in text_lower or "cold" in text_lower:
                    step = next((s for s in process_steps if "chill" in s.lower() or "freez" in s.lower() or "stor" in s.lower()), step)

                # Tailor severity by product category
                severity = 3
                if category == "biological":
                    if product_category in ["meat", "seafood", "rte", "dairy_pasteurized"]:
                        severity = 5
                    else:
                        severity = 4

                hazards.append({
                    "name": f"{category.title()} hazard — {chunk.section[:60]}",
                    "category": category,
                    "process_step": step,
                    "source_in_process": chunk.section,
                    "likelihood": 3,
                    "severity": severity,
                    "recommended_control": f"Apply CCP monitoring per FSSAI {product_category.capitalize()} standards",
                    "ai_confidence": min(chunk.score, 0.85),
                    "citations": [chunk.citation],
                })
                break

    return hazards[:10]


def _format_hazard_summary(hazards: list[dict], analysis: str) -> str:
    """Format hazard list for chat display."""
    if not hazards:
        return f"{analysis}\n\nNo hazards identified. Please review process flow or add custom hazards."

    lines = ["## Hazard Analysis Results\n", analysis, "\n### Identified Hazards\n"]
    for i, h in enumerate(hazards, 1):
        rpn = h.get("likelihood", 3) * h.get("severity", 3)
        lines.append(
            f"**{i}. {h['name']}** ({h['category']})\n"
            f"  - Step: {h['process_step']}\n"
            f"  - Likelihood: {h.get('likelihood', '?')} | Severity: {h.get('severity', '?')} | RPN: {rpn}\n"
            f"  - Control: {h.get('recommended_control', 'N/A')}\n"
            f"  - Confidence: {h.get('ai_confidence', 0):.0%}\n"
            f"  - Sources: {', '.join(h.get('citations', [])) or 'N/A'}\n"
        )

    lines.append("\n*Awaiting your review and confirmation before CCP determination.*")
    return "\n".join(lines)
