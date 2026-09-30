# Sources and how they were checked

Unofficial; not government guidance. ai-assurance-kit is *informed by* the sources below. It does not implement, certify or satisfy any of them, and nothing here is a summary you should rely on instead of reading the source.

## How checking was done

The rule for this project is: anything the kit says about public guidance is checked against the primary source, or it is phrased generically, or it is left out.

When the kit was written (September 2026), the build environment could not reach gov.uk, ico.org.uk or nist.gov directly. So each source was checked in the best available way, and this page says which:

- **Read in an official copy**: the text was read in full from a copy published by the organisation responsible (for example on its own GitHub account).
- **Confirmed via search**: a fact (a date, a page title, a URL) was confirmed from search results pointing at the primary page, but the page itself was not read.
- **Not fetched; kept generic**: the kit only points to the source and makes no specific claim about its content.

Quotations of NIST text are lightly normalised (capitalisation, dashes) and shortened where marked `[...]`.

## Sources

### Algorithmic Transparency Recording Standard (ATRS): guidance

- URL: <https://www.gov.uk/government/publications/guidance-for-organisations-using-the-algorithmic-transparency-recording-standard>
- Status: **read in an official copy.** The PDF "ATRS Guidance for v4.0" and "Change log ATRS v3.0 to v4.0" in the Government Digital Service's repository <https://github.com/co-cddo/algorithmic-transparency-recording-standard> (latest commit 4 July 2025), which says it holds a PDF of the guidance published on GOV.UK.
- Confirmed:
  - the template has two tiers: Tier 1 (Summary Information) for the general public, and Tier 2, split across eight sections, for specialist audiences;
  - the eight Tier 2 section names used in [CROSSWALK.md](CROSSWALK.md), including the v4.0 split of data into Development Data and Operational Data, and the renaming of "Decision-making Process" to "Deployment Context";
  - the scope wording: mandatory "for all government departments, and for ALBs which deliver public or frontline services, or directly interact with the general public", and within those organisations "for algorithmic tools which have a significant influence on a decision-making process with public effect, or directly interact with the general public";
  - the senior responsible owner should be a role title, not a named individual;
  - records need clearance before publication, and substantive changes (the guidance's examples include a pilot tool moving to production) mean updating the record;
  - the guidance refers readers to the ICO's DPIA guidance and to the Orange Book. The URLs this kit uses for the ICO pages, the scope policy, the AI Playbook and the Orange Book are taken from the links in this PDF.

### ATRS mandatory scope and exemptions policy

- URL: <https://www.gov.uk/government/publications/algorithmic-transparency-recording-standard-mandatory-scope-and-exemptions-policy>
- Status: **scope wording read in an official copy** (as quoted in the ATRS guidance above); the policy page itself **not fetched**. Publication in December 2024 **confirmed via search**.
- How the kit uses it: `AIAK-TRANS-001` prompts for a recorded determination when a record says a tool is public-facing or significantly influences decisions with public effect. It never says a tool *is* in scope.

### AI Playbook for the UK Government

- URL: <https://www.gov.uk/government/publications/ai-playbook-for-the-uk-government>
- Status: **not fetched from GOV.UK.** The ten principle titles were checked against the GOV.UK heading anchors (for example `#principle-4-you-have-meaningful-human-control-at-the-right-stages`) recorded in a Crown Commercial Service dataset (<https://github.com/Crown-Commercial-Service/GCA-Ardoq>, `gov_standards.json`). A Government Digital Service copy of the GOV.UK summary page (in <https://github.com/alphagov/govuk-topic-taxonomy-static-suggestions-experiment>) confirms that "the playbook includes 10 principles civil servants should uphold when using AI" and that it expands on the Generative AI Framework for HMG published in January 2024. Publication in February 2025 **confirmed via search**.
- Note: some secondary summaries word principles 4, 5 and 9 slightly differently (for example "at the right stage" rather than "stages"). The kit uses the wording in the GOV.UK anchors. Re-check against GOV.UK before quoting.
- How the kit uses it: principle numbers in the crosswalk and in some rule citations. The kit does not quote the Playbook's body text.

### ICO guidance on data protection impact assessments (DPIAs)

- URL: <https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/accountability-and-governance/data-protection-impact-assessments-dpias/>
- Status: **not fetched; kept generic.** The URL comes from the ATRS guidance's link; the page titles ("When do we need to do a DPIA?", "Examples of processing 'likely to result in high risk'") were **confirmed via search**.
- How the kit uses it: `AIAK-DATA-001` only notices that personal data is involved and no DPIA screening decision is recorded. The kit does not encode the ICO's screening criteria and does not decide whether a DPIA is needed.

### ICO guidance on rights related to automated decision-making, including profiling

- URL: <https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/individual-rights/individual-rights/rights-related-to-automated-decision-making-including-profiling/>
- Status: **not fetched; kept generic.** URL from the ATRS guidance's link.
- How the kit uses it: `AIAK-DEC-001` asks for a challenge route and suggests asking a data protection lead whether rules on solely automated decisions apply. It makes no legal claim.

### The AQuA Book

- URL: <https://www.gov.uk/guidance/the-aqua-book>
- Status: **read in an official copy, with a caveat.** The role definitions were read in the Government Analysis Function's source repository <https://github.com/best-practice-and-impact/aqua_book_revision>. That repository holds the *final pre-publication draft* of the second edition and says the draft "has no official status"; it says the second edition was published on GOV.UK in July 2025.
- Confirmed (in the draft): the four roles commissioner, analyst, assurer and approver; "The roles of analyst and assurer shall be distinct from each other"; and, in the Proportionality chapter, "The assurer and the analyst shall be independent."
- Re-check against the published GOV.UK edition before quoting.

### The Orange Book

- URL: <https://www.gov.uk/government/publications/orange-book>
- Status: **not fetched; kept generic.** URL from the ATRS guidance's link, where it is described as further guidance on conducting risk assessments for public sector projects. The part titles ("Risk management principles", "The risk control framework") were seen in the Crown Commercial Service dataset above.
- How the kit uses it: as a pointer from the risk checks. The kit's prompts that a risk above appetite needs an owner and a control are the project's own design, not quotations from the Orange Book.

### NIST AI Risk Management Framework (AI RMF 1.0)

- URL: <https://www.nist.gov/itl/ai-risk-management-framework> (publication: NIST AI 100-1, DOI 10.6028/NIST.AI.100-1)
- Status: **read in an official copy.** The four functions, their one-line descriptions and the subcategory text were read from NIST's own machine-readable AI RMF 1.0 dataset (an export of NIST's Cybersecurity and Privacy Reference Tool) in <https://github.com/usnistgov/capordino> (`cprt_AI_100_1_0_0_07-07-2026.json`). The title, identifier, year (2023) and DOI were read from NIST's bibliographic record in <https://github.com/usnistgov/NIST-Tech-Pubs>. The release date (26 January 2023) and that the framework is intended for voluntary use were **confirmed via search**.
- How the kit uses it: function and subcategory references in the crosswalk and in rule citations. Only subcategories whose text is stored in `NIST_SUBCATEGORIES` in `src/ai_assurance_kit/sources.py` can be cited.

## Re-checking

Guidance changes. To re-check:

1. Open each URL above and compare it with what this page says was confirmed.
2. For the ATRS, check the current template version and its section names against `ATRS_SECTIONS` in `sources.py`.
3. For the AI Playbook, compare the principle headings with `AI_PLAYBOOK_PRINCIPLES` in `sources.py`.
4. For NIST, compare any cited subcategory with `NIST_SUBCATEGORIES`.
5. Update this page with the date and method, and adjust rule wording if a source has moved on.
