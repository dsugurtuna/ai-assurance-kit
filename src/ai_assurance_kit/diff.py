"""Compare two versions of a record and flag the changes that should trigger re-review.

Two layers:
* a generic field-by-field diff, so nothing changes silently;
* a short list of *material* change rules, each with a reason. These are the changes that alter
  what the system can do, what data it touches, who it affects or how much it is relied on.

Why not treat every change as material? Because then every typo fix triggers a review and
people learn to ignore the flag. Why not only look at the material rules? Because a reviewer
should still see everything that moved.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from ai_assurance_kit.policy import Policy
from ai_assurance_kit.schema import (
    ACTION_MODE_ORDER,
    DECISION_ROLE_ORDER,
    AIUseRecord,
    Status,
)

_KEYED_LISTS = {"risks": "id", "controls": "id", "connectors": "name"}


@dataclass(frozen=True)
class Change:
    path: str
    summary: str
    before: Any = None
    after: Any = None
    reason: str = ""
    # Generic field paths this material change fully explains, so they are not repeated under
    # "other". None means the change's own path and everything below it. A material change
    # never hides an edit it does not describe, such as a removal next to an addition.
    covers: tuple[str, ...] | None = field(default=None, compare=False)

    def describe(self) -> str:
        """The summary, plus before and after when both are short enough to read inline."""
        short = all(
            v is None or (not isinstance(v, (list, dict)) and len(str(v)) <= 40)
            for v in (self.before, self.after)
        )
        if self.summary == "changed" and short:
            return f"{self.before} -> {self.after}"
        return self.summary

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "summary": self.summary,
            "before": self.before,
            "after": self.after,
            "reason": self.reason,
        }


@dataclass
class DiffReport:
    old_label: str
    new_label: str
    material: list[Change] = field(default_factory=list)
    other: list[Change] = field(default_factory=list)

    @property
    def needs_review(self) -> bool:
        return bool(self.material)

    def to_dict(self) -> dict[str, Any]:
        return {
            "old": self.old_label,
            "new": self.new_label,
            "needs_review": self.needs_review,
            "material": [c.to_dict() for c in self.material],
            "other": [c.to_dict() for c in self.other],
        }


# --------------------------------------------------------------------------- generic diff


@dataclass(frozen=True)
class _Items:
    """An unkeyed list of objects (evaluation, decisions), compared item by item.

    Each item is identified by all of its fields, not just its label, so an edit to any field
    (for example marking evidence as independent) is a change.
    """

    items: tuple[str, ...]  # canonical JSON of each item
    labels: tuple[str, ...]  # what a reader sees


def flatten(value: Any, path: str = "") -> dict[str, Any]:
    """Flatten a JSON-like value into {dotted.path: leaf}.

    Lists of objects with a natural key (risk id, control id, connector name) are keyed by it and
    flattened further, so reordering is not a change. Other lists of objects (evaluation,
    decisions) become one leaf that field_changes compares item by item, so an added item reads
    as one change wherever it is inserted, and reordering is not a change. Lists of plain
    values are kept whole and compared as sorted tuples.
    """
    out: dict[str, Any] = {}
    if isinstance(value, dict):
        for k, v in value.items():
            out.update(flatten(v, f"{path}.{k}" if path else str(k)))
    elif isinstance(value, list):
        key = _KEYED_LISTS.get(path.rsplit(".", 1)[-1])
        if value and all(isinstance(v, dict) for v in value):
            if key and all(v.get(key) is not None for v in value):
                for v in value:
                    out.update(flatten(v, f"{path}[{v[key]}]"))
            else:
                out[path] = _Items(
                    tuple(json.dumps(v, sort_keys=True, default=str) for v in value),
                    tuple(_item_label(v) for v in value),
                )
        else:
            out[path] = tuple(sorted(value, key=str))
    else:
        out[path] = value
    return out


def _item_changes(path: str, before: Any, after: Any) -> list[Change]:
    """Match unkeyed items by content: what was added, removed or edited, ignoring order."""
    old = before if isinstance(before, _Items) else _Items((), ())
    new = after if isinstance(after, _Items) else _Items((), ())
    unmatched_new = list(range(len(new.items)))
    unmatched_old: list[int] = []
    for i, item in enumerate(old.items):
        j = next((j for j in unmatched_new if new.items[j] == item), None)
        if j is None:
            unmatched_old.append(i)
        else:
            unmatched_new.remove(j)
    # Leftovers on both sides are read as edits, in order; the rest as removals or additions.
    # An edit carries the whole item, because the edited field may not be in the label.
    changes = [
        Change(f"{path}[{j}]", "changed", json.loads(old.items[i]), json.loads(new.items[j]))
        for i, j in zip(unmatched_old, unmatched_new, strict=False)
    ]
    changes += [
        Change(f"{path}[{i}]", "removed", old.labels[i], None)
        for i in unmatched_old[len(unmatched_new) :]
    ]
    changes += [
        Change(f"{path}[{j}]", "added", None, new.labels[j])
        for j in unmatched_new[len(unmatched_old) :]
    ]
    return changes


def _item_label(item: dict[str, Any]) -> str:
    """A short, stable one-line label for an unkeyed list item such as an evaluation entry."""
    head = [str(item[k]) for k in ("date", "type", "kind") if item.get(k) is not None]
    rest = item.get("summary") or item.get("note") or item.get("by") or ""
    text = " ".join(head)
    return f"{text}: {rest}" if rest else text


def _show(value: Any) -> Any:
    return list(value) if isinstance(value, tuple) else value


def field_changes(old: AIUseRecord, new: AIUseRecord) -> list[Change]:
    a = flatten(old.model_dump(mode="json"))
    b = flatten(new.model_dump(mode="json"))
    changes: list[Change] = []
    for path in sorted(set(a) | set(b)):
        before, after = a.get(path), b.get(path)
        if before == after:
            continue
        if isinstance(before, _Items) or isinstance(after, _Items):
            changes.extend(_item_changes(path, before, after))
            continue
        # An empty list that gains items (or loses them all) shows up as item changes instead.
        if () in (before, after) and any(p.startswith(path + "[") for p in {*a, *b}):
            continue
        if path not in a:
            summary = "added"
        elif path not in b:
            summary = "removed"
        elif before is None:
            summary = "set"
        elif after is None:
            summary = "cleared"
        else:
            summary = "changed"
        changes.append(Change(path, summary, _show(before), _show(after)))
    return changes


# --------------------------------------------------------------------------- material rules


def _added(old: list[str], new: list[str]) -> list[str]:
    seen = {s.casefold() for s in old}
    return [s for s in new if s.casefold() not in seen]


def _only_additions(old: list[str], new: list[str]) -> tuple[str, ...] | None:
    """Cover the whole field only when nothing was removed from it; otherwise cover nothing."""
    return None if not _added(new, old) else ()


def material_changes(old: AIUseRecord, new: AIUseRecord, policy: Policy) -> list[Change]:
    out: list[Change] = []

    # Data
    if cats := _added(old.data.categories, new.data.categories):
        out.append(
            Change(
                "data.categories",
                f"New data categories: {', '.join(cats)}",
                old.data.categories,
                new.data.categories,
                "New kinds of data change what can go wrong and who is affected.",
                _only_additions(old.data.categories, new.data.categories),
            )
        )
    if not old.data.personal_data and new.data.personal_data:
        out.append(
            Change(
                "data.personal_data",
                "Now processes personal data",
                False,
                True,
                "DPIA screening, retention and access need to be looked at again.",
            )
        )
    if not old.data.special_category_data and new.data.special_category_data:
        out.append(
            Change(
                "data.special_category_data",
                "Now processes special category data",
                False,
                True,
                "Special category data raises the level of scrutiny for data protection.",
            )
        )
    if srcs := _added(old.data.sources, new.data.sources):
        out.append(
            Change(
                "data.sources",
                f"New data sources: {', '.join(srcs)}",
                old.data.sources,
                new.data.sources,
                "New sources can change data quality, lawful basis and security exposure.",
                _only_additions(old.data.sources, new.data.sources),
            )
        )

    # Access
    old_conns = {c.name: c for c in old.access.connectors}
    for conn in new.access.connectors:
        perms = ", ".join(p.value for p in conn.permissions)
        if conn.name not in old_conns:
            out.append(
                Change(
                    f"access.connectors[{conn.name}]",
                    f"New connector '{conn.name}' ({perms})",
                    reason="Connecting a new system is a separate decision from building the tool.",
                )
            )
            continue
        was_system, now_system = old_conns[conn.name].system, conn.system
        if was_system and now_system and was_system.casefold() != now_system.casefold():
            out.append(
                Change(
                    f"access.connectors[{conn.name}].system",
                    f"Connector '{conn.name}' now connects to a different system",
                    was_system,
                    now_system,
                    "Connecting a new system is a separate decision from building the tool.",
                )
            )
        before_perms = [p.value for p in old_conns[conn.name].permissions]
        after_perms = [p.value for p in conn.permissions]
        if gained := _added(before_perms, after_perms):
            out.append(
                Change(
                    f"access.connectors[{conn.name}].permissions",
                    f"Connector '{conn.name}' gains {', '.join(gained)} permission",
                    before_perms,
                    after_perms,
                    "New permissions change what the system can do, whether or not it does it.",
                    _only_additions(before_perms, after_perms),
                )
            )
    if old.access.users != new.access.users:
        out.append(
            Change(
                "access.users",
                "Who can use the tool has changed",
                old.access.users,
                new.access.users,
                "Sharing a tool more widely is a separate decision from building it.",
            )
        )

    # Actions
    if ACTION_MODE_ORDER[new.actions.mode] > ACTION_MODE_ORDER[old.actions.mode]:
        out.append(
            Change(
                "actions.mode",
                f"Action mode moves from {old.actions.mode.value} to {new.actions.mode.value}",
                old.actions.mode.value,
                new.actions.mode.value,
                "Moving from reading or drafting towards acting on its own needs stronger "
                "controls.",
            )
        )
    if rec := _added(old.actions.recipients, new.actions.recipients):
        out.append(
            Change(
                "actions.recipients",
                f"New recipients: {', '.join(rec)}",
                old.actions.recipients,
                new.actions.recipients,
                "New recipients are new people or systems affected when an action is wrong.",
                _only_additions(old.actions.recipients, new.actions.recipients),
            )
        )
    if old.actions.human_approval_step and not new.actions.human_approval_step:
        out.append(
            Change(
                "actions.human_approval_step",
                "Human approval step removed",
                old.actions.human_approval_step,
                None,
                "Removing an approval step removes a control.",
            )
        )
    if old.actions.stop_mechanism and not new.actions.stop_mechanism:
        out.append(
            Change(
                "actions.stop_mechanism",
                "Way to stop the system removed",
                old.actions.stop_mechanism,
                None,
                "Removing the way to pause or switch off the system removes a control.",
            )
        )

    # Reliance
    for name, label in (
        ("public_facing", "Now public-facing"),
        ("public_effect", "Outputs now feed decisions with public effect"),
        ("significant_influence", "Outputs now significantly influence decisions"),
    ):
        if not getattr(old.reliance, name) and getattr(new.reliance, name):
            out.append(
                Change(
                    f"reliance.{name}",
                    label,
                    False,
                    True,
                    "This can change transparency duties and the level of review.",
                )
            )
    if (
        DECISION_ROLE_ORDER[new.reliance.decision_role]
        > DECISION_ROLE_ORDER[old.reliance.decision_role]
    ):
        out.append(
            Change(
                "reliance.decision_role",
                f"Decision role moves from {old.reliance.decision_role.value} to "
                f"{new.reliance.decision_role.value}",
                old.reliance.decision_role.value,
                new.reliance.decision_role.value,
                "Outputs are relied on more heavily than before.",
            )
        )
    if old.reliance.human_review and not new.reliance.human_review:
        out.append(
            Change(
                "reliance.human_review",
                "Human review of outputs removed",
                old.reliance.human_review,
                None,
                "Removing review removes a control.",
            )
        )
    if old.reliance.challenge_route and not new.reliance.challenge_route:
        out.append(
            Change(
                "reliance.challenge_route",
                "Challenge route removed",
                old.reliance.challenge_route,
                None,
                "Affected people no longer have a recorded way to question an outcome.",
            )
        )
    if old.reliance.user_notice and not new.reliance.user_notice:
        out.append(
            Change(
                "reliance.user_notice",
                "User notice removed",
                old.reliance.user_notice,
                None,
                "People may no longer be told that AI is involved.",
            )
        )
    if groups := _added(old.reliance.relied_on_by, new.reliance.relied_on_by):
        out.append(
            Change(
                "reliance.relied_on_by",
                f"New groups relying on the outputs: {', '.join(groups)}",
                old.reliance.relied_on_by,
                new.reliance.relied_on_by,
                "More people rely on the outputs, so an error reaches further.",
                _only_additions(old.reliance.relied_on_by, new.reliance.relied_on_by),
            )
        )
    factor = policy.changes.scale_factor
    for name in ("users", "uses_per_month"):
        before = getattr(old.reliance.scale, name)
        after = getattr(new.reliance.scale, name)
        if (
            before is not None
            and after is not None
            and after > before
            and (before == 0 or after / before >= factor)
        ):
            out.append(
                Change(
                    f"reliance.scale.{name}",
                    f"Scale rises: {name.replace('_', ' ')} {before} to {after}",
                    before,
                    after,
                    f"A rise of {factor:g}x or more (policy threshold) means errors reach more "
                    "people.",
                )
            )

    # System
    for name in ("model_kind", "model", "provider", "hosting", "third_party_supplier"):
        # A blank answer is no answer: "" and None are the same here, as in the checks.
        before, after = getattr(old.system, name) or None, getattr(new.system, name) or None
        if before != after:
            out.append(
                Change(
                    f"system.{name}",
                    f"{name.replace('_', ' ').capitalize()} changed",
                    str(before) if before is not None else None,
                    str(after) if after is not None else None,
                    "Evaluation evidence was gathered on the old system and may not carry over.",
                )
            )

    # Lifecycle
    if new.status is Status.live and old.status is not Status.live:
        out.append(
            Change(
                "status",
                f"Moves to live (from {old.status.value})",
                old.status.value,
                new.status.value,
                "The ATRS guidance gives a pilot tool moving to production as an example of a "
                "substantive change.",
            )
        )

    # Risks newly above appetite
    appetite = policy.risk.appetite_score
    old_scores = {r.id: r.score for r in old.risks}
    for r in new.risks:
        was = old_scores.get(r.id)
        if r.score > appetite and (was is None or was <= appetite):
            path = f"risks[{r.id}]"
            out.append(
                Change(
                    path,
                    f"New risk {r.id} is above appetite ({r.score} > {appetite})"
                    if was is None
                    else f"Risk {r.id} is now above appetite ({r.score} > {appetite})",
                    was,
                    r.score,
                    "A risk above appetite needs an owner and a treatment decision.",
                    # A new risk is covered whole, like a new connector. For an existing risk
                    # only the score is explained; owner or control edits still show.
                    None if was is None else (f"{path}.likelihood", f"{path}.impact"),
                )
            )
    return out


def diff_records(
    old: AIUseRecord,
    new: AIUseRecord,
    policy: Policy,
    old_label: str = "old",
    new_label: str = "new",
) -> DiffReport:
    """Compare two records. Material changes first; everything else under ``other``."""
    material = material_changes(old, new, policy)
    covered = [p for m in material for p in (m.covers if m.covers is not None else (m.path,))]

    def is_covered(path: str) -> bool:
        return any(path == c or path.startswith((c + ".", c + "[")) for c in covered)

    other = [c for c in field_changes(old, new) if not is_covered(c.path)]
    return DiffReport(old_label, new_label, material, other)
