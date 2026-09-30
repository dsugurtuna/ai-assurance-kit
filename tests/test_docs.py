"""Docs that are generated from code must match the code."""

from __future__ import annotations

import io
import re

import pytest

from ai_assurance_kit.docs import CROSSWALK_BEGIN, CROSSWALK_END, crosswalk_table, rules_markdown
from ai_assurance_kit.sources import AI_PLAYBOOK_PRINCIPLES, NIST_FUNCTIONS
from tests.conftest import ROOT

DOCS = ROOT / "docs"


def test_rules_reference_is_current() -> None:
    assert (DOCS / "RULES.md").read_text(encoding="utf-8") == rules_markdown(), (
        "run: aiak rules --format md > docs/RULES.md"
    )


def test_crosswalk_checks_table_is_current() -> None:
    text = (DOCS / "CROSSWALK.md").read_text(encoding="utf-8")
    start, end = text.index(CROSSWALK_BEGIN), text.index(CROSSWALK_END) + len(CROSSWALK_END)
    assert text[start:end] + "\n" == crosswalk_table(), (
        "replace the generated block with: aiak rules --format crosswalk"
    )


def test_crosswalk_lists_all_playbook_principles_and_nist_functions() -> None:
    text = (DOCS / "CROSSWALK.md").read_text(encoding="utf-8")
    for title in AI_PLAYBOOK_PRINCIPLES.values():
        assert title in text, title
    for function in NIST_FUNCTIONS:
        assert function in text


def test_readme_has_disclaimer_and_footer() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "Unofficial" in readme[:1500]
    assert "not government guidance" in readme.lower()
    assert readme.rstrip().endswith(
        "Personal project by [Ugur Tuna](https://github.com/dsugurtuna). Not affiliated with or "
        "endorsed by any employer."
    )


def test_readme_quickstart_commands_exist() -> None:
    from ai_assurance_kit.cli import build_parser

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    commands = set(re.findall(r"^aiak (\w+)", readme, flags=re.MULTILINE))
    assert {"init", "check", "render", "diff", "register"} <= commands
    known = set(build_parser()._subparsers._group_actions[0].choices)  # type: ignore[union-attr]
    assert commands <= known


def test_docs_do_not_claim_compliance() -> None:
    banned = re.compile(r"\b(compliant with|certif(ies|ied)|ensures compliance|guarantees)\b", re.I)
    for path in [ROOT / "README.md", *DOCS.glob("*.md")]:
        for line in path.read_text(encoding="utf-8").splitlines():
            if banned.search(line):
                assert "not" in line.lower() or "does not" in line.lower(), f"{path.name}: {line}"


def test_readme_real_output_is_real(monkeypatch: pytest.MonkeyPatch) -> None:
    # The README quotes the output of one command as "Real output". It must be exactly that.
    from ai_assurance_kit.cli import main

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    found = re.search(r"Real output of `aiak ([^`]+)`:\n\n```text\n(.*?)```", readme, re.S)
    assert found, "the README should quote a real command's output"
    argv, quoted = found.group(1).split(), found.group(2)
    monkeypatch.chdir(ROOT)
    out = io.StringIO()
    main(argv, stdout=out)
    assert out.getvalue() == quoted
