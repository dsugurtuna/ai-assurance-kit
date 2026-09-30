from __future__ import annotations

import io
import json
import os
from pathlib import Path

import pytest
import yaml

from ai_assurance_kit.cli import main
from tests.conftest import (
    CLEAN,
    EXAMPLES,
    ROOT,
    assert_markdown_contains_text_safely,
    hostile_data,
)

CHATBOT = str(EXAMPLES / "service-chatbot.yaml")
NOTES = str(EXAMPLES / "meeting-notes-summariser.yaml")
GRANT_V1 = str(EXAMPLES / "history" / "grant-triage.v1.yaml")
GRANT = str(EXAMPLES / "grant-triage.yaml")
DAY = ["--today", "2026-09-30"]


def run(*argv: str) -> tuple[int, str]:
    out = io.StringIO()
    code = main(list(argv), stdout=out)
    return code, out.getvalue()


def test_version(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0
    assert "aiak 0.1.0" in capsys.readouterr().out


def test_help_carries_disclaimer(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit):
        main(["--help"])
    assert "Unofficial. Not government guidance." in capsys.readouterr().out


def test_init_then_check(tmp_path: Path) -> None:
    target = tmp_path / "record.yaml"
    code, out = run("init", str(target))
    assert code == 0
    assert target.exists()
    assert "aiak check" in out
    code, out = run("check", str(target), *DAY)
    assert code == 0
    assert "AIAK-META-001" in out


def test_init_refuses_to_overwrite(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    target = tmp_path / "record.yaml"
    target.write_text("keep me", encoding="utf-8")
    code, _ = run("init", str(target))
    assert code == 2
    assert target.read_text(encoding="utf-8") == "keep me"
    assert "--force" in capsys.readouterr().err
    code, _ = run("init", str(target), "--force")
    assert code == 0
    assert "schema_version" in target.read_text(encoding="utf-8")


def test_validate(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    code, out = run("validate", str(EXAMPLES))
    assert code == 0
    assert out.count(": valid") == 3
    bad = tmp_path / "bad.yaml"
    bad.write_text("id: x\n", encoding="utf-8")
    code, _ = run("validate", str(bad))
    assert code == 2
    assert "title: Field required" in capsys.readouterr().err


def test_validate_names_each_unreadable_file_and_carries_on(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    text = Path(GRANT).read_text(encoding="utf-8")
    bad_date = tmp_path / "a-bad-date.yaml"
    bad_date.write_text(text.replace("next_review: 2026-12-01", "next_review: 2026-13-01"))
    latin1 = tmp_path / "b-latin1.yaml"
    latin1.write_text(text.replace("Grant application", "Grant café"), encoding="latin-1")
    code, out = run("validate", str(bad_date), str(latin1), GRANT)
    assert code == 2
    assert "grant-triage.yaml: valid" in out  # the good file is still validated
    err = capsys.readouterr().err
    assert str(bad_date) in err
    assert str(latin1) in err


def test_policy_saved_by_windows_powershell_loads(tmp_path: Path) -> None:
    # Windows PowerShell 5 writes UTF-16 when output is redirected: aiak policy > policy.yaml
    _, text = run("policy")
    saved = tmp_path / "policy.yaml"
    saved.write_text(text, encoding="utf-16")
    code, out = run("policy", "--validate", str(saved))
    assert code == 0
    assert "valid policy" in out


def test_check_text_output() -> None:
    code, out = run("check", CHATBOT, *DAY)
    assert code == 0
    assert out.startswith("Unofficial. Not government guidance.")
    assert "Level: Use-specific review" in out
    assert "2 high, 4 warning, 2 info" in out
    assert "Why:" not in out


def test_check_explain_shows_rationale_and_sources() -> None:
    _, out = run("check", CHATBOT, *DAY, "--explain")
    assert "Why: The AQuA Book" in out
    assert (
        "See: The AQuA Book: Roles and responsibilities <https://www.gov.uk/guidance/the-aqua-book>"
        in out
    )


@pytest.mark.parametrize(
    ("path", "threshold", "expected"),
    [
        (CHATBOT, "high", 1),
        (NOTES, "high", 0),
        (NOTES, "warning", 1),
        (NOTES, "info", 1),
    ],
)
def test_check_fail_on(path: str, threshold: str, expected: int) -> None:
    code, _ = run("check", path, *DAY, "--fail-on", threshold)
    assert code == expected


def test_check_json() -> None:
    code, out = run("check", str(EXAMPLES), *DAY, "--format", "json")
    assert code == 0
    payload = json.loads(out)
    assert [p["record_id"] for p in payload] == [
        "grant-application-triage",
        "meeting-notes-summariser",
        "service-helpline-chatbot",
    ]
    grant = payload[0]
    assert grant["level"]["id"] == "senior_specialist"
    assert grant["counts"] == {"high": 2, "warning": 2, "info": 0}
    assert grant["findings"][0]["sources"]


def test_check_invalid_file_exits_2(tmp_path: Path) -> None:
    bad = tmp_path / "bad.yaml"
    bad.write_text("[]", encoding="utf-8")
    code, _ = run("check", str(bad))
    assert code == 2


def test_check_with_custom_policy(tmp_path: Path) -> None:
    code, policy_text = run("policy")
    assert code == 0
    custom = tmp_path / "policy.yaml"
    custom.write_text(
        policy_text.replace("disabled_rules: []", "disabled_rules: [AIAK-REV-001]"),
        encoding="utf-8",
    )
    code, out = run("check", NOTES, *DAY, "--policy", str(custom), "--fail-on", "info")
    assert code == 0
    assert "0 high, 0 warning, 0 info" in out


def test_check_bad_policy_exits_2(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    bad = tmp_path / "policy.yaml"
    bad.write_text("policy_name: x\n", encoding="utf-8")
    code, _ = run("check", NOTES, "--policy", str(bad))
    assert code == 2
    assert "not a valid policy" in capsys.readouterr().err


def test_bad_date_is_a_usage_error() -> None:
    with pytest.raises(SystemExit) as exc:
        main(["check", NOTES, "--today", "30/09/2026"])
    assert exc.value.code == 2


def test_diff_outputs() -> None:
    code, out = run("diff", GRANT_V1, GRANT)
    assert code == 0
    # 11 since v1 -> v2 also adds applicants to the groups relying on the outputs.
    assert "Material changes (11): re-review suggested" in out
    code, out = run("diff", GRANT_V1, GRANT, "--format", "md")
    assert "## Material changes (re-review suggested)" in out
    code, out = run("diff", GRANT_V1, GRANT, "--format", "json")
    assert json.loads(out)["needs_review"] is True
    code, _ = run("diff", GRANT_V1, GRANT, "--fail-on-material")
    assert code == 1
    code, out = run("diff", GRANT, GRANT, "--fail-on-material")
    assert code == 0
    assert "No material changes" in out


def test_diff_markdown_escapes_record_text(tmp_path: Path) -> None:
    old, new = tmp_path / "old.yaml", tmp_path / "new.yaml"
    old.write_text(yaml.safe_dump(CLEAN), encoding="utf-8")
    new.write_text(yaml.safe_dump(hostile_data("a|b\nMARK<script>x</script>")), encoding="utf-8")
    code, out = run("diff", str(old), str(new), "--format", "md")
    assert code == 0
    assert "## Material changes" in out
    assert_markdown_contains_text_safely(out, "MARK")


def test_render_to_files(tmp_path: Path) -> None:
    html = tmp_path / "card.html"
    code, _ = run("render", CHATBOT, *DAY, "-o", str(html))
    assert code == 0
    assert html.read_text(encoding="utf-8").startswith("<!doctype html>")
    md = tmp_path / "card.md"
    code, _ = run("render", CHATBOT, *DAY, "-o", str(md))
    assert md.read_text(encoding="utf-8").startswith("# Permit service helpline chatbot")
    code, out = run("render", CHATBOT, *DAY, "--format", "html")
    assert "<!doctype html>" in out


def test_register(tmp_path: Path) -> None:
    code, out = run("register", str(EXAMPLES), *DAY)
    assert code == 0
    assert "| Record |" in out
    csv_path = tmp_path / "register.csv"
    code, _ = run("register", str(EXAMPLES), *DAY, "-o", str(csv_path))
    assert csv_path.read_text(encoding="utf-8").startswith("id,title,status")


def test_register_warns_on_duplicate_ids(capsys: pytest.CaptureFixture[str]) -> None:
    code, _ = run("register", GRANT, GRANT_V1, *DAY)
    assert code == 0
    assert "appears more than once" in capsys.readouterr().err


@pytest.mark.parametrize(
    "argv",
    [
        ["check", "--fail-on", "high"],  # a CI gate must not pass because nothing was checked
        ["validate"],
        ["register"],
    ],
)
def test_directory_with_no_records_is_an_error(
    argv: list[str], tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    (tmp_path / "notes.txt").write_text("not a record", encoding="utf-8")
    command, *options = argv
    code, _ = run(command, str(tmp_path), *options)
    assert code == 2
    assert "no record files" in capsys.readouterr().err


def test_directory_scan_ignores_suffix_case(tmp_path: Path) -> None:
    # Windows file names are case-insensitive, and RECORD.YAML is a common spelling there.
    (tmp_path / "GRANT.YAML").write_text(Path(GRANT).read_text("utf-8"), encoding="utf-8")
    code, out = run("validate", str(tmp_path))
    assert code == 0
    assert "GRANT.YAML: valid" in out


def test_unexpanded_wildcards_are_expanded(capsys: pytest.CaptureFixture[str]) -> None:
    # cmd.exe and PowerShell pass `records\*.yaml` to the program unexpanded; POSIX shells do
    # the same when the pattern is quoted.
    code, out = run("validate", str(EXAMPLES / "*.yaml"))
    assert code == 0
    assert out.count(": valid") == 3
    code, _ = run("validate", str(EXAMPLES / "*.nothing"))
    assert code == 2
    assert "no files match" in capsys.readouterr().err


@pytest.mark.parametrize(
    "argv",
    [
        ["render", CHATBOT, "-o", "{missing}/card.html"],
        ["register", str(EXAMPLES), "-o", "{missing}/register.csv"],
        ["schema", "-o", "{missing}/schema.json"],
        ["init", "{missing}/record.yaml"],
    ],
)
def test_unwritable_output_is_a_usage_error_not_a_crash(
    argv: list[str], tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # An unhandled exception exits 1, which the CLI reserves for "a --fail-on threshold was met".
    missing = tmp_path / "no" / "such" / "dir"
    code, _ = run(*(a.replace("{missing}", str(missing)) for a in argv))
    assert code == 2
    assert "cannot write" in capsys.readouterr().err


def test_output_format_from_extension_ignores_case(tmp_path: Path) -> None:
    card = tmp_path / "CARD.HTML"
    run("render", CHATBOT, *DAY, "-o", str(card))
    assert card.read_text(encoding="utf-8").startswith("<!doctype html>")
    register = tmp_path / "REGISTER.CSV"
    run("register", str(EXAMPLES), *DAY, "-o", str(register))
    assert register.read_text(encoding="utf-8").startswith("id,title,status")


def test_schema_command(tmp_path: Path) -> None:
    code, out = run("schema")
    assert code == 0
    assert json.loads(out)["title"] == "AI use record"
    target = tmp_path / "s.json"
    run("schema", "-o", str(target))
    assert json.loads(target.read_text(encoding="utf-8"))["$schema"].endswith("2020-12/schema")


def test_rules_command() -> None:
    code, out = run("rules")
    assert code == 0
    assert "AIAK-ROLE-001" in out
    _, md = run("rules", "--format", "md")
    assert md == (ROOT / "docs" / "RULES.md").read_text(encoding="utf-8")


def test_policy_command(tmp_path: Path) -> None:
    code, out = run("policy", "--features")
    assert code == 0
    assert "significant_public_effect" in out
    example = tmp_path / "p.yaml"
    _, text = run("policy")
    example.write_text(text, encoding="utf-8")
    code, out = run("policy", "--validate", str(example))
    assert code == 0
    assert "valid policy" in out


@pytest.mark.parametrize(
    ("old", "new"),
    [
        ("    equals: autonomous", "    equals: autonomus"),  # trigger that could never fire
        ("disabled_rules: []", "disabled_rules: [AIAK-TRANS-01]"),  # rule id that does not exist
    ],
)
def test_policy_validate_catches_mistakes_check_would_hit(
    old: str, new: str, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _, text = run("policy")
    assert old in text
    custom = tmp_path / "p.yaml"
    custom.write_text(text.replace(old, new), encoding="utf-8")
    code, _ = run("policy", "--validate", str(custom))
    assert code == 2
    assert "not a valid policy" in capsys.readouterr().err


def test_cli_runs_as_module_entry_point() -> None:
    # The console script is declared in pyproject.toml; check the target exists and is callable.
    from ai_assurance_kit import cli

    assert callable(cli.main)
    assert os.path.exists(Path(cli.__file__))
