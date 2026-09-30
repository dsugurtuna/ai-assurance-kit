"""The ``aiak`` command line.

Exit codes: 0 success; 1 a ``--fail-on`` threshold was met (or material changes with
``--fail-on-material``); 2 invalid input or usage.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import textwrap
from collections.abc import Sequence
from importlib import resources
from pathlib import Path
from typing import TextIO

from ai_assurance_kit import __version__
from ai_assurance_kit.checks import all_rules, meets_threshold
from ai_assurance_kit.checks.engine import Severity
from ai_assurance_kit.diff import DiffReport, diff_records
from ai_assurance_kit.docs import crosswalk_table, rules_markdown
from ai_assurance_kit.levels import FEATURES
from ai_assurance_kit.loader import RECORD_SUFFIXES, RecordError, find_record_files, load_record
from ai_assurance_kit.policy import Policy, example_policy_text, load_policy
from ai_assurance_kit.register import RegisterFormat, render_register
from ai_assurance_kit.render import (
    DISCLAIMER,
    Assessment,
    CardFormat,
    assess,
    md_code,
    md_text,
    render_card,
)
from ai_assurance_kit.schema import json_schema

EXIT_OK, EXIT_THRESHOLD, EXIT_INVALID = 0, 1, 2
WIDTH = 100


def _date(value: str) -> dt.date:
    try:
        return dt.date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"not an ISO date (YYYY-MM-DD): {value}") from exc


def _write(path: Path, text: str) -> bool:
    """Write a file, reporting failure as a usage problem rather than a traceback.

    An unhandled exception would exit 1, which this CLI reserves for a met --fail-on threshold.
    """
    try:
        path.write_text(text, encoding="utf-8")
    except OSError as exc:
        print(f"error: cannot write {path} ({exc.strerror})", file=sys.stderr)
        return False
    return True


def _emit(text: str, output: str | None, stdout: TextIO) -> int:
    if output:
        if not _write(Path(output), text):
            return EXIT_INVALID
        print(f"wrote {output}", file=sys.stderr)
    else:
        stdout.write(text if text.endswith("\n") else text + "\n")
    return EXIT_OK


def _has_suffix(output: str | None, *suffixes: str) -> bool:
    return bool(output) and Path(str(output)).suffix.lower() in suffixes


def _record_files(paths: Sequence[str]) -> tuple[list[Path], bool]:
    """Expand files and directories. A directory with no record files is an input error.

    Otherwise a mistyped or empty directory would be "checked" with nothing in it, and a CI
    gate such as `aiak check records/ --fail-on high` would pass.
    """
    files: list[Path] = []
    ok = True
    for raw in paths:
        found = find_record_files([raw])
        if not found:
            suffixes = ", ".join(RECORD_SUFFIXES)
            print(f"{raw}: no record files ({suffixes}) in this directory", file=sys.stderr)
            ok = False
        files.extend(found)
    return files, ok


def _wrap(text: str, indent: str, first: str | None = None) -> str:
    return textwrap.fill(
        text,
        width=WIDTH,
        initial_indent=indent if first is None else first,
        subsequent_indent=indent,
        break_long_words=False,
        break_on_hyphens=False,
    )


# --------------------------------------------------------------------------- commands


def cmd_init(args: argparse.Namespace, out: TextIO) -> int:
    target = Path(args.path)
    if target.exists() and not args.force:
        print(f"{target} already exists; use --force to overwrite", file=sys.stderr)
        return EXIT_INVALID
    template = (
        resources.files("ai_assurance_kit")
        .joinpath("data", "record.template.yaml")
        .read_text(encoding="utf-8")
    )
    if not _write(target, template):
        return EXIT_INVALID
    out.write(f"wrote {target}. Fill it in, then run: aiak check {target}\n")
    return EXIT_OK


def cmd_validate(args: argparse.Namespace, out: TextIO) -> int:
    paths, found_all = _record_files(args.files)
    status = EXIT_OK if found_all else EXIT_INVALID
    for path in paths:
        try:
            record = load_record(path)
        except RecordError as exc:
            print(str(exc), file=sys.stderr)
            status = EXIT_INVALID
            continue
        out.write(f"{path}: valid ({record.id}, schema {record.schema_version})\n")
    return status


def _text_report(path: Path, a: Assessment, explain: bool) -> str:
    r = a.record
    lines = [f"{path}", f"  {r.title}  [status: {r.status.value}]"]
    lines.append(f"  Level: {a.level.level.label}  (policy: {a.level.policy_name})")
    for reason in a.level.reasons:
        lines.append(
            _wrap(f"{reason.level.label}: {reason.reason} ({reason.condition})", " " * 6, "    - ")
        )
    c = a.counts
    lines.append(
        f"  Prompts for human judgement, not verdicts: {c['high']} high, "
        f"{c['warning']} warning, {c['info']} info"
    )
    for f in a.findings:
        lines.append(f"    {f.severity.value.upper():<8}{f.rule.id}  {f.rule.title}")
        lines.append(_wrap(f.message, " " * 12))
        if explain:
            lines.append(_wrap(f"Why: {f.rule.rationale}", " " * 12))
            for ref in f.rule.refs:
                lines.append(f"{' ' * 12}See: {ref.label()} <{ref.doc.url}>")  # URLs unwrapped
    if not a.findings:
        lines.append("    No checks fired (that is not the same as assured).")
    return "\n".join(lines) + "\n"


def cmd_check(args: argparse.Namespace, out: TextIO) -> int:
    policy = load_policy(args.policy)
    today = args.today or dt.date.today()
    results: list[tuple[Path, Assessment]] = []
    paths, found_all = _record_files(args.files)
    status = EXIT_OK if found_all else EXIT_INVALID
    for path in paths:
        try:
            results.append((path, assess(load_record(path), policy, today)))
        except RecordError as exc:
            print(str(exc), file=sys.stderr)
            status = EXIT_INVALID
    if args.format == "json":
        payload = [
            {
                "file": str(path),
                "record_id": a.record.id,
                "status": a.record.status.value,
                "checked_as_at": a.today.isoformat(),
                "level": {
                    "id": a.level.level.id,
                    "label": a.level.level.label,
                    "policy": a.level.policy_name,
                    "reasons": [
                        {"level": x.level.id, "reason": x.reason, "condition": x.condition}
                        for x in a.level.reasons
                    ],
                },
                "counts": a.counts,
                "findings": [f.to_dict() for f in a.findings],
            }
            for path, a in results
        ]
        out.write(json.dumps(payload, indent=2) + "\n")
    else:
        out.write(f"{DISCLAIMER}\n\n")
        out.write("\n".join(_text_report(p, a, args.explain) for p, a in results))
    if status == EXIT_OK and args.fail_on:
        threshold = Severity(args.fail_on)
        if any(meets_threshold(a.findings, threshold) for _, a in results):
            return EXIT_THRESHOLD
    return status


def _diff_text(report: DiffReport) -> str:
    lines = [f"Comparing {report.old_label} -> {report.new_label}"]
    if report.material:
        lines.append(f"Material changes ({len(report.material)}): re-review suggested")
        for c in report.material:
            lines.append(f"  * {c.summary}")
            lines.append(_wrap(f"why: {c.reason}", "      "))
    else:
        lines.append("No material changes found by the kit's change rules.")
    if report.other:
        lines.append(f"Other changes ({len(report.other)}):")
        for c in report.other:
            lines.append(f"  - {c.path}: {c.describe()}")
    return "\n".join(lines) + "\n"


def _diff_markdown(report: DiffReport) -> str:
    old, new = md_code(report.old_label), md_code(report.new_label)
    lines = [f"# Changes: {old} to {new}", "", f"> {DISCLAIMER}", ""]
    if report.material:
        lines += ["## Material changes (re-review suggested)", "", "| Change | Why it matters |"]
        lines += ["|---|---|"]
        lines += [f"| {md_text(c.summary)} | {md_text(c.reason)} |" for c in report.material]
    else:
        lines += ["No material changes found by the kit's change rules."]
    if report.other:
        lines += ["", "## Other changes", ""]
        lines += [f"- {md_code(c.path)}: {md_text(c.describe())}" for c in report.other]
    return "\n".join(lines) + "\n"


def cmd_diff(args: argparse.Namespace, out: TextIO) -> int:
    policy = load_policy(args.policy)
    old, new = load_record(args.old), load_record(args.new)
    report = diff_records(old, new, policy, args.old, args.new)
    if args.format == "json":
        out.write(json.dumps(report.to_dict(), indent=2, default=str) + "\n")
    elif args.format == "md":
        out.write(_diff_markdown(report))
    else:
        out.write(_diff_text(report))
    if args.fail_on_material and report.needs_review:
        return EXIT_THRESHOLD
    return EXIT_OK


def cmd_render(args: argparse.Namespace, out: TextIO) -> int:
    policy = load_policy(args.policy)
    record = load_record(args.file)
    fmt: CardFormat = args.format or ("html" if _has_suffix(args.output, ".html", ".htm") else "md")
    text = render_card(
        record,
        policy,
        fmt=fmt,
        today=args.today,
        source=Path(args.file).as_posix(),
        redact_names=args.redact_names,
    )
    return _emit(text, args.output, out)


def cmd_register(args: argparse.Namespace, out: TextIO) -> int:
    policy = load_policy(args.policy)
    today = args.today or dt.date.today()
    items: list[tuple[str, Assessment]] = []
    paths, found_all = _record_files(args.paths)
    failed = not found_all
    for path in paths:
        try:
            items.append((path.as_posix(), assess(load_record(path), policy, today)))
        except RecordError as exc:
            print(str(exc), file=sys.stderr)
            failed = True
    if failed:
        return EXIT_INVALID
    ids = [a.record.id for _, a in items]
    for dup in sorted({i for i in ids if ids.count(i) > 1}):
        print(f"warning: record id '{dup}' appears more than once", file=sys.stderr)
    fmt: RegisterFormat = args.format or ("csv" if _has_suffix(args.output, ".csv") else "md")
    return _emit(render_register(items, fmt=fmt, today=today), args.output, out)


def cmd_schema(args: argparse.Namespace, out: TextIO) -> int:
    return _emit(json.dumps(json_schema(), indent=2) + "\n", args.output, out)


def cmd_rules(args: argparse.Namespace, out: TextIO) -> int:
    if args.format == "md":
        out.write(rules_markdown())
    elif args.format == "crosswalk":
        out.write(crosswalk_table())
    else:
        for rule in all_rules():
            out.write(f"{rule.id:<15}{rule.severity.value:<9}{rule.title}\n")
    return EXIT_OK


def cmd_policy(args: argparse.Namespace, out: TextIO) -> int:
    if args.features:
        for name, feat in FEATURES.items():
            out.write(f"{name:<27}{feat.description}\n")
        return EXIT_OK
    if args.validate:
        policy: Policy = load_policy(args.validate)
        out.write(f"{args.validate}: valid policy '{policy.policy_name}'\n")
        return EXIT_OK
    out.write(example_policy_text())
    return EXIT_OK


# --------------------------------------------------------------------------- parser


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="aiak",
        description=(
            "ai-assurance-kit: describe an AI use case as a structured record, run explainable "
            "checks, and render a one-page card."
        ),
        epilog=DISCLAIMER,
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True, metavar="COMMAND")

    def policy_opt(p: argparse.ArgumentParser) -> None:
        p.add_argument(
            "--policy", help="policy YAML (default: the bundled example policy; adapt it)"
        )

    def today_opt(p: argparse.ArgumentParser) -> None:
        p.add_argument(
            "--today",
            type=_date,
            help="assess as at this date (YYYY-MM-DD); default is today. Useful for "
            "reproducible output.",
        )

    p = sub.add_parser("init", help="write a starter record to fill in")
    p.add_argument("path", nargs="?", default="ai-use-record.yaml")
    p.add_argument("--force", action="store_true", help="overwrite an existing file")
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("validate", help="check files against the record schema only")
    p.add_argument("files", nargs="+", help="record files or directories")
    p.set_defaults(func=cmd_validate)

    p = sub.add_parser("check", help="validate, assess the level and run the checks")
    p.add_argument("files", nargs="+", help="record files or directories")
    policy_opt(p)
    today_opt(p)
    p.add_argument("--format", choices=["text", "json"], default="text")
    p.add_argument("--explain", action="store_true", help="show each rule's rationale and sources")
    p.add_argument(
        "--fail-on",
        choices=[s.value for s in Severity],
        help="exit 1 if any prompt is at or above this severity (for CI)",
    )
    p.set_defaults(func=cmd_check)

    p = sub.add_parser("diff", help="compare two versions of a record; flag material changes")
    p.add_argument("old")
    p.add_argument("new")
    policy_opt(p)
    p.add_argument("--format", choices=["text", "md", "json"], default="text")
    p.add_argument("--fail-on-material", action="store_true", help="exit 1 if re-review is due")
    p.set_defaults(func=cmd_diff)

    p = sub.add_parser("render", help="render a one-page card (Markdown or HTML)")
    p.add_argument("file")
    p.add_argument("--format", choices=["md", "html"], help="default: from -o extension, else md")
    p.add_argument("-o", "--output", help="write to this file instead of stdout")
    p.add_argument(
        "--redact-names", action="store_true", help="show role titles only, not personal names"
    )
    policy_opt(p)
    today_opt(p)
    p.set_defaults(func=cmd_render)

    p = sub.add_parser("register", help="build a portfolio register from many records")
    p.add_argument("paths", nargs="+", help="record files or directories (not recursive)")
    p.add_argument("--format", choices=["md", "csv"], help="default: from -o extension, else md")
    p.add_argument("-o", "--output")
    policy_opt(p)
    today_opt(p)
    p.set_defaults(func=cmd_register)

    p = sub.add_parser("schema", help="print the record JSON Schema")
    p.add_argument("-o", "--output")
    p.set_defaults(func=cmd_schema)

    p = sub.add_parser("rules", help="list the checks")
    p.add_argument("--format", choices=["text", "md", "crosswalk"], default="text")
    p.set_defaults(func=cmd_rules)

    p = sub.add_parser("policy", help="print the example policy, or list level features")
    group = p.add_mutually_exclusive_group()
    group.add_argument("--features", action="store_true", help="list features triggers can use")
    group.add_argument("--validate", metavar="FILE", help="validate a policy file")
    p.set_defaults(func=cmd_policy)
    return parser


def main(argv: Sequence[str] | None = None, stdout: TextIO | None = None) -> int:
    out = stdout or sys.stdout
    args = build_parser().parse_args(argv)
    try:
        code: int = args.func(args, out)
    except RecordError as exc:
        print(str(exc), file=sys.stderr)
        return EXIT_INVALID
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_INVALID
    return code


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
