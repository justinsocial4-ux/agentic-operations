from __future__ import annotations

import pytest
from pydantic import ValidationError

from orchestrator.canonical import (
    ConsumptionGraph,
    InstrumentedDecisionInputs,
    SourcedDecisionValue,
    build_export_bundle,
    canonical_json_bytes,
)
from orchestrator.contracts.enums import ExecutionModeV1, ImplementationProofV1, LiveValidationProofV1
from orchestrator.contracts.proof import SourceProofInputV1


def proof(implementation: ImplementationProofV1) -> SourceProofInputV1:
    return SourceProofInputV1(
        execution_mode=ExecutionModeV1.FILE_IMPORT,
        implementation_proof=implementation,
        live_validation_proof=LiveValidationProofV1.NOT_LIVE_VALIDATED,
    )


def test_instrumented_access_records_consumption_and_serializer_derives_classification() -> None:
    graph = ConsumptionGraph()
    graph.manifest_source("src-deals")
    graph.manifest_source("src-lineage-only")
    inputs = InstrumentedDecisionInputs({
        "urgency": SourcedDecisionValue("src-deals", "deal.urgency_bp", 8000),
    })
    calculation = inputs.session(graph)
    value = calculation.read("urgency")
    assert calculation.emit("priority", value) == 8000

    bundle = build_export_bundle(
        artifact_id="export-1",
        payload={"priority_bp": 8000},
        source_proofs={
            "src-deals": proof(ImplementationProofV1.FULLY_IMPLEMENTED_CONTRACT_TESTED),
            "src-lineage-only": proof(ImplementationProofV1.ADAPTER_INTERFACE_ONLY),
        },
        consumption_graph=graph,
    )
    assert bundle.source_proof_by_instance["src-deals"].decision_bearing is True
    assert bundle.source_proof_by_instance["src-lineage-only"].decision_bearing is False
    assert bundle.run_proof_summary is not None
    assert bundle.run_proof_summary.implementation_proof is ImplementationProofV1.FULLY_IMPLEMENTED_CONTRACT_TESTED


def test_decision_emit_without_instrumented_read_is_rejected() -> None:
    graph = ConsumptionGraph()
    graph.manifest_source("src-deals")
    session = InstrumentedDecisionInputs({}).session(graph)
    with pytest.raises(ValueError, match="without recorded input consumption"):
        session.emit("priority", 100)


def test_omitted_reachable_source_proof_is_rejected() -> None:
    graph = ConsumptionGraph()
    graph.manifest_source("src-deals")
    with pytest.raises(ValueError, match="proof closure mismatch"):
        build_export_bundle(artifact_id="x", payload={}, source_proofs={}, consumption_graph=graph)


def test_caller_cannot_supply_decision_bearing() -> None:
    with pytest.raises(ValidationError):
        SourceProofInputV1.model_validate({
            "execution_mode": "FILE_IMPORT",
            "implementation_proof": "FULLY_IMPLEMENTED_CONTRACT_TESTED",
            "live_validation_proof": "NOT_LIVE_VALIDATED",
            "decision_bearing": False,
        })


def test_canonical_serializer_is_order_stable_and_rejects_float() -> None:
    assert canonical_json_bytes({"b": 1, "a": "1.00"}) == b'{"a":"1.00","b":1}'
    with pytest.raises(ValueError, match="floating-point"):
        canonical_json_bytes({"score": 0.1})
