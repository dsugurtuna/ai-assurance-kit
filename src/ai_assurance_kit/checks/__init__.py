"""Explainable checks over an AI use record.

>>> from ai_assurance_kit.checks import run_checks
"""

from __future__ import annotations

import datetime as dt

from ai_assurance_kit.checks import rules as _rules  # noqa: F401  (registers the rules)
from ai_assurance_kit.checks.engine import (
    SEVERITY_ORDER,
    CheckContext,
    Finding,
    Hit,
    Rule,
    Severity,
    sort_findings,
)
from ai_assurance_kit.checks.rules import REGISTRY
from ai_assurance_kit.policy import Policy
from ai_assurance_kit.schema import AIUseRecord


def all_rules() -> list[Rule]:
    """Every registered rule, in registration order."""
    return REGISTRY.all()


def run_checks(record: AIUseRecord, policy: Policy, today: dt.date | None = None) -> list[Finding]:
    """Run every enabled rule and return findings, most severe first."""
    ctx = CheckContext(policy=policy, today=today or dt.date.today())
    disabled = set(policy.disabled_rules)
    unknown = sorted(disabled - {r.id for r in REGISTRY})
    if unknown:
        raise ValueError(f"policy disables unknown rule ids: {', '.join(unknown)}")
    findings: list[Finding] = []
    for rule in REGISTRY:
        if rule.id not in disabled:
            findings.extend(rule.run(record, ctx))
    return sort_findings(findings)


def count_by_severity(findings: list[Finding]) -> dict[str, int]:
    counts = {s.value: 0 for s in sorted(Severity, key=lambda s: -SEVERITY_ORDER[s])}
    for f in findings:
        counts[f.severity.value] += 1
    return counts


def meets_threshold(findings: list[Finding], threshold: Severity) -> bool:
    """True if any finding is at or above the given severity."""
    return any(SEVERITY_ORDER[f.severity] >= SEVERITY_ORDER[threshold] for f in findings)


__all__ = [
    "CheckContext",
    "Finding",
    "Hit",
    "Rule",
    "Severity",
    "all_rules",
    "count_by_severity",
    "meets_threshold",
    "run_checks",
]
