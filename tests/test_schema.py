from __future__ import annotations

import copy
import json
from importlib import resources
from typing import Any

import jsonschema
import pytest
import yaml

from ai_assurance_kit.loader import RecordError, find_record_files, load_record, parse_record
from ai_assurance_kit.schema import AIUseRecord, json_schema
from tests.conftest import CLEAN, EXAMPLES, ROOT, set_path

EXAMPLE_FILES = sorted(EXAMPLES.glob("*.yaml")) + sorted((EXAMPLES / "history").glob("*.yaml"))


def _as_json(data: Any) -> Any:
    """YAML parses dates as date objects; JSON validators expect strings."""
    return json.loads(json.dumps(data, default=str))


def _problems(changes: dict[str, Any]) -> list[str]:
    data = copy.deepcopy(CLEAN)
    for path, value in changes.items():
        set_path(data, path, value)
    with pytest.raises(RecordError) as exc:
        parse_record(data)
    return [str(p) for p in exc.value.problems]


def test_there_are_four_example_files() -> None:
    assert len(EXAMPLE_FILES) == 4


@pytest.mark.parametrize("path", EXAMPLE_FILES, ids=lambda p: p.name)
def test_examples_are_valid(path: Any) -> None:
    record = load_record(path)
    assert isinstance(record, AIUseRecord)


def test_examples_are_marked_fictional() -> None:
    for path in EXAMPLE_FILES:
        assert "FICTIONAL EXAMPLE" in path.read_text(encoding="utf-8"), path


def test_init_template_is_valid() -> None:
    text = (
        resources.files("ai_assurance_kit")
        .joinpath("data", "record.template.yaml")
        .read_text(encoding="utf-8")
    )
    record = parse_record(yaml.safe_load(text))
    assert record.status.value == "proposed"


def test_clean_fixture_is_valid() -> None:
    assert parse_record(copy.deepcopy(CLEAN)).id == "clean-record"


def test_unknown_field_is_rejected_with_location() -> None:
    problems = _problems({"data.personal_date": True})
    assert any(p.startswith("data.personal_date: unknown field") for p in problems)


def test_special_category_implies_personal_data() -> None:
    problems = _problems({"data.special_category_data": True, "data.personal_data": False})
    assert any("special category data is a kind of personal data" in p for p in problems)


def test_unknown_control_reference() -> None:
    risks = copy.deepcopy(CLEAN["risks"])
    risks[0]["controls"] = ["C9"]
    problems = _problems({"risks": risks})
    assert any("R1 refers to unknown controls: C9" in p for p in problems)


def test_duplicate_risk_ids() -> None:
    risks = copy.deepcopy(CLEAN["risks"]) * 2
    assert any("duplicate risk ids: R1" in p for p in _problems({"risks": risks}))


def test_duplicate_connector_names() -> None:
    conns = [{"name": "Docs", "permissions": ["read"]}] * 2
    assert any(
        "duplicate connector names: Docs" in p for p in _problems({"access.connectors": conns})
    )


@pytest.mark.parametrize(
    ("path", "value"),
    [
        ("id", "Not A Slug"),
        ("status", "deployed"),
        ("actions.mode", "fully_automatic"),
        ("reliance.decision_role", "verdict"),
        ("data.categories", []),
        ("reliance.scale.users", -1),
    ],
)
def test_invalid_values(path: str, value: Any) -> None:
    assert any(p.startswith(path) for p in _problems({path: value}))


@pytest.mark.parametrize("value", [0, 6])
def test_likelihood_must_be_1_to_5(value: int) -> None:
    risks = copy.deepcopy(CLEAN["risks"])
    risks[0]["likelihood"] = value
    assert any(p.startswith("risks[0].likelihood") for p in _problems({"risks": risks}))


def test_load_record_reports_bad_yaml(tmp_path: Any) -> None:
    bad = tmp_path / "bad.yaml"
    bad.write_text("id: [unclosed", encoding="utf-8")
    with pytest.raises(RecordError, match="not valid YAML"):
        load_record(bad)


