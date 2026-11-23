# Crosswalk

Unofficial; not government guidance. This page maps the kit's record fields and checks to the AI Playbook for the UK Government, the Algorithmic Transparency Recording Standard (ATRS), the AQuA Book roles, the NIST AI Risk Management Framework (AI RMF 1.0), and high-level obligations in the **EU AI Act (Regulation (EU) 2024/1689)** and **ISO/IEC 42001:2023**.

The mapping is the project's own judgement about where each field or check is *relevant*. It is not an official mapping, and a row here does not mean the kit implements or satisfies the item it points to. How each source was checked is in [SOURCES.md](SOURCES.md).

## Record fields

ATRS sections are those of ATRS v4.0: Tier 1 ("Summary Information") is written for the general public; Tier 2 (eight sections) is for specialist audiences such as civil society, journalists, academic researchers and other public sector organisations. AI Playbook principles are referred to by number (listed [below](#ai-playbook-principles)). NIST AI RMF references are functions, or subcategories whose text is stored in `src/ai_assurance_kit/sources.py`.

| Record field | ATRS v4.0 section | AI Playbook principle | NIST AI RMF | Notes |
|---|---|---|---|---|
| `id`, `title`, `summary` | Summary Information (Tier 1) | 7 | MAP 1.1 | Write `summary` for a general reader, as ATRS Tier 1 asks. |
| `status` | Summary Information (Tier 1) has a "Phase" field | 5 | MANAGE 1.1 | The kit's lifecycle is proposed, approved to build, in test, live, retired. |
| `purpose`, `benefits` | Description and Rationale (Tier 2) | 1, 6 | MAP 1.1 | |
| `alternatives_considered` | Description and Rationale (Tier 2) | 6 | MANAGE 2.1 | Checked by `AIAK-PURP-001`. |
| `accountability.*` | Owner and Responsibility (Tier 2) | 9, 10 | GOVERN 2.1 | ATRS asks for the senior responsible owner as a role title. See [roles](#aqua-book-roles). |
| `system.*` | Tool Specification; Model Specification (Tier 2) | 1, 3 | MAP 4.2 | |
| `system.third_party_supplier` | Owner and Responsibility (Tier 2): third party involvement | 8 | GOVERN 6.1 | |
| `data.categories`, `data.sources` | Development Data Specification; Operational Data Specification (Tier 2) | 2 | MEASURE 2.10 | ATRS v4.0 split data into development and operational sections. |
| `data.personal_data`, `data.special_category_data`, `data.retention` | Operational Data Specification (Tier 2) | 2 | MEASURE 2.10 | |
| `data.dpia` | Risks, Mitigations and Impact Assessments (Tier 2) | 2 | MEASURE 2.10 | The kit records the screening decision; it does not make it. |
| `access.users`, `access.connectors` | Tool Specification (Tier 2) | 3 | MAP 4.2 | Permissions are explicit so excess power is visible. |
| `actions.*` | Deployment Context (Tier 2) | 4 | GOVERN 3.2, MAP 3.5, MANAGE 2.4 | Ordered: read only < drafts < writes with approval < autonomous. |
| `reliance.decision_role`, `reliance.human_review`, `reliance.how_outputs_are_used` | Deployment Context (Tier 2) | 4 | MAP 2.2, MAP 3.5 | ATRS v4.0 calls these "integration into broader operational process" and "human review". |
| `reliance.challenge_route` | Deployment Context (Tier 2): appeals and review | 2 | MEASURE 3.3 | |
| `reliance.public_facing`, `reliance.public_effect`, `reliance.significant_influence` | ATRS mandatory scope | 7 | MAP 1.1 | Used to prompt for an ATRS scope determination (`AIAK-TRANS-001`). |
| `reliance.user_notice` | (no direct field) | 7 | MAP 2.2 | How people are told that AI is involved. |
| `reliance.scale` | (no direct field in v4.0 confirmed) | 5 | MAP 1.1 | Scale rises are material changes in `aiak diff`. |
| `risks`, `controls` | Risks, Mitigations and Impact Assessments (Tier 2) | 2, 3, 10 | GOVERN 1.3, MAP 1.5, MAP 5.1, MANAGE 1.3 | Appetite comes from the policy file. For UK government risk management guidance see the Orange Book. |
| `evaluation` | Model Specification (Tier 2): model performance, including bias and fairness evaluation | 1, 5 | MEASURE 1.3, MEASURE 2.3, MEASURE 4.2 | |
| `decisions` | Publishing: clearance before publication | 5, 10 | MANAGE 1.1 | Build, data, access, sharing and go-live are separate decisions. |
| `transparency.*` | The whole ATRS record | 7 | GOVERN | The kit's record is not an ATRS record and does not replace the official template. |
| `review.*` | Guidance: updating your ATRS record | 5 | GOVERN 1.5 | |
| `aiak register` (many records) | ATRS repository of published records | 10 | GOVERN 1.6 | An inventory of AI uses. |

## AQuA Book roles

The AQuA Book defines four roles for analytical quality assurance: commissioner, analyst, assurer and approver, and keeps the analyst and assurer roles separate (see [SOURCES.md](SOURCES.md#the-aqua-book)). The kit borrows that structure for AI use cases:

| Kit role | Nearest AQuA Book role | Why the kit adds or changes it |
|---|---|---|
| `business_owner` | Commissioner | Owns the use and its outcomes, not just the request. |
| `builder` | Analyst | Builds or configures the system and does its own checks. |
| `assurer` | Assurer | Reviews the builder's work; `AIAK-ROLE-001` prompts when it is the same person. |
| `approver` | Approver | Signs off that assurance is appropriate. |
| `maintainer` | (none) | Added because AI systems change after launch; `AIAK-ROLE-003` prompts when a live system has none. |

## Checks

Generated from the rule registry by `aiak rules --format crosswalk`; a test fails if this block is out of date. Full rationale for each check is in [RULES.md](RULES.md).

<!-- BEGIN GENERATED: aiak rules --format crosswalk -->

| Check | AI Playbook principle | ATRS guidance section | NIST AI RMF | Other sources |
|---|---|---|---|---|
| AIAK-META-001 Template placeholders remain | - | - | - | ai-assurance-kit design principle: Make uncertainty visible |
| AIAK-ACT-001 Sends or writes without a human approval step | 4 | - | GOVERN 3.2, MAP 3.5 | ai-assurance-kit design principle: Read freely, write carefully |
| AIAK-ACT-002 No way to stop the system is recorded | - | - | MANAGE 2.4 | ai-assurance-kit design principle: Read freely, write carefully |
| AIAK-ACT-003 Connector permissions exceed what the system is recorded as doing | 3 | - | MAP 4.2 | ai-assurance-kit design principle: Read freely, write carefully |
| AIAK-ACT-004 Recipients of sends or writes are not recorded | - | - | MAP 1.1 | ai-assurance-kit design principle: Read freely, write carefully |
| AIAK-DATA-001 Personal data with no DPIA screening recorded | - | Development Data Specification (Tier 2); Risks, Mitigations and Impact Assessments (Tier 2) | MEASURE 2.10 | ICO guidance on data protection impact assessments (DPIAs) |
| AIAK-DATA-002 No retention period recorded for personal data | - | Operational Data Specification (Tier 2) | MEASURE 2.10 | - |
| AIAK-DATA-003 Special category data screened out of a DPIA without a recorded rationale | - | - | - | ICO guidance on data protection impact assessments (DPIAs) |
| AIAK-TRANS-001 ATRS: likely in scope, record the determination | - | ATRS purpose and scope; Scope and exemptions policy | - | - |
| AIAK-TRANS-002 Public-facing use with no user notice recorded | 7 | ATRS purpose and scope | - | - |
| AIAK-ROLE-001 Builder and assurer appear to be the same person | - | - | MEASURE 1.3 | The AQuA Book: Roles and responsibilities |
| AIAK-ROLE-002 No assurer named | - | - | GOVERN 2.1 | The AQuA Book: Proportionality |
| AIAK-ROLE-003 Live with no named maintainer | 5 | Owner and Responsibility (Tier 2) | MANAGE 4.1, GOVERN 2.1 | - |
| AIAK-EVAL-001 Live with no evaluation evidence | 5 | - | MEASURE 2.3, MANAGE 1.1 | - |
| AIAK-EVAL-002 Only usage metrics recorded as evidence | - | - | MEASURE 2.3 | ai-assurance-kit design principle: Usage is not quality |
| AIAK-EVAL-003 Model-graded evidence without a human-checked sample | - | - | MEASURE 4.2, MEASURE 1.3 | ai-assurance-kit design principle: A second model is a critic, not a verifier |
| AIAK-EVAL-004 No independent evaluation recorded | - | - | MEASURE 1.3 | The AQuA Book: Roles and responsibilities |
| AIAK-REV-001 Review date has passed | - | Updating your ATRS record | GOVERN 1.5 | - |
| AIAK-REV-002 No next review date | - | - | GOVERN 1.5 | - |
| AIAK-RISK-001 Risk above appetite with no owner | - | - | GOVERN 1.3, MAP 1.5, MANAGE 1.3 | The Orange Book: management of risk |
| AIAK-RISK-002 Risk above appetite with no control in place | - | - | MANAGE 1.3 | The Orange Book: management of risk |
| AIAK-RISK-003 No risks recorded | - | Risks, Mitigations and Impact Assessments (Tier 2) | MAP 5.1 | - |
| AIAK-PURP-001 No alternatives recorded | 6 | Description and Rationale (Tier 2) | MANAGE 2.1 | ai-assurance-kit design principle: Fix the data before adding an agent |
| AIAK-DEC-001 Automated decisions with public effect and no challenge route | - | Deployment Context (Tier 2) | MEASURE 3.3 | ICO guidance on rights related to automated decision-making, including profiling |
| AIAK-DEC-002 Decision support with no human review described | 4 | - | MAP 2.2, MAP 3.5 | - |
| AIAK-LIFE-001 Status is ahead of the recorded decisions | 10 | - | MANAGE 1.1 | ai-assurance-kit design principle: Permission to build is not permission to deploy |

<!-- END GENERATED -->

## AI Playbook principles

The ten principles of the [AI Playbook for the UK Government](https://www.gov.uk/government/publications/ai-playbook-for-the-uk-government):

1. You know what AI is and what its limitations are
2. You use AI lawfully, ethically and responsibly
3. You know how to use AI securely
4. You have meaningful human control at the right stages
5. You understand how to manage the full AI life cycle
6. You use the right tool for the job
7. You are open and collaborative
8. You work with commercial colleagues from the start
9. You have the skills and expertise needed to implement and use AI solutions
10. You use these principles alongside your organisation's policies and have the right assurance in place

## NIST AI RMF core functions

The four functions of the [NIST AI RMF 1.0](https://www.nist.gov/itl/ai-risk-management-framework) (NIST AI 100-1), with NIST's one-line descriptions:

| Function | Description |
|---|---|
| GOVERN | A culture of risk management is cultivated and present. |
| MAP | Context is recognized and risks related to context are identified. |
| MEASURE | Identified risks are assessed, analyzed, or tracked. |
| MANAGE | Risks are prioritized and acted upon based on a projected impact. |

The subcategories cited by the checks, with their text, are in `NIST_SUBCATEGORIES` in [`src/ai_assurance_kit/sources.py`](../src/ai_assurance_kit/sources.py).

## EU AI Act (Regulation (EU) 2024/1689)

Indicative orientation mapping to [Regulation (EU) 2024/1689 on EUR-Lex](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024R1689). This kit does not determine EU AI Act risk classification or establish legal conformity; legal teams decide applicability.

| Record field / check area | Relevant EU AI Act articles | Governance question prompted |
|---|---|---|
| `purpose`, `reliance.*`, proportionality policy | Title III / Annex III scoping context; Art. 27 (Fundamental rights impact assessment context) | Could this use fall within high-risk deployment categories affecting fundamental rights or public services? |
| `risks`, `controls`, `review.*` | Art. 9 (Risk management system across lifecycle) | Are risks identified, owned, treated with named controls, and reviewed on a defined cadence? |
| `data.*` (`categories`, `sources`, `dpia`, `retention`) | Art. 10 (Data and data governance) | Are data sources, personal/special-category flags, retention, and DPIA screening documented? |
| Full YAML record (`system.*`, `access.*`, `decisions`) | Art. 11 & Annex IV context (Technical documentation); Art. 12 (Record-keeping context) | Is there an inspectable, versioned record of architecture, connectors, decisions, and changes (`aiak diff`)? |
| `reliance.user_notice`, `transparency.*` | Art. 13 (Transparency and provision of information to deployers); Art. 50 (Transparency for certain AI systems, including synthetic text/interaction notices) | Are affected people informed when interacting with AI or viewing synthetic outputs? |
| `actions.*`, `reliance.human_review`, `reliance.challenge_route` | Art. 14 (Human oversight) & Art. 26 (Obligations of deployers of high-risk AI systems) | Are send/write modes gated by human approval, stop mechanisms (`stop_mechanism`), and meaningful review? |
| `evaluation` (`offline_test_set`, `bias_review`, `security_review`, `AIAK-EVAL-*`) | Art. 15 (Accuracy, robustness and cybersecurity) | Is performance verified independently beyond raw usage counts before reliance in production? |

## ISO/IEC 42001:2023 (AI Management System)

Mapping to the public Harmonized Structure (Clauses 4–10) and Annex A control theme index of [ISO/IEC 42001:2023](https://www.iso.org/standard/81230.html). Because the full standard body text is behind a paywall (see [SOURCES.md](SOURCES.md)), this table maps at structural theme level only and does not verify conformance.

| ISO/IEC 42001:2023 structure | Nearest `ai-assurance-kit` mechanism | How teams use it in practice |
|---|---|---|
| **Clause 4** Context of the organisation | `organisation`, `purpose`, `reliance.*`, custom `policy.yaml` | Tailors risk appetite and proportionality thresholds to organisational context. |
| **Clause 5** Leadership | `accountability` (`business_owner`, `approver`, separate `assurer`) & `decisions` | Enforces named senior accountability and separates building from assuring (`AIAK-ROLE-001`). |
| **Clause 6** Planning (risks, objectives) | `risks`, `controls`, policy risk appetite (`AIAK-RISK-001`, `AIAK-RISK-002`) | Captures likelihood/impact scores, named owners, and linked mitigations before build/go-live. |
| **Clause 7** Support (competence, documented information) | Versioned YAML records, `json_schema`, rendered executive cards | Maintains auditable, diffable documentation in Git rather than scattered slide decks. |
| **Clause 8** Operation (impact assessment, lifecycle) | `status` lifecycle gating (`AIAK-LIFE-001`), `data.dpia`, `access.connectors`, `actions.stop_mechanism` | Tracks gated progression (`proposed` -> `approved_to_build` -> `in_test` -> `live` -> `retired`). |
| **Clause 9** Performance evaluation | `evaluation` timeline (`human_review_sample`, `red_team`, `bias_review`, `AIAK-EVAL-001..004`) | Separates exposure (`usage_metrics`) from grounded quality checks (`AIAK-EVAL-002`). |
| **Clause 10** Improvement | `review.last_reviewed`, `review.next_review`, `aiak diff --fail-on-material` | Flags stale reviews (`AIAK-REV-001`) and triggers re-review when scope, model, or autonomy shifts. |
| **Annex A** Control objectives (AI impact, data, third parties, lifecycle) | `system.third_party_supplier`, `transparency.*`, `data.*`, `actions.*` | Keeps third-party suppliers, data lineage, transparency obligations, and kill switches inspectable per use case. |
