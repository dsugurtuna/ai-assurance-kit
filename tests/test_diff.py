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


def test_blank_supplier_normalises_to_no_diff(make_record: Make, policy: Policy) -> None:
    report = diff_records(
        make_record({"system.third_party_supplier": "  "}),
        make_record({"system.third_party_supplier": None}),
        policy,
    )
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


@pytest.mark.parametrize(
    ("before", "after", "path"),
    [
        # More people rely on the outputs: who it affects and how much it is relied on.
        (
            {},
            {"reliance.relied_on_by": ["Staff", "Members of the public"]},
            "reliance.relied_on_by",
        ),
        # A different kind of model under the same product label.
        ({}, {"system.model_kind": "predictive"}, "system.model_kind"),
        # An existing connector now points at a different system.
        (
            {"access.connectors": [{"name": "Docs", "system": "Wiki", "permissions": ["read"]}]},
            {
                "access.connectors": [
                    {"name": "Docs", "system": "HR system", "permissions": ["read"]}
                ]
            },
            "access.connectors[Docs].system",
        ),
        # Safeguards removed, like the approval step and human review already are.
        (
            {"actions.stop_mechanism": "Admin switch."},
            {"actions.stop_mechanism": None},
            "actions.stop_mechanism",
        ),
        (
            {"reliance.challenge_route": "Complaints route."},
            {"reliance.challenge_route": None},
            "reliance.challenge_route",
        ),
        (
            {"reliance.user_notice": "Banner says AI is used."},
            {"reliance.user_notice": None},
            "reliance.user_notice",
        ),
        # Removing or downgrading an in-place control is material.
        (
            {
                "controls": [
                    {"id": "C1", "description": "Human edits.", "status": "in_place"},
                    {"id": "C2", "description": "Second safeguard.", "status": "in_place"},
                ]
            },
            {"controls": [{"id": "C1", "description": "Human edits.", "status": "in_place"}]},
            "controls[C2]",
        ),
        (
            {},
            {"controls": [{"id": "C1", "description": "Human edits.", "status": "planned"}]},
            "controls[C1].status",
        ),
        # Regressing DPIA status is material.
        (
            {"data.dpia": {"status": "completed", "decided_by": "DPO"}},
            {"data.dpia": {"status": "required_in_progress", "decided_by": "DPO"}},
            "data.dpia.status",
        ),
        (
            {"data.dpia": {"status": "completed", "decided_by": "DPO"}},
            {"data.dpia": {"status": "not_screened", "decided_by": "DPO"}},
            "data.dpia.status",
        ),
        # Large first-time scale entry is material.
        (
            {"reliance.scale": {"users": None, "uses_per_month": 100}},
            {"reliance.scale": {"users": 50000, "uses_per_month": 100}},
            "reliance.scale.users",
        ),
    ],
)
def test_more_material_changes(
    before: dict[str, Any], after: dict[str, Any], path: str, make_record: Make, policy: Policy
) -> None:
    old = make_record(before)
    new = make_record({**before, **after})
    assert path in _material(old, new, policy)


@pytest.mark.parametrize(
    ("before", "after"),
    [
        # Recording a connector's system for the first time is not a new connection.
        (
            {},
            {"access.connectors": [{"name": "Docs", "system": "Wiki", "permissions": ["read"]}]},
        ),
        # A blank supplier is no supplier; the change is not material.
        ({}, {"system.third_party_supplier": "  "}),
        # Fewer groups relying on the outputs.
        ({"reliance.relied_on_by": ["Staff", "Managers"]}, {"reliance.relied_on_by": ["Staff"]}),
        # DPIA progressing forward is not a regression.
        (
            {"data.dpia": {"status": "not_screened"}},
            {"data.dpia": {"status": "completed", "decided_by": "DPO"}},
        ),
        # Removing a planned control is not material.
        (
            {
                "controls": [
                    {"id": "C1", "description": "Human edits.", "status": "in_place"},
                    {"id": "C2", "description": "Planned.", "status": "planned"},
                ]
            },
            {"controls": [{"id": "C1", "description": "Human edits.", "status": "in_place"}]},
        ),
        # Small first-time scale entry below threshold is not material.
        (
            {"reliance.scale": {"users": None, "uses_per_month": None}},
            {"reliance.scale": {"users": 25, "uses_per_month": 400}},
        ),
    ],
)
def test_more_changes_that_are_not_material(
    before: dict[str, Any], after: dict[str, Any], make_record: Make, policy: Policy
) -> None:
    old = make_record(before)
    new = make_record({**before, **after})
    assert _material(old, new, policy) == []


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


