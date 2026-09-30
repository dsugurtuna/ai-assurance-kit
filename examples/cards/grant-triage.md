# Grant application triage

> **Unofficial. Not government guidance. Checks are prompts for human judgement, not verdicts.**

**Status:** in test · **Record:** `grant-application-triage` v2 · **Checked as at:** 2026-09-30 · **Next review:** 2026-12-01

A model scores incoming applications to a community grants scheme against the published eligibility criteria and suggests an order for assessors to work in. Assessors review every application; the model does not accept or reject any. Applicants now get an automatic acknowledgement with an expected decision date.

## At a glance

| | |
|---|---|
| Purpose | Applications arrive in peaks and assessors work in date order, so clearly eligible, time-sensitive applications can wait weeks. A suggested order should shorten those waits, and an acknowledgement tells applicants when to expect a decision. |
| Business owner | Grants programme director (Taylor Sample) |
| Builder | Data scientist (Jamie Example) |
| Maintainer | Analysis team lead (Robin Demo) |
| Assurer | Analytical assurance reviewer (Avery Test) |
| Approver | Grants programme director (Taylor Sample) |
| System | predictive: Gradient-boosted classifier over text features from in-house, hosting organisation cloud |
| Data | Application form answers; Applicant organisation details, including contact names; Past assessor outcomes; Previous grant payments to the applicant |
| Personal data | yes · DPIA: required in progress · retention: Scores and reasons are kept with the case file under the scheme's retention schedule. Training extracts are deleted after 12 months. |
| Connectors | Application portal export (read); Finance system extract (read); Case management queue (read, write); Applicant email (send) |
| Actions | autonomous: Writes the suggested order and reasons onto each case, and emails each applicant an acknowledgement with an expected decision date. Neither step waits for a person. |
| Human approval | not recorded |
| Relied on by | Grants assessors; Grants team leaders; Applicants (expected decision date) (decision support) |
| Public | public-facing: no · public effect: yes · significant influence: yes |
| ATRS determination | in scope: Treated as in scope because the suggested order influences when applicants get a decision. An ATRS record will be drafted before the tool is used by assessors. |

## Proportionality level: Senior or specialist approval

A senior accountable owner approves the use after specialist review, and the approval is recorded as a separate go-live decision.

Why this level (policy: Example policy (adapt before use)):

- **Senior or specialist approval**: Outputs significantly influence decisions that affect the public or organisations. (`significant_public_effect = true`)
- **Senior or specialist approval**: The system sends or writes without a person approving each action. (`action_mode = autonomous`)
- **Use-specific review**: Personal data is processed. (`personal_data = true`)
- **Use-specific review**: The system sends or writes on its own, not only drafts for a person. (`sends_or_writes = true`)
- **Use-specific review**: Outputs support decisions, so errors can shape outcomes. (`decision_role = decision_support`)

## Prompts for human judgement (2 high, 2 warning, 0 info)

| Severity | Check | Prompt |
|---|---|---|
| high | AIAK-ACT-001: Sends or writes without a human approval step | The system sends or writes without a person approving each action. Record who decided that per-action approval is not needed, the limits that apply (what, to whom, how often) and how errors are noticed and reversed. |
| high | AIAK-RISK-001: Risk above appetite with no owner | Risk R4 scores 3 x 4 = 12, above the policy appetite of 9, and has no owner. Name the role that owns it. |
| warning | AIAK-ACT-002: No way to stop the system is recorded | Record how the system can be paused or switched off quickly, who can do it, and when it was last tried. |
| warning | AIAK-RISK-002: Risk above appetite with no control in place | Risk R4 (12) is above appetite and no linked control is in place (planned: none linked). Put a control in place, or record who accepts the risk. |

## Risks (appetite: scores above 9)

| ID | Risk | L x I | Owner | Controls |
|---|---|---|---|---|
| R1 | The model ranks applications from some kinds of organisation lower because past outcomes reflect past bias. | 3 x 4 = 12 (above) | Grants programme director | C1 (in place), C2 (in place) |
| R4 | An acknowledgement gives a wrong expected decision date, or goes to the wrong applicant. | 3 x 4 = 12 (above) | none | none |
| R2 | Assessors defer to the suggested priority instead of forming their own view. | 3 x 3 = 9 | Analysis team lead | C3 (planned) |
| R3 | An urgent application is flagged as not urgent and waits longer. | 2 x 4 = 8 | Grants programme director | C2 (in place) |

## Evidence and decisions

- 2026-06-03 · decision, approve build: by Grants programme director. Approved to build and test offline only. Connecting live application data and use by assessors need separate decisions.
- 2026-07-20 · decision, connect data: by Data Protection Officer. Application portal export connected for offline testing.
- 2026-08-14 · evidence, offline test set: Offline test on held-out past applications, with assessor outcomes as labels and results broken down by organisation type and region.
- 2026-09-05 · evidence, bias review (independent): The analytical assurance team re-ran the offline test and reviewed performance across organisation types and regions (control C1).

---

Sources behind the prompts above: [AI Playbook for the UK Government](https://www.gov.uk/government/publications/ai-playbook-for-the-uk-government); [NIST AI Risk Management Framework (AI RMF 1.0, NIST AI 100-1)](https://www.nist.gov/itl/ai-risk-management-framework); [The Orange Book: management of risk](https://www.gov.uk/government/publications/orange-book); [ai-assurance-kit design principle](https://github.com/dsugurtuna/ai-assurance-kit/blob/main/docs/WHY.md).
The kit is informed by these sources; it does not implement or certify against them.

Generated from `examples/grant-triage.yaml` by ai-assurance-kit 0.1.0. Unofficial. Not government guidance. Checks are prompts for human judgement, not verdicts.
