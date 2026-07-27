from __future__ import annotations

from orchestrator.canonical import (
    ConsumptionGraph,
    InstrumentedDecisionInputs,
    SourcedDecisionValue,
    build_export_bundle,
)
from orchestrator.contracts.enums import (
    ExecutionModeV1,
    ImplementationProofV1,
    LiveValidationProofV1,
)
from orchestrator.contracts.proof import SourceProofInputV1
from orchestrator.ui.demo import build_demo_run
from orchestrator.ui.state import proof_rows, run_summary_line


def test_demo_renders_one_proof_row_per_source_with_three_separate_fields() -> None:
    run = build_demo_run()
    rows = proof_rows(run.export_bundle)
    # Every manifested source in the closure has its own row (no collapse).
    assert {r.source_instance_id for r in rows} == set(run.export_bundle.source_proof_by_instance)
    for row in rows:
        # Three separate proof fields, not one scalar tuple.
        assert row.execution_mode
        assert row.implementation_proof
        assert row.live_validation_proof


def test_conservative_run_summary_is_weakest_decision_bearing_source() -> None:
    run = build_demo_run()
    line = run_summary_line(run.export_bundle)
    assert "WEAKEST_DECISION_BEARING_SOURCE" in line
    # All fictional sources are NOT_LIVE_VALIDATED, so the composed run is too.
    assert "NOT_LIVE_VALIDATED" in line
    assert "LIVE_SANDBOX_VALIDATED" not in line


def test_mixed_proof_rows_weakest_source_drives_summary_no_strongest_wins() -> None:
    # One strong live-validated decision-bearing source + one weaker one.
    graph = ConsumptionGraph()
    graph.manifest_source("src-strong")
    graph.manifest_source("src-weak")
    inputs = InstrumentedDecisionInputs({
        "a": SourcedDecisionValue("src-strong", "deal.x", 1),
        "b": SourcedDecisionValue("src-weak", "cap.y", 2),
    })
    session = inputs.session(graph)
    session.emit("assignment", (session.read("a"), session.read("b")))
    bundle = build_export_bundle(
        artifact_id="mixed",
        payload={"status": "RECOMMENDATION_ONLY"},
        source_proofs={
            "src-strong": SourceProofInputV1(
                execution_mode=ExecutionModeV1.DIRECT_CONNECTOR_ENABLED,
                implementation_proof=ImplementationProofV1.FULLY_IMPLEMENTED_CONTRACT_TESTED,
                live_validation_proof=LiveValidationProofV1.LIVE_SANDBOX_VALIDATED,
            ),
            "src-weak": SourceProofInputV1(
                execution_mode=ExecutionModeV1.FILE_IMPORT,
                implementation_proof=ImplementationProofV1.FULLY_IMPLEMENTED_CONTRACT_TESTED,
                live_validation_proof=LiveValidationProofV1.NOT_LIVE_VALIDATED,
            ),
        },
        consumption_graph=graph,
    )
    rows = {r.source_instance_id: r for r in proof_rows(bundle)}
    assert rows["src-strong"].live_validation_proof == "LIVE_SANDBOX_VALIDATED"
    assert rows["src-weak"].live_validation_proof == "NOT_LIVE_VALIDATED"
    # Weakest wins: composed run label is NOT_LIVE_VALIDATED.
    assert "NOT_LIVE_VALIDATED" in run_summary_line(bundle)


def test_runtime_success_never_auto_promotes_proof(app) -> None:
    # Running the fictional demo (successful execution) leaves live validation NOT_LIVE_VALIDATED.
    app.button(key="run_demo").click().run()
    app.button(key="skip_to_results").click().run()
    proof_texts = [m.value for m in app.markdown]
    joined = " ".join(proof_texts)
    assert "NOT_LIVE_VALIDATED" in joined
    assert "LIVE_SANDBOX_VALIDATED" not in joined


def test_ui_proof_rows_render_in_expanders(app) -> None:
    app.button(key="run_demo").click().run()
    app.button(key="skip_to_results").click().run()
    expander_labels = [e.label for e in app.get("expander")]
    assert any(label.startswith("Source demo-") for label in expander_labels)
