from __future__ import annotations

from datetime import datetime

from .canonical import canonical_sha256
from .contracts.phase3 import (
    DigestFactV2,
    LeadershipDigestV2,
    ScenarioComparisonV2,
    SolverReceiptV1,
)


def build_leadership_digest(
    *,
    solver_receipt: SolverReceiptV1,
    scenario_comparison: ScenarioComparisonV2 | None,
    created_at: datetime,
) -> LeadershipDigestV2:
    """Create deterministic statements from validated receipt fields only."""
    sources = set(solver_receipt.source_manifest_ids)
    mappings = set(solver_receipt.mapping_profile_sha256s)
    if scenario_comparison is not None:
        if (
            scenario_comparison.run_id != solver_receipt.run_id
            or scenario_comparison.policy_sha256 != solver_receipt.policy_sha256
        ):
            raise ValueError("digest artifacts do not share one frozen run")
        sources.update(scenario_comparison.source_manifest_ids)
        mappings.update(scenario_comparison.mapping_profile_sha256s)

    facts: list[DigestFactV2] = []
    if solver_receipt.status == "OPTIMAL":
        assert solver_receipt.serviced_priority_total is not None
        assert solver_receipt.portfolio_match_total is not None
        assert solver_receipt.peak_projected_utilization_bp is not None
        facts.extend((
            DigestFactV2(
                fact_id="solver-optimality",
                source_artifact_id=solver_receipt.solver_receipt_id,
                statement=(
                    "CP-SAT proved all portfolio objective phases OPTIMAL under the frozen "
                    "eligibility, capacity, and policy receipts."
                ),
            ),
            DigestFactV2(
                fact_id="solver-assignment-count",
                source_artifact_id=solver_receipt.solver_receipt_id,
                statement=f"The recommendation contains {len(solver_receipt.assignments)} assigned deal(s).",
            ),
            DigestFactV2(
                fact_id="solver-objective-vector",
                source_artifact_id=solver_receipt.solver_receipt_id,
                statement=(
                    f"The proven objective vector is serviced priority "
                    f"{solver_receipt.serviced_priority_total}, portfolio match "
                    f"{solver_receipt.portfolio_match_total}, and peak projected utilization "
                    f"{solver_receipt.peak_projected_utilization_bp} basis points."
                ),
            ),
        ))
    else:
        facts.append(DigestFactV2(
            fact_id="solver-non-optimal-status",
            source_artifact_id=solver_receipt.solver_receipt_id,
            statement=(
                f"No optimal assignment recommendation is claimed; solver status is "
                f"{solver_receipt.status}."
            ),
        ))

    if scenario_comparison is not None:
        base_deficits = sum(cell.surplus_deficit_units < 0 for cell in scenario_comparison.base_cells)
        scenario_deficits = sum(cell.surplus_deficit_units < 0 for cell in scenario_comparison.scenario_cells)
        facts.append(DigestFactV2(
            fact_id="emea-scenario-assumption",
            source_artifact_id=scenario_comparison.scenario_comparison_id,
            statement=(
                "Under the user-selected EMEA +25% effort assumption, deficit cells changed "
                f"from {base_deficits} to {scenario_deficits}; this assumption is not a forecast."
            ),
        ))

    identity = {
        "solver_receipt_id": solver_receipt.solver_receipt_id,
        "scenario_comparison_id": (
            scenario_comparison.scenario_comparison_id if scenario_comparison is not None else None
        ),
        "facts": facts,
    }
    return LeadershipDigestV2(
        schema_version="orchestrator.leadership-digest.v2",
        digest_id=f"digest-{canonical_sha256(identity)[:32]}",
        run_id=solver_receipt.run_id,
        policy_sha256=solver_receipt.policy_sha256,
        source_manifest_ids=tuple(sorted(sources)),
        mapping_profile_sha256s=tuple(sorted(mappings)),
        generation_mode="DETERMINISTIC_FACT_BOUND",
        facts=tuple(facts),
        recommendation_only=True,
        production_readiness="NOT_ASSESSED",
        created_at=created_at,
    )
