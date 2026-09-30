# Changelog

All notable changes to this project are recorded here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses [semantic versioning](https://semver.org/).

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
