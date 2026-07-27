from __future__ import annotations

from typing import Literal

from pydantic import Field

from .contracts.base import Identifier, StrictContract
from .contracts.enums import LaneV1
from .mapping.health import REQUIRED_POPULATIONS_BY_LANE


class SourcePopulationStatusV1(StrictContract):
    source_manifest_id: Identifier
    population: Literal[
        "DEAL_WORK_REQUEST", "CONSULTANT", "CAPACITY_AVAILABILITY",
        "WORKLOAD_COMMITMENT", "SKILL_ASSERTION", "CONVERSATION_EVIDENCE", "POLICY",
    ]
    state: Literal["COMPLETE", "BOUNDED_PARTIAL", "SOURCE_FAILED", "AUTH_FAILED"]
    affected_consultant_ids: tuple[Identifier, ...] = ()


class PartialSourceDecisionV1(StrictContract):
    ingested_state: Literal["INGESTED", "INGESTED_PARTIAL"]
    downstream_allowed: bool
    missing_required_populations: tuple[str, ...]
    incomplete_consultant_ids: tuple[Identifier, ...]
    conversation_dimensions_default_unknown: bool
    restriction_reason_codes: tuple[Identifier, ...]


def evaluate_partial_source_policy(
    *,
    lane: LaneV1,
    statuses: tuple[SourcePopulationStatusV1, ...],
) -> PartialSourceDecisionV1:
    """Apply source-local failure rules without inventing zero/full populations."""
    by_population: dict[str, list[SourcePopulationStatusV1]] = {}
    for status in statuses:
        by_population.setdefault(status.population, []).append(status)

    missing: set[str] = set()
    incomplete_consultants: set[str] = set()
    reasons: set[str] = set()
    any_partial = False
    conversation_unknown = False

    for population, rows in by_population.items():
        failed = [row for row in rows if row.state != "COMPLETE"]
        if not failed:
            continue
        any_partial = True
        if population == "CONVERSATION_EVIDENCE":
            conversation_unknown = True
            reasons.add("OPTIONAL_CONVERSATION_EVIDENCE_UNAVAILABLE")
            continue
        affected = {consultant_id for row in failed for consultant_id in row.affected_consultant_ids}
        if population in {"CAPACITY_AVAILABILITY", "WORKLOAD_COMMITMENT"} and affected:
            incomplete_consultants.update(affected)
            reasons.add("AFFECTED_CONSULTANTS_CAPACITY_INCOMPLETE")
            continue
        if population in REQUIRED_POPULATIONS_BY_LANE[lane] or population == "POLICY":
            missing.add(population)

    present = set(by_population)
    for required in REQUIRED_POPULATIONS_BY_LANE[lane]:
        if required not in present:
            missing.add(required)
    if "POLICY" not in present or any(row.state != "COMPLETE" for row in by_population.get("POLICY", [])):
        missing.add("POLICY")
    if missing:
        reasons.add("REQUIRED_SOURCE_POPULATION_UNAVAILABLE")

    downstream_allowed = not missing
    return PartialSourceDecisionV1(
        ingested_state="INGESTED_PARTIAL" if any_partial or missing else "INGESTED",
        downstream_allowed=downstream_allowed,
        missing_required_populations=tuple(sorted(missing)),
        incomplete_consultant_ids=tuple(sorted(incomplete_consultants)),
        conversation_dimensions_default_unknown=conversation_unknown,
        restriction_reason_codes=tuple(sorted(reasons)),
    )
