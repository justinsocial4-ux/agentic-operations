from __future__ import annotations

from datetime import datetime

from orchestrator.canonical import canonical_sha256
from orchestrator.contracts.analyst import (
    AnalysisModeV2,
    AnalystDigestFactV2,
    AnalystDigestV2,
    AnalystObservationProjectionV2,
    QuarantineRecordV2,
)

_STATE_PHRASE = {
    "SUPPORTED": "is SUPPORTED by",
    "CONFLICT": "is in CONFLICT across",
    "UNKNOWN": "remains UNKNOWN with",
}


def _statement(projection: AnalystObservationProjectionV2) -> str:
    count = len(projection.citations)
    if projection.state == "UNKNOWN":
        return (
            f"Dimension '{projection.dimension_id}' remains UNKNOWN with no exact citation; "
            f"this is not an assertion of absence."
        )
    noun = "exact validated citation" if count == 1 else "exact validated citations"
    return (
        f"Dimension '{projection.dimension_id}' {_STATE_PHRASE[projection.state]} "
        f"{count} {noun} from authorized transcript segments."
    )


def build_analyst_digest(
    *,
    run_id: str,
    deal_source_id: str,
    policy_sha256: str,
    analysis_mode: AnalysisModeV2,
    projections: tuple[AnalystObservationProjectionV2, ...],
    quarantined: tuple[QuarantineRecordV2, ...],
    created_at: datetime,
) -> AnalystDigestV2:
    """Build a digest that states ONLY validator-proven facts.

    It cannot invent context, infer sentiment/intent/authority/performance, score
    employees, or create actions. Every fact restates a validated dimension state and
    its exact citation references. Quarantined observations are counted for manager
    attention only and never contribute a fact or a decision.
    """
    for projection in projections:
        if projection.deal_source_id != deal_source_id or projection.run_id != run_id:
            raise ValueError("digest projections must share one deal and run")
        if not projection.validated:
            raise ValueError("digest accepts only validated projections")

    facts = tuple(
        AnalystDigestFactV2(
            dimension_id=projection.dimension_id,
            state=projection.state,
            provenance="TRANSCRIPT",
            citation_excerpt_ids=tuple(citation.excerpt_id for citation in projection.citations),
            citation_sha256s=tuple(citation.quote_sha256 for citation in projection.citations),
            statement=_statement(projection),
        )
        for projection in sorted(projections, key=lambda item: item.dimension_id)
    )

    identity = {
        "run_id": run_id,
        "deal_source_id": deal_source_id,
        "policy_sha256": policy_sha256,
        "facts": [fact.model_dump(mode="json") for fact in facts],
        "quarantined_count": len(quarantined),
    }
    return AnalystDigestV2(
        schema_version="orchestrator.analyst-digest.v2",
        digest_id=f"analyst-digest-{canonical_sha256(identity)[:32]}",
        run_id=run_id,
        deal_source_id=deal_source_id,
        policy_sha256=policy_sha256,
        analysis_mode=analysis_mode,
        generation_mode="VALIDATOR_FACT_BOUND",
        facts=facts,
        quarantined_count=len(quarantined),
        recommendation_only=True,
        production_readiness="NOT_ASSESSED",
        created_at=created_at,
    )
