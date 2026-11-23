"""Validate real published GOV.UK ATRS examples alongside synthetic examples."""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import pytest

from ai_assurance_kit.checks import run_checks
from ai_assurance_kit.levels import assess_level
from ai_assurance_kit.loader import load_record
from ai_assurance_kit.policy import load_policy
from ai_assurance_kit.render import render_card
from tests.conftest import ROOT

PUBLISHED_DIR = ROOT / "examples" / "published-atrs"
PUBLISHED_FILES = sorted(PUBLISHED_DIR.glob("*.yaml"))
TODAY = dt.date(2026, 11, 22)


def test_three_published_atrs_records_exist() -> None:
    assert [p.name for p in PUBLISHED_FILES] == [
        "cabinet-office-assist.yaml",
        "cqc-risk-categorisation.yaml",
        "ofsted-social-care-writing-assistant.yaml",
    ]


@pytest.mark.parametrize("path", PUBLISHED_FILES, ids=lambda p: p.name)
def test_published_atrs_records_load_check_and_render(path: Path) -> None:
    record = load_record(path)
    policy = load_policy()
    result = assess_level(record, policy)
    findings = run_checks(record, policy, today=TODAY)
    card_md = render_card(record, policy=policy, fmt="md", today=TODAY)
    card_html = render_card(record, policy=policy, fmt="html", today=TODAY)

    assert record.transparency.record_url is not None
    assert record.transparency.record_url.startswith(
        "https://www.gov.uk/algorithmic-transparency-records/"
    )
    assert result.level.id in {lv.id for lv in policy.levels}
    assert record.title in card_md
    assert "Unofficial" in card_html
    assert isinstance(findings, list)


def test_published_atrs_surface_realistic_gaps() -> None:
    cqc = load_record(PUBLISHED_DIR / "cqc-risk-categorisation.yaml")
    ofsted = load_record(PUBLISHED_DIR / "ofsted-social-care-writing-assistant.yaml")
    assist = load_record(PUBLISHED_DIR / "cabinet-office-assist.yaml")

    policy = load_policy()
    cqc_ids = {f.rule.id for f in run_checks(cqc, policy, today=TODAY)}
    assist_ids = {f.rule.id for f in run_checks(assist, policy, today=TODAY)}
    ofsted_ids = {f.rule.id for f in run_checks(ofsted, policy, today=TODAY)}

    # Live records without a separate maintainer or assurer surface governance prompts cleanly.
    assert "AIAK-ROLE-003" in cqc_ids
    assert "AIAK-ROLE-002" in assist_ids
    # Retired Ofsted record skips live-only maintainer/review rules cleanly.
    assert "AIAK-ROLE-003" not in ofsted_ids
