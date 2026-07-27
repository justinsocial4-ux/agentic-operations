from __future__ import annotations

from dataclasses import dataclass

from orchestrator.contracts.enums import SnapshotSemanticsV1


class DeletionReconciliationError(ValueError):
    pass


@dataclass(frozen=True)
class FileDeletionResult:
    tombstoned_source_record_ids: tuple[str, ...]
    deletion_state: str


def reconcile_file_deletions(
    *,
    snapshot_semantics: SnapshotSemanticsV1,
    previous_source_record_ids: frozenset[str],
    current_source_record_ids: frozenset[str],
    explicit_tombstone_source_record_ids: frozenset[str] = frozenset(),
    confirmed_same_source_profile_population: bool = False,
) -> FileDeletionResult:
    if snapshot_semantics is SnapshotSemanticsV1.FULL_SNAPSHOT:
        if not confirmed_same_source_profile_population:
            raise DeletionReconciliationError(
                "full-snapshot absence requires confirmation of the same source/profile/population"
            )
        tombstones = previous_source_record_ids - current_source_record_ids
        return FileDeletionResult(tuple(sorted(tombstones)), "FULL_SNAPSHOT_ABSENCE_CONFIRMED")
    if snapshot_semantics is SnapshotSemanticsV1.BOUNDED_DELTA:
        unknown = explicit_tombstone_source_record_ids - previous_source_record_ids
        if unknown:
            raise DeletionReconciliationError("delta tombstone references an unknown prior source record")
        return FileDeletionResult(tuple(sorted(explicit_tombstone_source_record_ids)), "EXPLICIT_TOMBSTONES_ONLY")
    return FileDeletionResult((), "REPLAY_FIXTURE_NO_DELETION_INFERENCE")
