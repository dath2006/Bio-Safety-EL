"""Database persistence helper functions for state serialization."""

import uuid
from typing import Optional
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import (
    HACCPPlan,
    ProcessStep,
    Hazard,
    CriticalControlPoint,
    CriticalLimit,
    MonitoringProcedure,
    CorrectiveAction
)
from models.state import HACCPState, create_initial_state


async def load_plan_state(db: AsyncSession, plan_id: str) -> Optional[HACCPState]:
    """
    Load HACCPPlan from database and deserialize it into a state dictionary.
    """
    plan_uuid = uuid.UUID(plan_id) if isinstance(plan_id, str) else plan_id
    
    query = (
        select(HACCPPlan)
        .where(HACCPPlan.id == plan_uuid)
        .options(
            selectinload(HACCPPlan.process_steps),
            selectinload(HACCPPlan.hazards),
            selectinload(HACCPPlan.ccps).selectinload(CriticalControlPoint.critical_limits),
            selectinload(HACCPPlan.ccps).selectinload(CriticalControlPoint.monitoring_procedures),
            selectinload(HACCPPlan.ccps).selectinload(CriticalControlPoint.corrective_actions),
        )
    )
    result = await db.execute(query)
    plan = result.scalar_one_or_none()
    
    if not plan:
        return None
        
    state = create_initial_state(plan_id=str(plan.id), user_id=plan.user_id)
    state["business_name"] = plan.business_name
    state["product_category"] = plan.product_category
    state["process_steps"] = [s.step_name for s in plan.process_steps]
    state["current_stage"] = plan.current_stage
    state["awaiting_human_input"] = plan.awaiting_human_input
    state["verification_schedule"] = plan.verification_schedule or {}
    state["records_generated"] = plan.records_generated or []
    state["status"] = plan.status
    
    # Deserialize Hazards
    state["hazards_identified"] = [
        {
            "name": h.name,
            "category": h.category,
            "process_step": h.process_step,
            "likelihood": h.likelihood,
            "severity": h.severity,
            "rpn": h.rpn,
            "recommended_control": h.recommended_control,
            "ai_confidence": h.ai_confidence,
            "citations": h.citations,
            "user_confirmed": h.user_confirmed,
        }
        for h in plan.hazards
    ]
    state["hazards_user_confirmed"] = all(h.user_confirmed for h in plan.hazards) if plan.hazards else False
    
    # Deserialize CCPs
    state["ccps_approved"] = [
        {
            "hazard_name": c.hazard.name if c.hazard else "",
            "process_step": c.process_step,
            "decision_tree_path": c.decision_tree_path,
            "user_override": c.user_override,
            "override_justification": c.override_justification,
        }
        for c in plan.ccps
    ]
    state["ccps_user_approved"] = len(plan.ccps) > 0 and plan.current_stage not in ("intake", "hazard_review", "ccp_determination", "ccp_review")
    
    # Deserialize Limits, Monitoring & Actions
    limits_dict = {}
    procedures = []
    actions = []
    
    for ccp in plan.ccps:
        h_name = ccp.hazard.name if ccp.hazard else ""
        ccp_key = f"{ccp.process_step} - {h_name}"
        
        for cl in ccp.critical_limits:
            limits_dict[ccp_key] = {
                "parameter": cl.parameter,
                "min_value": cl.min_value,
                "max_value": cl.max_value,
                "unit": cl.unit,
                "source_citation": cl.source_citation,
                "user_validated": cl.user_validated,
            }
        for mp in ccp.monitoring_procedures:
            procedures.append({
                "ccp_hazard": ccp_key,
                "method": mp.method,
                "frequency": mp.frequency,
                "responsible_person": mp.responsible_person,
                "record_format": mp.record_format,
            })
        for ca in ccp.corrective_actions:
            actions.append({
                "ccp_hazard": ccp_key,
                "trigger_condition": ca.trigger_condition,
                "immediate_action": ca.immediate_action,
                "root_cause_procedure": ca.root_cause_procedure,
                "personnel": ca.personnel,
            })
            
    state["critical_limits"] = limits_dict
    state["monitoring_procedures"] = procedures
    state["corrective_actions"] = actions
    
    return state


