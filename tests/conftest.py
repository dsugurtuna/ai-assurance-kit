from __future__ import annotations

import copy
import datetime as dt
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from ai_assurance_kit.checks import run_checks
from ai_assurance_kit.checks.engine import Finding
from ai_assurance_kit.loader import parse_record
from ai_assurance_kit.policy import Policy, load_policy
from ai_assurance_kit.schema import AIUseRecord

ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = ROOT / "examples"
TODAY = dt.date(2026, 9, 30)

# A complete, tidy record that should trigger no rule under the example policy on TODAY.
CLEAN: dict[str, Any] = {
    "schema_version": "1.0",
    "id": "clean-record",
    "title": "Clean test record",
    "version": "1",
    "status": "live",
    "summary": "A tool used in tests.",
    "purpose": "To exercise every rule.",
    "benefits": ["Tests pass."],
    "alternatives_considered": "A spreadsheet; not enough.",
    "accountability": {
        "business_owner": {"role": "Service owner", "name": "Owner Person"},
        "builder": {"role": "Developer", "name": "Builder Person"},
        "maintainer": {"role": "Service manager", "name": "Maintainer Person"},
        "assurer": {"role": "Assurance lead", "name": "Assurer Person"},
        "approver": {"role": "Director"},
    },
    "system": {
        "description": "A test system.",
        "model_kind": "generative",
        "model": "Test model",
        "provider": "in-house",
        "hosting": "organisation_cloud",
    },
    "data": {
        "categories": ["Test data"],
        "personal_data": False,
        "special_category_data": False,
        "sources": ["Test source"],
        "retention": "30 days",
        "dpia": {"status": "screened_not_required", "decided_by": "DPO"},
    },
    "access": {
        "users": "Test users",
        "connectors": [{"name": "Docs", "permissions": ["read"]}],
    },
    "actions": {
        "mode": "drafts",
        "description": "Writes drafts.",
        "human_approval_step": "A person edits and sends.",
        "recipients": ["Author"],
    },
    "reliance": {
        "relied_on_by": ["Staff"],
        "how_outputs_are_used": "As drafts.",
        "decision_role": "information_only",
        "public_facing": False,
        "public_effect": False,
        "significant_influence": False,
        "human_review": "Author checks.",
        "scale": {"users": 10, "uses_per_month": 100},
    },
    "risks": [
        {
            "id": "R1",
            "description": "Wrong draft.",
            "likelihood": 2,
            "impact": 2,
            "owner": "Service owner",
            "controls": ["C1"],
        }
    ],
    "controls": [{"id": "C1", "description": "Human edits.", "status": "in_place"}],
    "evaluation": [
        {
            "date": "2026-03-01",
            "kind": "human_review_sample",
            "summary": "Checked a sample.",
            "independent": True,
        }
    ],
    "decisions": [
        {"type": "approve_build", "date": "2026-01-01", "by": "Director"},
        {"type": "go_live", "date": "2026-04-01", "by": "Director"},
    ],
    "transparency": {"atrs_determination": "out_of_scope", "rationale": "Internal."},
    "review": {"last_reviewed": "2026-04-01", "next_review": "2027-04-01"},
}


def set_path(data: dict[str, Any], path: str, value: Any) -> None:
    """Set a dotted path such as 'data.dpia.status' in a nested dict."""
    *parents, leaf = path.split(".")
    node = data
    for key in parents:
        node = node[key]
    node[leaf] = value


Mutation = dict[str, Any]


@pytest.fixture
def make_record() -> Callable[..., AIUseRecord]:
    def factory(changes: Mutation | None = None) -> AIUseRecord:
        data = copy.deepcopy(CLEAN)
        for path, value in (changes or {}).items():
            set_path(data, path, value)
        return parse_record(data)

    return factory


@pytest.fixture(scope="session")
def policy() -> Policy:
    return load_policy()


@pytest.fixture
def fired(policy: Policy) -> Callable[[AIUseRecord], list[Finding]]:
    def run(record: AIUseRecord) -> list[Finding]:
        return run_checks(record, policy, TODAY)

    return run
