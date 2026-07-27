from __future__ import annotations

from typing import Literal

from pydantic import Field

from .base import StrictContract
from .enums import ExecutionModeV1, ImplementationProofV1, LiveValidationProofV1


class SourceProofInputV1(StrictContract):
    """No decision_bearing field: callers cannot classify proof rows."""

    execution_mode: ExecutionModeV1
    implementation_proof: ImplementationProofV1
    live_validation_proof: LiveValidationProofV1


class SerializedSourceProofV1(StrictContract):
    execution_mode: ExecutionModeV1
    implementation_proof: ImplementationProofV1
    live_validation_proof: LiveValidationProofV1
    decision_bearing: bool


class RunProofSummaryV1(StrictContract):
    implementation_proof: ImplementationProofV1
    live_validation_proof: LiveValidationProofV1
    derivation: Literal["WEAKEST_DECISION_BEARING_SOURCE"]


class ExportBundleV2(StrictContract):
    schema_version: Literal["orchestrator.export-bundle.v2"]
    artifact_id: str = Field(min_length=1)
    source_proof_by_instance: dict[str, SerializedSourceProofV1]
    run_proof_summary: RunProofSummaryV1 | None
    payload_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    execution_authorized: Literal[False]
    external_writes_attempted: Literal[False]
    assignment_status: Literal["RECOMMENDATION_ONLY"]
    production_ready: Literal[False]
