"""Public sources that inform the kit, with the pointers rules and docs cite.

Every rule cites one or more entries here. A citation means "this source is relevant to the
prompt", not "this source requires what the rule checks". The kit is informed by these sources;
it does not implement, certify or satisfy any of them.

See docs/SOURCES.md for how each source was checked and what remains unverified.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Source:
    """A public document the kit draws on."""

    id: str
    title: str
    publisher: str
    url: str


@dataclass(frozen=True)
class Ref:
    """A citation: a source plus an optional pointer inside it (a section, principle or ID)."""

    source: str
    pointer: str = ""

    @property
    def doc(self) -> Source:
        return SOURCES[self.source]

    def label(self) -> str:
        return f"{self.doc.title}: {self.pointer}" if self.pointer else self.doc.title


SOURCES: dict[str, Source] = {
    s.id: s
    for s in (
        Source(
            id="ai-playbook",
            title="AI Playbook for the UK Government",
            publisher="GOV.UK",
            url="https://www.gov.uk/government/publications/ai-playbook-for-the-uk-government",
        ),
        Source(
            id="atrs-guidance",
            title="Algorithmic Transparency Recording Standard (ATRS) guidance",
            publisher="GOV.UK",
            url=(
                "https://www.gov.uk/government/publications/"
                "guidance-for-organisations-using-the-algorithmic-transparency-recording-standard"
            ),
        ),
        Source(
            id="atrs-scope",
            title="ATRS mandatory scope and exemptions policy",
            publisher="GOV.UK",
            url=(
                "https://www.gov.uk/government/publications/"
                "algorithmic-transparency-recording-standard-mandatory-scope-and-exemptions-policy"
            ),
        ),
        Source(
            id="ico-dpia",
            title="ICO guidance on data protection impact assessments (DPIAs)",
            publisher="Information Commissioner's Office",
            url=(
                "https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/"
                "accountability-and-governance/data-protection-impact-assessments-dpias/"
            ),
        ),
        Source(
            id="ico-adm",
            title=(
                "ICO guidance on rights related to automated decision-making, including profiling"
            ),
            publisher="Information Commissioner's Office",
            url=(
                "https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/"
                "individual-rights/individual-rights/"
                "rights-related-to-automated-decision-making-including-profiling/"
            ),
        ),
        Source(
            id="aqua-book",
            title="The AQuA Book",
            publisher="GOV.UK",
            url="https://www.gov.uk/guidance/the-aqua-book",
        ),
        Source(
            id="orange-book",
            title="The Orange Book: management of risk",
            publisher="GOV.UK (HM Treasury)",
            url="https://www.gov.uk/government/publications/orange-book",
        ),
        Source(
            id="nist-ai-rmf",
            title="NIST AI Risk Management Framework (AI RMF 1.0, NIST AI 100-1)",
            publisher="US National Institute of Standards and Technology",
            url="https://www.nist.gov/itl/ai-risk-management-framework",
        ),
        Source(
            id="kit",
            title="ai-assurance-kit design principle",
            publisher="this project",
            url="https://github.com/dsugurtuna/ai-assurance-kit/blob/main/docs/WHY.md",
        ),
    )
}

# Principle titles of the AI Playbook for the UK Government, used in the crosswalk.
# Checked against the GOV.UK heading anchors (see docs/SOURCES.md for how).
AI_PLAYBOOK_PRINCIPLES: dict[int, str] = {
    1: "You know what AI is and what its limitations are",
    2: "You use AI lawfully, ethically and responsibly",
    3: "You know how to use AI securely",
    4: "You have meaningful human control at the right stages",
    5: "You understand how to manage the full AI life cycle",
    6: "You use the right tool for the job",
    7: "You are open and collaborative",
    8: "You work with commercial colleagues from the start",
    9: "You have the skills and expertise needed to implement and use AI solutions",
    10: (
        "You use these principles alongside your organisation's policies and have the right "
        "assurance in place"
    ),
}

# ATRS v4.0 sections. Tier 1 is for the general public; Tier 2 is for specialist audiences.
ATRS_SECTIONS: tuple[str, ...] = (
    "Summary Information (Tier 1)",
    "Owner and Responsibility (Tier 2)",
    "Description and Rationale (Tier 2)",
    "Deployment Context (Tier 2)",
    "Tool Specification (Tier 2)",
    "Model Specification (Tier 2)",
    "Development Data Specification (Tier 2)",
    "Operational Data Specification (Tier 2)",
    "Risks, Mitigations and Impact Assessments (Tier 2)",
)

# NIST AI RMF 1.0 core functions and their one-line descriptions.
NIST_FUNCTIONS: dict[str, str] = {
    "GOVERN": "A culture of risk management is cultivated and present.",
    "MAP": "Context is recognized and risks related to context are identified.",
    "MEASURE": "Identified risks are assessed, analyzed, or tracked.",
    "MANAGE": "Risks are prioritized and acted upon based on a projected impact.",
}


# The NIST AI RMF subcategories this kit cites, with their text as published by NIST in its
# AI RMF 1.0 reference dataset. Only these pointers can be cited, so the crosswalk cannot drift
# away from text that was checked.
NIST_SUBCATEGORIES: dict[str, str] = {
    "GOVERN 1.3": (
        "Processes and procedures are in place to determine the needed level of risk "
        "management activities based on the organization's risk tolerance."
    ),
    "GOVERN 1.5": (
        "Ongoing monitoring and periodic review of the risk management process and its outcomes "
        "are planned, organizational roles and responsibilities are clearly defined, including "
        "determining the frequency of periodic review."
    ),
    "GOVERN 1.6": (
        "Mechanisms are in place to inventory AI systems and are resourced according to "
        "organizational risk priorities."
    ),
    "GOVERN 2.1": (
        "Roles and responsibilities and lines of communication related to mapping, measuring, "
        "and managing AI risks are documented and are clear to individuals and teams throughout "
        "the organization."
    ),
    "GOVERN 3.2": (
        "Policies and procedures are in place to define and differentiate roles and "
        "responsibilities for human-AI configurations and oversight of AI systems."
    ),
    "GOVERN 6.1": (
        "Policies and procedures are in place that address AI risks associated with third-party "
        "entities, including risks of infringement of a third party's intellectual property or "
        "other rights."
    ),
    "MAP 1.1": (
        "Intended purpose, potentially beneficial uses, context-specific laws, norms and "
        "expectations, and prospective settings in which the AI system will be deployed are "
        "understood and documented. [...]"
    ),
    "MAP 1.5": "Organizational risk tolerances are determined and documented.",
    "MAP 2.2": (
        "Information about the AI system's knowledge limits and how system output may be "
        "utilized and overseen by humans is documented. [...]"
    ),
    "MAP 3.5": (
        "Processes for human oversight are defined, assessed, and documented in accordance with "
        "organizational policies from GOVERN function."
    ),
    "MAP 4.2": (
        "Internal risk controls for components of the AI system including third-party AI "
        "technologies are identified and documented."
    ),
    "MAP 5.1": (
        "Likelihood and magnitude of each identified impact (both potentially beneficial and "
        "harmful) based on expected use, past uses of AI systems in similar contexts, public "
        "incident reports, feedback from those external to the team that developed or deployed "
        "the AI system, or other data are identified and documented."
    ),
    "MEASURE 1.3": (
        "Internal experts who did not serve as front-line developers for the system and/or "
        "independent assessors are involved in regular assessments and updates. [...]"
    ),
    "MEASURE 2.3": (
        "AI system performance or assurance criteria are measured qualitatively or "
        "quantitatively and demonstrated for conditions similar to deployment setting(s). "
        "Measures are documented."
    ),
    "MEASURE 2.10": (
        "Privacy risk of the AI system - as identified in the MAP function - is examined and "
        "documented."
    ),
    "MEASURE 3.3": (
        "Feedback processes for end users and impacted communities to report problems and "
        "appeal system outcomes are established and integrated into AI system evaluation "
        "metrics."
    ),
    "MEASURE 4.2": (
        "Measurement results regarding AI system trustworthiness in deployment context(s) and "
        "across AI lifecycle are informed by input from domain experts and other relevant AI "
        "actors to validate whether the system is performing consistently as intended. "
        "Results are documented."
    ),
    "MANAGE 1.1": (
        "A determination is made as to whether the AI system achieves its intended purpose and "
        "stated objectives and whether its development or deployment should proceed."
    ),
    "MANAGE 1.3": (
        "Responses to the AI risks deemed high priority as identified by the Map function, are "
        "developed, planned, and documented. Risk response options can include mitigating, "
        "transferring, avoiding, or accepting."
    ),
    "MANAGE 2.1": (
        "Resources required to manage AI risks are taken into account, along with viable non-AI "
        "alternative systems, approaches, or methods - to reduce the magnitude or likelihood of "
        "potential impacts."
    ),
    "MANAGE 2.4": (
        "Mechanisms are in place and applied, responsibilities are assigned and understood to "
        "supersede, disengage, or deactivate AI systems that demonstrate performance or outcomes "
        "inconsistent with intended use."
    ),
    "MANAGE 4.1": (
        "Post-deployment AI system monitoring plans are implemented, including mechanisms for "
        "capturing and evaluating input from users and other relevant AI actors, appeal and "
        "override, decommissioning, incident response, recovery, and change management."
    ),
}


def playbook(n: int) -> Ref:
    """Cite an AI Playbook principle by number."""
    if n not in AI_PLAYBOOK_PRINCIPLES:
        raise ValueError(f"unknown AI Playbook principle: {n}")
    return Ref("ai-playbook", f"Principle {n}: {AI_PLAYBOOK_PRINCIPLES[n]}")


def atrs(section: str) -> Ref:
    """Cite an ATRS section by its v4.0 name."""
    if section not in ATRS_SECTIONS:
        raise ValueError(f"unknown ATRS section: {section}")
    return Ref("atrs-guidance", section)


def nist(pointer: str) -> Ref:
    """Cite a NIST AI RMF function (e.g. 'MAP') or a checked subcategory (e.g. 'GOVERN 2.1')."""
    if pointer not in NIST_FUNCTIONS and pointer not in NIST_SUBCATEGORIES:
        raise ValueError(f"NIST AI RMF pointer not in the checked list: {pointer}")
    return Ref("nist-ai-rmf", pointer)
