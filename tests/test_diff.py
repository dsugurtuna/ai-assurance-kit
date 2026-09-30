from __future__ import annotations

import copy
from collections.abc import Callable
from typing import Any

import pytest

from ai_assurance_kit.diff import diff_records, flatten
from ai_assurance_kit.loader import load_record, parse_record
from ai_assurance_kit.policy import Policy
from ai_assurance_kit.schema import AIUseRecord
from tests.conftest import CLEAN, EXAMPLES, set_path

Make = Callable[..., AIUseRecord]


def _material(old: AIUseRecord, new: AIUseRecord, policy: Policy) -> list[str]:
    return [c.path for c in diff_records(old, new, policy).material]


def test_identical_records_have_no_changes(make_record: Make, policy: Policy) -> None:
    report = diff_records(make_record(), make_record(), policy)
    assert (report.material, report.other, report.needs_review) == ([], [], False)


@pytest.mark.parametrize(
    ("changes", "path"),
    [
        ({"data.categories": ["Test data", "Health records"]}, "data.categories"),
        ({"data.personal_data": True}, "data.personal_data"),
        (
            {"data.personal_data": True, "data.special_category_data": True},
            "data.special_category_data",
        ),
        ({"data.sources": ["Test source", "CRM"]}, "data.sources"),
        (
            {
                "access.connectors": [
                    {"name": "Docs", "permissions": ["read"]},
                    {"name": "CRM", "permissions": ["read"]},
                ]
            },
            "access.connectors[CRM]",
        ),
        (
            {"access.connectors": [{"name": "Docs", "permissions": ["read", "send"]}]},
            "access.connectors[Docs].permissions",
        ),
        ({"access.users": "Everyone"}, "access.users"),
        ({"actions.mode": "autonomous"}, "actions.mode"),
        ({"actions.recipients": ["Author", "Customers"]}, "actions.recipients"),
        ({"actions.human_approval_step": None}, "actions.human_approval_step"),
        ({"reliance.public_facing": True}, "reliance.public_facing"),
        ({"reliance.public_effect": True}, "reliance.public_effect"),
        ({"reliance.significant_influence": True}, "reliance.significant_influence"),
        ({"reliance.decision_role": "decision_support"}, "reliance.decision_role"),
        ({"reliance.human_review": None}, "reliance.human_review"),
        ({"reliance.scale": {"users": 20, "uses_per_month": 100}}, "reliance.scale.users"),
        ({"system.model": "Another model"}, "system.model"),
        ({"system.hosting": "vendor_saas"}, "system.hosting"),
        (
            {
                "risks": [
                    {
                        "id": "R1",
                        "description": "Wrong draft.",
                        "likelihood": 4,
                        "impact": 4,
                        "owner": "Owner",
                        "controls": ["C1"],
                    }
                ]
            },
            "risks[R1]",
        ),
    ],
)
def test_material_changes(
    changes: dict[str, Any], path: str, make_record: Make, policy: Policy
) -> None:
    assert path in _material(make_record(), make_record(changes), policy)


def test_status_to_live_is_material(make_record: Make, policy: Policy) -> None:
    old = make_record({"status": "in_test"})
    report = diff_records(old, make_record(), policy)
    change = next(c for c in report.material if c.path == "status")
    assert "pilot tool moving to production" in change.reason


@pytest.mark.parametrize(
    "changes",
    [
        {"actions.mode": "read_only"},  # less autonomous
        {"reliance.scale": {"users": 19, "uses_per_month": 100}},  # 1.9x, below 2x
        {"reliance.scale": {"users": 5, "uses_per_month": 100}},  # smaller
        {"summary": "A reworded summary."},
        {"data.categories": ["TEST DATA"]},  # case-only change is not a new category
    ],
)
def test_not_material(changes: dict[str, Any], make_record: Make, policy: Policy) -> None:
    assert _material(make_record(), make_record(changes), policy) == []


def test_scale_factor_comes_from_policy(make_record: Make, policy: Policy) -> None:
    strict = policy.model_copy(
        update={"changes": policy.changes.model_copy(update={"scale_factor": 1.5})}
    )
    new = make_record({"reliance.scale": {"users": 15, "uses_per_month": 100}})
    assert _material(make_record(), new, strict) == ["reliance.scale.users"]


def test_reordering_keyed_lists_is_not_a_change(policy: Policy) -> None:
    a = copy.deepcopy(CLEAN)
    set_path(
        a,
        "access.connectors",
        [
            {"name": "Docs", "permissions": ["read"]},
            {"name": "Wiki", "permissions": ["read"]},
        ],
    )
    b = copy.deepcopy(a)
    b["access"]["connectors"].reverse()
    report = diff_records(parse_record(a), parse_record(b), policy)
    assert (report.material, report.other) == ([], [])


def test_other_changes_are_listed(make_record: Make, policy: Policy) -> None:
    report = diff_records(make_record(), make_record({"version": "2", "summary": "New."}), policy)
    assert [c.path for c in report.other] == ["summary", "version"]
    assert report.other[1].describe() == "1 -> 2"


def test_material_paths_are_not_repeated_in_other(make_record: Make, policy: Policy) -> None:
    new = make_record(
        {
            "access.connectors": [
                {"name": "Docs", "permissions": ["read"]},
                {"name": "CRM", "permissions": ["read"]},
            ]
        }
    )
    report = diff_records(make_record(), new, policy)
    assert not any(c.path.startswith("access.connectors[CRM]") for c in report.other)


def test_added_list_items_read_as_one_change(make_record: Make, policy: Policy) -> None:
    extra = {"date": "2026-05-01", "kind": "pilot", "summary": "Pilot."}
    new = make_record({"evaluation": [*CLEAN["evaluation"], extra]})
    report = diff_records(make_record(), new, policy)
    assert [(c.path, c.summary) for c in report.other] == [("evaluation[1]", "added")]


def test_flatten_keys_lists() -> None:
    flat = flatten({"risks": [{"id": "R1", "impact": 2}], "tags": ["b", "a"]})
    assert flat == {"risks[R1].id": "R1", "risks[R1].impact": 2, "tags": ("a", "b")}


def test_grant_triage_example_diff(policy: Policy) -> None:
    old = load_record(EXAMPLES / "history" / "grant-triage.v1.yaml")
    new = load_record(EXAMPLES / "grant-triage.yaml")
    report = diff_records(old, new, policy)
    summaries = [c.summary for c in report.material]
    assert report.needs_review
    assert "Action mode moves from drafts to autonomous" in summaries
    assert "New connector 'Applicant email' (send)" in summaries
    assert "New recipients: Grants case management system, Applicants" in summaries
    assert "Scale rises: uses per month 400 to 1500" in summaries
    assert "Human approval step removed" in summaries
    assert report.to_dict()["needs_review"] is True
