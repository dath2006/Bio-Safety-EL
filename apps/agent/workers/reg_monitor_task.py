"""
Celery task for regulatory monitoring — runs daily to scan FSSAI/Codex for updates
and generate ComplianceAlert records for all active HACCP plans.

Usage:
  # Start the worker (from apps/agent directory):
  celery -A workers.reg_monitor_task worker --loglevel=info

  # Start the beat scheduler for daily cron:
  celery -A workers.reg_monitor_task beat --loglevel=info

  # Combined (for development):
  celery -A workers.reg_monitor_task worker --beat --loglevel=info
"""
from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path

# Add agent root to Python path when running as Celery worker
sys.path.insert(0, str(Path(__file__).parent.parent))

from celery import Celery
from celery.schedules import crontab
from kombu import Queue

from config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()

# ─── Celery App ───────────────────────────────────────────────────────────────

app = Celery(
    "haccp_workers",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",
    enable_utc=True,
    task_queues=(
        Queue("default"),
        Queue("regulatory"),
    ),
    task_default_queue="default",
    worker_prefetch_multiplier=1,
    task_acks_late=True,
)

# ─── Beat Schedule (Daily Cron) ───────────────────────────────────────────────

app.conf.beat_schedule = {
    "daily-regulatory-scan": {
        "task": "workers.reg_monitor_task.scan_all_plans",
        "schedule": crontab(hour=6, minute=0),  # Run at 6 AM IST daily
        "options": {"queue": "regulatory"},
    },
}


# ─── Tasks ───────────────────────────────────────────────────────────────────

@app.task(
    name="workers.reg_monitor_task.scan_all_plans",
    bind=True,
    max_retries=3,
    queue="regulatory",
    soft_time_limit=300,
)
def scan_all_plans(self):
    """
    Celery task: scan all active HACCP plans for regulatory compliance alerts.
    Runs daily via beat scheduler or can be triggered on-demand.
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop.run_until_complete(_async_scan_all_plans())
    except Exception as exc:
        logger.exception("Regulatory scan failed: %s", exc)
        raise self.retry(exc=exc, countdown=60)


@app.task(
    name="workers.reg_monitor_task.scan_single_plan",
    bind=True,
    max_retries=2,
    queue="regulatory",
    soft_time_limit=120,
)
def scan_single_plan(self, plan_id: str):
    """
    Celery task: scan a single HACCP plan for regulatory compliance alerts.
    Can be triggered on-demand from the API.
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop.run_until_complete(_async_scan_single_plan(plan_id))
    except Exception as exc:
        logger.exception("Regulatory scan for plan %s failed: %s", plan_id, exc)
        raise self.retry(exc=exc, countdown=30)


# ─── Async Helpers ────────────────────────────────────────────────────────────

async def _async_scan_all_plans() -> dict:
    """Scan all active/in-progress HACCP plans."""
    from db.session import async_session_factory
    from db.models import HACCPPlan, ComplianceAlert
    from sqlalchemy import select

    results = {"plans_scanned": 0, "alerts_created": 0, "errors": []}

    async with async_session_factory() as session:
        # Fetch active plans
        query = select(HACCPPlan).where(
            HACCPPlan.status.in_(["in_progress", "complete"])
        )
        res = await session.execute(query)
        plans = res.scalars().all()

        for plan in plans:
            try:
                alerts = await _run_monitor_for_plan(
                    plan_id=str(plan.id),
                    business_name=plan.business_name or "",
                    product_category=plan.product_category or "general",
                    session=session,
                )
                results["alerts_created"] += len(alerts)
                results["plans_scanned"] += 1
            except Exception as exc:
                logger.error("Error scanning plan %s: %s", plan.id, exc)
                results["errors"].append(str(plan.id))

    logger.info("Regulatory scan complete: %s", results)
    return results


async def _async_scan_single_plan(plan_id: str) -> dict:
    """Scan a single plan by ID."""
    from db.session import async_session_factory
    from db.models import HACCPPlan
    from db.persistence import load_plan_state
    from sqlalchemy import select

    async with async_session_factory() as session:
        query = select(HACCPPlan).where(HACCPPlan.id == plan_id)
        res = await session.execute(query)
        plan = res.scalar_one_or_none()

        if not plan:
            return {"error": f"Plan {plan_id} not found"}

        alerts = await _run_monitor_for_plan(
            plan_id=plan_id,
            business_name=plan.business_name or "",
            product_category=plan.product_category or "general",
            session=session,
        )
        return {"plan_id": plan_id, "alerts_created": len(alerts)}


async def _run_monitor_for_plan(
    plan_id: str,
    business_name: str,
    product_category: str,
    session,
) -> list:
    """Run the regulatory monitor agent and persist any new alerts."""
    from db.models import ComplianceAlert
    from db.persistence import load_plan_state
    from graphs.reg_monitor import run_regulatory_monitor

    # Build plan section context from stored state
    plan_state = await load_plan_state(session, plan_id)
    plan_sections: list[str] = []
    if plan_state:
        # Extract section summaries for comparison
        hazards = plan_state.get("hazards_identified", [])
        ccps = plan_state.get("ccps_approved", [])
        limits = plan_state.get("critical_limits", {})

        if hazards:
            plan_sections.append(f"Hazard Analysis: {len(hazards)} hazards identified")
        if ccps:
            plan_sections.append(f"CCPs: {', '.join(c.get('process_step', '') for c in ccps[:3])}")
        if limits:
            plan_sections.append(f"Critical Limits: {', '.join(list(limits.keys())[:3])}")

    # Run the monitoring agent
    alert_dicts = await run_regulatory_monitor(
        plan_id=plan_id,
        business_name=business_name,
        product_category=product_category,
        plan_sections=plan_sections,
    )

    # Persist alerts that don't already exist
    created = []
    for alert_data in alert_dicts:
        alert = ComplianceAlert(
            regulatory_source=alert_data.get("regulatory_source", "FSSAI"),
            change_summary=alert_data.get("change_summary", ""),
            affected_sections=alert_data.get("affected_sections", []),
            status="active",
        )
        session.add(alert)
        created.append(alert)

    if created:
        await session.commit()
        logger.info("Created %d regulatory alerts for plan %s", len(created), plan_id)

    return created


if __name__ == "__main__":
    app.start()
