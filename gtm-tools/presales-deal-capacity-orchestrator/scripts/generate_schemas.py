from __future__ import annotations

import json
from pathlib import Path

from orchestrator.contracts.adapter import AdapterCapabilityV1
from orchestrator.contracts.connectors import (
    ConnectorPageV1,
    ConnectorPreflightReceiptV1,
    DeletionReceiptV1,
    SourceSchemaMetadataV1,
)
from orchestrator.contracts.domain import (
    ConsultantFitReceiptV2,
    EligibilityReceiptV2,
    PriorityBlockedReceiptV2,
    PriorityReceiptV2,
    ReadinessReceiptV2,
    WeeklyCapacityReceiptV1,
)
from orchestrator.contracts.manifest import SourceManifestV1
from orchestrator.contracts.phase3 import (
    AssignmentRecommendationV2,
    CapacityCellV2,
    LeadershipDigestV2,
    ScenarioComparisonV2,
    SolverReceiptV1,
)
from orchestrator.contracts.mapping import MappingProfileV1
from orchestrator.contracts.policy import PolicyV2
from orchestrator.contracts.proof import ExportBundleV2
from orchestrator.contracts.records import (
    AnalystObservationV2,
    CapacityAvailabilityV1,
    ConsultantV2,
    ConversationEvidenceMetadataV1,
    ConversationSegmentV1,
    DealWorkRequestV2,
    SkillAssertionV1,
    WorkloadCommitmentV1,
)
from orchestrator.mapping.health import DataHealthReceiptV1
from orchestrator.contracts.setup import AuthorizationAttestationV1, RunSetupAcceptanceV1

ROOT = Path(__file__).resolve().parents[1]
MODELS = {
    "source_manifest_v1.schema.json": SourceManifestV1,
    "mapping_profile_v1.schema.json": MappingProfileV1,
    "conversation_segment_v1.schema.json": ConversationSegmentV1,
    "analyst_observation_v2.schema.json": AnalystObservationV2,
    "export_bundle_v2.schema.json": ExportBundleV2,
    "adapter_capability_v1.schema.json": AdapterCapabilityV1,
    "connector_page_v1.schema.json": ConnectorPageV1,
    "connector_preflight_v1.schema.json": ConnectorPreflightReceiptV1,
    "deletion_receipt_v1.schema.json": DeletionReceiptV1,
    "source_schema_metadata_v1.schema.json": SourceSchemaMetadataV1,
    "deal_work_request_v2.schema.json": DealWorkRequestV2,
    "policy_v2.schema.json": PolicyV2,
    "run_setup_acceptance_v1.schema.json": RunSetupAcceptanceV1,
    "authorization_attestation_v1.schema.json": AuthorizationAttestationV1,
    "consultant_v2.schema.json": ConsultantV2,
    "capacity_availability_v1.schema.json": CapacityAvailabilityV1,
    "workload_commitment_v1.schema.json": WorkloadCommitmentV1,
    "skill_assertion_v1.schema.json": SkillAssertionV1,
    "conversation_evidence_metadata_v1.schema.json": ConversationEvidenceMetadataV1,
    "data_health_receipt_v1.schema.json": DataHealthReceiptV1,
    "readiness_receipt_v2.schema.json": ReadinessReceiptV2,
    "priority_receipt_v2.schema.json": PriorityReceiptV2,
    "priority_blocked_receipt_v2.schema.json": PriorityBlockedReceiptV2,
    "weekly_capacity_receipt_v1.schema.json": WeeklyCapacityReceiptV1,
    "eligibility_receipt_v2.schema.json": EligibilityReceiptV2,
    "consultant_fit_receipt_v2.schema.json": ConsultantFitReceiptV2,
    "solver_receipt_v1.schema.json": SolverReceiptV1,
    "assignment_recommendation_v2.schema.json": AssignmentRecommendationV2,
    "capacity_cell_v2.schema.json": CapacityCellV2,
    "scenario_comparison_v2.schema.json": ScenarioComparisonV2,
    "leadership_digest_v2.schema.json": LeadershipDigestV2,
}


def main() -> None:
    output = ROOT / "schemas"
    output.mkdir(exist_ok=True)
    for filename, model in MODELS.items():
        (output / filename).write_text(
            json.dumps(model.model_json_schema(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )


if __name__ == "__main__":
    main()
