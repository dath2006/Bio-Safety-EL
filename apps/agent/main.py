"""FastAPI application — HACCP AI Agent API (Phase 1)."""

import sys
import asyncio
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    try:
        import uvicorn.loops.asyncio as uvicorn_asyncio
        uvicorn_asyncio.asyncio_loop_factory = lambda use_subprocess=False: asyncio.SelectorEventLoop
    except ImportError:
        pass

import uuid
from contextlib import asynccontextmanager
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from llm import get_chat_model, has_llm
from db.session import get_db, init_db
from db.persistence import load_plan_state, save_plan_state
from db.models import HACCPPlan, MonitoringLog, ComplianceAlert, RegulatoryChunk, UploadedDocument
from sqlalchemy import select, func
from datetime import datetime
from graphs.haccp_graph import build_haccp_graph, create_initial_state
from rag.ingest import run_full_ingestion
from rag.retriever import RegulatoryRetriever, chunks_to_context
from tools.rag_tool import create_regulatory_search_tool
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from utils.pdf_generator import generate_haccp_pdf

settings = get_settings()

# Map human-readable category display names → DB slug keys
_CATEGORY_MAP: dict[str, str] = {
    "dairy pasteurized": "dairy_pasteurized",
    "dairy": "dairy",
    "ready-to-eat meals": "rte",
    "ready to eat": "rte",
    "rte": "rte",
    "catering & food service": "catering",
    "catering": "catering",
    "food service": "food_service",
    "street food": "street_food",
    "cold storage": "cold_chain",
    "cold chain / frozen": "cold_chain",
    "cold chain": "cold_chain",
    "bakery & confectionery": "general",
    "bakery": "general",
    "meat & poultry": "meat",
    "meat": "meat",
    "seafood & fish": "seafood",
    "seafood": "seafood",
    "beverages": "beverages",
    "spices & condiments": "spices",
    "spices": "spices",
    "packaged food": "packaged_food",
    "packaged_food": "packaged_food",
    "general": "general",
}


def _normalize_category(cat: str | None) -> str | None:
    """Convert display name or free-form category to a DB slug."""
    if not cat:
        return None
    slug = _CATEGORY_MAP.get(cat.strip().lower())
    if slug:
        return slug
    # Fallback: lowercase + spaces→underscores (handles already-slugged values)
    return cat.strip().lower().replace(" ", "_") or None



@asynccontextmanager
async def lifespan(app: FastAPI):
    get_settings.cache_clear()
    await init_db()
    yield


