"""Load AI use records from YAML or JSON files and report problems in plain language."""

from __future__ import annotations

import glob
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from ai_assurance_kit.schema import AIUseRecord

RECORD_SUFFIXES = (".yaml", ".yml", ".json")


@dataclass(frozen=True)
class Problem:
    """One validation problem, located by a dotted path into the record."""

    location: str
    message: str

    def __str__(self) -> str:
        return f"{self.location}: {self.message}" if self.location else self.message


class RecordError(Exception):
    """Raised when a file cannot be read or does not describe a valid record."""

    def __init__(self, path: Path, problems: list[Problem], kind: str = "AI use record") -> None:
        self.path = path
        self.problems = problems
        lines = "\n".join(f"  - {p}" for p in problems)
        super().__init__(f"{path}: not a valid {kind}\n{lines}")


def _location(loc: tuple[int | str, ...]) -> str:
    parts: list[str] = []
    for item in loc:
        if isinstance(item, int):
            parts.append(f"[{item}]")
        else:
            parts.append(("." if parts else "") + item)
    return "".join(parts)


def problems_from(error: ValidationError) -> list[Problem]:
    """Turn a pydantic ValidationError into short, located messages."""
    out: list[Problem] = []
    for err in error.errors(include_url=False):
        message = str(err["msg"])
        if message.startswith("Value error, "):
            message = message[len("Value error, ") :]
        if err["type"] == "extra_forbidden":
            message = "unknown field (check the spelling against the schema)"
        out.append(Problem(_location(tuple(err["loc"])), message))
    return out


class _StrictLoader(yaml.SafeLoader):
    """PyYAML's safe loader, with two silent behaviours turned into errors.

    * A repeated key: PyYAML keeps the last value, so ``personal_data: true`` followed later by
      ``personal_data: false`` would quietly say "no personal data". Like an unknown field, it
      is an error.
    * An impossible date such as ``2026-13-01``: PyYAML raises a bare ValueError with no file
      or line. It becomes a YAML error with its location.
    """

    def construct_mapping(self, node: yaml.MappingNode, deep: bool = False) -> dict[Any, Any]:
        seen: set[Any] = set()
        for key_node, _ in node.value:
            if key_node.tag == "tag:yaml.org,2002:merge":
                continue  # "<<" merges may legitimately be overridden by explicit keys
            key = self.construct_object(key_node, deep=deep)
            try:
                duplicate = key in seen
            except TypeError:  # an unhashable key; the base class reports it
                continue
            if duplicate:
                raise yaml.constructor.ConstructorError(
                    None, None, f"found duplicate key {key!r}", key_node.start_mark
                )
            seen.add(key)
        return super().construct_mapping(node, deep=deep)

    def construct_yaml_timestamp(self, node: yaml.ScalarNode) -> Any:
        try:
            return super().construct_yaml_timestamp(node)
        except ValueError as exc:
            raise yaml.constructor.ConstructorError(
                None, None, f"{node.value!r} is not a valid date ({exc})", node.start_mark
            ) from exc


_StrictLoader.add_constructor("tag:yaml.org,2002:timestamp", _StrictLoader.construct_yaml_timestamp)


def _yaml_problem(exc: yaml.YAMLError) -> str:
    """One readable line: what is wrong and where, without PyYAML's '<byte string>' excerpt."""
    if isinstance(exc, yaml.reader.ReaderError):
        return (
            "not readable as UTF-8 or UTF-16 text "
            f"({exc.reason} at byte {exc.position}); save the file as UTF-8"
        )
    if isinstance(exc, yaml.MarkedYAMLError) and exc.problem_mark is not None:
        mark = exc.problem_mark
        detail = "; ".join(x for x in (exc.problem, exc.context) if x)
        return f"not valid YAML at line {mark.line + 1}, column {mark.column + 1}: {detail}"
    return "not valid YAML: " + " ".join(str(exc).split())


def read_yaml(path: Path, kind: str = "AI use record") -> Any:
    """Parse a YAML or JSON file, reporting any problem as a RecordError naming the file.

    The file is read as bytes so the parser can detect UTF-8 (with or without a byte-order
    mark) and UTF-16 with a byte-order mark, which Windows tools often write.
    """
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise RecordError(path, [Problem("", f"cannot read file ({exc.strerror})")], kind) from exc
    try:
        # JSON is a subset of YAML 1.2 for our purposes.
        return yaml.load(raw, Loader=_StrictLoader)  # a SafeLoader subclass: no arbitrary objects
    except yaml.YAMLError as exc:
        raise RecordError(path, [Problem("", _yaml_problem(exc))], kind) from exc


def read_mapping(path: Path) -> dict[str, Any]:
    """Read a YAML or JSON file that must contain a mapping at the top level."""
    data = read_yaml(path)
    if not isinstance(data, dict):
        raise RecordError(path, [Problem("", "the file must contain a mapping of fields")])
    return data


def parse_record(data: dict[str, Any], path: Path | None = None) -> AIUseRecord:
    """Validate a mapping as an AI use record."""
    try:
        return AIUseRecord.model_validate(data)
    except ValidationError as exc:
        raise RecordError(path or Path("<record>"), problems_from(exc)) from exc


def load_record(path: str | Path) -> AIUseRecord:
    """Load and validate one record file."""
    p = Path(path)
    return parse_record(read_mapping(p), p)


def find_record_files(paths: list[str | Path]) -> list[Path]:
    """Expand files, directories (non-recursive) and wildcards into a list of record files.

    Wildcards such as ``records/*.yaml`` are expanded here because Windows shells pass them to
    the program unexpanded. A pattern or directory that matches nothing adds nothing.
    """
    found: list[Path] = []
    for raw in paths:
        p = Path(raw)
        if p.is_dir():
            found.extend(
                sorted(
                    c for c in p.iterdir() if c.is_file() and c.suffix.lower() in RECORD_SUFFIXES
                )
            )
        elif is_wildcard(raw):
            found.extend(sorted(m for m in map(Path, glob.glob(str(raw))) if m.is_file()))
        else:
            found.append(p)
    return found


def is_wildcard(raw: str | Path) -> bool:
    """True for a path that does not exist and contains glob characters, such as *.yaml."""
    return not Path(raw).exists() and any(ch in str(raw) for ch in "*?[")
