from __future__ import annotations

from typing import Any, Mapping, TypeAlias

from orchestrator.canonical import canonical_json_bytes
from orchestrator.contracts.enums import LaneV1
from orchestrator.contracts.records import (
    CapacityAvailabilityV1,
    ConsultantV2,
    DealWorkRequestV2,
    SkillAssertionV1,
    WorkloadCommitmentV1,
)

OperationalRecord: TypeAlias = DealWorkRequestV2 | ConsultantV2 | CapacityAvailabilityV1 | WorkloadCommitmentV1 | SkillAssertionV1

_DEAL_FIELDS: dict[LaneV1, frozenset[str]] = {
    LaneV1.DEAL_PRIORITIZATION: frozenset({
        "schema_version", "work_request_id", "deal_source_id", "request_type",
        "milestone_type", "milestone_due_time", "commercial_amount",
        "commercial_currency", "commercial_basis", "corporate_currency_normalization",
        "structured_evidence_references", "conversation_ids", "source_freshness",
        "lineage_receipt_ids",
    }),
    LaneV1.ASSIGNMENT_RECOMMENDATION: frozenset({
        "schema_version", "work_request_id", "deal_source_id", "region_source_value",
        "region_id", "request_type", "milestone_type", "milestone_due_time",
        "effort_units", "commercial_amount", "commercial_currency", "commercial_basis",
        "corporate_currency_normalization", "required_skill_ids", "required_languages",
        "required_working_window_overlap_minutes", "continuity_consultant_id",
        "structured_evidence_references", "conversation_ids", "source_freshness",
        "lineage_receipt_ids",
    }),
    LaneV1.CAPACITY_HEATMAP: frozenset({
        "schema_version", "work_request_id", "deal_source_id", "region_source_value",
        "region_id", "milestone_due_time", "effort_units", "required_skill_ids",
        "source_freshness", "lineage_receipt_ids",
    }),
}


def _validate_json_model(model: type[OperationalRecord], payload: Mapping[str, Any]) -> OperationalRecord:
    return model.model_validate_json(canonical_json_bytes(payload))


def project_deal(payload: Mapping[str, Any], lane: LaneV1) -> DealWorkRequestV2:
    selected = {key: value for key, value in payload.items() if key in _DEAL_FIELDS[lane]}
    selected.setdefault("schema_version", "orchestrator.deal-work-request.v2")
    deal = DealWorkRequestV2.model_validate_json(canonical_json_bytes(selected))
    deal.validate_for_lane(lane)
    return deal


def project_consultant(payload: Mapping[str, Any], lane: LaneV1) -> ConsultantV2:
    if lane is LaneV1.DEAL_PRIORITIZATION:
        raise ValueError("Deal prioritization consumes no consultant roster")
    common = {
        "schema_version", "consultant_source_id", "active_eligibility",
        "supported_region_ids", "manager_approved_skill_ids", "policy_receipt_ids",
    }
    if lane is LaneV1.ASSIGNMENT_RECOMMENDATION:
        common |= {"time_zone", "working_windows", "languages"}
    selected = {key: value for key, value in payload.items() if key in common}
    selected.setdefault("schema_version", "orchestrator.consultant.v2")
    consultant = ConsultantV2.model_validate_json(canonical_json_bytes(selected))
    return consultant.validate_for_lane(lane)


def project_operational_record(kind: str, payload: Mapping[str, Any], lane: LaneV1) -> OperationalRecord:
    if kind == "DEAL_WORK_REQUEST":
        return project_deal(payload, lane)
    if kind == "CONSULTANT":
        return project_consultant(payload, lane)
    models: dict[str, tuple[type[OperationalRecord], str]] = {
        "CAPACITY_AVAILABILITY": (CapacityAvailabilityV1, "orchestrator.capacity-availability.v1"),
        "WORKLOAD_COMMITMENT": (WorkloadCommitmentV1, "orchestrator.workload-commitment.v1"),
        "SKILL_ASSERTION": (SkillAssertionV1, "orchestrator.skill-assertion.v1"),
    }
    if kind not in models:
        raise ValueError("unknown operational record kind")
    if lane is LaneV1.DEAL_PRIORITIZATION:
        raise ValueError(f"Deal prioritization does not consume {kind}")
    model, schema_version = models[kind]
    selected = dict(payload)
    selected.setdefault("schema_version", schema_version)
    return _validate_json_model(model, selected)


def serialized_projection(record: OperationalRecord) -> dict[str, Any]:
    """Persist only fields present in the strict lane projection; absent stays absent."""
    return record.model_dump(mode="json", exclude_unset=True)
