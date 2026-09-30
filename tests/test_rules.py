from __future__ import annotations

import copy
import re
from collections.abc import Callable
from typing import Any

import pytest

from ai_assurance_kit.checks import (
    all_rules,
    count_by_severity,
    meets_threshold,
    run_checks,
)
from ai_assurance_kit.checks.engine import Finding, Severity
from ai_assurance_kit.policy import Policy
from ai_assurance_kit.schema import AIUseRecord
from ai_assurance_kit.sources import NIST_SUBCATEGORIES, SOURCES
from tests.conftest import CLEAN, TODAY

Make = Callable[..., AIUseRecord]
Fired = Callable[[AIUseRecord], list[Finding]]

_EVIDENCE = CLEAN["evaluation"][0]


def _risk(likelihood: int, impact: int, owner: str | None, controls: list[str]) -> list[Any]:
    return [
        {
            "id": "R9",
            "description": "A risk.",
            "likelihood": likelihood,
            "impact": impact,
            "owner": owner,
            "controls": controls,
        }
    ]


# Each rule, with a change to the clean record that should make it fire.
TRIGGERS: dict[str, dict[str, Any]] = {
    "AIAK-META-001": {"title": "REPLACE with a name"},
    "AIAK-ACT-001": {"actions.mode": "autonomous"},
    "AIAK-ACT-002": {"actions.mode": "writes_with_approval"},
    "AIAK-ACT-003": {
        "actions.mode": "read_only",
        "access.connectors": [{"name": "Mail", "permissions": ["read", "send"]}],
    },
    "AIAK-ACT-004": {
        "actions.mode": "writes_with_approval",
        "actions.recipients": [],
        "actions.stop_mechanism": "Admin switch.",
    },
    "AIAK-DATA-001": {"data.personal_data": True, "data.dpia": {"status": "not_screened"}},
    "AIAK-DATA-002": {"data.personal_data": True, "data.retention": None},
    "AIAK-DATA-003": {
        "data.personal_data": True,
        "data.special_category_data": True,
        "data.dpia": {"status": "screened_not_required"},
    },
    "AIAK-TRANS-001": {
        "reliance.public_facing": True,
        "transparency.atrs_determination": "not_assessed",
    },
    "AIAK-TRANS-002": {"reliance.public_facing": True},
    "AIAK-ROLE-001": {"accountability.assurer": {"role": "Assurer", "name": "  builder   PERSON "}},
    "AIAK-ROLE-002": {"accountability.assurer": None},
    "AIAK-ROLE-003": {"accountability.maintainer": None},
    "AIAK-EVAL-001": {"evaluation": []},
    "AIAK-EVAL-002": {
        "evaluation": [{"date": "2026-03-01", "kind": "usage_metrics", "summary": "Use counts."}]
    },
    "AIAK-EVAL-003": {
        "evaluation": [
            {
                "date": "2026-03-01",
                "kind": "model_graded",
                "summary": "Graded.",
                "independent": True,
            }
        ]
    },
    "AIAK-EVAL-004": {"evaluation": [{**_EVIDENCE, "independent": False}]},
    "AIAK-REV-001": {"review.next_review": "2026-09-29"},
    "AIAK-REV-002": {"review.next_review": None},
    "AIAK-RISK-001": {"risks": _risk(4, 4, None, ["C1"])},
    "AIAK-RISK-002": {"risks": _risk(4, 4, "Owner", [])},
    "AIAK-RISK-003": {"risks": []},
    "AIAK-PURP-001": {"alternatives_considered": None},
    "AIAK-DEC-001": {
        "reliance.decision_role": "automated_decision",
        "reliance.public_effect": True,
    },
    "AIAK-DEC-002": {"reliance.decision_role": "decision_support", "reliance.human_review": None},
    "AIAK-LIFE-001": {"decisions": [CLEAN["decisions"][0]]},
}


def _ids(findings: list[Finding]) -> set[str]:
    return {f.rule.id for f in findings}


def test_clean_record_triggers_nothing(make_record: Make, fired: Fired) -> None:
    assert fired(make_record()) == []


def test_every_rule_has_a_trigger_case() -> None:
    assert set(TRIGGERS) == {r.id for r in all_rules()}


@pytest.mark.parametrize("rule_id", sorted(TRIGGERS))
def test_rule_fires(rule_id: str, make_record: Make, fired: Fired) -> None:
    findings = fired(make_record(TRIGGERS[rule_id]))
    assert rule_id in _ids(findings)
    finding = next(f for f in findings if f.rule.id == rule_id)
    assert finding.message
    assert finding.fields, "each finding should point at the fields it concerns"


