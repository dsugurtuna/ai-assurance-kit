"""Aggregate many records into a portfolio register (CSV or Markdown)."""

from __future__ import annotations

import csv
import datetime as dt
import io
from collections.abc import Sequence
from typing import Literal

from ai_assurance_kit import __version__
from ai_assurance_kit.render import DISCLAIMER, Assessment, environment, yes_no

RegisterFormat = Literal["csv", "md"]

REGISTER_COLUMNS: tuple[str, ...] = (
    "id",
    "title",
    "status",
    "business_owner",
    "level",
    "high",
    "warning",
    "info",
    "personal_data",
    "public_facing",
    "action_mode",
    "decision_role",
    "atrs_determination",
    "next_review",
    "review_overdue",
    "file",
)


def register_rows(items: Sequence[tuple[str, Assessment]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for source, a in items:
        r = a.record
        counts = a.counts
        rows.append(
            {
                "id": r.id,
                "title": r.title,
                "status": r.status.value,
                "business_owner": r.accountability.business_owner.role,
                "level": a.level.level.label,
                "high": str(counts["high"]),
                "warning": str(counts["warning"]),
                "info": str(counts["info"]),
                "personal_data": yes_no(r.data.personal_data),
                "public_facing": yes_no(r.reliance.public_facing),
                "action_mode": r.actions.mode.value,
                "decision_role": r.reliance.decision_role.value,
                "atrs_determination": r.transparency.atrs_determination.value,
                "next_review": r.review.next_review.isoformat() if r.review.next_review else "",
                "review_overdue": yes_no(a.review_overdue),
                "file": source,
            }
        )
    return rows


_FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def _csv_safe(value: str) -> str:
    """Neutralise spreadsheet formula prefixes before writing CSV cells."""
    if value and (value[0] in _FORMULA_PREFIXES or value.lstrip().startswith(("=", "+", "-", "@"))):
        return f"'{value}"
    return value


def render_register(
    items: Sequence[tuple[str, Assessment]],
    fmt: RegisterFormat = "md",
    today: dt.date | None = None,
) -> str:
    """Render a portfolio register as CSV or a Markdown table."""
    rows = register_rows(items)
    if fmt == "csv":
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=REGISTER_COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows({k: _csv_safe(v) for k, v in row.items()} for row in rows)
        return buf.getvalue()
    template = environment().get_template("register.md.j2")
    as_at = today.isoformat() if today else (items[0][1].today.isoformat() if items else "")
    return template.render(rows=rows, as_at=as_at, disclaimer=DISCLAIMER, version=__version__)
