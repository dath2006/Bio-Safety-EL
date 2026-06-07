"""Intake processor node — collects and validates plan setup data."""

from langchain_core.messages import AIMessage

from models.state import HACCPState

VALID_PRODUCT_CATEGORIES = {
    "dairy_pasteurized",
    "dairy",
    "dairy_fermented",
    "rte",
    "meat",
    "street_food",
    "catering",
    "food_service",
    "general",
}


async def intake_processor(state: HACCPState) -> dict:
    """
    Validate business name, product category, and process steps.
    Returns partial state update with validation messages.
    """
    errors: list[str] = []

    if not state.get("business_name", "").strip():
        errors.append("Business name is required.")

    product_category = state.get("product_category", "").strip()
    if not product_category:
        errors.append("Product category is required (e.g. 'dairy_pasteurized').")
    elif product_category not in VALID_PRODUCT_CATEGORIES:
        errors.append(
            f"Unknown product category '{product_category}'. "
            f"Valid options: {', '.join(sorted(VALID_PRODUCT_CATEGORIES))}"
        )

    process_steps = state.get("process_steps", [])
    if not process_steps or len(process_steps) < 2:
        errors.append("At least two process flow steps are required for hazard analysis.")

    if errors:
        return {
            "current_stage": "intake",
            "awaiting_human_input": True,
            "messages": [
                AIMessage(
                    content=(
                        "Please complete the intake information before proceeding:\n"
                        + "\n".join(f"- {e}" for e in errors)
                    )
                )
            ],
        }

    return {
        "current_stage": "hazard_analysis",
        "awaiting_human_input": False,
        "messages": [
            AIMessage(
                content=(
                    f"Intake complete for **{state['business_name']}** "
                    f"({product_category}). Process flow has {len(process_steps)} steps. "
                    "Proceeding to AI-assisted hazard analysis."
                )
            )
        ],
    }
