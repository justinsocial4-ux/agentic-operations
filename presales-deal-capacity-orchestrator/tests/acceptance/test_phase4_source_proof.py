from orchestrator.canonical import (
    ConsumptionGraph,
    InstrumentedDecisionInputs,
    SourcedDecisionValue,
    build_export_bundle,
)
from orchestrator.ingestion.clickup import ClickUpAdapter
from orchestrator.ingestion.salesforce import SalesforceAdapter


def test_salesforce_and_clickup_contribute_source_indexed_contract_proof_without_auto_promotion() -> None:
    graph = ConsumptionGraph()
    graph.manifest_source("src-salesforce")
    graph.manifest_source("src-clickup")
    inputs = InstrumentedDecisionInputs({
        "deal": SourcedDecisionValue("src-salesforce", "deal.id", "deal-synthetic"),
        "capacity": SourcedDecisionValue("src-clickup", "capacity.units", 20),
    })
    session = inputs.session(graph)
    session.emit("assignment", (session.read("deal"), session.read("capacity")))
    bundle = build_export_bundle(
        artifact_id="phase4-proof-synthetic",
        payload={"status": "RECOMMENDATION_ONLY"},
        source_proofs={
            "src-salesforce": SalesforceAdapter.proof(),
            "src-clickup": ClickUpAdapter.proof(),
        },
        consumption_graph=graph,
    )
    assert set(bundle.source_proof_by_instance) == {"src-salesforce", "src-clickup"}
    assert all(row.decision_bearing for row in bundle.source_proof_by_instance.values())
    assert all(
        row.implementation_proof == "FULLY_IMPLEMENTED_CONTRACT_TESTED"
        and row.live_validation_proof == "NOT_LIVE_VALIDATED"
        for row in bundle.source_proof_by_instance.values()
    )
    assert bundle.run_proof_summary is not None
    assert bundle.run_proof_summary.live_validation_proof == "NOT_LIVE_VALIDATED"
