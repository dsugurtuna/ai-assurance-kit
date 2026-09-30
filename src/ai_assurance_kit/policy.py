"""Organisation policy: risk appetite, proportionality levels and change thresholds.

The kit ships one *example* policy (``data/policy.example.yaml``). It is a starting point, not a
recommendation: every organisation should set its own appetite, levels and triggers.
"""

from __future__ import annotations

from importlib import resources
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from ai_assurance_kit.loader import Problem, RecordError, problems_from, read_yaml

EXAMPLE_POLICY_RESOURCE = "policy.example.yaml"


class _Model(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class RiskPolicy(_Model):
    appetite_score: int = Field(
        ge=1,
        le=25,
        description="Risks scoring above this (likelihood x impact, 1-25) are above appetite.",
    )


class Level(_Model):
    id: str = Field(pattern=r"^[a-z0-9_]+$")
    label: str
    means: str = Field(description="What this level asks for, in a sentence or two.")


class Trigger(_Model):
    """Raise the minimum level when a record feature meets a condition."""

    feature: str
    level: str
    reason: str
    equals: bool | int | str | None = None
    one_of: list[str] | None = Field(default=None, alias="in")
    at_least: int | None = Field(default=None, alias="gte")

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    @model_validator(mode="after")
    def _exactly_one_condition(self) -> Trigger:
        given = [
            name
            for name, value in (
                ("equals", self.equals),
                ("in", self.one_of),
                ("gte", self.at_least),
            )
            if value is not None
        ]
        if len(given) != 1:
            raise ValueError("a trigger needs exactly one of: equals, in, gte")
        return self

    def matches(self, value: object) -> bool:
        if self.equals is not None:
            return value == self.equals and type(value) is type(self.equals)
        if self.one_of is not None:
            return isinstance(value, str) and value in self.one_of
        if self.at_least is not None:
            return (
                isinstance(value, int) and not isinstance(value, bool) and (value >= self.at_least)
            )
        return False  # pragma: no cover - guarded by the validator

    def condition(self) -> str:
        if self.equals is not None:
            shown = str(self.equals).lower() if isinstance(self.equals, bool) else self.equals
            return f"{self.feature} = {shown}"
        if self.one_of is not None:
            return f"{self.feature} in [{', '.join(self.one_of)}]"
        return f"{self.feature} >= {self.at_least}"


class ChangePolicy(_Model):
    scale_factor: float = Field(
        default=2.0,
        gt=1.0,
        description="A rise in users or monthly uses by at least this factor is material.",
    )


class Policy(_Model):
    policy_name: str
    risk: RiskPolicy
    levels: list[Level] = Field(min_length=1)
    triggers: list[Trigger] = Field(default_factory=list)
    changes: ChangePolicy = Field(default_factory=ChangePolicy)
    disabled_rules: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _consistent(self) -> Policy:
        # Local imports avoid a cycle: levels and the rules both import this module.
        from ai_assurance_kit.checks.rules import REGISTRY
        from ai_assurance_kit.levels import FEATURES

        ids = [lv.id for lv in self.levels]
        problems: list[str] = []
        if len(set(ids)) != len(ids):
            problems.append("level ids must be unique")
        for i, trig in enumerate(self.triggers):
            if trig.level not in ids:
                problems.append(f"triggers[{i}] uses unknown level '{trig.level}'")
            if trig.feature not in FEATURES:
                known = ", ".join(sorted(FEATURES))
                problems.append(
                    f"triggers[{i}] uses unknown feature '{trig.feature}' (known: {known})"
                )
            elif problem := FEATURES[trig.feature].problem_with(trig):
                problems.append(f"triggers[{i}]: {problem}")
        # Checked here as well as when the checks run, so `aiak policy --validate` catches it.
        if unknown := sorted(set(self.disabled_rules) - {r.id for r in REGISTRY}):
            problems.append(f"disabled_rules names unknown rule ids: {', '.join(unknown)}")
        if problems:
            raise ValueError("; ".join(problems))
        return self

    def rank(self, level_id: str) -> int:
        return [lv.id for lv in self.levels].index(level_id)

    def level(self, level_id: str) -> Level:
        return self.levels[self.rank(level_id)]


def example_policy_text() -> str:
    """Return the example policy YAML shipped with the package."""
    return (
        resources.files("ai_assurance_kit")
        .joinpath("data", EXAMPLE_POLICY_RESOURCE)
        .read_text(encoding="utf-8")
    )


def parse_policy(data: dict[str, Any], path: Path | None = None) -> Policy:
    try:
        return Policy.model_validate(data)
    except ValidationError as exc:
        raise RecordError(path or Path("<policy>"), problems_from(exc), "policy") from exc


def load_policy(path: str | Path | None = None) -> Policy:
    """Load a policy file, or the bundled example policy when ``path`` is None."""
    if path is None:
        data = yaml.safe_load(example_policy_text())
        return parse_policy(data, Path(EXAMPLE_POLICY_RESOURCE))
    p = Path(path)
    data = read_yaml(p, "policy")
    if not isinstance(data, dict):
        raise RecordError(p, [Problem("", "the policy file must contain a mapping")], "policy")
    return parse_policy(data, p)
