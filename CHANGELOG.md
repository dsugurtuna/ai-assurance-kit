# Changelog

All notable changes to this project are recorded here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses [semantic versioning](https://semver.org/).

## [Unreleased]

### Added

- Risk residual scoring and formal waiver fields on `Risk` (`residual_likelihood`, `residual_impact`, `accepted_by`, `acceptance_rationale`, `acceptance_expiry`) with schema validation and card rendering.
- `-o`/`--output` option on `aiak check` and `aiak diff` (with format inference from `.md`/`.json` extensions on `diff`).
- `Person.team` attribution and `transparency.record_url` rendering (safe `http`/`https` links only) on Markdown and HTML cards.
- Three public GOV.UK ATRS reference adaptations in `examples/published-atrs/` (Ofsted, Cabinet Office GCS Assist, CQC), published under OGL v3.0 and documented with schema-adapter proxy notes.
- Primary-source verification details in `docs/SOURCES.md` and exploratory, non-normative structural orientation notes in `docs/CROSSWALK.md` (with Clause 9 vs 10 and EU AI Act Art. 13/26(11)/50 mappings aligned).

### Changed

- `AIAK-DATA-001` now also prompts when a `live` personal-data system still has `dpia.status: required_in_progress`, or when `screened_not_required` omits `dpia.decided_by`.
- `AIAK-ACT-003` now flags excess `delete` and `admin` connector permissions on `writes_with_approval` and `autonomous` modes instead of returning early.
- `AIAK-ROLE-001` now flags identical `builder` and `assurer` roles (within the same or unspecified team) when distinct personal names are omitted.
- `AIAK-TRANS-001` now prompts when a likely in-scope system is marked `out_of_scope` without a `transparency.rationale`.
- `AIAK-RISK-002` respects active risk acceptances (`accepted_by` + `acceptance_rationale` with non-expired `acceptance_expiry`) and re-prompts when acceptance expires or lacks a rationale.
- `AIAK-RISK-003` (no risks recorded) is now a warning, not info, so a record with no risks cannot pass a `--fail-on warning` gate that the same record with an untreated risk would fail.
- The schema is stricter where it used to coerce: numbers and true/false fields no longer accept quoted text (`"4"`, `"no"`) or `yes` for a number, list entries and optional text fields reject empty strings (with `third_party_supplier` normalising blank text to `null`), and the next review cannot be before the last one. The JSON Schema and `aiak validate` agree on these cases.
- `aiak diff` treats more changes as material: removing or downgrading an `in_place` control, regressing `data.dpia.status`, first-time scale entries at or above `initial_scale_threshold` (default `1000`), new groups relying on the outputs, a change of model kind, a connector pointing at a different system, and removing the stop mechanism, challenge route or user notice.
- Policy validation rejects triggers that can never fire (a misspelt value, or a condition of the wrong type) and unknown rule ids in `disabled_rules`.

### Fixed

- `find_record_files` wildcard expansion now filters by record suffixes (`.yaml`, `.yml`, `.json`) so globs such as `examples/*` skip `README.md`.
- CSV portfolio registers neutralise spreadsheet formula prefixes (`=`, `+`, `-`, `@`, tab, CR).
- `--redact-names` cards no longer show a name in the `AIAK-ROLE-001` prompt.
- Markdown cards, registers and diffs escape record text everywhere (pipes, newlines and raw HTML).
- `aiak diff` no longer hides edits behind a material change, treats empty strings consistently with `null` in scalar comparisons, and compares evidence and decisions by content, so an edited field or an item added at the top of the list is reported correctly.
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
