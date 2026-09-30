# Contributing

Thanks for looking. Issues and pull requests are welcome.

## Set up

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest && ruff check . && ruff format --check . && mypy
```

Everything runs offline. Please keep it that way: no network calls and no API keys in tests.

## Adding or changing a check

1. Add the rule in `src/ai_assurance_kit/checks/rules.py` with an ID (`AIAK-AREA-NNN`), a title, a severity, a rationale and at least one citation.
2. Phrase the message as what to record or decide next. Avoid verdict words such as "non-compliant" or "violation"; a test looks for them.
3. Cite only sources in `src/ai_assurance_kit/sources.py`. To cite something new, add it there and record how you checked it in `docs/SOURCES.md`. Cite NIST AI RMF subcategories only if their text is in `NIST_SUBCATEGORIES`.
4. Add a trigger case to `TRIGGERS` in `tests/test_rules.py`, and a boundary test if the condition has one.
5. Regenerate the generated docs:

   ```bash
   aiak rules --format md > docs/RULES.md
   aiak rules --format crosswalk   # paste over the generated block in docs/CROSSWALK.md
   ```

6. If the change affects the example cards, regenerate them with `AIAK_UPDATE_SNAPSHOTS=1 pytest tests/test_render.py` and read the diff.

## Changing the schema

Update `src/ai_assurance_kit/schema.py`, then `aiak schema -o schema/ai-use-record.schema.json`. Breaking changes need a new `schema_version` and a note in `CHANGELOG.md`.

## Style

British English, plain words, short sentences. Say what the code does and its limits. Examples must be fictional and generic, and marked as such.
