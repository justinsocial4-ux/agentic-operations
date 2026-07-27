from __future__ import annotations

import hashlib
from typing import Literal

from pydantic import Field

from .canonical import ConsumptionGraph, InstrumentedDecisionInputs, SourcedDecisionValue, canonical_sha256
from .contracts.base import Identifier, Sha256, StrictContract
from .contracts.mapping import MappingProfileV1


class LineageEdgeV1(StrictContract):
    schema_version: Literal["orchestrator.lineage-edge.v1"]
    lineage_edge_id: Identifier
    run_id: Identifier
    source_manifest_id: Identifier
    page_receipt_id: Identifier
    source_record_id: Identifier
    source_field_id: str = Field(min_length=1, max_length=256)
    source_pointer: str = Field(min_length=1, max_length=512)
    raw_selected_value_sha256: Sha256
    mapping_profile_id: Identifier
    mapping_rule_id: Identifier
    conversion_id: str = Field(min_length=1, max_length=64)
    canonical_artifact_id: Identifier
    canonical_field_id: str = Field(min_length=1, max_length=256)
    validation_state: Literal["ACCEPTED", "QUARANTINED"]
    quarantine_reason: str | None = Field(default=None, max_length=128)


def build_lineage_edges(
    *,
    run_id: str,
    source_manifest_id: str,
    page_receipt_id: str,
    source_record_id: str,
    source_row: dict[str, object],
    profile: MappingProfileV1,
    canonical_artifact_id: str,
    source_format: Literal["CSV", "JSON"],
) -> tuple[LineageEdgeV1, ...]:
    edges: list[LineageEdgeV1] = []
    for rule in profile.rules:
        if rule.source_field_id not in source_row:
            continue
        value_hash = canonical_sha256(source_row[rule.source_field_id])
        edge_digest = hashlib.sha256(
            f"{canonical_artifact_id}\0{rule.rule_id}\0{value_hash}".encode()
        ).hexdigest()
        pointer = rule.source_field_id if source_format == "CSV" else f"/{rule.source_field_id.replace('~', '~0').replace('/', '~1')}"
        edges.append(LineageEdgeV1(
            schema_version="orchestrator.lineage-edge.v1",
            lineage_edge_id=f"lin-{edge_digest[:32]}",
            run_id=run_id,
            source_manifest_id=source_manifest_id,
            page_receipt_id=page_receipt_id,
            source_record_id=source_record_id,
            source_field_id=rule.source_field_id,
            source_pointer=pointer,
            raw_selected_value_sha256=value_hash,
            mapping_profile_id=profile.profile_id,
            mapping_rule_id=rule.rule_id,
            conversion_id=rule.conversion_id,
            canonical_artifact_id=canonical_artifact_id,
            canonical_field_id=rule.canonical_target_field,
            validation_state="ACCEPTED",
        ))
    return tuple(edges)


__all__ = [
    "ConsumptionGraph", "InstrumentedDecisionInputs", "LineageEdgeV1",
    "SourcedDecisionValue", "build_lineage_edges",
]
