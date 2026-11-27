"""The rules. Each one is a prompt for human judgement, not a verdict.

Writing a rule:
* keep the condition narrow and objective (it reads the record, nothing else);
* phrase the message as what to record or decide next, not as "non-compliant";
* cite the source that makes the prompt worth asking, with a pointer a reader can find;
* add a trigger test and a non-trigger test in tests/test_rules.py.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from ai_assurance_kit.checks.engine import CheckContext, Hit, Registry, Severity
from ai_assurance_kit.schema import (
    STATUS_ORDER,
    ActionMode,
    AIUseRecord,
    ATRSDetermination,
    ControlStatus,
    DecisionRole,
    DecisionType,
    DPIAStatus,
    EvidenceKind,
    Permission,
    Person,
    Status,
)
from ai_assurance_kit.sources import Ref, atrs, nist, playbook

REGISTRY = Registry()
rule = REGISTRY.rule

PLACEHOLDER = "REPLACE"

_READ_FREELY = Ref("kit", "Read freely, write carefully")
_BUILD_NOT_DEPLOY = Ref("kit", "Permission to build is not permission to deploy")
_USAGE_NOT_QUALITY = Ref("kit", "Usage is not quality")
_CRITIC_NOT_VERIFIER = Ref("kit", "A second model is a critic, not a verifier")
_FIX_DATA_FIRST = Ref("kit", "Fix the data before adding an agent")


def _at_least(record: AIUseRecord, status: Status) -> bool:
    return STATUS_ORDER[record.status] >= STATUS_ORDER[status]


def _norm(name: str) -> str:
    return " ".join(name.casefold().split())


def _same_person(a: Person | None, b: Person | None) -> bool:
    return bool(a and b and a.name and b.name and _norm(a.name) == _norm(b.name))


def _same_role_without_distinct_names(a: Person | None, b: Person | None) -> bool:
    if a is None or b is None or (a.name and b.name):
        return False
    if _norm(a.role) != _norm(b.role):
        return False
    return not a.team or not b.team or _norm(a.team) == _norm(b.team)


def _strings(value: Any, path: str = "") -> Iterator[tuple[str, str]]:
    if isinstance(value, dict):
        for k, v in value.items():
            yield from _strings(v, f"{path}.{k}" if path else str(k))
    elif isinstance(value, list):
        for i, v in enumerate(value):
            yield from _strings(v, f"{path}[{i}]")
    elif isinstance(value, str):
        yield path, value


# --------------------------------------------------------------------------- record hygiene


@rule(
    "AIAK-META-001",
    "Template placeholders remain",
    Severity.info,
    """A record that still contains template text reads as complete but is not. Checks on
    placeholder values say little about the real use.""",
    refs=[Ref("kit", "Make uncertainty visible")],
    skip_statuses=(),
)
def placeholders(record: AIUseRecord, ctx: CheckContext) -> Iterator[Hit]:
    fields = tuple(
        path for path, text in _strings(record.model_dump(mode="json")) if PLACEHOLDER in text
    )
    if fields:
        yield Hit(
            f"{len(fields)} field(s) still contain '{PLACEHOLDER}' template text. "
            "Fill them in, or write 'unknown' so the gap is visible.",
            fields,
        )


# --------------------------------------------------------------------------- actions


@rule(
    "AIAK-ACT-001",
    "Sends or writes without a human approval step",
    Severity.high,
    """Actions that send or write change things outside the tool and are hard to undo. Reading
    and drafting can be checked afterwards; sending and writing need a person, or an explicit
    decision to go without one, before the action happens.""",
    refs=[
        _READ_FREELY,
        playbook(4),
        nist("GOVERN 3.2"),
        nist("MAP 3.5"),
    ],
)
def sends_without_approval(record: AIUseRecord, ctx: CheckContext) -> Iterator[Hit]:
    a = record.actions
    if a.mode is ActionMode.autonomous:
        yield Hit(
            "The system sends or writes without a person approving each action. Record who "
            "decided that per-action approval is not needed, the limits that apply (what, to "
            "whom, how often) and how errors are noticed and reversed.",
            ("actions.mode",),
        )
    elif a.mode is ActionMode.writes_with_approval and not a.human_approval_step:
        yield Hit(
            "The record says actions are approved, but no approval step is described. Record "
            "who approves each send or write, what they see first, and what happens on reject.",
            ("actions.human_approval_step",),
        )


@rule(
    "AIAK-ACT-002",
    "No way to stop the system is recorded",
    Severity.warning,
    """A system that acts needs a known, tested way to pause it. Without one, a fault keeps
    acting while people work out who can switch it off.""",
    refs=[nist("MANAGE 2.4"), _READ_FREELY],
)
def no_stop_mechanism(record: AIUseRecord, ctx: CheckContext) -> Iterator[Hit]:
    a = record.actions
    if a.mode in (ActionMode.writes_with_approval, ActionMode.autonomous) and not a.stop_mechanism:
        yield Hit(
            "Record how the system can be paused or switched off quickly, who can do it, and "
            "when it was last tried.",
            ("actions.stop_mechanism",),
        )


_TOO_MUCH_BY_MODE: dict[ActionMode, set[Permission]] = {
    ActionMode.read_only: {Permission.write, Permission.send, Permission.delete, Permission.admin},
    ActionMode.drafts: {Permission.send, Permission.delete, Permission.admin},
    ActionMode.writes_with_approval: {Permission.delete, Permission.admin},
    ActionMode.autonomous: {Permission.delete, Permission.admin},
}


@rule(
    "AIAK-ACT-003",
    "Connector permissions exceed what the system is recorded as doing",
    Severity.warning,
    """Permissions are what a system can do; the action mode is what the team says it does. A
    gap between the two is unused power that a fault, a prompt injection or a later change can
    use.""",
    refs=[_READ_FREELY, playbook(3), nist("MAP 4.2")],
)
def excess_permissions(record: AIUseRecord, ctx: CheckContext) -> Iterator[Hit]:
    mode = record.actions.mode
    too_much = _TOO_MUCH_BY_MODE[mode]
    for i, conn in enumerate(record.access.connectors):
        extra = sorted(p.value for p in too_much.intersection(conn.permissions))
        if extra:
            if mode in (ActionMode.read_only, ActionMode.drafts):
                advice = (
                    "Remove the permission, or update the action mode and the controls that go "
                    "with it."
                )
            else:
                advice = (
                    "Remove the excess permission, or record why it is needed and the controls "
                    "that restrict it."
                )
            yield Hit(
                f"Connector '{conn.name}' has {', '.join(extra)} permission while the action mode "
                f"is '{mode.value}'. {advice}",
                (f"access.connectors[{i}].permissions",),
            )


@rule(
    "AIAK-ACT-004",
    "Recipients of sends or writes are not recorded",
    Severity.warning,
    """Who receives an action decides who is affected when it goes wrong. It is also what a
    later change review compares against.""",
    refs=[_READ_FREELY, nist("MAP 1.1")],
)
def no_recipients(record: AIUseRecord, ctx: CheckContext) -> Iterator[Hit]:
    a = record.actions
    if a.mode in (ActionMode.writes_with_approval, ActionMode.autonomous) and not a.recipients:
        yield Hit(
            "List who receives what the system sends or writes (for example 'applicants' or "
            "'case management system').",
            ("actions.recipients",),
        )


# --------------------------------------------------------------------------- data


@rule(
    "AIAK-DATA-001",
    "Personal data without a completed DPIA or screening decision",
    Severity.high,
    """Whether a data protection impact assessment is needed is a decision for the
    organisation, typically involving its data protection lead. The kit cannot make it, but it
    can notice when no decision is recorded or a live system has an unfinished DPIA.""",
    refs=[
        Ref("ico-dpia"),
        atrs("Development Data Specification (Tier 2)"),
        atrs("Risks, Mitigations and Impact Assessments (Tier 2)"),
        nist("MEASURE 2.10"),
    ],
)
def no_dpia_screening(record: AIUseRecord, ctx: CheckContext) -> Iterator[Hit]:
    d = record.data
    if not d.personal_data:
        return
    if d.dpia.status is DPIAStatus.not_screened:
        yield Hit(
            "Personal data is involved and no DPIA screening is recorded. Ask your data "
            "protection lead to screen it, then record the outcome, who decided and when.",
            ("data.dpia.status",),
        )
    elif record.status is Status.live and d.dpia.status is DPIAStatus.required_in_progress:
        yield Hit(
            "Personal data is involved and the system is live while its DPIA is still in "
            "progress. Complete the DPIA and update data.dpia.status, or record who decided to "
            "go live before completion.",
            ("data.dpia.status",),
        )
    elif d.dpia.status is DPIAStatus.screened_not_required and not d.dpia.decided_by:
        yield Hit(
            "Personal data is involved and the DPIA was screened as not required, with no "
            "deciding role recorded. Record who made that screening call and when.",
            ("data.dpia.decided_by",),
        )


@rule(
    "AIAK-DATA-002",
    "No retention period recorded for personal data",
    Severity.warning,
    """AI tools create new copies of data: prompts, outputs, logs and caches. Each needs a
    retention period, or it is kept by default.""",
    refs=[atrs("Operational Data Specification (Tier 2)"), nist("MEASURE 2.10")],
)
def no_retention(record: AIUseRecord, ctx: CheckContext) -> Iterator[Hit]:
    if record.data.personal_data and not record.data.retention:
        yield Hit(
            "Record how long inputs, outputs and logs containing personal data are kept, and "
            "where.",
            ("data.retention",),
        )


@rule(
    "AIAK-DATA-003",
    "Special category data screened out of a DPIA without a recorded rationale",
    Severity.info,
    """Screening special category data as not needing a DPIA may be right, but the reasoning
    should be findable later.""",
    refs=[Ref("ico-dpia")],
)
def special_category_screened_out(record: AIUseRecord, ctx: CheckContext) -> Iterator[Hit]:
    d = record.data
    if (
        d.special_category_data
        and d.dpia.status is DPIAStatus.screened_not_required
        and not (d.dpia.reference and d.dpia.decided_by)
    ):
        yield Hit(
            "Special category data is involved and the DPIA was screened as not required. Add "
            "a reference to the screening note and the role that decided.",
            ("data.dpia.reference", "data.dpia.decided_by"),
        )


# --------------------------------------------------------------------------- transparency


@rule(
    "AIAK-TRANS-001",
    "ATRS: likely in scope, record the determination",
    Severity.warning,
    """The ATRS guidance says the standard is mandatory for all government departments and for
    arm's-length bodies which deliver public or frontline services or directly interact with the
    general public; within those organisations it is mandatory for algorithmic tools which "have
    a significant influence on a decision-making process with public effect, or directly
    interact with the general public". The kit cannot decide whether a tool is in scope or
    whether an exemption applies; it only notices the features that make the question worth
    asking.""",
    refs=[
        Ref("atrs-scope"),
        Ref("atrs-guidance", "ATRS purpose and scope"),
    ],
)
def atrs_determination(record: AIUseRecord, ctx: CheckContext) -> Iterator[Hit]:
    r = record.reliance
    reasons = []
    if r.public_facing:
        reasons.append("members of the public interact with it directly")
    if r.public_effect and r.significant_influence:
        reasons.append("its outputs significantly influence decisions with public effect")
    if not reasons:
        return
    if record.transparency.atrs_determination is ATRSDetermination.not_assessed:
        yield Hit(
            f"The record says {' and '.join(reasons)}. If your organisation is covered by the "
            "ATRS mandatory scope, this tool is likely in scope. Record the determination (in "
            "scope or out of scope, and why) in transparency.atrs_determination.",
            ("transparency.atrs_determination",),
        )
    elif (
        record.transparency.atrs_determination is ATRSDetermination.out_of_scope
        and not record.transparency.rationale
    ):
        yield Hit(
            f"The record says {' and '.join(reasons)}, yet transparency.atrs_determination is "
            "'out_of_scope' with no rationale recorded. Record why an exemption or scope "
            "exclusion applies in transparency.rationale.",
            ("transparency.rationale",),
        )


@rule(
    "AIAK-TRANS-002",
    "Public-facing use with no user notice recorded",
    Severity.info,
    """People who interact with an AI system directly should be able to tell that they are
    doing so, and where to go if it gets something wrong.""",
    refs=[playbook(7), Ref("atrs-guidance", "ATRS purpose and scope")],
)
def no_user_notice(record: AIUseRecord, ctx: CheckContext) -> Iterator[Hit]:
    if record.reliance.public_facing and not record.reliance.user_notice:
        yield Hit(
            "Record how members of the public are told that AI is involved and what it can "
            "and cannot do.",
            ("reliance.user_notice",),
        )


# --------------------------------------------------------------------------- roles


@rule(
    "AIAK-ROLE-001",
    "Builder and assurer appear to be the same person",
    Severity.high,
    """The AQuA Book, which this kit borrows its roles from, keeps the analyst and assurer roles
    separate: the analyst assures their own work, and formal assurance comes from someone else.
    The kit treats the builder as the analyst role.""",
    refs=[Ref("aqua-book", "Roles and responsibilities"), nist("MEASURE 1.3")],
)
def builder_is_assurer(record: AIUseRecord, ctx: CheckContext) -> Iterator[Hit]:
    acc = record.accountability
    if _same_person(acc.builder, acc.assurer):
        assert acc.assurer is not None
        # Name the roles, not the person: names are optional and can be redacted from cards,
        # and prompts are copied into cards, JSON output and CI logs.
        yield Hit(
            f"The builder ('{acc.builder.role}') and the assurer ('{acc.assurer.role}') are "
            "recorded with the same name. Name an assurer who did not build it, or record why "
            "that is not possible and who accepts that.",
            ("accountability.builder", "accountability.assurer"),
        )
    elif _same_role_without_distinct_names(acc.builder, acc.assurer):
        assert acc.assurer is not None
        yield Hit(
            f"The builder and the assurer are both recorded under the same role "
            f"('{acc.builder.role}') without distinct names. Name a separate assurer role or "
            "distinct people, or record why that is not possible and who accepts that.",
            ("accountability.builder", "accountability.assurer"),
        )


@rule(
    "AIAK-ROLE-002",
    "No assurer named",
    Severity.warning,
    """Proportionate assurance still needs someone to do it. Once a use is approved to build,
    it should be clear who will check it.""",
    refs=[Ref("aqua-book", "Proportionality"), nist("GOVERN 2.1")],
)
def no_assurer(record: AIUseRecord, ctx: CheckContext) -> Iterator[Hit]:
    if _at_least(record, Status.approved_to_build) and record.accountability.assurer is None:
        yield Hit(
            "Name the role that will assure this use (someone other than the builder).",
            ("accountability.assurer",),
        )


@rule(
    "AIAK-ROLE-003",
    "Live with no named maintainer",
    Severity.high,
    """AI systems change after launch: models are updated, data drifts, prompts are edited.
    A live system with nobody responsible for it degrades without anyone noticing.""",
    refs=[
        nist("MANAGE 4.1"),
        nist("GOVERN 2.1"),
        atrs("Owner and Responsibility (Tier 2)"),
        playbook(5),
    ],
)
def no_maintainer(record: AIUseRecord, ctx: CheckContext) -> Iterator[Hit]:
    if record.status is Status.live and record.accountability.maintainer is None:
        yield Hit(
            "Name who monitors the live system, applies updates and responds to incidents.",
            ("accountability.maintainer",),
        )


# --------------------------------------------------------------------------- evaluation


@rule(
    "AIAK-EVAL-001",
    "Live with no evaluation evidence",
    Severity.high,
    """Going live should rest on evidence that the system works well enough for this use, in
    conditions like the real ones.""",
    refs=[nist("MEASURE 2.3"), nist("MANAGE 1.1"), playbook(5)],
)
def live_without_evidence(record: AIUseRecord, ctx: CheckContext) -> Iterator[Hit]:
    if record.status is Status.live and not record.evaluation:
        yield Hit(
            "No evaluation evidence is recorded. Add what was tested, on what data, by whom, "
            "and what the results were, including the human effort needed to check outputs.",
            ("evaluation",),
        )


@rule(
    "AIAK-EVAL-002",
    "Only usage metrics recorded as evidence",
    Severity.warning,
    """How often a tool is used says nothing about whether its outputs are right. Usage can
    rise while quality falls.""",
    refs=[_USAGE_NOT_QUALITY, nist("MEASURE 2.3")],
)
def usage_only(record: AIUseRecord, ctx: CheckContext) -> Iterator[Hit]:
    kinds = {e.kind for e in record.evaluation}
    if kinds == {EvidenceKind.usage_metrics}:
        yield Hit(
            "All recorded evidence is usage metrics. Add evidence about output quality, such "
            "as a human-checked sample.",
            ("evaluation",),
        )


_HUMAN_CHECKED = frozenset({EvidenceKind.human_review_sample, EvidenceKind.pilot})


@rule(
    "AIAK-EVAL-003",
    "Model-graded evidence without a human-checked sample",
    Severity.warning,
    """A second model can find problems, but agreement between models is not verification.
    Model grading needs calibrating against outputs checked by people who know the subject.""",
    refs=[_CRITIC_NOT_VERIFIER, nist("MEASURE 4.2"), nist("MEASURE 1.3")],
)
def model_graded_without_human_sample(record: AIUseRecord, ctx: CheckContext) -> Iterator[Hit]:
    kinds = {e.kind for e in record.evaluation}
    if EvidenceKind.model_graded in kinds and not kinds & _HUMAN_CHECKED:
        yield Hit(
            "Quality evidence includes model grading but no human-checked sample or pilot. Add "
            "a sample checked by people with subject knowledge, and record how often they "
            "disagreed with the grader.",
            ("evaluation",),
        )


@rule(
    "AIAK-EVAL-004",
    "No independent evaluation recorded",
    Severity.info,
    """Evaluation by the team that built a system is necessary but tends to test what the team
    expected. Someone outside the build team finds different problems.""",
    refs=[nist("MEASURE 1.3"), Ref("aqua-book", "Roles and responsibilities")],
)
def no_independent_evidence(record: AIUseRecord, ctx: CheckContext) -> Iterator[Hit]:
    if (
        _at_least(record, Status.in_test)
        and record.evaluation
        and not any(e.independent for e in record.evaluation)
    ):
        yield Hit(
            "None of the recorded evaluations is marked independent. Record any done by "
            "someone outside the build team, or plan one.",
            ("evaluation",),
        )


# --------------------------------------------------------------------------- review


@rule(
    "AIAK-REV-001",
    "Review date has passed",
    Severity.warning,
    """A record is a snapshot. After its review date nobody has confirmed that it still
    describes the system.""",
    refs=[nist("GOVERN 1.5"), Ref("atrs-guidance", "Updating your ATRS record")],
)
def review_overdue(record: AIUseRecord, ctx: CheckContext) -> Iterator[Hit]:
    due = record.review.next_review
    if due is not None and due < ctx.today:
        days = (ctx.today - due).days
        yield Hit(
            f"The next review was due on {due.isoformat()} ({days} day{'' if days == 1 else 's'} "
            f"before {ctx.today.isoformat()}). Review the record, or set a new date and say why.",
            ("review.next_review",),
        )


@rule(
    "AIAK-REV-002",
    "No next review date",
    Severity.warning,
    """Systems in test or live use change. A review date makes someone look again.""",
    refs=[nist("GOVERN 1.5")],
)
def no_review_date(record: AIUseRecord, ctx: CheckContext) -> Iterator[Hit]:
    if _at_least(record, Status.in_test) and record.review.next_review is None:
        yield Hit("Set review.next_review.", ("review.next_review",))


# --------------------------------------------------------------------------- risks


@rule(
    "AIAK-RISK-001",
    "Risk above appetite with no owner",
    Severity.high,
    """A risk above the organisation's appetite needs someone accountable for treating it or
    for accepting it. Without an owner it is recorded but not managed.""",
    refs=[Ref("orange-book"), nist("GOVERN 1.3"), nist("MAP 1.5"), nist("MANAGE 1.3")],
)
def risk_without_owner(record: AIUseRecord, ctx: CheckContext) -> Iterator[Hit]:
    appetite = ctx.policy.risk.appetite_score
    for i, r in enumerate(record.risks):
        if r.score > appetite and not r.owner:
            yield Hit(
                f"Risk {r.id} scores {r.likelihood} x {r.impact} = {r.score}, above the policy "
                f"appetite of {appetite}, and has no owner. Name the role that owns it.",
                (f"risks[{i}].owner",),
            )


@rule(
    "AIAK-RISK-002",
    "Risk above appetite with no control in place",
    Severity.warning,
    """Planned controls do not reduce risk yet. A risk above appetite should have at least one
    control in place, or an active recorded decision to accept it (accepted_by and
    acceptance_rationale, with an optional acceptance_expiry).""",
    refs=[nist("MANAGE 1.3"), Ref("orange-book")],
)
def risk_without_control(record: AIUseRecord, ctx: CheckContext) -> Iterator[Hit]:
    appetite = ctx.policy.risk.appetite_score
    for i, r in enumerate(record.risks):
        if r.score <= appetite:
            continue
        linked = [c for cid in r.controls if (c := record.control(cid)) is not None]
        if any(c.status is ControlStatus.in_place for c in linked):
            continue
        if linked:
            state = (
                f"none of its controls is in place yet (planned: {', '.join(c.id for c in linked)})"
            )
        else:
            state = "it has no linked controls"
        if r.accepted_by is not None:
            if r.acceptance_expiry is not None and r.acceptance_expiry < ctx.today:
                yield Hit(
                    f"Risk {r.id} ({r.score}) is above appetite and {state}; its recorded "
                    f"acceptance expired on {r.acceptance_expiry.isoformat()}. Put a control in "
                    "place, or renew the acceptance.",
                    (f"risks[{i}].acceptance_expiry", f"risks[{i}].controls"),
                )
                continue
            if not r.acceptance_rationale:
                yield Hit(
                    f"Risk {r.id} ({r.score}) is above appetite and {state}; acceptance is "
                    "recorded without a rationale. Add acceptance_rationale, or put a control in "
                    "place.",
                    (f"risks[{i}].acceptance_rationale", f"risks[{i}].controls"),
                )
                continue
            continue
        yield Hit(
            f"Risk {r.id} ({r.score}) is above appetite and {state}. Put a control in place, "
            "or record who accepts the risk.",
            (f"risks[{i}].controls",),
        )


@rule(
    "AIAK-RISK-003",
    "No risks recorded",
    Severity.warning,
    """An empty risk list usually means the risks have not been assessed yet, not that there
    are none. It is a warning, like a missing assurer or review date, so that a record with no
    risks recorded cannot pass a `--fail-on warning` gate that the same record with an honestly
    recorded, untreated risk would fail.""",
    refs=[atrs("Risks, Mitigations and Impact Assessments (Tier 2)"), nist("MAP 5.1")],
)
def no_risks(record: AIUseRecord, ctx: CheckContext) -> Iterator[Hit]:
    if _at_least(record, Status.approved_to_build) and not record.risks:
        yield Hit("Record the main risks, with likelihood, impact and owner.", ("risks",))


# --------------------------------------------------------------------------- purpose


@rule(
    "AIAK-PURP-001",
    "No alternatives recorded",
    Severity.info,
    """Many problems brought to AI are better solved by fixing the data or the process, or by
    ordinary automation. Recording what else was considered shows the choice was made.""",
    refs=[
        atrs("Description and Rationale (Tier 2)"),
        nist("MANAGE 2.1"),
        playbook(6),
        _FIX_DATA_FIRST,
    ],
)
def no_alternatives(record: AIUseRecord, ctx: CheckContext) -> Iterator[Hit]:
    if not record.alternatives_considered:
        yield Hit(
            "Record the simpler or non-AI options considered and why they were not chosen.",
            ("alternatives_considered",),
        )


# --------------------------------------------------------------------------- decisions about people


@rule(
    "AIAK-DEC-001",
    "Automated decisions with public effect and no challenge route",
    Severity.high,
    """When an output is the decision, the people affected need a way to question it. Rules on
    solely automated decisions may also apply; that is a question for your data protection
    lead.""",
    refs=[
        atrs("Deployment Context (Tier 2)"),
        Ref("ico-adm"),
        nist("MEASURE 3.3"),
    ],
)
def automated_without_challenge(record: AIUseRecord, ctx: CheckContext) -> Iterator[Hit]:
    r = record.reliance
    if (
        r.decision_role is DecisionRole.automated_decision
        and r.public_effect
        and not r.challenge_route
    ):
        yield Hit(
            "Record how affected people can question or appeal an outcome, and ask your data "
            "protection lead whether rules on solely automated decisions apply.",
            ("reliance.challenge_route",),
        )


@rule(
    "AIAK-DEC-002",
    "Decision support with no human review described",
    Severity.warning,
    """Decision support is only support if a person reviews the output with enough time,
    information and authority to disagree with it.""",
    refs=[playbook(4), nist("MAP 2.2"), nist("MAP 3.5")],
)
def decision_support_without_review(record: AIUseRecord, ctx: CheckContext) -> Iterator[Hit]:
    r = record.reliance
    if r.decision_role is DecisionRole.decision_support and not r.human_review:
        yield Hit(
            "Describe who reviews outputs before they shape a decision, what they see, and how "
            "often they overrule the system.",
            ("reliance.human_review",),
        )


# --------------------------------------------------------------------------- lifecycle


_REQUIRED_DECISIONS: dict[Status, tuple[DecisionType, ...]] = {
    Status.approved_to_build: (DecisionType.approve_build,),
    Status.in_test: (DecisionType.approve_build,),
    Status.live: (DecisionType.approve_build, DecisionType.go_live),
}


@rule(
    "AIAK-LIFE-001",
    "Status is ahead of the recorded decisions",
    Severity.warning,
    """Approving a build, connecting data, granting access and going live are separate
    decisions, often for different people. A status with no matching decision suggests one
    approval is being read as another.""",
    refs=[_BUILD_NOT_DEPLOY, nist("MANAGE 1.1"), playbook(10)],
)
def status_ahead_of_decisions(record: AIUseRecord, ctx: CheckContext) -> Iterator[Hit]:
    recorded = {d.type for d in record.decisions}
    missing = [t.value for t in _REQUIRED_DECISIONS.get(record.status, ()) if t not in recorded]
    if missing:
        yield Hit(
            f"Status is '{record.status.value}' but no {' or '.join(missing)} decision is "
            "recorded. Record who decided, and when.",
            ("decisions",),
        )
