"""SQLAlchemy ORM models for HACCP AI System (Phase 2)."""

import uuid
from datetime import date, datetime
from typing import Any, List, Optional

from pgvector.sqlalchemy import Vector
from sqlalchemy import Date, DateTime, ForeignKey, Integer, Float, Boolean, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class RegulatoryChunk(Base):
    """RAG knowledge base chunk stored in PostgreSQL with pgvector."""

    __tablename__ = "regulatory_chunks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    source_body: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    document_title: Mapped[str] = mapped_column(String(500), nullable=False)
    section: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    text: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[Any] = mapped_column(Vector(1536), nullable=True)
    amendment_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    product_categories: Mapped[List[str]] = mapped_column(
        ARRAY(String), nullable=False, default=list
    )
    hazard_types: Mapped[List[str]] = mapped_column(
        ARRAY(String), nullable=False, default=list
    )
    chunk_metadata: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Organization(Base):
    """Organization / FBO profile."""

    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    fssai_license_no: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    product_categories: Mapped[List[str]] = mapped_column(
        ARRAY(String), nullable=False, default=list
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    plans: Mapped[List["HACCPPlan"]] = relationship("HACCPPlan", back_populates="organization")


class HACCPPlan(Base):
    """HACCP Plan master record."""

    __tablename__ = "haccp_plans"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    org_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True
    )
    user_id: Mapped[str] = mapped_column(String(255), nullable=False, default="demo-user")
    business_name: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="draft")  # draft, in_progress, complete
    current_stage: Mapped[str] = mapped_column(String(50), nullable=False, default="intake")
    awaiting_human_input: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    product_category: Mapped[str] = mapped_column(String(100), nullable=False)
    version: Mapped[str] = mapped_column(String(20), nullable=False, default="1.0")
    verification_schedule: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    records_generated: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    organization: Mapped[Optional["Organization"]] = relationship("Organization", back_populates="plans")
    process_steps: Mapped[List["ProcessStep"]] = relationship("ProcessStep", back_populates="plan", cascade="all, delete-orphan", order_by="ProcessStep.step_order")
    hazards: Mapped[List["Hazard"]] = relationship("Hazard", back_populates="plan", cascade="all, delete-orphan")
    ccps: Mapped[List["CriticalControlPoint"]] = relationship("CriticalControlPoint", back_populates="plan", cascade="all, delete-orphan")
    audit_events: Mapped[List["AuditEvent"]] = relationship("AuditEvent", back_populates="plan", cascade="all, delete-orphan")


class ProcessStep(Base):
    """User-defined process flow diagram steps."""

    __tablename__ = "process_steps"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("haccp_plans.id", ondelete="CASCADE"), nullable=False
    )
    step_name: Mapped[str] = mapped_column(String(255), nullable=False)
    step_order: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    plan: Mapped["HACCPPlan"] = relationship("HACCPPlan", back_populates="process_steps")


class Hazard(Base):
    """Identified hazards with AI scoring and user confirmation status."""

    __tablename__ = "hazards"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("haccp_plans.id", ondelete="CASCADE"), nullable=False
    )
    process_step: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)  # biological, chemical, physical
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    likelihood: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    severity: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    rpn: Mapped[int] = mapped_column(Integer, nullable=False, default=9)
    recommended_control: Mapped[str] = mapped_column(Text, nullable=False, default="")
    ai_confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    user_confirmed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    citations: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=False, default=list)

    plan: Mapped["HACCPPlan"] = relationship("HACCPPlan", back_populates="hazards")
    ccps: Mapped[List["CriticalControlPoint"]] = relationship("CriticalControlPoint", back_populates="hazard", cascade="all, delete-orphan")