app = FastAPI(
    title="HACCP AI Agent API",
    description="AI-Powered HACCP Documentation & Regulatory Compliance System",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Request / Response Models ---


class IntakeRequest(BaseModel):
    business_name: str
    product_category: str = Field(
        examples=["dairy_pasteurized"],
        description="Product category key, e.g. dairy_pasteurized, rte, general",
    )
    process_steps: list[str] = Field(
        min_length=2,
        examples=[["Raw milk reception", "Storage", "Pasteurization", "Packaging", "Cold storage"]],
    )
    user_id: str = "demo-user"


class PlanRunResponse(BaseModel):
    plan_id: str
    current_stage: str
    awaiting_human_input: bool
    hazards_identified: list[dict]
    rag_sources: list[str]
    message: str


class ChatRequest(BaseModel):
    message: str
    product_category: str = "dairy_pasteurized"
    stream: bool = False


class ChatResponse(BaseModel):
    answer: str
    sources: list[str]
    confidence: str


class IngestResponse(BaseModel):
    status: str
    documents_processed: int
    chunks_created: int
    pgvector_stored: int
    chromadb_stored: int


class HealthResponse(BaseModel):
    status: str
    version: str
    services: dict[str, str]


class HumanDecisionRequest(BaseModel):
    gate: str
    action: str  # approve, reject, modify, reanalyze
    payload: dict = Field(default_factory=dict)
    justification: str | None = None


class PlanSummaryResponse(BaseModel):
    plan_id: str
    business_name: str
    product_category: str
    status: str
    current_stage: str
    created_at: datetime


# --- Routes ---


@app.get("/health", response_model=HealthResponse)
async def health_check(db: AsyncSession = Depends(get_db)):
    """Health check with service status."""
    services: dict[str, str] = {"api": "ok", "postgres": "unknown", "chromadb": "unknown"}

    try:
        retriever = RegulatoryRetriever()
        count = await retriever.count_chunks(db)
        services["postgres"] = f"ok ({count} chunks)"
    except Exception as e:
        services["postgres"] = f"error: {e}"

    try:
        retriever = RegulatoryRetriever()
        retriever.get_chroma_collection()
        services["chromadb"] = "ok"
    except Exception as e:
        services["chromadb"] = f"error: {e}"

    return HealthResponse(
        status="healthy",
        version="0.1.0",
        services=services,
    )


@app.post("/api/ingest", response_model=IngestResponse)
async def ingest_documents(
    clear_existing: bool = True,
    db: AsyncSession = Depends(get_db),
):
    """Ingest regulatory documents into ChromaDB + pgvector."""
    try:
        result = await run_full_ingestion(db, clear_existing=clear_existing)
        return IngestResponse(status="success", **result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {e}") from e


@app.post("/api/plans/run")
async def run_plan_intake_and_hazards(
    request: IntakeRequest,
    db: AsyncSession = Depends(get_db),
):
    """Run intake validation → hazard analysis and persist initial state."""
    plan_id = str(uuid.uuid4())
    state = create_initial_state(plan_id=plan_id, user_id=request.user_id)
    state["business_name"] = request.business_name
    state["product_category"] = _normalize_category(request.product_category)
    state["process_steps"] = request.process_steps

    async with AsyncPostgresSaver.from_conn_string(settings.database_url_sync) as checkpointer:
        await checkpointer.setup()
        graph = build_haccp_graph(db_session=db, checkpointer=checkpointer)
        config = {"configurable": {"thread_id": plan_id}}
        result = await graph.ainvoke(state, config)

    # Save to PostgreSQL tables
    await save_plan_state(db, result)

    # Load full serialized state from DB to return to client
    full_state = await load_plan_state(db, plan_id)
    if not full_state:
        raise HTTPException(status_code=404, detail="Plan state could not be loaded")
    
    # Inject last message into the response
    if result.get("messages"):
        last_msg = result["messages"][-1]
        full_state["message"] = getattr(last_msg, "content", str(last_msg))
    else:
        full_state["message"] = ""

    return full_state


@app.get("/api/plans", response_model=list[PlanSummaryResponse])
async def list_plans(db: AsyncSession = Depends(get_db)):
    """List all plans stored in the database."""
    query = select(HACCPPlan).order_by(HACCPPlan.created_at.desc())
    result = await db.execute(query)
    plans = result.scalars().all()
    return [
        PlanSummaryResponse(
            plan_id=str(p.id),
            business_name=p.business_name,
            product_category=p.product_category,
            status=p.status,
            current_stage=p.current_stage,
            created_at=p.created_at,
        )
        for p in plans
    ]


@app.get("/api/plans/{id}")
async def get_plan(id: str, db: AsyncSession = Depends(get_db)):
    """Fetch complete state of a plan."""
    state = await load_plan_state(db, id)
    if not state:
        raise HTTPException(status_code=404, detail=f"Plan {id} not found.")
    return state


@app.post("/api/plans/{id}/resume")
async def resume_plan(
    id: str,
    decision: HumanDecisionRequest,
    db: AsyncSession = Depends(get_db),
):
    """Resume execution of a paused plan with a user decision."""
    state = await load_plan_state(db, id)
    if not state:
        raise HTTPException(status_code=404, detail=f"Plan {id} not found.")

    async with AsyncPostgresSaver.from_conn_string(settings.database_url_sync) as checkpointer:
        await checkpointer.setup()
        graph = build_haccp_graph(db_session=db, checkpointer=checkpointer)
        config = {"configurable": {"thread_id": id}}

        # 1. Update checkpointer with loaded state
        await graph.aupdate_state(config, state)

        # 2. Inject decision payload
        decision_data = {
            "gate": decision.gate,
            "action": decision.action,
            "payload": decision.payload,
            "justification": decision.justification,
        }
        await graph.aupdate_state(config, {"human_decision": decision_data})

        # 3. Resume graph execution (invoked with None because checkpointer holds the state)
        result = await graph.ainvoke(None, config)

    # 4. Save updated state to PostgreSQL tables
    await save_plan_state(db, result)

    # 5. Load full serialized state from DB to return to client
    full_state = await load_plan_state(db, id)
    if not full_state:
        raise HTTPException(status_code=404, detail=f"Plan {id} state could not be loaded.")

    # Inject last message into the response
    if result.get("messages"):
        last_msg = result["messages"][-1]
        full_state["message"] = getattr(last_msg, "content", str(last_msg))
    else:
        full_state["message"] = ""

    return full_state


@app.post("/api/chat", response_model=ChatResponse)
async def chat_query(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    RAG-grounded Q&A endpoint.
    Demo query: 'What are the biological hazards in pasteurization of milk per FSSAI?'
    """
    retriever = RegulatoryRetriever()
    chunks = await retriever.retrieve(
        session=db,
        query=request.message,
        product_category=_normalize_category(request.product_category),
        hazard_type="biological" if "biological" in request.message.lower() else None,
        source_body="FSSAI" if "fssai" in request.message.lower() else None,
    )

    sources = [c.citation for c in chunks]
    context = chunks_to_context(chunks)
    avg_score = sum(c.score for c in chunks) / len(chunks) if chunks else 0.0

    if has_llm() and chunks:
        try:
            llm = get_chat_model(temperature=0.1)
            system = (
                "You are a food safety expert. Answer based on the provided regulatory context.\n\n"
                "First, you MUST write a thinking phase detailing your analysis of the food safety "
                "regulations, hazards, and thresholds, wrapped inside <thinking>...</thinking> XML tags.\n"
                "Then, write your final response outlining the regulatory compliance advice.\n"
                f"Cite these sources: {', '.join(sources)}"
            )
            response = await llm.ainvoke([
                SystemMessage(content=system),
                HumanMessage(content=f"Context:\n{context}\n\nQuestion: {request.message}"),
            ])
            answer = response.content
        except Exception as exc:
            answer = (
                f"<thinking>\nException while calling LLM: {exc}\nExtracting raw context excerpts.\n</thinking>\n"
                f"LLM unavailable. Showing retrieved excerpts instead.\n\n"
                f"Based on {len(chunks)} regulatory excerpts (avg relevance: {avg_score:.0%}):\n\n"
                + context[:3000]
            )
    elif chunks:
        answer = (
            f"<thinking>\nNo active LLM setup. Summarizing excerpts directly.\n</thinking>\n"
            f"Based on {len(chunks)} regulatory excerpts (avg relevance: {avg_score:.0%}):\n\n"
            + context[:3000]
        )
    else:
        answer = (
            "No relevant regulatory documents found. Please run /api/ingest first "
            "to populate the knowledge base."
        )

    confidence = "high" if avg_score >= 0.7 else "medium" if avg_score >= 0.5 else "low"

    return ChatResponse(answer=answer, sources=sources, confidence=confidence)


@app.post("/api/chat/stream")
async def chat_stream(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
):
    """SSE streaming chat for Vercel AI SDK integration."""
    retriever = RegulatoryRetriever()
    chunks = await retriever.retrieve(
        session=db,
        query=request.message,
        product_category=_normalize_category(request.product_category),
    )
    context = chunks_to_context(chunks)
    sources = [c.citation for c in chunks]
    avg_score = sum(c.score for c in chunks) / len(chunks) if chunks else 0.0
    confidence = "high" if avg_score >= 0.7 else "medium" if avg_score >= 0.5 else "low"

    async def event_generator():
        import json
        meta = {"sources": sources, "confidence": confidence}
        yield f"data: METADATA:{json.dumps(meta)}\n\n"

        if not has_llm():
            thinking_mock = (
                "<thinking>\n"
                f"No LLM active. Analyzing retrieved {len(chunks)} context excerpts...\n"
                f"Grounded source materials: {', '.join(sources)}\n"
                "</thinking>\n"
            )
            for char in thinking_mock:
                yield f"data: {char}\n\n"

            text = f"Based on {len(chunks)} regulatory excerpts (avg relevance: {avg_score:.0%}):\n\n" + context[:2000]
            words = text.split(" ")
            for w in words:
                chunk_escaped = (w + " ").replace("\n", "\\n")
                yield f"data: {chunk_escaped}\n\n"
                await asyncio.sleep(0.02)
            yield "data: [DONE]\n\n"
            return

        try:
            llm = get_chat_model(temperature=0.1, streaming=True)
            system = (
                "You are a food safety expert. Answer based on the provided regulatory context.\n\n"
                "First, you MUST write a thinking phase detailing your analysis of the food safety "
                "regulations, hazards, and thresholds, wrapped inside <thinking>...</thinking> XML tags.\n"
                "Then, write your final response outlining the regulatory compliance advice.\n"
                f"Cite these sources: {', '.join(sources)}"
            )
            async for chunk in llm.astream([
                SystemMessage(content=system),
                HumanMessage(content=f"Context:\n{context}\n\nQuestion: {request.message}"),
            ]):
                if chunk.content:
                    text = str(chunk.content).replace("\n", "\\n")
                    yield f"data: {text}\n\n"
        except Exception as exc:
            fallback = f"<thinking>\\nError running LLM: {exc}\\n</thinking>\\nLLM error: {exc}\\n\\n{chunks_to_context(chunks)[:2000]}"
            yield f"data: {fallback}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/api/search")
async def search_regulatory(
    q: str,
    product_category: str | None = None,
    hazard_type: str | None = None,
    source_body: str | None = None,
    top_k: int = 5,
    db: AsyncSession = Depends(get_db),
):
    """Direct regulatory document search."""
    retriever = RegulatoryRetriever()
    chunks = await retriever.retrieve(
        session=db,
        query=q,
        top_k=top_k,
        product_category=_normalize_category(product_category),
        hazard_type=hazard_type,
        source_body=source_body,
    )
    return {
        "query": q,
        "count": len(chunks),
        "results": [
            {
                "text": c.text,
                "citation": c.citation,
                "score": c.score,
                "source_body": c.source_body,
                "hazard_types": c.hazard_types,
                "product_categories": c.product_categories,
            }
            for c in chunks
        ],
    }


class MonitoringLogCreate(BaseModel):
    ccp_hazard: str
    parameter: str
    value: float
    unit: str = ""
    monitored_by: str = "QA"


@app.get("/api/stats")
async def get_stats(db: AsyncSession = Depends(get_db)):
    """Fetch dashboard statistics."""
    total_query = select(func.count(HACCPPlan.id))
    total_res = await db.execute(total_query)
    total_plans = total_res.scalar_one() or 0

    active_query = select(func.count(HACCPPlan.id)).where(HACCPPlan.status == "in_progress")
    active_res = await db.execute(active_query)
    active_plans = active_res.scalar_one() or 0

    completed_query = select(func.count(HACCPPlan.id)).where(HACCPPlan.status == "complete")
    completed_res = await db.execute(completed_query)
    completed_plans = completed_res.scalar_one() or 0

    chunks_query = select(func.count(RegulatoryChunk.id))
    chunks_res = await db.execute(chunks_query)
    rag_chunks = chunks_res.scalar_one() or 0

    return {
        "total_plans": total_plans,
        "active_plans": active_plans,
        "completed_plans": completed_plans,
        "rag_chunks": rag_chunks,
        "categories_covered": 11,
    }


@app.get("/api/plans/{id}/monitoring")
async def get_monitoring_logs(id: str, db: AsyncSession = Depends(get_db)):
    """Retrieve monitoring logs for a plan."""
    plan_uuid = uuid.UUID(id)
    query = select(MonitoringLog).where(MonitoringLog.plan_id == plan_uuid).order_by(MonitoringLog.timestamp.desc())
    res = await db.execute(query)
    logs = res.scalars().all()
    return {"logs": logs}


@app.post("/api/plans/{id}/monitoring")
async def log_monitoring_entry(
    id: str,
    entry: MonitoringLogCreate,
    db: AsyncSession = Depends(get_db),
):
    """Log a critical parameter measurement and check for deviation."""
    plan_uuid = uuid.UUID(id)
    state = await load_plan_state(db, id)
    if not state:
        raise HTTPException(status_code=404, detail=f"Plan {id} not found.")

    is_deviation = False
    corrective_action_required = None

    ccp_key = entry.ccp_hazard
    limits = state.get("critical_limits", {})
    if ccp_key in limits:
        limit = limits[ccp_key]
        if limit.get("parameter", "").lower() == entry.parameter.lower():
            min_val = limit.get("min_value")
            max_val = limit.get("max_value")
            if min_val is not None and entry.value < min_val:
                is_deviation = True
            if max_val is not None and entry.value > max_val:
                is_deviation = True

    if is_deviation:
        actions = state.get("corrective_actions", [])
        matching_action = next((a for a in actions if a.get("ccp_hazard") == ccp_key), None)
        if matching_action:
            corrective_action_required = matching_action.get("immediate_action")
        else:
            corrective_action_required = (
                "Deviation detected! Immediate action: Isolate affected product, adjust process parameter, and notify supervisor."
            )

    db_log = MonitoringLog(
        plan_id=plan_uuid,
        ccp_hazard=entry.ccp_hazard,
        parameter=entry.parameter,
        value=entry.value,
        unit=entry.unit,
        is_deviation=is_deviation,
        corrective_action_required=corrective_action_required,
        monitored_by=entry.monitored_by,
    )
    db.add(db_log)
    await db.commit()

    return {
        "status": "recorded",
        "is_deviation": is_deviation,
        "corrective_action_required": corrective_action_required,
    }


@app.get("/api/plans/{id}/alerts")
async def get_compliance_alerts(id: str, db: AsyncSession = Depends(get_db)):
    """Fetch compliance score and alerts."""
    state = await load_plan_state(db, id)
    if not state:
        raise HTTPException(status_code=404, detail=f"Plan {id} not found.")

    has_steps = len(state.get("process_steps", [])) > 0
    has_hazards = len(state.get("hazards_identified", [])) > 0 and state.get("hazards_user_confirmed", False)
    has_ccps = len(state.get("ccps_approved", [])) > 0

    limits = state.get("critical_limits", {})
    has_limits = len(limits) > 0 and all(l.get("user_validated", False) for l in limits.values())

    has_monitoring = len(state.get("monitoring_procedures", [])) > 0

    passing_sections = sum([
        1 if has_steps else 0,
        1 if has_hazards else 0,
        1 if has_ccps else 0,
        1 if has_limits else 0,
        1 if has_monitoring else 0,
    ])
    compliance_score = int(passing_sections / 5 * 100)

    query = select(ComplianceAlert).order_by(ComplianceAlert.created_at.desc())
    res = await db.execute(query)
    alerts = res.scalars().all()

    if not alerts:
        alert1 = ComplianceAlert(
            regulatory_source="FSSAI",
            change_summary="Microbiological standards amendment 2026 — revised Listeria limits for RTE dairy.",
            affected_sections=["Pasteurization CCP", "Critical Limits"],
            status="active",
        )
        alert2 = ComplianceAlert(
            regulatory_source="Codex",
            change_summary="Updated guidance on environmental monitoring frequency in cold storage.",
            affected_sections=["Verification Schedule"],
            status="active",
        )
        db.add(alert1)
        db.add(alert2)
        await db.commit()

        res = await db.execute(query)
        alerts = res.scalars().all()

    sections = [
        {
            "title": "HACCP Prerequisites & Foundation",
            "items": [
                ["Business name and category defined", bool(state.get("business_name") and state.get("product_category"))],
                ["Process flow steps established", has_steps],
            ]
        },
        {
            "title": "Hazard Analysis & CCPs",
            "items": [
                ["Hazard identification reviewed", state.get("hazards_user_confirmed", False)],
                ["Critical Control Points approved", has_ccps],
            ]
        },
        {
            "title": "Process Controls & Monitoring",
            "items": [
                ["Critical limits validated", has_limits],
                ["Monitoring procedures assigned", has_monitoring],
            ]
        },
        {
            "title": "Corrective Actions & Verification",
            "items": [
                ["Corrective action procedures ready", len(state.get("corrective_actions", [])) > 0],
                ["Verification schedule planned", bool(state.get("verification_schedule"))],
            ]
        }
    ]

    return {
        "compliance_score": compliance_score,
        "alerts": alerts,
        "sections": sections,
    }


@app.post("/api/plans/{id}/generate-pdf")
async def generate_pdf_endpoint(id: str, db: AsyncSession = Depends(get_db)):
    """Generate and cache a PDF report of the HACCP plan."""
    state = await load_plan_state(db, id)
    if not state:
        raise HTTPException(status_code=404, detail=f"Plan {id} not found.")

    try:
        import tempfile
        import os
        pdf_bytes = generate_haccp_pdf(state)
        temp_dir = tempfile.gettempdir()
        pdf_path = os.path.join(temp_dir, f"haccp_{id}.pdf")
        with open(pdf_path, "wb") as f:
            f.write(pdf_bytes)
        return {"job_id": f"job_{id}", "status": "completed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {e}")


@app.get("/api/plans/{id}/pdf")
async def get_pdf_endpoint(id: str):
    """Retrieve the cached PDF report."""
    import tempfile
    import os
    temp_dir = tempfile.gettempdir()
    pdf_path = os.path.join(temp_dir, f"haccp_{id}.pdf")
    if not os.path.exists(pdf_path):
        raise HTTPException(status_code=404, detail="PDF report not found. Run generate-pdf first.")
    return FileResponse(pdf_path, media_type="application/pdf", filename=f"haccp_plan_{id}.pdf")


@app.get("/api/documents")
async def list_documents(db: AsyncSession = Depends(get_db)):
    """List all registered and dynamically uploaded documents and chunk counts."""
    from rag.ingest import DOCUMENT_REGISTRY
    
    query = select(UploadedDocument)
    res = await db.execute(query)
    dynamic_docs = res.scalars().all()
    
    docs = []
    for d in DOCUMENT_REGISTRY:
        docs.append({
            "filename": d["file"],
            "title": d["document_title"],
            "source_body": d["source_body"],
            "amendment_date": d.get("amendment_date"),
            "product_categories": d.get("product_categories", []),
            "type": "seed"
        })
    for d in dynamic_docs:
        amend_date = d.amendment_date.isoformat() if d.amendment_date else None
        docs.append({
            "filename": d.filename,
            "title": d.document_title,
            "source_body": d.source_body,
            "amendment_date": amend_date,
            "product_categories": d.product_categories,
            "type": "custom"
        })
        
    for doc in docs:
        chunk_count_query = select(func.count(RegulatoryChunk.id)).where(
            RegulatoryChunk.chunk_metadata["file"].astext == doc["filename"]
        )
        count_res = await db.execute(chunk_count_query)
        doc["chunks_count"] = count_res.scalar_one() or 0
        
    return {"documents": docs}


@app.post("/api/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    source_body: str = Form(...),
    document_title: str = Form(...),
    amendment_date: str | None = Form(None),
    product_categories: str = Form("[]"),
    db: AsyncSession = Depends(get_db),
):
    """Upload custom markdown regulations, save to disk, register, and index."""
    import json
    from pathlib import Path
    from datetime import date
    import os
    
    sources_dir = Path(__file__).parent / "rag" / "sources"
    file_path = sources_dir / file.filename
    
    try:
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to write file: {e}")
        
    try:
        categories = json.loads(product_categories)
        if not isinstance(categories, list):
            categories = [categories]
    except Exception:
        categories = [c.strip() for c in product_categories.split(",") if c.strip()]
        
    amend_d = None
    if amendment_date:
        try:
            amend_d = date.fromisoformat(amendment_date)
        except ValueError:
            pass
            
    check_query = select(UploadedDocument).where(UploadedDocument.filename == file.filename)
    check_res = await db.execute(check_query)
    existing = check_res.scalar_one_or_none()
    
    if existing:
        existing.source_body = source_body
        existing.document_title = document_title
        existing.amendment_date = amend_d
        existing.product_categories = categories
    else:
        new_doc = UploadedDocument(
            filename=file.filename,
            source_body=source_body,
            document_title=document_title,
            amendment_date=amend_d,
            product_categories=categories
        )
        db.add(new_doc)
        
    await db.commit()
    
    try:
        ingest_result = await run_full_ingestion(db, clear_existing=True)
        return {
            "status": "success", 
            "message": "Document uploaded and indexed successfully.", 
            "ingest_result": ingest_result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {e}")


@app.delete("/api/documents/{filename}")
async def delete_document(filename: str, db: AsyncSession = Depends(get_db)):
    """Delete uploaded custom regulatory file and re-ingest database."""
    from pathlib import Path
    import os
    
    query = select(UploadedDocument).where(UploadedDocument.filename == filename)
    res = await db.execute(query)
    doc = res.scalar_one_or_none()
    
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found or is a protected seed document.")
        
    await db.delete(doc)
    await db.commit()
    
    sources_dir = Path(__file__).parent / "rag" / "sources"
    file_path = sources_dir / filename
    if file_path.exists():
        try:
            os.remove(file_path)
        except Exception as e:
            print(f"Error removing file: {e}")
            
    try:
        ingest_result = await run_full_ingestion(db, clear_existing=True)
        return {
            "status": "success", 
            "message": "Document deleted and index updated.", 
            "ingest_result": ingest_result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {e}")



@app.post("/api/regulatory/check")
async def trigger_regulatory_check(db: AsyncSession = Depends(get_db)):
    """
    On-demand: run the regulatory monitoring agent across all active plans.
    Searches FSSAI and Codex sources for updates and generates ComplianceAlert records.
    """
    from db.models import HACCPPlan
    from graphs.reg_monitor import run_regulatory_monitor
    from db.persistence import load_plan_state

    query = select(HACCPPlan).where(
        HACCPPlan.status.in_(["in_progress", "complete"])
    )
    res = await db.execute(query)
    plans = res.scalars().all()

    total_alerts = 0
    scanned = 0
    errors = []

    for plan in plans:
        try:
            plan_state = await load_plan_state(db, str(plan.id))
            plan_sections: list[str] = []
            if plan_state:
                hazards = plan_state.get("hazards_identified", [])
                ccps = plan_state.get("ccps_approved", [])
                if hazards:
                    plan_sections.append(f"Hazards: {len(hazards)} identified")
                if ccps:
                    plan_sections.append(f"CCPs: {', '.join(c.get('process_step', '') for c in ccps[:3])}")

            alert_dicts = await run_regulatory_monitor(
                plan_id=str(plan.id),
                business_name=plan.business_name or "",
                product_category=plan.product_category or "general",
                plan_sections=plan_sections,
            )

            for alert_data in alert_dicts:
                from db.models import ComplianceAlert
                alert = ComplianceAlert(
                    regulatory_source=alert_data.get("regulatory_source", "FSSAI"),
                    change_summary=alert_data.get("change_summary", ""),
                    affected_sections=alert_data.get("affected_sections", []),
                    status="active",
                )
                db.add(alert)
                total_alerts += 1

            await db.commit()
            scanned += 1
        except Exception as exc:
            errors.append({"plan_id": str(plan.id), "error": str(exc)})

    return {
        "status": "complete",
        "plans_scanned": scanned,
        "alerts_created": total_alerts,
        "errors": errors,
    }


@app.get("/api/compliance/alerts")
async def get_global_compliance_alerts(db: AsyncSession = Depends(get_db)):
    """Return the global feed of all regulatory compliance alerts."""
    from db.models import ComplianceAlert
    query = select(ComplianceAlert).order_by(ComplianceAlert.created_at.desc()).limit(50)
    res = await db.execute(query)
    alerts = res.scalars().all()

    return {
        "alerts": [
            {
                "id": str(a.id),
                "regulatory_source": a.regulatory_source,
                "change_summary": a.change_summary,
                "affected_sections": a.affected_sections,
                "status": a.status,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in alerts
        ]
    }


if __name__ == "__main__":
    import os
    import uvicorn

    reload = os.getenv("AGENT_RELOAD", "false").lower() in ("1", "true", "yes")

    uvicorn.run(
        "main:app",
        host=settings.agent_host,
        port=settings.agent_port,
        reload=reload,
    )
