# Permit service helpline chatbot

> **Unofficial. Not government guidance. Checks are prompts for human judgement, not verdicts.**

**Status:** in test · **Record:** `service-helpline-chatbot` v2 · **Checked as at:** 2026-09-30 · **Next review:** 2026-10-31

A chatbot on the agency's website answers common questions about applying for a business permit, using only the agency's published guidance pages. Each answer links to its source page, and the chatbot offers a callback from the helpline when it cannot help.

## At a glance

| | |
|---|---|
| Purpose | The helpline receives many repeat questions that published guidance already answers. The chatbot aims to answer these at any time of day and free helpline staff for complex cases. |
| Business owner | Head of Permits Service (Riley Placeholder) |
| Builder | Contact centre technology lead (Sam Mock) |
| Maintainer | Contact centre technology lead (Sam Mock) |
| Assurer | Contact centre technology lead (acting assurer) (Sam Mock) |
| Approver | not recorded |
| System | generative: General-purpose LLM (API) from Model API vendor, hosting organisation cloud, supplier Chatbot platform supplier |
| Data | Published guidance pages; Questions typed by members of the public; Conversation logs |
| Personal data | yes · DPIA: required in progress · retention: not recorded |
| Connectors | Guidance index (read); Helpline handover (read, write) |
| Actions | writes with approval: Answers questions in the chat window. When a user asks for a person, it drafts a callback request for the contact centre queue. |
| Human approval | The user reviews and confirms the callback request before it is created. |
| Relied on by | Members of the public applying for a permit (information only) |
| Public | public-facing: yes · public effect: no · significant influence: no |
| ATRS determination | not assessed |

## Proportionality level: Use-specific review

A reviewer outside the build team checks this use case before it goes live, with input from data protection, security or accessibility specialists as the reasons suggest.

Why this level (policy: Example policy (adapt before use)):

- **Use-specific review**: Personal data is processed. (`personal_data = true`)
- **Use-specific review**: Members of the public interact with the system directly. (`public_facing = true`)
- **Use-specific review**: The system sends or writes on its own, not only drafts for a person. (`sends_or_writes = true`)

## Prompts for human judgement (2 high, 4 warning, 2 info)

| Severity | Check | Prompt |
|---|---|---|
| high | AIAK-RISK-001: Risk above appetite with no owner | Risk R3 scores 4 x 3 = 12, above the policy appetite of 9, and has no owner. Name the role that owns it. |
| high | AIAK-ROLE-001: Builder and assurer appear to be the same person | Builder and assurer are both recorded as 'Sam Mock'. Name an assurer who did not build it, or record why that is not possible and who accepts that. |
| warning | AIAK-DATA-002: No retention period recorded for personal data | Record how long inputs, outputs and logs containing personal data are kept, and where. |
| warning | AIAK-EVAL-003: Model-graded evidence without a human-checked sample | Quality evidence includes model grading but no human-checked sample or pilot. Add a sample checked by people with subject knowledge, and record how often they disagreed with the grader. |
| warning | AIAK-RISK-002: Risk above appetite with no control in place | Risk R3 (12) is above appetite and no linked control is in place (planned: C3). Put a control in place, or record who accepts the risk. |
| warning | AIAK-TRANS-001: ATRS: likely in scope, record the determination | The record says members of the public interact with it directly. If your organisation is covered by the ATRS mandatory scope, this tool is likely in scope. Record the determination (in scope or out of scope, and why) in transparency.atrs_determination. |
| info | AIAK-EVAL-004: No independent evaluation recorded | None of the recorded evaluations is marked independent. Record any done by someone outside the build team, or plan one. |
| info | AIAK-TRANS-002: Public-facing use with no user notice recorded | Record how members of the public are told that AI is involved and what it can and cannot do. |

## Risks (appetite: scores above 9)

| ID | Risk | L x I | Owner | Controls |
|---|---|---|---|---|
| R1 | The chatbot gives a wrong or out-of-date answer, and someone submits an incomplete application as a result. | 3 x 4 = 12 (above) | Head of Permits Service | C1 (in place), C2 (planned) |
| R3 | Users type personal details into the chat, and conversation logs keep them for longer than needed. | 4 x 3 = 12 (above) | none | C3 (planned) |
| R2 | Prompt injection makes the chatbot produce offensive or off-topic content. | 2 x 4 = 8 | none | C1 (in place) |

## Evidence and decisions

- 2026-05-02 · decision, approve build: by Director of Operations. Approved to build and test with helpline staff. Public launch needs a separate decision.
- 2026-08-10 · evidence, red team: The build team tried prompt-injection and off-topic prompts against the test version.
- 2026-08-24 · evidence, model graded: A second model graded the chatbot's answers to a set of anonymised past helpline questions against the guidance pages.

---

Sources behind the prompts above: [AI Playbook for the UK Government](https://www.gov.uk/government/publications/ai-playbook-for-the-uk-government); [ATRS mandatory scope and exemptions policy](https://www.gov.uk/government/publications/algorithmic-transparency-recording-standard-mandatory-scope-and-exemptions-policy); [Algorithmic Transparency Recording Standard (ATRS) guidance](https://www.gov.uk/government/publications/guidance-for-organisations-using-the-algorithmic-transparency-recording-standard); [NIST AI Risk Management Framework (AI RMF 1.0, NIST AI 100-1)](https://www.nist.gov/itl/ai-risk-management-framework); [The AQuA Book](https://www.gov.uk/guidance/the-aqua-book); [The Orange Book: management of risk](https://www.gov.uk/government/publications/orange-book); [ai-assurance-kit design principle](https://github.com/dsugurtuna/ai-assurance-kit/blob/main/docs/WHY.md).
The kit is informed by these sources; it does not implement or certify against them.

Generated from `examples/service-chatbot.yaml` by ai-assurance-kit 0.1.0. Unofficial. Not government guidance. Checks are prompts for human judgement, not verdicts.
