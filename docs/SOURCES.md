# Sources and how they were checked

Unofficial; not government guidance. ai-assurance-kit is *informed by* the sources below. It does not implement, certify or satisfy any of them, and nothing here is a summary you should rely on instead of reading the source.

## How checking was done

The rule for this project is: anything the kit says about public guidance is checked against the primary source, or it is phrased generically, or it is left out.

All primary URLs below were fetched and verified directly against live GOV.UK, ICO and NIST pages on 22 November 2026, alongside official publisher-maintained machine-readable copies where noted:

- **Verified directly on primary page**: the URL resolves live and the text relied on was checked directly on the publisher's official website.
- **Cross-checked in an official repository**: where a publisher also publishes a machine-readable dataset or template repository on GitHub (such as NIST's CPRT JSON or GDS's ATRS template PDF), exact section names or subcategory quotations were additionally cross-checked against that copy.

Quotations of NIST text are lightly normalised (capitalisation, dashes) and shortened where marked `[...]`.

## Sources

### Algorithmic Transparency Recording Standard (ATRS): guidance

- URL: <https://www.gov.uk/government/publications/guidance-for-organisations-using-the-algorithmic-transparency-recording-standard>
- Status: **verified directly on GOV.UK** (published 5 January 2023, last updated 8 May 2025; HTML guidance read directly on 22 November 2026) and **cross-checked against the official GDS repository** (<https://github.com/co-cddo/algorithmic-transparency-recording-standard>, holding "ATRS Guidance for v4.0" and "Change log ATRS v3.0 to v4.0").
- Confirmed:
  - the template has two tiers: Tier 1 (`Summary Information`) aimed at the general public, and Tier 2 split across eight further sheets for specialist audiences;
  - the eight Tier 2 section names used in [CROSSWALK.md](CROSSWALK.md): `Owner and responsibility`, `Description and Rationale`, `Deployment Context`, `Tool Specification`, `Model Specification`, `Development Data Specification`, `Operational Data Specification`, and `Risks, Mitigations and Impact Assessments`;
  - enable senior responsible owners (as role titles) to take meaningful accountability for algorithmic tools and their outputs;
  - records need clearance before publication, and substantive changes (including moving a pilot tool to production) mean updating the ATRS record;
  - the guidance points readers to DPIAs and the Orange Book for risk assessments in public sector projects.

### ATRS mandatory scope and exemptions policy

- URL: <https://www.gov.uk/government/publications/algorithmic-transparency-recording-standard-mandatory-scope-and-exemptions-policy>
- Status: **verified directly on GOV.UK** (published 17 December 2024; HTML policy read directly on 22 November 2026).
- Confirmed:
  - mandated across all government departments since 6 February 2024, with stated intent to extend across the broader public sector, including arm's-length bodies (ALBs) delivering public or frontline services;
  - applies to algorithmic tools that either have a significant influence on a decision-making process with public effect or directly interact with the general public.
- How the kit uses it: `AIAK-TRANS-001` prompts for a recorded determination when a record says a tool is public-facing or significantly influences decisions with public effect. It never says a tool *is* in scope.

### AI Playbook for the UK Government

- URL: <https://www.gov.uk/government/publications/ai-playbook-for-the-uk-government>
- Status: **verified directly on GOV.UK** (published 10 February 2025, expanding on the Generative AI Framework for HMG published in January 2024; full HTML playbook read directly on 22 November 2026).
- Confirmed: all ten principle titles (`#principle-1-...` through `#principle-10-...`) match the live GOV.UK HTML headings used in `AI_PLAYBOOK_PRINCIPLES` in `src/ai_assurance_kit/sources.py`.
- How the kit uses it: principle numbers in the crosswalk and in some rule citations. The kit does not quote the Playbook's body text.

### ICO guidance on data protection impact assessments (DPIAs)

- URL: <https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/accountability-and-governance/data-protection-impact-assessments-dpias/>
- Status: **verified directly on ico.org.uk** (22 November 2026); kept generic at the screening level.
- Confirmed: live ICO guidance covering *What is a DPIA?*, *When do we need to do a DPIA?*, *How do we carry out a DPIA?*, and *Examples of processing 'likely to result in high risk'*.
- How the kit uses it: `AIAK-DATA-001` only notices that personal data is involved and no DPIA screening decision is recorded. The kit does not encode the ICO's screening criteria and does not decide whether a DPIA is needed.

### ICO guidance on rights related to automated decision-making, including profiling

- URL: <https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/individual-rights/individual-rights/rights-related-to-automated-decision-making-including-profiling/>
- Status: **verified directly on ico.org.uk** (22 November 2026); kept generic.
- Confirmed: live ICO guidance covering UK GDPR Article 22 protections for solely automated individual decision-making with legal or similarly significant effects, including providing simple ways for individuals to request human intervention or challenge a decision.
- How the kit uses it: `AIAK-DEC-001` asks for a challenge route and suggests asking a data protection lead whether rules on solely automated decisions apply. It makes no legal claim.

### The AQuA Book

- URL: <https://www.gov.uk/guidance/the-aqua-book>
- Status: **verified directly on GOV.UK** (published edition dated 30 July 2025 read directly on 22 November 2026).
- Confirmed in the published GOV.UK edition: the four roles (`commissioner`, `analyst`, `assurer`, `approver`); `"The roles of analyst and assurer shall be distinct from each other"`; and `"The assurer and the analyst shall be independent."`

### The Orange Book

- URL: <https://www.gov.uk/government/publications/orange-book>
- Status: **verified directly on GOV.UK** (HTML edition read directly on 22 November 2026); kept generic.
- Confirmed: structured into Part I (`Risk Management Principles`, Sections A–E) and Part II (`Risk Control Framework`, Sections F–G), accompanied by the *Risk Appetite Guidance Note*.
- How the kit uses it: as a pointer from the risk checks. The kit's prompts that a risk above appetite needs an owner and a control are the project's own design, not quotations from the Orange Book.

### NIST AI Risk Management Framework (AI RMF 1.0)

- URL: <https://www.nist.gov/itl/ai-risk-management-framework> (publication: NIST AI 100-1, DOI 10.6028/NIST.AI.100-1)
- Status: **verified directly on nist.gov** (released 26 January 2023; intended for voluntary use) and **cross-checked against NIST's official machine-readable dataset** (an export of NIST's Cybersecurity and Privacy Reference Tool) in <https://github.com/usnistgov/capordino> (`cprt_AI_100_1_0_0_07-07-2026.json`) and bibliographic record in <https://github.com/usnistgov/NIST-Tech-Pubs>.
- How the kit uses it: function and subcategory references in the crosswalk and in rule citations. Only subcategories whose text is stored in `NIST_SUBCATEGORIES` in `src/ai_assurance_kit/sources.py` can be cited.

