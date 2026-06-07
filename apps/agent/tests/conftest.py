"""Pytest configuration and fixtures."""

import sys
from pathlib import Path

import pytest

# Ensure agent package is importable
AGENT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(AGENT_ROOT))


@pytest.fixture
def sample_process_steps():
    return [
        "Raw milk reception",
        "Cold storage",
        "Pasteurization (HTST 72°C/15s)",
        "Aseptic packaging",
        "Refrigerated dispatch",
    ]


@pytest.fixture
def dairy_pasteurized_intake():
    return {
        "business_name": "Demo Dairy Pvt Ltd",
        "product_category": "dairy_pasteurized",
        "process_steps": [
            "Raw milk reception",
            "Cold storage",
            "Pasteurization (HTST 72°C/15s)",
            "Aseptic packaging",
            "Refrigerated dispatch",
        ],
    }
