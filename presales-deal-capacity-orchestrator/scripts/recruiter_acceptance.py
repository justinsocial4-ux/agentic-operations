"""Headless recruiter-acceptance check for the fictional demo path.

Drives the deterministic, credential-free fictional demo run the dashboard uses
and asserts it produces the recruiter-visible artifacts: a prioritized queue, an
assignment recommendation, a capacity heatmap, the EMEA assumption scenario, a
fact-bound digest, a source-indexed proof map, and a conservative
NOT_LIVE_VALIDATED run summary. No account, credential, network, or model.

    uv run --frozen python scripts/recruiter_acceptance.py
"""
from __future__ import annotations

from orchestrator.contracts.enums import LaneV1
from orchestrator.ui.demo import build_demo_run


def main() -> int:
    run = build_demo_run(LaneV1.ASSIGNMENT_RECOMMENDATION)
    checks: list[tuple[str, bool]] = []

    checks.append(("prioritized queue non-empty", len(run.priority_queue) >= 1))
    checks.append(("assignment recommendation present", run.assignment_recommendation is not None))
    checks.append(("solver receipt present", run.solver_receipt is not None))
    checks.append(("capacity heatmap non-empty", len(run.capacity_cells) >= 1))
    checks.append(("EMEA scenario present", run.scenario_comparison is not None))
    checks.append(("leadership digest present", run.digest is not None))

    bundle = run.export_bundle
    checks.append(("source-indexed proof map non-empty", len(bundle.source_proof_by_instance) >= 1))
    checks.append((
        "every proof row is contract-tested / not-live-validated",
        all(
            row.implementation_proof == "FULLY_IMPLEMENTED_CONTRACT_TESTED"
            and row.live_validation_proof == "NOT_LIVE_VALIDATED"
            for row in bundle.source_proof_by_instance.values()
        ),
    ))
    checks.append(("run summary present", bundle.run_proof_summary is not None))
    checks.append((
        "conservative run label is NOT_LIVE_VALIDATED",
        bundle.run_proof_summary is not None
        and bundle.run_proof_summary.live_validation_proof == "NOT_LIVE_VALIDATED"
        and bundle.run_proof_summary.derivation == "WEAKEST_DECISION_BEARING_SOURCE",
    ))
    checks.append(("assignment status RECOMMENDATION_ONLY", bundle.assignment_status == "RECOMMENDATION_ONLY"))
    checks.append(("no external writes attempted", bundle.external_writes_attempted is False))
    checks.append(("production not ready", bundle.production_ready is False))
    checks.append((
        "conversation evidence is additive only (never a standalone lane)",
        run.conversation_attachment is not None and run.conversation_attachment.is_standalone_lane is False,
    ))

    failed = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
    if failed:
        print(f"\nRecruiter acceptance FAILED: {failed}")
        return 1
    print("\nRecruiter acceptance PASSED (fictional demo, credential-free).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
