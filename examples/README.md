# Examples

**Fictional.** The organisation ("Example Agency"), services, people, dates and figures in these records are invented to show how a record is filled in. They do not describe any real organisation or system.

| Record | What it shows |
|---|---|
| [meeting-notes-summariser.yaml](meeting-notes-summariser.yaml) | An internal, live tool that drafts meeting notes for the chair to edit. Mostly tidy; its review date has passed. |
| [service-chatbot.yaml](service-chatbot.yaml) | A public-facing chatbot in test. Shows the ATRS scope prompt, builder and assurer being the same person, model-graded evidence without a human-checked sample, and risks without owners. |
| [grant-triage.yaml](grant-triage.yaml) | A model that orders grant applications for human review, now also sending acknowledgements on its own. Shows the senior-or-specialist level and autonomous sends. |
| [history/grant-triage.v1.yaml](history/grant-triage.v1.yaml) | The earlier version of the grant record, for `aiak diff`. |

The rendered cards and register in [cards/](cards/) were produced with the example policy, as at 30 September 2026:

```bash
for name in meeting-notes-summariser service-chatbot grant-triage; do
  aiak render examples/$name.yaml --today 2026-09-30 -o examples/cards/$name.md
  aiak render examples/$name.yaml --today 2026-09-30 -o examples/cards/$name.html
done
aiak register examples/ --today 2026-09-30 -o examples/cards/register.md
```

The same files are used as snapshots by `tests/test_render.py`, so they cannot drift from the code.
