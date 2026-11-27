from __future__ import annotations

import copy
import datetime as dt
import re
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

# Keys whose values are enumerations, dates, numbers, flags or constrained slugs. Every other
# string in a record is free text that a person typed and a renderer must treat as data.
_NOT_FREE_TEXT = {
    "schema_version",
    "status",
    "model_kind",
    "hosting",
    "permissions",
    "mode",
    "decision_role",
    "kind",
    "type",
    "atrs_determination",
    "date",
    "last_reviewed",
    "next_review",
}


def hostile_data(text: str) -> dict[str, Any]:
    """CLEAN with every free-text string replaced by ``text`` plus a unique suffix.

    Used to check that output formats escape what a record author typed. Optional text fields
    that CLEAN leaves empty are filled too, and cross-references are kept valid.
    """
    data = copy.deepcopy(CLEAN)
    # Optional text fields CLEAN leaves out; None here is replaced with text below.
    for path in (
        "organisation",
        "system.platform",
        "system.third_party_supplier",
        "data.dpia.reference",
        "actions.stop_mechanism",
        "reliance.challenge_route",
        "reliance.user_notice",
        "transparency.record_url",
    ):
        set_path(data, path, None)
    for person in data["accountability"].values():
        person.update(name=None, team=None)
    data["access"]["connectors"][0].update(system=None, purpose=None)
    data["risks"][0].update(accepted_by=None, acceptance_rationale=None)
    data["controls"][0]["owner"] = None
    data["evaluation"][0].update(performed_by=None, link=None)
    data["decisions"][0]["note"] = None
    counter = iter(range(10_000))

    def fill(node: Any, key: str = "", top: bool = False) -> Any:
        if key in _NOT_FREE_TEXT or (top and key == "id"):
            return node
        if isinstance(node, dict):
            return {k: fill(v, k, top=node is data) for k, v in node.items()}
        if isinstance(node, list):
            return [fill(v) for v in node]
        if isinstance(node, str) or node is None:
            return f"{text}{next(counter)}"  # unique, so every field can be told apart
        return node  # numbers and flags

    out: dict[str, Any] = fill(data)
    out["risks"][0]["controls"] = [out["controls"][0]["id"]]
    return out


def assert_markdown_contains_text_safely(text: str, marker: str) -> None:
    """Hostile record text (see hostile_data) must not break Markdown structure or inject HTML.

    ``marker`` is the part of the hostile text that follows a newline: it must never start a
    line, because that means a value broke out of its table row, list item or heading. Text
    inside a code span is shown literally by Markdown renderers, so raw HTML is only an
    injection outside code spans.
    """
    assert marker in text, "the hostile text should appear in the output"
    header_cells: int | None = None
    for line in text.splitlines():
        assert not line.startswith(marker), f"a value broke onto its own line: {line!r}"
        outside_code = re.sub(r"`[^`]*`", "", line)
        assert "<script" not in outside_code.lower(), f"raw HTML in Markdown: {line!r}"
        if line.startswith("|"):
            cells = len(re.findall(r"(?<!\\)\|", line))
            header_cells = header_cells if header_cells is not None else cells
            assert cells == header_cells, f"table row has the wrong number of cells: {line!r}"
        else:
            header_cells = None


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
