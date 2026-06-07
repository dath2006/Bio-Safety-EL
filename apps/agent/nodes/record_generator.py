"""Record generator node — compiles record templates for the plan."""

from langchain_core.messages import AIMessage
from models.state import HACCPState


async def record_generator(state: HACCPState) -> dict:
    """
    Compile a list of required record-keeping logs and templates (Principle 7).
    """
    ccps = state.get("ccps_approved", [])
    
    # Base templates required for any FSSAI FSMS plan
    records = [
        "FSMS Plan Master Document",
        "Corrective Action & Deviation Register",
        "Thermometer / Sensor Calibration Log",
        "Employee Health & Personal Hygiene Checklists",
        "Pest Control Log & Treatment Schedule",
        "Internal Audit & Management Review Log",
        "Product Recall & Traceability Record Form"
    ]
    
    # Add dynamic logs based on approved CCPs
    for ccp in ccps:
        step = ccp["process_step"]
        hazard = ccp["hazard_name"]
        records.append(f"CCP Log Sheet: {step} ({hazard} monitoring)")

    summary_lines = ["## Record Keeping Requirements (P7)\n"]
    summary_lines.append("Compiled FSSAI-mandated record forms and logging templates:\n")
    for r in records:
        summary_lines.append(f"  - 📄 {r}")
        
    return {
        "records_generated": records,
        "current_stage": "plan_validator",
        "messages": [
            AIMessage(content="\n".join(summary_lines))
        ]
    }
