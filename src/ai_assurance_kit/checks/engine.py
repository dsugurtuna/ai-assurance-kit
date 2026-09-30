"""A small, explainable rule engine.

Each rule is a plain function plus metadata: an ID, a severity, a rationale and citations. A rule
returns zero or more *hits*; each hit becomes a finding phrased as a prompt for human judgement.

Why plain functions and not a rules DSL? Because the checks are few, the logic is easy to read in
Python, and a reviewer can see exactly what fires and why. The metadata is what makes each rule
explainable; the function is what makes it testable.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Callable, Iterable, Iterator
from dataclasses import dataclass, field
from enum import StrEnum

from ai_assurance_kit.policy import Policy
from ai_assurance_kit.schema import AIUseRecord, Status
from ai_assurance_kit.sources import Ref


class Severity(StrEnum):
    """How soon a prompt needs a human answer. None of these is a verdict."""

    info = "info"  # worth recording; no action required to proceed
    warning = "warning"  # needs a recorded human decision before the next stage
    high = "high"  # resolve, or explicitly accept with a named owner, before relying on the use


SEVERITY_ORDER: dict[Severity, int] = {Severity.info: 0, Severity.warning: 1, Severity.high: 2}


@dataclass(frozen=True)
class CheckContext:
    policy: Policy
    today: dt.date


@dataclass(frozen=True)
class Hit:
    """What a rule reports: a prompt and the record fields it concerns."""

    message: str
    fields: tuple[str, ...] = ()


RuleFn = Callable[[AIUseRecord, CheckContext], Iterable[Hit]]


@dataclass(frozen=True)
class Rule:
    id: str
    title: str
    severity: Severity
    rationale: str
    refs: tuple[Ref, ...]
    fn: RuleFn
    skip_statuses: frozenset[Status] = field(default_factory=lambda: frozenset({Status.retired}))

    def run(self, record: AIUseRecord, ctx: CheckContext) -> list[Finding]:
        if record.status in self.skip_statuses:
            return []
        return [
            Finding(rule=self, message=h.message, fields=h.fields) for h in self.fn(record, ctx)
        ]


@dataclass(frozen=True)
class Finding:
    rule: Rule
    message: str
    fields: tuple[str, ...] = ()

    @property
    def severity(self) -> Severity:
        return self.rule.severity

    def to_dict(self) -> dict[str, object]:
        return {
            "rule_id": self.rule.id,
            "severity": self.severity.value,
            "title": self.rule.title,
            "message": self.message,
            "fields": list(self.fields),
            "rationale": self.rule.rationale,
            "sources": [
                {"title": r.doc.title, "pointer": r.pointer, "url": r.doc.url}
                for r in self.rule.refs
            ],
        }


class Registry:
    """Holds rules in a stable order and refuses duplicate IDs."""

    def __init__(self) -> None:
        self._rules: dict[str, Rule] = {}

    def rule(
        self,
        id: str,
        title: str,
        severity: Severity,
        rationale: str,
        refs: Iterable[Ref],
        skip_statuses: Iterable[Status] = (Status.retired,),
    ) -> Callable[[RuleFn], RuleFn]:
        def register(fn: RuleFn) -> RuleFn:
            if id in self._rules:
                raise ValueError(f"duplicate rule id {id}")
            self._rules[id] = Rule(
                id=id,
                title=title,
                severity=severity,
                rationale=" ".join(rationale.split()),
                refs=tuple(refs),
                fn=fn,
                skip_statuses=frozenset(skip_statuses),
            )
            return fn

        return register

    def __iter__(self) -> Iterator[Rule]:
        return iter(self._rules.values())

    def all(self) -> list[Rule]:
        return list(self._rules.values())

    def get(self, rule_id: str) -> Rule:
        return self._rules[rule_id]


def sort_findings(findings: Iterable[Finding]) -> list[Finding]:
    """Most severe first, then by rule ID, then by message, so output is stable."""
    return sorted(findings, key=lambda f: (-SEVERITY_ORDER[f.severity], f.rule.id, f.message))