def test_load_record_needs_a_mapping(tmp_path: Any) -> None:
    bad = tmp_path / "list.yaml"
    bad.write_text("- a\n- b\n", encoding="utf-8")
    with pytest.raises(RecordError, match="mapping"):
        load_record(bad)


def test_load_record_missing_file(tmp_path: Any) -> None:
    with pytest.raises(RecordError, match="cannot read file"):
        load_record(tmp_path / "missing.yaml")


GRANT_TEXT = (EXAMPLES / "grant-triage.yaml").read_text(encoding="utf-8")


def test_duplicate_keys_are_an_error_not_a_silent_overwrite(tmp_path: Any) -> None:
    # YAML parsers usually keep the last value, so this record would quietly say that no
    # personal data is involved. Like an unknown field, a repeated key must be an error.
    text = GRANT_TEXT.replace("  personal_data: true\n", "  personal_data: true\n  retention: x\n")
    text = text.replace("  special_category_data: false\n", "  personal_data: false\n", 1)
    path = tmp_path / "dupe.yaml"
    path.write_text(text, encoding="utf-8")
    with pytest.raises(RecordError, match=r"line \d+.*duplicate key 'personal_data'") as exc:
        load_record(path)
    assert str(path) in str(exc.value)


def test_invalid_date_is_a_record_error_with_its_location(tmp_path: Any) -> None:
    path = tmp_path / "date.yaml"
    path.write_text(GRANT_TEXT.replace("next_review: 2026-12-01", "next_review: 2026-13-01"))
    with pytest.raises(RecordError, match=r"line \d+.*2026-13-01"):
        load_record(path)


def test_yaml_syntax_error_is_one_located_line(tmp_path: Any) -> None:
    bad = tmp_path / "bad.yaml"
    bad.write_text("id: [unclosed\n", encoding="utf-8")
    with pytest.raises(RecordError) as exc:
        load_record(bad)
    (problem,) = exc.value.problems
    assert "\n" not in str(problem)
    assert "<unicode string>" not in str(problem)
    assert "line 2, column 1" in str(problem)


@pytest.mark.parametrize("encoding", ["utf-8-sig", "utf-16"])
def test_windows_encodings_load(encoding: str, tmp_path: Any) -> None:
    # Windows editors often add a byte-order mark, and Windows PowerShell 5 writes UTF-16 when
    # output is redirected to a file (for example `aiak policy > my-policy.yaml`).
    path = tmp_path / "record.yaml"
    path.write_text(GRANT_TEXT, encoding=encoding)
    assert load_record(path).id == "grant-application-triage"


def test_text_that_is_not_utf8_is_a_record_error(tmp_path: Any) -> None:
    path = tmp_path / "latin1.yaml"
    path.write_text(GRANT_TEXT.replace("Grant application triage", "Grant café"), "latin-1")
    with pytest.raises(RecordError, match="UTF-8"):
        load_record(path)


def test_find_record_files_is_not_recursive() -> None:
    found = find_record_files([EXAMPLES])
    assert [p.name for p in found] == [
        "grant-triage.yaml",
        "meeting-notes-summariser.yaml",
        "service-chatbot.yaml",
    ]


def test_committed_json_schema_is_current() -> None:
    committed = json.loads((ROOT / "schema" / "ai-use-record.schema.json").read_text("utf-8"))
    assert committed == json_schema(), "run: aiak schema -o schema/ai-use-record.schema.json"


@pytest.mark.parametrize("path", EXAMPLE_FILES, ids=lambda p: p.name)
def test_json_schema_accepts_examples(path: Any) -> None:
    data = _as_json(yaml.safe_load(path.read_text(encoding="utf-8")))
    jsonschema.Draft202012Validator(json_schema()).validate(data)


def test_json_schema_rejects_unknown_field() -> None:
    data = _as_json(copy.deepcopy(CLEAN))
    data["surprise"] = True
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.Draft202012Validator(json_schema()).validate(data)


def test_json_schema_is_a_valid_2020_12_schema() -> None:
    jsonschema.Draft202012Validator.check_schema(json_schema())
