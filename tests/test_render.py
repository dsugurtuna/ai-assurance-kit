"""Rendering tests.

The committed cards in examples/cards/ double as snapshots. To regenerate them after an
intentional change, run:  AIAK_UPDATE_SNAPSHOTS=1 pytest tests/test_render.py
(or the `aiak render ... --today 2026-09-30` commands listed in examples/README.md).
"""

from __future__ import annotations

import os
from collections.abc import Callable
from html.parser import HTMLParser
from pathlib import Path

import pytest

from ai_assurance_kit.loader import load_record
from ai_assurance_kit.policy import Policy
from ai_assurance_kit.register import REGISTER_COLUMNS, render_register
from ai_assurance_kit.render import assess, render_card
from ai_assurance_kit.schema import AIUseRecord
from tests.conftest import EXAMPLES, ROOT, TODAY

Make = Callable[..., AIUseRecord]
CARDS = EXAMPLES / "cards"
NAMES = ["meeting-notes-summariser", "service-chatbot", "grant-triage"]
UPDATE = os.environ.get("AIAK_UPDATE_SNAPSHOTS") == "1"


def _card(name: str, fmt: str, policy: Policy) -> str:
    record = load_record(EXAMPLES / f"{name}.yaml")
    return render_card(record, policy, fmt=fmt, today=TODAY, source=f"examples/{name}.yaml")  # type: ignore[arg-type]


@pytest.mark.parametrize("fmt", ["md", "html"])
@pytest.mark.parametrize("name", NAMES)
def test_card_snapshots(name: str, fmt: str, policy: Policy) -> None:
    rendered = _card(name, fmt, policy)
    snapshot = CARDS / f"{name}.{fmt}"
    if UPDATE:
        CARDS.mkdir(exist_ok=True)
        snapshot.write_text(rendered, encoding="utf-8")
    assert snapshot.exists(), f"missing snapshot {snapshot.relative_to(ROOT)}"
    assert rendered == snapshot.read_text(encoding="utf-8"), (
        f"{snapshot.relative_to(ROOT)} is out of date; see the docstring of this test module"
    )


def test_card_has_disclaimer_and_level(policy: Policy) -> None:
    text = _card("service-chatbot", "md", policy)
    assert "Unofficial. Not government guidance." in text
    assert "## Proportionality level: Use-specific review" in text
    assert "`public_facing = true`" in text
    assert "AIAK-ROLE-001" in text


def test_redacted_card_hides_names(policy: Policy) -> None:
    record = load_record(EXAMPLES / "service-chatbot.yaml")
    text = render_card(record, policy, today=TODAY, redact_names=True)
    assert "Riley Placeholder" not in text
    assert "Head of Permits Service" in text
    assert "(names redacted)" in text


def test_markdown_escapes_table_pipes(make_record: Make, policy: Policy) -> None:
    text = render_card(make_record({"purpose": "Either | or"}), policy, today=TODAY)
    assert "| Purpose | Either \\| or |" in text


def test_card_with_no_findings_says_so(make_record: Make, policy: Policy) -> None:
    text = render_card(make_record(), policy, today=TODAY)
    assert "not that the use is assured" in text


class _Checker(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.tags: list[str] = []
        self.attrs: list[tuple[str, dict[str, str | None]]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.tags.append(tag)
        self.attrs.append((tag, dict(attrs)))


@pytest.mark.parametrize("name", NAMES)
def test_html_card_is_accessible_and_standalone(name: str, policy: Policy) -> None:
    html = _card(name, "html", policy)
    checker = _Checker()
    checker.feed(html)
    assert '<html lang="en-GB">' in html
    assert "<title>" in html
    assert "script" not in checker.tags, "cards must work without JavaScript"
    assert "link" not in checker.tags, "cards must not load external stylesheets"
    assert "@media print" in html
    assert checker.tags.count("main") == 1
    headers = [a for tag, a in checker.attrs if tag == "th"]
    assert headers
    assert all(a.get("scope") == "col" for a in headers)


def test_html_escapes_record_text(make_record: Make, policy: Policy) -> None:
    html = render_card(
        make_record({"title": "<script>x</script>"}), policy, fmt="html", today=TODAY
    )
    assert "<script>x" not in html
    assert "&lt;script&gt;x" in html


def test_register_markdown_and_csv(policy: Policy) -> None:
    items = [
        (f"examples/{n}.yaml", assess(load_record(EXAMPLES / f"{n}.yaml"), policy, TODAY))
        for n in NAMES
    ]
    md = render_register(items, fmt="md", today=TODAY)
    assert "3 record(s)" in md
    assert "2026-09-01 (overdue)" in md
    csv_text = render_register(items, fmt="csv", today=TODAY)
    lines = csv_text.strip().splitlines()
    assert lines[0] == ",".join(REGISTER_COLUMNS)
    assert len(lines) == 4


def test_example_register_snapshot(policy: Policy) -> None:
    items = [
        (p.relative_to(ROOT).as_posix(), assess(load_record(p), policy, TODAY))
        for p in sorted(EXAMPLES.glob("*.yaml"))
    ]
    rendered = render_register(items, fmt="md", today=TODAY)
    snapshot = CARDS / "register.md"
    if UPDATE:
        snapshot.write_text(rendered, encoding="utf-8")
    assert rendered == Path(snapshot).read_text(encoding="utf-8")
