"""Tests for HACCPState models."""

from models.state import HazardRecord, create_initial_state


def test_create_initial_state():
    state = create_initial_state("test-plan-id")
    assert state["plan_id"] == "test-plan-id"
    assert state["current_stage"] == "intake"
    assert state["hazards_identified"] == []


def test_hazard_record_rpn_calculation():
    hazard = HazardRecord(
        name="Pathogen survival",
        category="biological",
        process_step="Pasteurization",
        likelihood=4,
        severity=5,
    )
    assert hazard.rpn == 20


def test_hazard_record_defaults():
    hazard = HazardRecord(
        name="Metal fragment",
        category="physical",
        process_step="Packaging",
    )
    assert hazard.likelihood == 3
    assert hazard.severity == 3
    assert hazard.rpn == 9