class CriticalControlPoint(Base):
    """Approved Critical Control Points with full decision audit trail."""

    __tablename__ = "critical_control_points"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("haccp_plans.id", ondelete="CASCADE"), nullable=False
    )
    hazard_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("hazards.id", ondelete="CASCADE"), nullable=False
    )
    process_step: Mapped[str] = mapped_column(String(255), nullable=False)
    decision_tree_path: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    user_override: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    override_justification: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    plan: Mapped["HACCPPlan"] = relationship("HACCPPlan", back_populates="ccps")
    hazard: Mapped["Hazard"] = relationship("Hazard", back_populates="ccps")
    critical_limits: Mapped[List["CriticalLimit"]] = relationship("CriticalLimit", back_populates="ccp", cascade="all, delete-orphan")
    monitoring_procedures: Mapped[List["MonitoringProcedure"]] = relationship("MonitoringProcedure", back_populates="ccp", cascade="all, delete-orphan")
    corrective_actions: Mapped[List["CorrectiveAction"]] = relationship("CorrectiveAction", back_populates="ccp", cascade="all, delete-orphan")


class CriticalLimit(Base):
    """Validated critical limits with regulatory citations."""

    __tablename__ = "critical_limits"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    ccp_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("critical_control_points.id", ondelete="CASCADE"), nullable=False
    )
    parameter: Mapped[str] = mapped_column(String(255), nullable=False)
    min_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    max_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    unit: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    source_citation: Mapped[str] = mapped_column(Text, nullable=False, default="")
    user_validated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    ccp: Mapped["CriticalControlPoint"] = relationship("CriticalControlPoint", back_populates="critical_limits")


class MonitoringProcedure(Base):
    """Monitoring procedures for each approved CCP."""

    __tablename__ = "monitoring_procedures"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    ccp_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("critical_control_points.id", ondelete="CASCADE"), nullable=False
    )
    method: Mapped[str] = mapped_column(Text, nullable=False)
    frequency: Mapped[str] = mapped_column(String(255), nullable=False)
    responsible_person: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    record_format: Mapped[str] = mapped_column(String(255), nullable=False, default="")

    ccp: Mapped["CriticalControlPoint"] = relationship("CriticalControlPoint", back_populates="monitoring_procedures")


class CorrectiveAction(Base):
    """Corrective action procedures triggered on CCP deviation."""

    __tablename__ = "corrective_actions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    ccp_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("critical_control_points.id", ondelete="CASCADE"), nullable=False
    )
    trigger_condition: Mapped[str] = mapped_column(Text, nullable=False)
    immediate_action: Mapped[str] = mapped_column(Text, nullable=False)
    root_cause_procedure: Mapped[str] = mapped_column(Text, nullable=False, default="")
    personnel: Mapped[str] = mapped_column(String(255), nullable=False, default="")

    ccp: Mapped["CriticalControlPoint"] = relationship("CriticalControlPoint", back_populates="corrective_actions")


class AuditEvent(Base):
    """Immutable audit log of all decisions, overrides, and modifications."""

    __tablename__ = "audit_events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("haccp_plans.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g., hazard_override, ccp_override
    old_value: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    new_value: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)

    plan: Mapped["HACCPPlan"] = relationship("HACCPPlan", back_populates="audit_events")


class ComplianceAlert(Base):
    """Compliance alerts generated by the regulatory monitoring sub-agent."""

    __tablename__ = "compliance_alerts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    org_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    regulatory_source: Mapped[str] = mapped_column(String(255), nullable=False)
    change_summary: Mapped[str] = mapped_column(Text, nullable=False)
    affected_sections: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="active")  # active, resolved
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class MonitoringLog(Base):
    """CCP monitoring measurement log — one row per recorded reading."""

    __tablename__ = "monitoring_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("haccp_plans.id", ondelete="CASCADE"), nullable=False, index=True
    )
    ccp_hazard: Mapped[str] = mapped_column(String(500), nullable=False)
    parameter: Mapped[str] = mapped_column(String(255), nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    is_deviation: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    corrective_action_required: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    monitored_by: Mapped[str] = mapped_column(String(255), nullable=False, default="QA")
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )


class UploadedDocument(Base):
    """Metadata record for dynamically uploaded RAG documents."""

    __tablename__ = "uploaded_documents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    filename: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    source_body: Mapped[str] = mapped_column(String(50), nullable=False)
    document_title: Mapped[str] = mapped_column(String(500), nullable=False)
    amendment_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    product_categories: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

