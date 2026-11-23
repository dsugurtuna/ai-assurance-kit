# Published GOV.UK ATRS Examples

These three YAML records adapt real public submissions from the GOV.UK
[Algorithmic Transparency Recording Standard (ATRS) repository](https://www.gov.uk/algorithmic-transparency-records)
into `ai-assurance-kit` format. Each file links directly to its primary GOV.UK URL and notes the
published `public_updated_at` timestamp from the GOV.UK Content API.

Because public ATRS records summarise governance rather than exposing internal control registers,
formal approval dates, or named internal assurers, fields that are not stated in the public record
are left unset cleanly. Running `aiak check examples/published-atrs/` therefore illustrates what a
proportionate reviewer notices when auditing a public disclosure against internal assurance records.

| File | Organisation | Tool | Status in source | Primary GOV.UK record |
|---|---|---|---|---|
| [ofsted-social-care-writing-assistant.yaml](ofsted-social-care-writing-assistant.yaml) | Ofsted | AI Writing Assistant (Social Care) | Not progressed after beta (`retired`) | [ATRS record](https://www.gov.uk/algorithmic-transparency-records/ai-writing-assistant-social-care) |
| [cabinet-office-assist.yaml](cabinet-office-assist.yaml) | Cabinet Office (GCS) | Assist | Live (`c. 8,500` users) | [ATRS record](https://www.gov.uk/algorithmic-transparency-records/cabinet-office-assist) |
| [cqc-risk-categorisation.yaml](cqc-risk-categorisation.yaml) | Care Quality Commission | Risk Categorisation | Live (`~46,000` scores/month) | [ATRS record](https://www.gov.uk/algorithmic-transparency-records/care-quality-commission-risk-categorisation) |
