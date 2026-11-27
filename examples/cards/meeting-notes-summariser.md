# Meeting notes summariser

> **Unofficial. Not government guidance. Checks are prompts for human judgement, not verdicts.**

**Status:** live · **Record:** `meeting-notes-summariser` v3 · **Checked as at:** 2026-09-30 · **Next review:** 2026-09-01 (overdue)

Staff can ask an AI assistant to turn the transcript of an internal meeting into draft notes and a list of actions. The meeting chair edits and circulates the notes; nothing is sent automatically.

## At a glance

| | |
|---|---|
| Purpose | Internal meetings are often left without notes, or with notes in different formats. The tool gives the chair a first draft so that notes are produced soon after the meeting and in a standard format. |
| Business owner | Head of Corporate Services (Jordan Sample) |
| Builder | Digital team developer, Digital (Alex Example) |
| Maintainer | Digital service manager, Digital (Casey Demo) |
| Assurer | Data and AI assurance lead (Morgan Test) |
| Approver | Chief Information Officer |
| System | generative: General-purpose LLM (vendor-hosted) from Office software vendor, hosting vendor saas, supplier Office software vendor |
| Data | Meeting transcripts; Attendee names and job titles; Views expressed in meetings |
| Personal data | yes · DPIA: completed · retention: Transcripts are deleted after 30 days. Draft and final notes follow the organisation's records policy. |
| Connectors | Transcription store (read); Drafts folder (read, write) |
| Actions | drafts: Writes draft notes and an actions list into the chair's own drafts folder. |
| Human approval | The chair reads, edits and circulates the notes themselves. |
| Relied on by | Meeting chairs; Attendees, once the chair circulates the notes (information only) |
| Public | public-facing: no · public effect: no · significant influence: no |
| ATRS determination | out of scope: Internal use only; no interaction with the public and no influence on decisions with public effect. |

## Proportionality level: Use-specific review

A reviewer outside the build team checks this use case before it goes live, with input from data protection, security or accessibility specialists as the reasons suggest.

Why this level (policy: Example policy (adapt before use)):

- **Use-specific review**: Personal data is processed. (`personal_data = true`)

## Prompts for human judgement (0 high, 1 warning, 0 info)

| Severity | Check | Prompt |
|---|---|---|
| warning | AIAK-REV-001: Review date has passed | The next review was due on 2026-09-01 (29 days before 2026-09-30). Review the record, or set a new date and say why. |

## Risks (appetite: scores above 9)

| ID | Risk | L x I | Owner | Controls |
|---|---|---|---|---|
| R3 | Over time chairs stop checking drafts closely and circulate them as they are (automation bias). | 4 x 3 = 12 (above) | Digital service manager | C1 (in place), C4 (planned) |
| R1 | A draft attributes a view or an action to the wrong person, and the chair circulates it without noticing. | 3 x 3 = 9 | Head of Corporate Services | C1 (in place), C2 (in place) |
| R2 | Sensitive discussion ends up in widely circulated notes. | 2 x 4 = 8 | Head of Corporate Services | C3 (in place) |

## Evidence and decisions

- 2026-01-12 · decision, approve build: by Chief Information Officer
- 2026-01-25 · decision, connect data: by Data Protection Officer. Transcription store connected after the DPIA was completed.
- 2026-02-27 · evidence, human review sample: Pilot: chairs compared drafts with their own notes for a sample of meetings, logging each correction and the total time spent including checking.
- 2026-03-20 · evidence, human review sample (independent): The assurance lead checked a separate sample of drafts against the transcripts, looking for misattributed views and invented actions.
- 2026-04-01 · decision, go live: by Chief Information Officer
- 2026-06-30 · evidence, usage metrics: Monthly use, and the share of drafts circulated with no edits (tracked as a warning sign for R3, not as a measure of quality).

---

Sources behind the prompts above: [Algorithmic Transparency Recording Standard (ATRS) guidance](https://www.gov.uk/government/publications/guidance-for-organisations-using-the-algorithmic-transparency-recording-standard); [NIST AI Risk Management Framework (AI RMF 1.0, NIST AI 100-1)](https://www.nist.gov/itl/ai-risk-management-framework).
The kit is informed by these sources; it does not implement or certify against them.

Generated from `examples/meeting-notes-summariser.yaml` by ai-assurance-kit 0.1.0. Unofficial. Not government guidance. Checks are prompts for human judgement, not verdicts.
