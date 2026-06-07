"""HACCPState and related typed models for LangGraph orchestration."""

from typing import Annotated, Literal, Optional

from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field
from typing_extensions import TypedDict


HazardCategory = Literal["biological", "chemical", "physical"]
SourceBody = Literal["FSSAI", "Codex", "FDA", "ICMR"]


class HazardRecord(BaseModel):
    """A single identified hazard with risk scoring."""

    name: str
    category: HazardCategory
    process_step: str
    source_in_process: str = ""
    likelihood: int = Field(ge=1, le=5, default=3)
    severity: int = Field(ge=1, le=5, default=3)
    rpn: int = Field(ge=1, le=25, default=9)
    recommended_control: str = ""
    ai_confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    citations: list[str] = Field(default_factory=list)
    user_confirmed: bool = False

    def model_post_init(self, __context: object) -> None:
        self.rpn = self.likelihood * self.severity


class CCPCandidate(BaseModel):
    """Candidate critical control point from Codex decision tree."""

    hazard_name: str
    process_step: str
    is_ccp: bool
    confidence: float = Field(ge=0.0, le=1.0)
    decision_tree_path: list[str] = Field(default_factory=list)
    reasoning: str = ""


class CCP(BaseModel):
    """Approved critical control point."""

    hazard_name: str
    process_step: str
    decision_tree_path: list[str] = Field(default_factory=list)
    user_override: bool = False
    override_justification: Optional[str] = None


class CriticalLimit(BaseModel):
    """Validated critical limit for a CCP."""

    parameter: str
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    unit: str = ""
    source_citation: str = ""
    user_validated: bool = False


class MonitoringProcedure(BaseModel):
    """Monitoring procedure for an approved CCP."""

    ccp_hazard: str
    method: str
    frequency: str
    responsible_person: str = ""
    record_format: str = ""


class CorrectiveAction(BaseModel):
    """Corrective action procedure for CCP deviation."""

    ccp_hazard: str
    trigger_condition: str
    immediate_action: str
    root_cause_procedure: str = ""
    personnel: str = ""


class VerificationSchedule(BaseModel):
    """Verification and audit schedule."""

    review_interval: str = "quarterly"
    audit_checklist: list[str] = Field(default_factory=list)
    sign_off_responsibility: str = ""


class HumanDecision(BaseModel):
    """Structured human decision at a HITL gate."""

    gate: str
    action: Literal["approve", "reject", "modify", "reanalyze"]
    payload: dict = Field(default_factory=dict)
    justification: Optional[str] = None


class HACCPState(TypedDict):
    """Typed state schema for the HACCP orchestrator graph."""

    # Identity
    plan_id: str
    user_id: str
    business_name: str
    product_category: str
    process_steps: list[str]

    # P1 – Hazard Analysis
    hazards_identified: list[dict]
    hazards_user_confirmed: bool

    # P2 – CCP Determination
    ccp_candidates: list[dict]
    ccps_approved: list[dict]
    ccps_user_approved: bool

    # P3–P7 – Subsequent stages (Phase 2+)
    critical_limits: dict[str, dict]
    monitoring_procedures: list[dict]
    corrective_actions: list[dict]
    verification_schedule: dict
    records_generated: list[str]

    # Control flow
    current_stage: str
    awaiting_human_input: bool
    human_decision: Optional[dict]
    messages: Annotated[list, add_messages]
    rag_sources: list[str]


def create_initial_state(
    plan_id: str,
    user_id: str = "demo-user",
) -> HACCPState:
    """Return a fresh HACCPState with defaults."""
    return HACCPState(
        plan_id=plan_id,
        user_id=user_id,
        business_name="",
        product_category="",
        process_steps=[],
        hazards_identified=[],
        hazards_user_confirmed=False,
        ccp_candidates=[],
        ccps_approved=[],
        ccps_user_approved=False,
        critical_limits={},
        monitoring_procedures=[],
        corrective_actions=[],
        verification_schedule={},
        records_generated=[],
        current_stage="intake",
        awaiting_human_input=False,
        human_decision=None,
        messages=[],
        rag_sources=[],
    )
