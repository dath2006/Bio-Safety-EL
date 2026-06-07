"""Report generator node — compiles final plan data and metadata."""

from langchain_core.messages import AIMessage
from models.state import HACCPState


async def report_generator(state: HACCPState) -> dict:
    """
    Compile the final report summary.
    Sets the stage to completed.
    """
    business = state.get("business_name", "N/A")
    category = state.get("product_category", "N/A")
    ccps = state.get("ccps_approved", [])
    
    summary_lines = [
        "## HACCP Plan Compilation Complete\n",
        f"The HACCP plan for **{business}** ({category}) has been successfully compiled and saved.\n",
        "### Plan Summary:",
        f"  - **Process Steps**: {len(state.get('process_steps', []))} steps defined",
        f"  - **Identified Hazards**: {len(state.get('hazards_identified', []))} recorded",
        f"  - **Critical Control Points**: {len(ccps)} designated",
        f"  - **Record Logs**: {len(state.get('records_generated', []))} forms structured\n",
        "You can now preview the document, export it to JSON, or generate the FSSAI audit-ready PDF."
    ]

    return {
        "current_stage": "completed",
        "awaiting_human_input": False,
        "messages": [
            AIMessage(content="\n".join(summary_lines))
        ]
    }
