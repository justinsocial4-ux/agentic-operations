from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field, field_validator, model_validator

from orchestrator.contracts.base import Identifier, Sha256, StrictContract, require_offset_aware
from orchestrator.contracts.enums import LaneV1


class PopulationCountsV1(StrictContract):
    population: str = Field(min_length=1, max_length=80)
    declared: int = Field(ge=0)
    fetched: int = Field(ge=0)
    parsed: int = Field(ge=0)
    accepted: int = Field(ge=0)
    quarantined: int = Field(ge=0)
    excluded: int = Field(ge=0)
    duplicate: int = Field(ge=0)
    tombstoned: int = Field(ge=0)
    unmatched: int = Field(ge=0)
    read_complete: bool

    @model_validator(mode="after")
    def reconcile(self) -> "PopulationCountsV1":
        if self.fetched != self.parsed:
            raise ValueError("fetched population must equal parsed population")
        if self.parsed != self.accepted + self.quarantined + self.excluded + self.duplicate:
            raise ValueError("parsed population reconciliation failed")
        if self.read_complete and self.declared != self.fetched:
            raise ValueError("complete read must reconcile declared and fetched counts")
        return self


class SourceConflictV1(StrictContract):
    canonical_record_id: Identifier
    canonical_field_id: str = Field(min_length=1, max_length=256)
    winning_source_manifest_id: Identifier
    losing_source_manifest_ids: tuple[Identifier, ...] = Field(min_length=1)
    acknowledged: bool


class DataHealthReceiptV1(StrictContract):
    schema_version: Literal["orchestrator.data-health-receipt.v1"]
    receipt_id: Identifier
    run_id: Identifier
    lane: LaneV1
    source_manifest_ids: tuple[Identifier, ...] = Field(min_length=1)
    mapping_profile_sha256s: tuple[Sha256, ...] = Field(min_length=1)
    populations: tuple[PopulationCountsV1, ...] = Field(min_length=1)
    missing_required_populations: tuple[str, ...]
    orphan_reference_ids: tuple[Identifier, ...]
    incomplete_consultant_ids: tuple[Identifier, ...]
    source_conflicts: tuple[SourceConflictV1, ...]
    conversation_duplicate_count: int = Field(ge=0)
    conversation_conflict_count: int = Field(ge=0)
    capped_source_manifest_ids: tuple[Identifier, ...]
    reconciliation_equation: Literal["parsed = accepted + quarantined + excluded + duplicate"]
    accepted_for_operational_commit: bool
    created_at: datetime

    @field_validator("created_at")
    @classmethod
    def aware_time(cls, value: datetime) -> datetime:
        return require_offset_aware(value)

    @model_validator(mode="after")
    def acceptance_is_honest(self) -> "DataHealthReceiptV1":
        blockers = (
            self.missing_required_populations
            or self.orphan_reference_ids
            or self.conversation_conflict_count
            or any(not conflict.acknowledged for conflict in self.source_conflicts)
        )
        if blockers and self.accepted_for_operational_commit:
            raise ValueError("blocked data health cannot be accepted")
        return self


REQUIRED_POPULATIONS_BY_LANE: dict[LaneV1, frozenset[str]] = {
    LaneV1.DEAL_PRIORITIZATION: frozenset({"DEAL_WORK_REQUEST"}),
    LaneV1.ASSIGNMENT_RECOMMENDATION: frozenset({
        "DEAL_WORK_REQUEST", "CONSULTANT", "CAPACITY_AVAILABILITY",
        "WORKLOAD_COMMITMENT", "SKILL_ASSERTION",
    }),
    LaneV1.CAPACITY_HEATMAP: frozenset({
        "DEAL_WORK_REQUEST", "CONSULTANT", "CAPACITY_AVAILABILITY",
        "WORKLOAD_COMMITMENT", "SKILL_ASSERTION",
    }),
}


def capacity_coverage(
    *,
    consultant_ids: frozenset[str],
    capacity_buckets_by_consultant: dict[str, frozenset[int]],
    workload_covered_consultant_ids: frozenset[str],
) -> tuple[tuple[str, ...], int]:
    """Conservatively require all four literal-v1 buckets and explicit workload coverage."""
    complete: set[str] = set()
    for consultant_id in consultant_ids:
        if (
            capacity_buckets_by_consultant.get(consultant_id, frozenset()) == frozenset({1, 2, 3, 4})
            and consultant_id in workload_covered_consultant_ids
        ):
            complete.add(consultant_id)
    incomplete = tuple(sorted(consultant_ids - complete))
    return incomplete, len(complete)


def assess_data_health(
    *,
    receipt_id: str,
    run_id: str,
    lane: LaneV1,
    source_manifest_ids: tuple[str, ...],
    mapping_profile_sha256s: tuple[str, ...],
    populations: tuple[PopulationCountsV1, ...],
    created_at: datetime,
    orphan_reference_ids: tuple[str, ...] = (),
    incomplete_consultant_ids: tuple[str, ...] = (),
    complete_consultant_count: int = 0,
    source_conflicts: tuple[SourceConflictV1, ...] = (),
    conversation_duplicate_count: int = 0,
    conversation_conflict_count: int = 0,
) -> DataHealthReceiptV1:
    present = {item.population for item in populations}
    missing = set(REQUIRED_POPULATIONS_BY_LANE[lane]) - present
    counts_by_name = {item.population: item for item in populations}
    if "DEAL_WORK_REQUEST" in counts_by_name and counts_by_name["DEAL_WORK_REQUEST"].accepted == 0:
        missing.add("DEAL_WORK_REQUEST")
    if lane is not LaneV1.DEAL_PRIORITIZATION and complete_consultant_count == 0:
        missing.add("COMPLETE_CONSULTANT_SUPPLY")
    capped = tuple(
        source_manifest_ids[index]
        for index, population in enumerate(populations)
        if not population.read_complete and index < len(source_manifest_ids)
    )
    blocked = bool(
        missing
        or orphan_reference_ids
        or conversation_conflict_count
        or any(not conflict.acknowledged for conflict in source_conflicts)
    )
    return DataHealthReceiptV1(
        schema_version="orchestrator.data-health-receipt.v1",
        receipt_id=receipt_id,
        run_id=run_id,
        lane=lane,
        source_manifest_ids=source_manifest_ids,
        mapping_profile_sha256s=mapping_profile_sha256s,
        populations=populations,
        missing_required_populations=tuple(sorted(missing)),
        orphan_reference_ids=tuple(sorted(set(orphan_reference_ids))),
        incomplete_consultant_ids=tuple(sorted(set(incomplete_consultant_ids))),
        source_conflicts=source_conflicts,
        conversation_duplicate_count=conversation_duplicate_count,
        conversation_conflict_count=conversation_conflict_count,
        capped_source_manifest_ids=tuple(sorted(set(capped))),
        reconciliation_equation="parsed = accepted + quarantined + excluded + duplicate",
        accepted_for_operational_commit=not blocked,
        created_at=created_at,
    )