@pytest.mark.parametrize("rule_id", sorted(TRIGGERS))
def test_rules_skip_retired_records(rule_id: str, make_record: Make, fired: Fired) -> None:
    changes = {**TRIGGERS[rule_id], "status": "retired"}
    fired_ids = _ids(fired(make_record(changes)))
    if rule_id == "AIAK-META-001":
        assert rule_id in fired_ids  # placeholders matter whatever the status
    else:
        assert rule_id not in fired_ids


# --------------------------------------------------------------------------- rule metadata


@pytest.mark.parametrize("rule", all_rules(), ids=lambda r: r.id)
def test_rule_metadata(rule: Any) -> None:
    assert re.fullmatch(r"AIAK-[A-Z]+-\d{3}", rule.id)
    assert rule.title
    assert rule.title[0].isupper()
    assert len(rule.rationale) > 40
    assert rule.refs, "every rule cites at least one source"
    for ref in rule.refs:
        assert ref.source in SOURCES
        if ref.source == "nist-ai-rmf" and " " in ref.pointer:
            assert ref.pointer in NIST_SUBCATEGORIES


@pytest.mark.parametrize("rule", all_rules(), ids=lambda r: r.id)
def test_messages_are_prompts_not_verdicts(rule: Any, make_record: Make, fired: Fired) -> None:
    banned = ("non-compliant", "noncompliant", "fails", "violat", "illegal", "unlawful")
    findings = [f for f in fired(make_record(TRIGGERS[rule.id])) if f.rule.id == rule.id]
    for text in [rule.title, rule.rationale, *(f.message for f in findings)]:
        assert not any(word in text.lower() for word in banned), text


# --------------------------------------------------------------------------- boundaries


def test_actions_drafts_may_write_to_a_drafts_location(make_record: Make, fired: Fired) -> None:
    record = make_record({"access.connectors": [{"name": "Drafts", "permissions": ["write"]}]})
    assert "AIAK-ACT-003" not in _ids(fired(record))


def test_actions_drafts_may_not_send(make_record: Make, fired: Fired) -> None:
    record = make_record({"access.connectors": [{"name": "Mail", "permissions": ["send"]}]})
    assert "AIAK-ACT-003" in _ids(fired(record))


def test_approval_described_satisfies_act_001(make_record: Make, fired: Fired) -> None:
    record = make_record(
        {
            "actions.mode": "writes_with_approval",
            "actions.human_approval_step": "Officer approves each send.",
            "actions.stop_mechanism": "Switch.",
        }
    )
    assert "AIAK-ACT-001" not in _ids(fired(record))


def test_role_001_prompt_names_roles_not_people(make_record: Make, fired: Fired) -> None:
    # Names are optional and redactable; prompts end up in cards, JSON and CI logs, so they
    # identify the roles involved rather than repeating the person's name.
    record = make_record(TRIGGERS["AIAK-ROLE-001"])
    finding = next(f for f in fired(record) if f.rule.id == "AIAK-ROLE-001")
    assert "builder person" not in finding.message.casefold()
    assert "'Developer'" in finding.message
    assert "'Assurer'" in finding.message


def test_same_person_needs_both_names(make_record: Make, fired: Fired) -> None:
    record = make_record(
        {
            "accountability.builder": {"role": "Developer"},
            "accountability.assurer": {"role": "Developer"},
        }
    )
    assert "AIAK-ROLE-001" not in _ids(fired(record))


def test_review_due_today_is_not_overdue(make_record: Make, fired: Fired) -> None:
    record = make_record({"review.next_review": TODAY.isoformat()})
    assert "AIAK-REV-001" not in _ids(fired(record))


def test_risk_at_appetite_is_not_above(make_record: Make, fired: Fired, policy: Policy) -> None:
    assert policy.risk.appetite_score == 9
    record = make_record({"risks": _risk(3, 3, None, [])})
    assert not {"AIAK-RISK-001", "AIAK-RISK-002"} & _ids(fired(record))


def test_planned_control_does_not_satisfy_risk_002(make_record: Make, fired: Fired) -> None:
    record = make_record(
        {
            "risks": _risk(4, 4, "Owner", ["C1"]),
            "controls": [{"id": "C1", "description": "Planned.", "status": "planned"}],
        }
    )
    finding = next(f for f in fired(record) if f.rule.id == "AIAK-RISK-002")
    assert "(planned: C1)" in finding.message


def test_model_grading_with_human_sample_is_fine(make_record: Make, fired: Fired) -> None:
    evidence = [
        {"date": "2026-03-01", "kind": "model_graded", "summary": "Graded."},
        _EVIDENCE,
    ]
    assert "AIAK-EVAL-003" not in _ids(fired(make_record({"evaluation": evidence})))