async def save_plan_state(db: AsyncSession, state: HACCPState) -> None:
    """
    Serialize state dictionary and save it to the database tables.
    """
    plan_uuid = uuid.UUID(state["plan_id"])
    
    # 1. Fetch or Create HACCPPlan
    query = select(HACCPPlan).where(HACCPPlan.id == plan_uuid)
    result = await db.execute(query)
    plan = result.scalar_one_or_none()
    
    if not plan:
        plan = HACCPPlan(id=plan_uuid)
        db.add(plan)
        
    plan.user_id = state.get("user_id", "demo-user")
    plan.business_name = state.get("business_name", "")
    plan.product_category = state.get("product_category", "")
    plan.current_stage = state.get("current_stage", "intake")
    plan.awaiting_human_input = state.get("awaiting_human_input", False)
    plan.verification_schedule = state.get("verification_schedule", {})
    plan.records_generated = state.get("records_generated", [])
    
    # Map stage to overall status
    if plan.current_stage == "completed":
        plan.status = "complete"
    elif plan.current_stage != "intake":
        plan.status = "in_progress"
    else:
        plan.status = "draft"
        
    # Flush to ensure plan exists before sync
    await db.flush()
    
    # 2. Sync Process Steps
    await db.execute(delete(ProcessStep).where(ProcessStep.plan_id == plan_uuid))
    for order, step_name in enumerate(state.get("process_steps", [])):
        db.add(ProcessStep(
            plan_id=plan_uuid,
            step_name=step_name,
            step_order=order,
            description=""
        ))
        
    # 3. Sync Hazards
    await db.execute(delete(Hazard).where(Hazard.plan_id == plan_uuid))
    haz_records = {}
    for h in state.get("hazards_identified", []):
        rpn = h.get("likelihood", 3) * h.get("severity", 3)
        db_haz = Hazard(
            plan_id=plan_uuid,
            process_step=h.get("process_step"),
            category=h.get("category"),
            name=h.get("name"),
            likelihood=h.get("likelihood", 3),
            severity=h.get("severity", 3),
            rpn=rpn,
            recommended_control=h.get("recommended_control", ""),
            ai_confidence=h.get("ai_confidence", 0.0),
            user_confirmed=h.get("user_confirmed", False) or state.get("hazards_user_confirmed", False),
            citations=h.get("citations", [])
        )
        db.add(db_haz)
        # Keep track to reference hazard ID during CCP sync
        haz_key = f"{h.get('process_step')} - {h.get('name')}"
        haz_records[haz_key] = db_haz
        
    # Flush to generate hazard IDs
    await db.flush()
    
    # 4. Sync CCPs and downstream items
    await db.execute(delete(CriticalControlPoint).where(CriticalControlPoint.plan_id == plan_uuid))
    
    limits = state.get("critical_limits", {})
    monitoring_list = state.get("monitoring_procedures", [])
    actions_list = state.get("corrective_actions", [])
    
    for ccp in state.get("ccps_approved", []):
        h_name = ccp.get("hazard_name", "")
        p_step = ccp.get("process_step", "")
        ccp_key = f"{p_step} - {h_name}"
        
        # Find hazard record
        haz_rec = haz_records.get(ccp_key)
        if not haz_rec:
            # Fallback fuzzy match
            matching_key = next((k for k in haz_records.keys() if p_step in k and h_name in k), None)
            if matching_key:
                haz_rec = haz_records[matching_key]
                
        if not haz_rec:
            # Create a shell hazard if not found (unexpected)
            haz_rec = Hazard(
                plan_id=plan_uuid,
                process_step=p_step,
                category="biological",
                name=h_name,
                user_confirmed=True
            )
            db.add(haz_rec)
            await db.flush()
            
        db_ccp = CriticalControlPoint(
            plan_id=plan_uuid,
            hazard_id=haz_rec.id,
            process_step=p_step,
            decision_tree_path=ccp.get("decision_tree_path", []),
            user_override=ccp.get("user_override", False),
            override_justification=ccp.get("override_justification")
        )
        db.add(db_ccp)
        await db.flush()
        
        # Add critical limit
        if ccp_key in limits:
            cl = limits[ccp_key]
            db.add(CriticalLimit(
                ccp_id=db_ccp.id,
                parameter=cl.get("parameter", "Control Parameter"),
                min_value=cl.get("min_value"),
                max_value=cl.get("max_value"),
                unit=cl.get("unit", ""),
                source_citation=cl.get("source_citation", ""),
                user_validated=cl.get("user_validated", False)
            ))
            
        # Add monitoring procedures
        for mp in monitoring_list:
            if mp.get("ccp_hazard") == ccp_key:
                db.add(MonitoringProcedure(
                    ccp_id=db_ccp.id,
                    method=mp.get("method", ""),
                    frequency=mp.get("frequency", ""),
                    responsible_person=mp.get("responsible_person", ""),
                    record_format=mp.get("record_format", "")
                ))
                
        # Add corrective actions
        for ca in actions_list:
            if ca.get("ccp_hazard") == ccp_key:
                db.add(CorrectiveAction(
                    ccp_id=db_ccp.id,
                    trigger_condition=ca.get("trigger_condition", ""),
                    immediate_action=ca.get("immediate_action", ""),
                    root_cause_procedure=ca.get("root_cause_procedure", ""),
                    personnel=ca.get("personnel", "")
                ))

    await db.commit()
