"""The AI use record: one structured description of one AI use case.

Design notes
------------
* ``extra="forbid"`` everywhere. A typo such as ``personal_date`` is an error, not a silently
  ignored field, because a silently ignored field is how a record ends up saying less than its
  author thinks it says.
* Enumerations are small and ordered where order means something (action mode, decision role,
  lifecycle status), so a diff can tell "more autonomous" from "less autonomous".
* Role titles are required; personal names are optional. Published transparency records usually
  name roles rather than people, while internal assurance sometimes needs to know whether two
  roles are held by the same person.
"""

from __future__ import annotations

import datetime as dt
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, StrictBool, model_validator

SCHEMA_VERSION = "1.0"


def _whole_number_only(value: object) -> object:
    # pydantic's lax mode would read `likelihood: yes` (YAML for true) as 1 and "4" as 4. The
    # published JSON Schema rejects both, and a record should say what it means.
    if isinstance(value, bool | str):
        raise ValueError("Input should be a whole number, not true/false or quoted text")
    return value


def _blank_to_none(value: object) -> object:
    # Preserve backwards compatibility where blank strings in optional fields such as
    # third_party_supplier are treated as unset rather than stored as "".
    if isinstance(value, str) and not value.strip():
        return None
    return value


# Types shared by the models below. The constraints also appear in the exported JSON Schema,
# so `aiak validate` and a JSON Schema validator accept and reject the same values.
WholeNumber = Annotated[int, BeforeValidator(_whole_number_only)]
# The bound comes before the validator so that it exports as JSON Schema "minimum".
Count = Annotated[int, Field(ge=0), BeforeValidator(_whole_number_only)]
Rating = Annotated[int, Field(ge=1, le=5), BeforeValidator(_whole_number_only)]
Text = Annotated[str, Field(min_length=1)]  # a non-empty entry: "" would say nothing
BlankAsNone = Annotated[str | None, BeforeValidator(_blank_to_none)]


class _Model(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, use_enum_values=False)


# --------------------------------------------------------------------------- enumerations


class Status(StrEnum):
    """Lifecycle status. Order matters: later statuses need more evidence."""

    proposed = "proposed"
    approved_to_build = "approved_to_build"
    in_test = "in_test"
    live = "live"
    retired = "retired"


STATUS_ORDER: dict[Status, int] = {s: i for i, s in enumerate(Status)}


class ModelKind(StrEnum):
    generative = "generative"
    predictive = "predictive"
    rules_based = "rules_based"
    other = "other"


class Hosting(StrEnum):
    vendor_saas = "vendor_saas"
    organisation_cloud = "organisation_cloud"
    on_premises = "on_premises"
    local_device = "local_device"
    other = "other"


class DPIAStatus(StrEnum):
    not_screened = "not_screened"
    screened_not_required = "screened_not_required"
    required_in_progress = "required_in_progress"
    completed = "completed"


class Permission(StrEnum):
    read = "read"
    write = "write"
    send = "send"
    delete = "delete"
    admin = "admin"


class ActionMode(StrEnum):
    """What the system does with its outputs. Order matters: later modes act more on their own."""

    read_only = "read_only"
    drafts = "drafts"
    writes_with_approval = "writes_with_approval"
    autonomous = "autonomous"


ACTION_MODE_ORDER: dict[ActionMode, int] = {m: i for i, m in enumerate(ActionMode)}


class DecisionRole(StrEnum):
    """How much the output shapes a decision. Order matters."""

    information_only = "information_only"
    decision_support = "decision_support"
    automated_decision = "automated_decision"


DECISION_ROLE_ORDER: dict[DecisionRole, int] = {r: i for i, r in enumerate(DecisionRole)}


class ControlStatus(StrEnum):
    planned = "planned"
    in_place = "in_place"


class EvidenceKind(StrEnum):
    human_review_sample = "human_review_sample"
    offline_test_set = "offline_test_set"
    pilot = "pilot"
    red_team = "red_team"
    bias_review = "bias_review"
    accessibility_test = "accessibility_test"
    security_review = "security_review"
    user_research = "user_research"
    model_graded = "model_graded"
    usage_metrics = "usage_metrics"
    other = "other"


class DecisionType(StrEnum):
    """Separate governance decisions. Permission to build is not permission to deploy."""

    approve_build = "approve_build"
    connect_data = "connect_data"
    grant_access = "grant_access"
    share = "share"
    go_live = "go_live"
    retire = "retire"


class ATRSDetermination(StrEnum):
    not_assessed = "not_assessed"
    in_scope = "in_scope"
    out_of_scope = "out_of_scope"


# --------------------------------------------------------------------------- sections


class Person(_Model):
    """A role holder. The role title is required; the name is optional."""

    role: str = Field(min_length=1, description="Role title, e.g. 'Service owner'.")
    name: Text | None = Field(
        default=None,
        description="Name of the person holding the role (internal use; can be redacted).",
    )
    team: Text | None = None


