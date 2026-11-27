# Published GOV.UK ATRS Reference Adaptations

These three YAML records are independent open-source schema adaptations of public submissions
published by their respective UK public bodies on the GOV.UK
[Algorithmic Transparency Recording Standard (ATRS) repository](https://www.gov.uk/algorithmic-transparency-records)
under the Open Government Licence v3.0 (OGL v3.0). They are reference examples only — not official
GOV.UK publications and not authored on behalf of those bodies. Each file links directly to its
primary GOV.UK URL and notes the `public_updated_at` timestamp from the GOV.UK Content API.

Because public ATRS records summarise governance rather than exposing internal control registers,
formal approval dates, named internal assurers, or `1..5` numeric risk scores, fields that are
not stated in the public record are either left unset cleanly or explicitly marked in each YAML
header as schema-required adapter proxies (for example, ordinal `1..5` `likelihood`/`impact`
estimates, `public_updated_at` fallback dates on evaluation entries, and placeholder `decided_by`
labels where omitted). Running `aiak check examples/published-atrs/` therefore illustrates what a
proportionate reviewer notices when comparing a public disclosure against internal assurance records.

| File | Organisation | Tool | Status in source | Primary GOV.UK record |
|---|---|---|---|---|
| [ofsted-social-care-writing-assistant.yaml](ofsted-social-care-writing-assistant.yaml) | Ofsted | AI Writing Assistant (Social Care) | Not progressed after beta (`retired`) | [ATRS record](https://www.gov.uk/algorithmic-transparency-records/ai-writing-assistant-social-care) |
| [cabinet-office-assist.yaml](cabinet-office-assist.yaml) | Cabinet Office (GCS) | Assist | Live (`c. 8,500` users) | [ATRS record](https://www.gov.uk/algorithmic-transparency-records/cabinet-office-assist) |
| [cqc-risk-categorisation.yaml](cqc-risk-categorisation.yaml) | Care Quality Commission | Risk Categorisation | Live (`~46,000` scores/month) | [ATRS record](https://www.gov.uk/algorithmic-transparency-records/care-quality-commission-risk-categorisation) |
