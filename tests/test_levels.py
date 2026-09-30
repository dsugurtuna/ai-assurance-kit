from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
import yaml

from ai_assurance_kit.levels import FEATURES, assess_level, record_features
from ai_assurance_kit.loader import RecordError, load_record
from ai_assurance_kit.policy import Policy, Trigger, example_policy_text, load_policy, parse_policy
from ai_assurance_kit.schema import AIUseRecord
from tests.conftest import EXAMPLES

Make = Callable[..., AIUseRecord]


def _policy_data() -> dict[str, Any]:
    data = yaml.safe_load(example_policy_text())
    assert isinstance(data, dict)
    return data


def test_example_policy_loads() -> None:
    policy = load_policy()
    assert [lv.id for lv in policy.levels] == ["standard", "use_specific", "senior_specialist"]
    assert policy.risk.appetite_score == 9
    assert "adapt" in policy.policy_name.lower()


def test_example_policy_says_it_is_an_example() -> None:
    assert example_policy_text().startswith("# EXAMPLE POLICY")


def test_clean_record_is_standard(make_record: Make, policy: Policy) -> None:
    result = assess_level(make_record(), policy)
    assert result.level.id == "standard"
    assert result.is_default


def test_personal_data_raises_to_use_specific(make_record: Make, policy: Policy) -> None:
    result = assess_level(make_record({"data.personal_data": True}), policy)
    assert result.level.id == "use_specific"
    assert [r.condition for r in result.reasons] == ["personal_data = true"]


def test_highest_level_wins_and_reasons_are_sorted(make_record: Make, policy: Policy) -> None:
    record = make_record({"data.personal_data": True, "actions.mode": "autonomous"})
    result = assess_level(record, policy)
    assert result.level.id == "senior_specialist"
    ranks = [policy.rank(r.level.id) for r in result.reasons]
    assert ranks == sorted(ranks, reverse=True)
    assert {r.condition for r in result.reasons} == {
        "personal_data = true",
        "sends_or_writes = true",
        "action_mode = autonomous",
    }


def test_gte_trigger(make_record: Make, policy: Policy) -> None:
    record = make_record({"reliance.scale": {"uses_per_month": 10000}})
    result = assess_level(record, policy)
    assert result.level.id == "use_specific"
    assert result.reasons[0].condition == "uses_per_month >= 10000"


def test_gte_ignores_missing_values(make_record: Make, policy: Policy) -> None:
    record = make_record({"reliance.scale": {"uses_per_month": None}})
    assert assess_level(record, policy).level.id == "standard"


def test_max_risk_score_feature(make_record: Make, policy: Policy) -> None:
    risks = [
        {"id": "R1", "description": "x", "likelihood": 4, "impact": 4, "owner": "o"},
        {"id": "R2", "description": "y", "likelihood": 2, "impact": 5, "owner": "o"},
    ]
    features = record_features(make_record({"risks": risks}), policy)
    assert features["max_risk_score"] == 16
    assert features["risks_above_appetite"] == 2


def test_every_feature_computes_for_examples(policy: Policy) -> None:
    for path in EXAMPLES.glob("*.yaml"):
        features = record_features(load_record(path), policy)
        assert set(features) == set(FEATURES)


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("meeting-notes-summariser.yaml", "use_specific"),
        ("service-chatbot.yaml", "use_specific"),
        ("grant-triage.yaml", "senior_specialist"),
    ],
)
def test_example_levels(name: str, expected: str, policy: Policy) -> None:
    assert assess_level(load_record(EXAMPLES / name), policy).level.id == expected


def test_trigger_equality_is_type_strict() -> None:
    trig = Trigger(feature="personal_data", level="x", reason="r", equals=True)
    assert trig.matches(True)
    assert not trig.matches(1)
    assert not trig.matches("true")


def test_trigger_in_condition() -> None:
    trig = Trigger.model_validate(
        {"feature": "action_mode", "level": "x", "reason": "r", "in": ["drafts", "autonomous"]}
    )
    assert trig.matches("drafts")
    assert not trig.matches("read_only")
    assert trig.condition() == "action_mode in [drafts, autonomous]"


@pytest.mark.parametrize(
    ("trigger", "message"),
    [
        (
            {"feature": "nope", "level": "standard", "reason": "r", "equals": True},
            "unknown feature",
        ),
        (
            {"feature": "personal_data", "level": "nope", "reason": "r", "equals": True},
            "unknown level",
        ),
        ({"feature": "personal_data", "level": "standard", "reason": "r"}, "exactly one of"),
        (
            {"feature": "users", "level": "standard", "reason": "r", "equals": 1, "gte": 2},
            "exactly one of",
        ),
    ],
)
def test_policy_validation(trigger: dict[str, Any], message: str) -> None:
    data = _policy_data()
    data["triggers"] = [trigger]
    with pytest.raises(RecordError, match=message):
        parse_policy(data)


def test_policy_rejects_duplicate_levels() -> None:
    data = _policy_data()
    data["levels"].append(dict(data["levels"][0]))
    with pytest.raises(RecordError, match="unique"):
        parse_policy(data)


def test_custom_policy_file(tmp_path: Path, make_record: Make) -> None:
    data = _policy_data()
    data["policy_name"] = "Stricter"
    data["triggers"] = [
        {"feature": "users", "gte": 5, "level": "senior_specialist", "reason": "Many users."}
    ]
    path = tmp_path / "policy.yaml"
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    policy = load_policy(path)
    result = assess_level(make_record(), policy)
    assert (result.level.id, result.policy_name) == ("senior_specialist", "Stricter")


def test_policy_file_errors(tmp_path: Path) -> None:
    with pytest.raises(RecordError, match="cannot read"):
        load_policy(tmp_path / "missing.yaml")
    bad = tmp_path / "bad.yaml"
    bad.write_text("- not a mapping\n", encoding="utf-8")
    with pytest.raises(RecordError, match="valid policy"):
        load_policy(bad)