def test_material_change_does_not_hide_other_edits_to_the_same_risk(
    make_record: Make, policy: Policy
) -> None:
    # R1 rises above appetite and, in the same edit, loses its owner and its control. The
    # material change explains the score; the owner and control edits must still be shown.
    new = make_record(
        {
            "risks": [
                {
                    "id": "R1",
                    "description": "Wrong draft.",
                    "likelihood": 4,
                    "impact": 4,
                    "owner": None,
                    "controls": [],
                }
            ]
        }
    )
    report = diff_records(make_record(), new, policy)
    assert [c.path for c in report.material] == ["risks[R1]"]
    other = {c.path: c for c in report.other}
    assert other["risks[R1].owner"].summary == "cleared"
    assert other["risks[R1].controls"].after == []
    assert "risks[R1].likelihood" not in other  # explained by the material change


@pytest.mark.parametrize(
    ("changes", "path"),
    [
        ({"data.categories": ["Health records"]}, "data.categories"),
        ({"data.sources": ["CRM"]}, "data.sources"),
        ({"actions.recipients": ["Customers"]}, "actions.recipients"),
        (
            {"access.connectors": [{"name": "Docs", "permissions": ["write"]}]},
            "access.connectors[Docs].permissions",
        ),
    ],
)
def test_additions_do_not_hide_removals(
    changes: dict[str, Any], path: str, make_record: Make, policy: Policy
) -> None:
    # Something was added (material) and something was removed in the same edit. The removal
    # is not explained by the material summary, so the field must also appear under "other".
    report = diff_records(make_record(), make_record(changes), policy)
    assert path in [c.path for c in report.material]
    assert path in [c.path for c in report.other]


def test_added_list_items_read_as_one_change(make_record: Make, policy: Policy) -> None:
    extra = {"date": "2026-05-01", "kind": "pilot", "summary": "Pilot."}
    new = make_record({"evaluation": [*CLEAN["evaluation"], extra]})
    report = diff_records(make_record(), new, policy)
    assert [(c.path, c.summary) for c in report.other] == [("evaluation[1]", "added")]


_SAMPLES = [
    {"date": f"2026-0{m}-01", "kind": "human_review_sample", "summary": f"Sample {m}."}
    for m in (3, 2, 1)
]


def test_item_added_to_a_newest_first_list_reads_as_one_change(
    make_record: Make, policy: Policy
) -> None:
    # Many teams list evidence newest first. Adding one item at the top must not report the
    # existing evidence as "changed", which would read as evidence being altered.
    old = make_record({"evaluation": _SAMPLES})
    pilot = {"date": "2026-04-01", "kind": "pilot", "summary": "Pilot."}
    new = make_record({"evaluation": [pilot, *_SAMPLES]})
    report = diff_records(old, new, policy)
    assert [(c.path, c.summary) for c in report.other] == [("evaluation[0]", "added")]
    assert report.other[0].after == "2026-04-01 pilot: Pilot."


def test_reordering_unkeyed_items_is_not_a_change(make_record: Make, policy: Policy) -> None:
    old = make_record({"evaluation": _SAMPLES})
    new = make_record({"evaluation": list(reversed(_SAMPLES))})
    assert diff_records(old, new, policy).other == []


def test_edit_to_one_item_is_reported_for_that_item(make_record: Make, policy: Policy) -> None:
    edited = [_SAMPLES[0], {**_SAMPLES[1], "independent": True}, _SAMPLES[2]]
    report = diff_records(
        make_record({"evaluation": _SAMPLES}), make_record({"evaluation": edited}), policy
    )
    assert [(c.path, c.summary) for c in report.other] == [("evaluation[1]", "changed")]
    change = report.other[0]
    assert (change.before["independent"], change.after["independent"]) == (False, True)


def test_removed_item_is_reported(make_record: Make, policy: Policy) -> None:
    report = diff_records(
        make_record({"evaluation": _SAMPLES}),
        make_record({"evaluation": [_SAMPLES[0], _SAMPLES[2]]}),
        policy,
    )
    assert [(c.path, c.summary, c.before) for c in report.other] == [
        ("evaluation[1]", "removed", "2026-02-01 human_review_sample: Sample 2.")
    ]


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
