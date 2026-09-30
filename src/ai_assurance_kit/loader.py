"""Load AI use records from YAML or JSON files and report problems in plain language."""

from __future__ import annotations

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


def read_mapping(path: Path) -> dict[str, Any]:
    """Read a YAML or JSON file that must contain a mapping at the top level."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise RecordError(path, [Problem("", f"cannot read file ({exc.strerror})")]) from exc
    try:
        data = yaml.safe_load(text)  # JSON is a subset of YAML 1.2 for our purposes
    except yaml.YAMLError as exc:
        raise RecordError(path, [Problem("", f"not valid YAML: {exc}")]) from exc
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
    """Expand files and directories (non-recursive) into a sorted list of record files."""
    found: list[Path] = []
    for raw in paths:
        p = Path(raw)
        if p.is_dir():
            found.extend(
                sorted(c for c in p.iterdir() if c.is_file() and c.suffix in RECORD_SUFFIXES)
            )
        else:
            found.append(p)
    return found