class Accountability(_Model):
    """Who owns, builds, maintains and assures the use.

    Loosely mirrors the AQuA Book roles: business owner ~ commissioner, builder ~ analyst,
    assurer ~ assurer, approver ~ approver. Maintainer is added because AI systems change
    after launch.
    """

    business_owner: Person = Field(description="Accountable for the use and its outcomes.")
    builder: Person = Field(description="Builds or configures the system.")
    maintainer: Person | None = Field(
        default=None, description="Keeps it working after launch: monitoring, updates, fixes."
    )
    assurer: Person | None = Field(
        default=None, description="Reviews the work independently of the builder."
    )
    approver: Person | None = Field(
        default=None, description="Signs off that assurance is appropriate for the use."
    )


class System(_Model):
    description: str = Field(min_length=1, description="What the system is, in a sentence.")
    model_kind: ModelKind
    model: str = Field(min_length=1, description="Model or product name, or a generic label.")
    provider: str = Field(min_length=1, description="Who provides the model, or 'in-house'.")
    platform: Text | None = Field(default=None, description="Where it runs or is built.")
    hosting: Hosting
    third_party_supplier: BlankAsNone = Field(
        default=None, description="Supplier of the tool or model, if a third party is involved."
    )


class DPIA(_Model):
    status: DPIAStatus = DPIAStatus.not_screened
    reference: Text | None = None
    decided_by: Text | None = Field(default=None, description="Role that made the screening call.")
    date: dt.date | None = None


class Data(_Model):
    categories: list[Text] = Field(min_length=1, description="Kinds of data the system uses.")
    personal_data: StrictBool
    special_category_data: StrictBool = False
    sources: list[Text] = Field(default_factory=list)
    retention: Text | None = Field(
        default=None, description="How long inputs, outputs and logs are kept."
    )
    dpia: DPIA = Field(default_factory=DPIA)

    @model_validator(mode="after")
    def _special_implies_personal(self) -> Data:
        if self.special_category_data and not self.personal_data:
            raise ValueError(
                "special_category_data is true but personal_data is false; "
                "special category data is a kind of personal data"
            )
        return self


class Connector(_Model):
    name: str = Field(min_length=1)
    system: Text | None = Field(default=None, description="The system it connects to.")
    permissions: list[Permission] = Field(min_length=1)
    purpose: Text | None = None


class Access(_Model):
    users: str = Field(min_length=1, description="Who can use the tool.")
    connectors: list[Connector] = Field(default_factory=list)

    @model_validator(mode="after")
    def _unique_connectors(self) -> Access:
        names = [c.name for c in self.connectors]
        dupes = sorted({n for n in names if names.count(n) > 1})
        if dupes:
            raise ValueError(f"duplicate connector names: {', '.join(dupes)}")
        return self


class Actions(_Model):
    mode: ActionMode
    description: str = Field(min_length=1, description="What the system does with its outputs.")
    human_approval_step: Text | None = Field(
        default=None, description="Who approves each send or write, and how."
    )
    recipients: list[Text] = Field(
        default_factory=list, description="Who receives what the system sends or writes."
    )
    stop_mechanism: Text | None = Field(
        default=None, description="How the system can be paused or switched off quickly."
    )


class Scale(_Model):
    users: Count | None = None
    uses_per_month: Count | None = None


class Reliance(_Model):
    relied_on_by: list[Text] = Field(min_length=1, description="Who relies on the outputs.")
    how_outputs_are_used: str = Field(min_length=1)
    decision_role: DecisionRole
    public_facing: StrictBool = Field(
        description="Members of the public interact with it directly."
    )
    public_effect: StrictBool = Field(
        description="Outputs feed decisions that affect members of the public or organisations."
    )
    significant_influence: StrictBool = Field(
        default=False, description="Outputs significantly influence those decisions."
    )
    human_review: Text | None = Field(
        default=None, description="How a person checks outputs before they are relied on."
    )
    challenge_route: Text | None = Field(
        default=None, description="How affected people can question or appeal an outcome."
    )
    user_notice: Text | None = Field(
        default=None, description="How people are told that AI is involved."
    )
    scale: Scale = Field(default_factory=Scale)


