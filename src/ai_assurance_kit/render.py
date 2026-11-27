"""Render a record as a one-page card: Markdown, or standalone accessible HTML."""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Any, Literal

from jinja2 import Environment, PackageLoader, StrictUndefined, select_autoescape

from ai_assurance_kit import __version__
from ai_assurance_kit.checks import count_by_severity, run_checks
from ai_assurance_kit.checks.engine import Finding
from ai_assurance_kit.levels import LevelResult, assess_level
from ai_assurance_kit.policy import Policy
from ai_assurance_kit.schema import AIUseRecord, Person, Status

CardFormat = Literal["md", "html"]

DISCLAIMER = (
    "Unofficial. Not government guidance. Checks are prompts for human judgement, not verdicts."
)


def md_text(value: object) -> str:
    """Make record or policy text safe inside Markdown: a table cell, list item or heading.

    Newlines are collapsed (they would end the row, item or heading), pipes are escaped (they
    would start a new table cell) and ``<`` is written as an entity, so text such as
    ``<script>`` stays text in renderers that pass raw HTML through.
    """
    text = "" if value is None else str(value)
    return " ".join(text.split()).replace("|", "\\|").replace("<", "&lt;")


def md_code(value: object) -> str:
    """Show a value as a one-line Markdown code span; a backtick would end the span early."""
    text = "" if value is None else str(value)
    return "`" + " ".join(text.split()).replace("`", "'") + "`"


def yes_no(value: bool) -> str:
    return "yes" if value else "no"


def _words(value: str) -> str:
    return value.replace("_", " ")


def environment() -> Environment:
    env = Environment(
        loader=PackageLoader("ai_assurance_kit", "templates"),
        autoescape=select_autoescape(
            enabled_extensions=("html", "html.j2"), default_for_string=False
        ),
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )
    env.filters["md"] = md_text
    env.filters["code"] = md_code
    env.filters["yesno"] = yes_no
    env.filters["words"] = _words
    return env


@dataclass(frozen=True)
class Assessment:
    """Everything the kit derives from one record under one policy on one date."""

    record: AIUseRecord
    findings: list[Finding]
    level: LevelResult
    today: dt.date

    @property
    def counts(self) -> dict[str, int]:
        return count_by_severity(self.findings)

    @property
    def review_overdue(self) -> bool:
        due = self.record.review.next_review
        return due is not None and due < self.today and self.record.status is not Status.retired


def assess(record: AIUseRecord, policy: Policy, today: dt.date | None = None) -> Assessment:
    day = today or dt.date.today()
    return Assessment(record, run_checks(record, policy, day), assess_level(record, policy), day)


def _person(p: Person | None, redact: bool) -> str:
    if p is None:
        return "not recorded"
    role = p.role
    if p.team and p.team.casefold() != p.role.casefold():
        role = f"{p.role}, {p.team}"
    if redact or not p.name:
        return role
    return f"{role} ({p.name})"


def _is_safe_http_url(url: str | None) -> bool:
    if not url or not url.startswith(("https://", "http://")):
        return False
    return not any(ch.isspace() or ch in '<>"`[](){}|\\' for ch in url)


def _card_context(a: Assessment, policy: Policy, source: str, redact: bool) -> dict[str, Any]:
    r = a.record
    acc = r.accountability
    appetite = policy.risk.appetite_score
    risks = sorted(r.risks, key=lambda x: (-x.score, x.id))
    cited: dict[str, tuple[str, str]] = {}
    for f in a.findings:
        for ref in f.rule.refs:
            cited.setdefault(ref.doc.id, (ref.doc.title, ref.doc.url))
    timeline = [
        {
            "date": e.date.isoformat(),
            "label": f"evidence, {_words(e.kind.value)}"
            + (" (independent)" if e.independent else ""),
            "text": e.summary,
        }
        for e in r.evaluation
    ] + [
        {
            "date": d.date.isoformat(),
            "label": f"decision, {_words(d.type.value)}",
            "text": f"by {d.by}" + (f". {d.note}" if d.note else ""),
        }
        for d in r.decisions
    ]
    timeline.sort(key=lambda item: item["date"])
    return {
        "r": r,
        "a": a,
        "timeline": timeline,
        "policy": policy,
        "appetite": appetite,
        "people": {
            "Business owner": _person(acc.business_owner, redact),
            "Builder": _person(acc.builder, redact),
            "Maintainer": _person(acc.maintainer, redact),
            "Assurer": _person(acc.assurer, redact),
            "Approver": _person(acc.approver, redact),
        },
        "risks": risks,
        "risk_rows": [
            {
                "risk": x,
                "above": x.score > appetite,
                "controls": ", ".join(
                    f"{c.id} ({_words(c.status.value)})"
                    for cid in x.controls
                    if (c := r.control(cid)) is not None
                )
                or "none",
            }
            for x in risks
        ],
        "cited": sorted(cited.values()),
        "record_url_is_link": _is_safe_http_url(r.transparency.record_url),
        "source": source,
        "version": __version__,
        "disclaimer": DISCLAIMER,
        "redacted": redact,
    }


def render_card(
    record: AIUseRecord,
    policy: Policy,
    fmt: CardFormat = "md",
    today: dt.date | None = None,
    source: str = "record",
    redact_names: bool = False,
) -> str:
    """Render a one-page card for a record."""
    a = assess(record, policy, today)
    template = environment().get_template("card.md.j2" if fmt == "md" else "card.html.j2")
    return template.render(**_card_context(a, policy, source, redact_names))
