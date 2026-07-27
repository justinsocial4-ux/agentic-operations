from __future__ import annotations

import hashlib
from datetime import datetime

from .canonical import canonical_sha256
from .contracts.domain import (
    ExactEvidenceCitationV2,
    ReadinessDimensionReceiptV2,
    ReadinessEvidenceV2,
    ReadinessReceiptV2,
)
from .contracts.enums import LaneV1
from .contracts.policy import PolicyV2
from .contracts.records import AnalystObservationV2, DealWorkRequestV2


def evidence_from_validated_observation(
    observation: AnalystObservationV2,
    *,
    validated_citation_ids: frozenset[str],
    incompatibility_receipt_id: str | None = None,
) -> ReadinessEvidenceV2:
    """Minimize an already exact-validated transcript observation for deterministic use.

    Quote text is hashed here and is not carried into the returned model or any
    deterministic consultant-selection input.
    """
    citations: list[ExactEvidenceCitationV2] = []
    for citation in observation.citations:
        citation_id = f"citation-{canonical_sha256(citation.model_dump(mode='json'))[:24]}"
        if citation_id not in validated_citation_ids:
            raise ValueError("transcript observation contains a citation not validated against its source segment")
        citations.append(ExactEvidenceCitationV2(
            citation_id=citation_id,
            source_record_id=f"{citation.conversation_id}:{citation.segment_id}",
            conversation_id=citation.conversation_id,
            segment_id=citation.segment_id,
            excerpt_sha256=hashlib.sha256(citation.quote.encode("utf-8")).hexdigest(),
            char_begin=citation.char_begin,
            char_end=citation.char_end,
            relative_begin_ms=citation.relative_begin_ms,
            exact_match_validated=True,
        ))
    return ReadinessEvidenceV2(
        dimension_id=observation.dimension_id,
        state=observation.state,
        provenance="TRANSCRIPT",
        citations=tuple(citations),
        incompatibility_receipt_id=incompatibility_receipt_id,
    )


def compute_readiness(
    *,
    run_id: str,
    deal: DealWorkRequestV2,
    policy: PolicyV2,
    policy_sha256: str,
    source_manifest_ids: tuple[str, ...],
    mapping_profile_sha256s: tuple[str, ...],
    evidence: tuple[ReadinessEvidenceV2, ...],
    created_at: datetime,
) -> ReadinessReceiptV2:
    """Apply the three-state readiness machine over the accepted PolicyV2 catalog."""
    deal.validate_for_lane(LaneV1.DEAL_PRIORITIZATION)
    source_manifest_ids = tuple(sorted(set(source_manifest_ids)))
    mapping_profile_sha256s = tuple(sorted(set(mapping_profile_sha256s)))
    assert deal.request_type is not None
    try:
        required = policy.required_readiness_subsets_by_request_type[deal.request_type]
    except KeyError as exc:
        raise ValueError("request type has no accepted required-readiness subset") from exc

    selected = set(policy.readiness_dimensions)
    if any(item.dimension_id not in selected for item in evidence):
        raise ValueError("evidence dimension is not selected by the accepted PolicyV2")

    receipts: list[ReadinessDimensionReceiptV2] = []
    for dimension_id in policy.readiness_dimensions:
        items = [item for item in evidence if item.dimension_id == dimension_id]
        explicit_conflicts = [item for item in items if item.state == "CONFLICT"]
        supported = [item for item in items if item.state == "SUPPORTED"]
        if explicit_conflicts:
            state = "CONFLICT"
            contributing = (*explicit_conflicts, *supported)
        elif supported:
            state = "SUPPORTED"
            contributing = tuple(supported)
        else:
            state = "UNKNOWN"
            contributing = ()

        citations_by_id = {
            citation.citation_id: citation
            for item in contributing
            for citation in item.citations
        }
        ordered_citations = tuple(citations_by_id[key] for key in sorted(citations_by_id))
        provenance = tuple(sorted({item.provenance for item in contributing}))
        incompatibility_ids = tuple(sorted({
            item.incompatibility_receipt_id
            for item in explicit_conflicts
            if item.incompatibility_receipt_id is not None
        }))
        receipts.append(ReadinessDimensionReceiptV2(
            dimension_id=dimension_id,
            state=state,
            citation_ids=tuple(item.citation_id for item in ordered_citations),
            citation_sha256s=tuple(item.excerpt_sha256 for item in ordered_citations),
            provenance=provenance,
            incompatibility_receipt_ids=incompatibility_ids,
        ))

    by_dimension = {item.dimension_id: item.state for item in receipts}
    conflicts = tuple(item for item in required if by_dimension[item] == "CONFLICT")
    unknowns = tuple(item for item in required if by_dimension[item] == "UNKNOWN")
    lane = "ASSIGNMENT_ELIGIBLE" if not conflicts and not unknowns else "DEAL_INSPECTION"
    reasons = tuple(
        [f"READINESS_CONFLICT:{item}" for item in conflicts]
        + [f"READINESS_UNKNOWN:{item}" for item in unknowns]
    )
    identity_payload = {
        "run_id": run_id,
        "deal_source_id": deal.deal_source_id,
        "request_type": deal.request_type,
        "dimensions": receipts,
        "required": required,
        "lane": lane,
        "policy_sha256": policy_sha256,
    }
    return ReadinessReceiptV2(
        schema_version="orchestrator.readiness-receipt.v2",
        readiness_receipt_id=f"readiness-{canonical_sha256(identity_payload)[:32]}",
        run_id=run_id,
        policy_sha256=policy_sha256,
        source_manifest_ids=source_manifest_ids,
        mapping_profile_sha256s=mapping_profile_sha256s,
        deal_source_id=deal.deal_source_id,
        request_type=deal.request_type,
        dimensions=tuple(receipts),
        required_dimension_ids=required,
        queue_lane=lane,
        reason_codes=reasons,
        created_at=created_at,
    )