class Risk(_Model):
    id: str = Field(min_length=1)
    description: str = Field(min_length=1)
    likelihood: Rating = Field(description="1 (rare) to 5 (almost certain).")
    impact: Rating = Field(description="1 (minimal) to 5 (severe).")
    owner: Text | None = Field(default=None, description="Role that owns this risk.")
    controls: list[Text] = Field(default_factory=list, description="IDs of controls that treat it.")
    residual_likelihood: Rating | None = Field(
        default=None,
        description="Expected likelihood after in-place controls (1 to 5).",
    )
    residual_impact: Rating | None = Field(
        default=None,
        description="Expected impact after in-place controls (1 to 5).",
    )
    accepted_by: Text | None = Field(
        default=None,
        description=(
            "Role that formally accepts the risk above appetite or without in-place controls."
        ),
    )
    acceptance_rationale: Text | None = Field(
        default=None,
        description="Why the risk is accepted and under what conditions.",
    )
    acceptance_expiry: dt.date | None = Field(
        default=None,
        description="Date by which a recorded risk acceptance expires and must be reviewed.",
    )

    @property
    def score(self) -> int:
        return self.likelihood * self.impact

    @property
    def residual_score(self) -> int | None:
        if self.residual_likelihood is None or self.residual_impact is None:
            return None
        return self.residual_likelihood * self.residual_impact

    @model_validator(mode="after")
    def _valid_residual_and_acceptance(self) -> Risk:
        if (self.residual_likelihood is None) != (self.residual_impact is None):
            raise ValueError("residual_likelihood and residual_impact must be set together")
        if (
            self.acceptance_rationale is not None or self.acceptance_expiry is not None
        ) and self.accepted_by is None:
            raise ValueError(
                "accepted_by is required when acceptance_rationale or acceptance_expiry is set"
            )
        return self


class Control(_Model):
    id: str = Field(min_length=1)
    description: str = Field(min_length=1)
    status: ControlStatus = ControlStatus.planned
    owner: Text | None = None


class Evidence(_Model):
    date: dt.date
    kind: EvidenceKind
    summary: str = Field(min_length=1)
    performed_by: Text | None = Field(default=None, description="Role that did the evaluation.")
    independent: StrictBool = Field(
        default=False, description="Done by someone other than the builder."
    )
    link: Text | None = None


class Decision(_Model):
    type: DecisionType
    date: dt.date
    by: str = Field(min_length=1, description="Role that took the decision.")
    note: Text | None = None


class Transparency(_Model):
    atrs_determination: ATRSDetermination = ATRSDetermination.not_assessed
    rationale: Text | None = None
    record_url: Text | None = None


class Review(_Model):
    last_reviewed: dt.date | None = None
    next_review: dt.date | None = None

    @model_validator(mode="after")
    def _next_after_last(self) -> Review:
        if self.last_reviewed and self.next_review and self.next_review < self.last_reviewed:
            raise ValueError(
                f"next_review ({self.next_review}) is before last_reviewed ({self.last_reviewed})"
            )
        return self


# --------------------------------------------------------------------------- the record


class AIUseRecord(_Model):
    """One AI use case, described well enough to review proportionately."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        title="AI use record",
        json_schema_extra={
            "description": (
                "A structured record of one AI use case (ai-assurance-kit). Unofficial; "
                "not government guidance."
            )
        },
    )

    schema_version: Literal["1.0"] = "1.0"
    id: str = Field(pattern=r"^[a-z0-9][a-z0-9-]*$", description="Stable slug, e.g. 'notes-ai'.")
    title: str = Field(min_length=1)
    version: str = Field(default="1", min_length=1, description="Version of this record.")
    status: Status
    organisation: Text | None = None
    summary: str = Field(
        min_length=1, description="Two or three plain-English sentences for a general reader."
    )
    purpose: str = Field(min_length=1, description="The problem this solves and for whom.")
    benefits: list[Text] = Field(default_factory=list)
    alternatives_considered: Text | None = Field(
        default=None, description="Non-AI or simpler options considered, and why not chosen."
    )
    accountability: Accountability
    system: System
    data: Data
    access: Access
    actions: Actions
    reliance: Reliance
    risks: list[Risk] = Field(default_factory=list)
    controls: list[Control] = Field(default_factory=list)
    evaluation: list[Evidence] = Field(default_factory=list)
    decisions: list[Decision] = Field(default_factory=list)
    transparency: Transparency = Field(default_factory=Transparency)
    review: Review = Field(default_factory=Review)

    @model_validator(mode="after")
    def _cross_references(self) -> AIUseRecord:
        problems: list[str] = []
        for label, ids in (
            ("risk", [r.id for r in self.risks]),
            ("control", [c.id for c in self.controls]),
        ):
            dupes = sorted({i for i in ids if ids.count(i) > 1})
            if dupes:
                problems.append(f"duplicate {label} ids: {', '.join(dupes)}")
        known = {c.id for c in self.controls}
        for risk in self.risks:
            missing = [c for c in risk.controls if c not in known]
            if missing:
                problems.append(f"risk {risk.id} refers to unknown controls: {', '.join(missing)}")
        if problems:
            raise ValueError("; ".join(problems))
        return self

    def control(self, control_id: str) -> Control | None:
        return next((c for c in self.controls if c.id == control_id), None)


def json_schema() -> dict[str, object]:
    """Return the JSON Schema (draft 2020-12) for an AI use record."""
    schema = AIUseRecord.model_json_schema()
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": (
            "https://raw.githubusercontent.com/dsugurtuna/ai-assurance-kit/main/"
            "schema/ai-use-record.schema.json"
        ),
        **schema,
    }