def test_recorded_atrs_determination_silences_trans_001(make_record: Make, fired: Fired) -> None:
    record = make_record(
        {"reliance.public_facing": True, "transparency.atrs_determination": "in_scope"}
    )
    assert "AIAK-TRANS-001" not in _ids(fired(record))


def test_significant_public_effect_triggers_trans_001(make_record: Make, fired: Fired) -> None:
    record = make_record(
        {
            "reliance.public_effect": True,
            "reliance.significant_influence": True,
            "transparency.atrs_determination": "not_assessed",
        }
    )
    finding = next(f for f in fired(record) if f.rule.id == "AIAK-TRANS-001")
    assert "significantly influence decisions with public effect" in finding.message


def test_public_effect_without_significant_influence_does_not(
    make_record: Make, fired: Fired
) -> None:
    record = make_record(
        {"reliance.public_effect": True, "transparency.atrs_determination": "not_assessed"}
    )
    assert "AIAK-TRANS-001" not in _ids(fired(record))


def test_proposed_records_are_not_asked_for_an_assurer(make_record: Make, fired: Fired) -> None:
    record = make_record({"status": "proposed", "accountability.assurer": None})
    assert "AIAK-ROLE-002" not in _ids(fired(record))


def test_in_test_needs_only_build_approval(make_record: Make, fired: Fired) -> None:
    record = make_record({"status": "in_test", "decisions": [CLEAN["decisions"][0]]})
    assert "AIAK-LIFE-001" not in _ids(fired(record))


def test_life_001_names_the_missing_decision(make_record: Make, fired: Fired) -> None:
    record = make_record({"decisions": []})
    finding = next(f for f in fired(record) if f.rule.id == "AIAK-LIFE-001")
    assert "approve_build or go_live" in finding.message


# --------------------------------------------------------------------------- engine


def test_findings_are_sorted_most_severe_first(make_record: Make, fired: Fired) -> None:
    changes = {**TRIGGERS["AIAK-PURP-001"], **TRIGGERS["AIAK-ROLE-003"], **TRIGGERS["AIAK-REV-002"]}
    severities = [f.severity for f in fired(make_record(changes))]
    assert severities == [Severity.high, Severity.warning, Severity.info]


def test_disabled_rules_are_skipped(make_record: Make, policy: Policy) -> None:
    custom = policy.model_copy(update={"disabled_rules": ["AIAK-PURP-001"]})
    record = make_record(TRIGGERS["AIAK-PURP-001"])
    assert run_checks(record, custom, TODAY) == []


def test_unknown_disabled_rule_is_an_error(make_record: Make, policy: Policy) -> None:
    custom = policy.model_copy(update={"disabled_rules": ["AIAK-NOPE-001"]})
    with pytest.raises(ValueError, match="AIAK-NOPE-001"):
        run_checks(make_record(), custom, TODAY)


def test_counts_and_threshold(make_record: Make, fired: Fired) -> None:
    findings = fired(make_record(TRIGGERS["AIAK-PURP-001"]))
    assert count_by_severity(findings) == {"high": 0, "warning": 0, "info": 1}
    assert meets_threshold(findings, Severity.info)
    assert not meets_threshold(findings, Severity.warning)


def test_finding_to_dict_has_sources(make_record: Make, fired: Fired) -> None:
    data = fired(make_record(TRIGGERS["AIAK-ROLE-001"]))[0].to_dict()
    assert data["rule_id"] == "AIAK-ROLE-001"
    assert data["severity"] == "high"
    assert any(s["url"].startswith("https://") for s in data["sources"])


def test_example_findings_are_stable(policy: Policy) -> None:
    """The examples are designed to show particular prompts; keep them that way."""
    from ai_assurance_kit.loader import load_record
    from tests.conftest import EXAMPLES

    expected = {
        "meeting-notes-summariser.yaml": {"AIAK-REV-001"},
        "service-chatbot.yaml": {
            "AIAK-ROLE-001",
            "AIAK-RISK-001",
            "AIAK-RISK-002",
            "AIAK-DATA-002",
            "AIAK-EVAL-003",
            "AIAK-EVAL-004",
            "AIAK-TRANS-001",
            "AIAK-TRANS-002",
        },
        "grant-triage.yaml": {"AIAK-ACT-001", "AIAK-ACT-002", "AIAK-RISK-001", "AIAK-RISK-002"},
    }
    for name, ids in expected.items():
        record = load_record(EXAMPLES / name)
        assert _ids(run_checks(record, policy, TODAY)) == ids, name


def test_clean_copy_is_not_mutated() -> None:
    before = copy.deepcopy(CLEAN)
    assert before == CLEAN
