from __future__ import annotations

from datetime import datetime

from .canonical import canonical_sha256
from .contracts.phase3 import (
    AlternativeCandidateV2,
    AssignmentRecommendationV2,
    DealAlternativesV2,
    HardConstraintProofV1,
    MatchContributionProofV1,
    PortfolioPairV1,
    PortfolioProblemV1,
    SolverReceiptV1,
)
from .contracts.policy import PolicyV2
from .optimizer import portfolio_problem_sha256, solve_portfolio


def _hard_proof(pair: PortfolioPairV1) -> HardConstraintProofV1:
    receipt = pair.eligibility
    return HardConstraintProofV1(
        eligibility_receipt_id=receipt.eligibility_receipt_id,
        eligible=receipt.eligible,
        checks=receipt.checks,
        reason_codes=receipt.reason_codes,
    )


def _match_proof(pair: PortfolioPairV1) -> MatchContributionProofV1 | None:
    if pair.fit is None:
        return None
    return MatchContributionProofV1(
        fit_receipt_id=pair.fit.fit_receipt_id,
        fit_bp=pair.fit.fit_bp,
        components=pair.fit.components,
    )


def build_assignment_recommendation(
    *,
    problem: PortfolioProblemV1,
    policy: PolicyV2,
    solver_receipt: SolverReceiptV1,
    created_at: datetime,
) -> AssignmentRecommendationV2:
    """Render hard proofs, contributions, and bounded forced-pair alternatives."""
    if (
        solver_receipt.run_id != problem.run_id
        or solver_receipt.policy_sha256 != problem.policy_sha256
    ):
        raise ValueError("solver receipt is outside the frozen portfolio problem")
    selected = {
        item.deal_source_id: item.consultant_source_id for item in solver_receipt.assignments
    }
    pairs_by_deal: dict[str, list[PortfolioPairV1]] = {}
    for pair in problem.pairs:
        pairs_by_deal.setdefault(pair.eligibility.deal_source_id, []).append(pair)

    deal_rows: list[DealAlternativesV2] = []
    for deal in sorted(problem.deals, key=lambda item: item.priority.deal_source_id):
        deal_id = deal.priority.deal_source_id
        pairs = sorted(
            pairs_by_deal.get(deal_id, []),
            key=lambda item: item.eligibility.consultant_source_id,
        )
        recommended_id = selected.get(deal_id)
        recommended_pair = next(
            (pair for pair in pairs if pair.eligibility.consultant_source_id == recommended_id),
            None,
        )

        rejected: list[AlternativeCandidateV2] = []
        eligible_rejected = sorted(
            (
                pair for pair in pairs
                if pair.eligibility.eligible
                and pair.eligibility.consultant_source_id != recommended_id
            ),
            key=lambda item: (
                -(item.fit.fit_bp if item.fit is not None else -1),
                item.eligibility.consultant_source_id,
            ),
        )[:2]
        for pair in eligible_rejected:
            consultant_id = pair.eligibility.consultant_source_id
            counterfactual = solve_portfolio(
                problem=problem,
                policy=policy,
                created_at=created_at,
                forced_pairs=((deal_id, consultant_id),),
            )
            equivalent = (
                counterfactual.status == "OPTIMAL"
                and solver_receipt.status == "OPTIMAL"
                and (
                    counterfactual.serviced_priority_total,
                    counterfactual.portfolio_match_total,
                    counterfactual.peak_projected_utilization_bp,
                ) == (
                    solver_receipt.serviced_priority_total,
                    solver_receipt.portfolio_match_total,
                    solver_receipt.peak_projected_utilization_bp,
                )
            )
            deltas = (None, None, None)
            if counterfactual.status == "OPTIMAL" and solver_receipt.status == "OPTIMAL":
                assert counterfactual.serviced_priority_total is not None
                assert counterfactual.portfolio_match_total is not None
                assert counterfactual.peak_projected_utilization_bp is not None
                assert solver_receipt.serviced_priority_total is not None
                assert solver_receipt.portfolio_match_total is not None
                assert solver_receipt.peak_projected_utilization_bp is not None
                deltas = (
                    counterfactual.serviced_priority_total - solver_receipt.serviced_priority_total,
                    counterfactual.portfolio_match_total - solver_receipt.portfolio_match_total,
                    counterfactual.peak_projected_utilization_bp - solver_receipt.peak_projected_utilization_bp,
                )
            rejected.append(AlternativeCandidateV2(
                consultant_source_id=consultant_id,
                disposition="EQUIVALENT_OPTIMUM" if equivalent else "REJECTED_ELIGIBLE",
                hard_constraint_proof=_hard_proof(pair),
                match_contributions=_match_proof(pair),
                counterfactual_status=counterfactual.status,
                serviced_priority_delta=deltas[0],
                portfolio_match_delta=deltas[1],
                peak_utilization_delta_bp=deltas[2],
            ))

        ineligible = tuple(AlternativeCandidateV2(
            consultant_source_id=pair.eligibility.consultant_source_id,
            disposition="INELIGIBLE",
            hard_constraint_proof=_hard_proof(pair),
            match_contributions=None,
            counterfactual_status=None,
        ) for pair in pairs if not pair.eligibility.eligible)
        deal_rows.append(DealAlternativesV2(
            deal_source_id=deal_id,
            recommended_consultant_source_id=recommended_id,
            recommended_hard_constraint_proof=(
                _hard_proof(recommended_pair) if recommended_pair is not None else None
            ),
            recommended_match_contributions=(
                _match_proof(recommended_pair) if recommended_pair is not None else None
            ),
            rejected_eligible_alternatives=tuple(rejected),
            ineligible_alternatives=ineligible,
        ))

    identity = {
        "problem": portfolio_problem_sha256(problem),
        "solver_receipt_id": solver_receipt.solver_receipt_id,
        "deals": deal_rows,
    }
    return AssignmentRecommendationV2(
        schema_version="orchestrator.assignment-recommendation.v2",
        recommendation_id=f"recommendation-{canonical_sha256(identity)[:32]}",
        run_id=problem.run_id,
        policy_sha256=problem.policy_sha256,
        source_manifest_ids=solver_receipt.source_manifest_ids,
        mapping_profile_sha256s=solver_receipt.mapping_profile_sha256s,
        solver_receipt_id=solver_receipt.solver_receipt_id,
        assignment_status="RECOMMENDATION_ONLY",
        solver_status=solver_receipt.status,
        deals=tuple(deal_rows),
        external_writes_attempted=False,
        created_at=created_at,
    )
