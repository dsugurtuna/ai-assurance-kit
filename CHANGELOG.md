# Changelog

All notable changes to this project are recorded here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses [semantic versioning](https://semver.org/).

## [Unreleased]

### Changed

- `AIAK-RISK-003` (no risks recorded) is now a warning, not info, so a record with no risks cannot pass a `--fail-on warning` gate that the same record with an untreated risk would fail.
- The schema is stricter where it used to coerce: numbers and true/false fields no longer accept quoted text (`"4"`, `"no"`) or `yes` for a number, list entries cannot be empty, and the next review cannot be before the last one. The JSON Schema and `aiak validate` now agree on these cases.
- `aiak diff` treats more changes as material: new groups relying on the outputs, a change of model kind, a connector pointing at a different system, and removing the stop mechanism, challenge route or user notice.
- Policy validation rejects triggers that can never fire (a misspelt value, or a condition of the wrong type) and unknown rule ids in `disabled_rules`.

### Fixed

- `--redact-names` cards no longer show a name in the `AIAK-ROLE-001` prompt.
- Markdown cards, registers and diffs escape record text everywhere (pipes, newlines and raw HTML).
- `aiak diff` no longer hides edits behind a material change, and compares evidence and decisions by content, so an edited field or an item added at the top of the list is reported correctly.
- Repeated YAML keys are an error instead of a silent overwrite. Invalid dates and files that are not UTF-8 are reported per file, and UTF-16 files written by Windows PowerShell load.
- A directory with no record files, an unmatched wildcard or an unwritable output path exits 2 with a message, instead of passing (exit 0) or crashing (exit 1). Wildcards and upper-case suffixes work on Windows.
- The README's sample output matches the command it quotes, and a test keeps it that way.

## [0.1.0] - 2026-09-30

### Added

- AI use record schema (`schema_version` 1.0) with pydantic v2 models and an exported JSON Schema (draft 2020-12).
- 26 explainable checks, each with an ID, severity, rationale and citations, phrased as prompts for human judgement.
- Proportionality levels computed from 14 named record features under a policy file, with an example policy to adapt.
- `aiak diff` with material-change rules for re-review.
- One-page cards in Markdown and standalone HTML, and a portfolio register in CSV and Markdown.
- `aiak` command line: `init`, `validate`, `check`, `diff`, `render`, `register`, `schema`, `rules`, `policy`.
- Three fictional example records, an earlier version of one for `aiak diff`, and their rendered cards.
- Documentation: crosswalk to the AI Playbook, ATRS and NIST AI RMF; generated checks reference; source checking notes; design rationale.