### EU AI Act (Regulation (EU) 2024/1689)

- URL: <https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024R1689> (ELI: <http://data.europa.eu/eli/reg/2024/1689/oj>)
- Status: **official EUR-Lex legislation identifier verified** (Regulation (EU) 2024/1689 of 13 June 2024 laying down harmonised rules on artificial intelligence).
- How the kit uses it: high-level structural orientation in [CROSSWALK.md](CROSSWALK.md) linking risk management (Article 9), data governance (Article 10), technical documentation (Article 11), record-keeping (Article 12), transparency (Articles 13 & 50), human oversight (Article 14), accuracy/robustness/cybersecurity (Article 15), and deployer obligations (Articles 26–27) to record fields. Does not provide legal classification or establish legal conformity.

### ISO/IEC 42001:2023 (AI Management System)

- URL: <https://www.iso.org/standard/81230.html>
- Status: **bibliographic catalogue entry identified**; normative standard body text is behind ISO's paywall and was not read directly in full.
- How the kit uses it: mapped in [CROSSWALK.md](CROSSWALK.md) solely at the level of ISO's public Harmonized Structure (Clauses 4–10: Context, Leadership, Planning, Support, Operation, Performance evaluation, Improvement) and publicly documented Annex A control themes. The kit does not verify or certify management-system conformance.

### Published GOV.UK ATRS example records

- Repository URL: <https://www.gov.uk/algorithmic-transparency-records>
- Status: **three real records fetched directly via GOV.UK Content API** (`public_updated_at` timestamps preserved in `examples/published-atrs/`):
  - Ofsted: *AI Writing Assistant (Social Care)* (<https://www.gov.uk/algorithmic-transparency-records/ai-writing-assistant-social-care>, updated `2026-09-24`)
  - Cabinet Office (GCS): *Assist* (<https://www.gov.uk/algorithmic-transparency-records/cabinet-office-assist>, updated `2026-07-30`)
  - Care Quality Commission: *Risk Categorisation* (<https://www.gov.uk/algorithmic-transparency-records/care-quality-commission-risk-categorisation>, updated `2026-03-30`)

## Re-checking

Guidance changes. To re-check:

1. Open each URL above and compare it with what this page says was confirmed.
2. For the ATRS, check the current template version and its section names against `ATRS_SECTIONS` in `sources.py`.
3. For the AI Playbook, compare the principle headings with `AI_PLAYBOOK_PRINCIPLES` in `sources.py`.
4. For NIST, compare any cited subcategory with `NIST_SUBCATEGORIES`.
5. Update this page with the date and method, and adjust rule wording if a source has moved on.
