"""Proportionality levels: how much review a use case needs, and why.

A level is computed from a small set of named *features* of the record (for example
``personal_data`` or ``action_mode``). The policy file lists triggers such as
"if action_mode is autonomous, the level is at least senior_specialist". The result is the
highest level any trigger reaches, plus every trigger that fired, so the reasoning is visible.

Why features rather than arbitrary expressions over the record? Because a named, documented
feature list is easy to review, test and explain to a governance board, and it keeps the policy
file free of code.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from ai_assurance_kit.policy import Level, Policy
from ai_assurance_kit.schema import (
    ActionMode,
    AIUseRecord,
    Permission,
)

FeatureValue = bool | int | str | None


@dataclass(frozen=True)
class Feature:
    name: str
    description: str
    compute: Callable[[AIUseRecord, Policy], FeatureValue]


def _max_risk(record: AIUseRecord, _policy: Policy) -> int:
    return max((r.score for r in record.risks), default=0)


def _risks_above_appetite(record: AIUseRecord, policy: Policy) -> int:
    return sum(1 for r in record.risks if r.score > policy.risk.appetite_score)


def _write_connectors(record: AIUseRecord, _policy: Policy) -> int:
    writing = {Permission.write, Permission.send, Permission.delete, Permission.admin}
    return sum(1 for c in record.access.connectors if writing.intersection(c.permissions))


_FEATURE_LIST: tuple[Feature, ...] = (
    Feature(
        "personal_data", "The system processes personal data.", lambda r, _: r.data.personal_data
    ),
    Feature(
        "special_category_data",
        "The system processes special category personal data.",
        lambda r, _: r.data.special_category_data,
    ),
    Feature(
        "public_facing",
        "Members of the public interact with the system directly.",
        lambda r, _: r.reliance.public_facing,
    ),
    Feature(
        "public_effect",
        "Outputs feed decisions affecting the public or organisations.",
        lambda r, _: r.reliance.public_effect,
    ),
    Feature(
        "significant_public_effect",
        "Outputs significantly influence decisions that affect the public or organisations.",
        lambda r, _: r.reliance.public_effect and r.reliance.significant_influence,
    ),
    Feature(
        "decision_role",
        "information_only, decision_support or automated_decision.",
        lambda r, _: r.reliance.decision_role.value,
    ),
    Feature(
        "action_mode",
        "read_only, drafts, writes_with_approval or autonomous.",
        lambda r, _: r.actions.mode.value,
    ),
    Feature(
        "sends_or_writes",
        "The system itself sends or writes (with or without approval).",
        lambda r, _: r.actions.mode in (ActionMode.writes_with_approval, ActionMode.autonomous),
    ),
    Feature(
        "write_connectors",
        "Number of connectors with write, send, delete or admin permission.",
        _write_connectors,
    ),
    Feature(
        "third_party_supplier",
        "A third party supplies the tool or model.",
        lambda r, _: r.system.third_party_supplier is not None,
    ),
    Feature("max_risk_score", "Highest likelihood x impact score (0 if no risks).", _max_risk),
    Feature(
        "risks_above_appetite",
        "Number of risks scoring above the policy appetite.",
        _risks_above_appetite,
    ),
    Feature("users", "Number of users, if recorded.", lambda r, _: r.reliance.scale.users),
    Feature(
        "uses_per_month",
        "Uses per month, if recorded.",
        lambda r, _: r.reliance.scale.uses_per_month,
    ),
)

FEATURES: dict[str, Feature] = {f.name: f for f in _FEATURE_LIST}


def record_features(record: AIUseRecord, policy: Policy) -> dict[str, FeatureValue]:
    """Compute every named feature for a record."""
    return {name: feat.compute(record, policy) for name, feat in FEATURES.items()}


@dataclass(frozen=True)
class Reason:
    level: Level
    reason: str
    condition: str
    value: FeatureValue


@dataclass(frozen=True)
class LevelResult:
    level: Level
    policy_name: str
    reasons: list[Reason] = field(default_factory=list)

    @property
    def is_default(self) -> bool:
        return not self.reasons


def assess_level(record: AIUseRecord, policy: Policy) -> LevelResult:
    """Return the proportionality level for a record under a policy, with reasons."""
    features = record_features(record, policy)
    reasons: list[Reason] = []
    for trig in policy.triggers:
        value = features[trig.feature]
        if trig.matches(value):
            reasons.append(Reason(policy.level(trig.level), trig.reason, trig.condition(), value))
    reasons.sort(key=lambda r: -policy.rank(r.level.id))
    level = reasons[0].level if reasons else policy.levels[0]
    return LevelResult(level=level, policy_name=policy.policy_name, reasons=reasons)
