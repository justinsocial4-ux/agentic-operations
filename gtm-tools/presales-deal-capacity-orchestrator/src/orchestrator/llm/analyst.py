from __future__ import annotations

import hashlib
import unicodedata
from dataclasses import dataclass
from typing import Any

from orchestrator.contracts.analyst import (
    AnalysisModeV2,
    AnalystObservationProjectionV2,
    AnalystProjectionCitationV2,
    QuarantineRecordV2,
)
from orchestrator.contracts.domain import ReadinessEvidenceV2
from orchestrator.contracts.records import AnalystObservationV2, ConversationSegmentV1
from orchestrator.readiness import evidence_from_validated_observation

from .provider import AnalystProvider
from .validator import (
    ObservationRejected,
    ValidatedObservation,
    build_segment_index,
    validate_raw_observation,
)

# The fixed section 12.4 catalog. A quarantine record can only label a dimension it
# recognizes; an off-catalog / injected dimension is recorded as None (unlabeled).
_CATALOG_DIMENSIONS = frozenset({
    "business-problem", "buyer-outcome", "technical-scope",
    "stakeholder-role-coverage", "success-criteria",
    "security-or-data-requirements", "evaluation-plan",
    "customer-owner-and-next-step", "milestone-date",
})


@dataclass(frozen=True)
class AnalystRunResult:
    input_sha256: str
    observations: tuple[AnalystObservationV2, ...]
    projections: tuple[AnalystObservationProjectionV2, ...]
    evidence: tuple[ReadinessEvidenceV2, ...]
    quarantined: tuple[QuarantineRecordV2, ...]


def compute_transcript_input_sha256(
    segments: tuple[ConversationSegmentV1, ...], *, deal_source_id: str
) -> str:
    """Deterministic, deal-scoped input hash binding observations to exact evidence."""
    digest = hashlib.sha256()
    scoped = sorted(
        (segment for segment in segments if segment.deal_source_id == deal_source_id),
        key=lambda segment: (segment.conversation_id, segment.segment_id),
    )
    for segment in scoped:
        normalized = unicodedata.normalize("NFC", segment.text.replace("\r\n", "\n").replace("\r", "\n"))
        digest.update(segment.conversation_id.encode("utf-8"))
        digest.update(b"\0")
        digest.update(segment.segment_id.encode("utf-8"))
        digest.update(b"\0")
        digest.update(normalized.encode("utf-8"))
        digest.update(b"\0")
    return digest.hexdigest()


def _projection(
    validated: ValidatedObservation, *, analysis_mode: AnalysisModeV2, input_sha256: str
) -> AnalystObservationProjectionV2:
    observation = validated.observation
    projection_citations = tuple(
        AnalystProjectionCitationV2(
            excerpt_id=excerpt_id,
            conversation_id=citation.conversation_id,
            segment_id=citation.segment_id,
            quote_sha256=quote_sha256,
            segment_text_sha256=segment_text_sha256,
            char_begin=citation.char_begin,
            char_end=citation.char_end,
            relative_begin_ms=citation.relative_begin_ms,
        )
        for citation, excerpt_id, quote_sha256, segment_text_sha256 in zip(
            observation.citations,
            validated.citation_excerpt_ids,
            validated.citation_quote_sha256s,
            validated.citation_segment_text_sha256s,
        )
    )
    return AnalystObservationProjectionV2(
        schema_version="orchestrator.analyst-observation-projection.v2",
        run_id=observation.run_id,
        analysis_mode=analysis_mode,
        input_sha256=input_sha256,
        deal_source_id=observation.deal_source_id,
        dimension_id=observation.dimension_id,
        state=observation.state,
        provenance="TRANSCRIPT",
        citations=projection_citations,
        incompatibility_receipt_id=validated.incompatibility_receipt_id,
        validated=True,
    )


def run_analyst(
    *,
    provider: AnalystProvider,
    segments: tuple[ConversationSegmentV1, ...],
    deal_source_id: str,
    accepted_dimensions: frozenset[str],
    dimension_ids: tuple[str, ...],
    run_id: str,
) -> AnalystRunResult:
    """Run one mode's analysis: propose -> validate -> at most one repair -> quarantine.

    The validator is mode-agnostic, so LIVE_LOCAL, RECORDED_ANALYST_REPLAY, and
    MANUAL_CITATION all produce identical validated observations for identical evidence.
    A citation that fails validation is blocked; the lane may attempt exactly ONE repair.
    After a second failure the observation is quarantined, never silently applied.
    """
    input_sha256 = compute_transcript_input_sha256(segments, deal_source_id=deal_source_id)
    verify = getattr(provider, "verify_bound_input", None)
    if callable(verify):
        verify(input_sha256)

    index = build_segment_index(segments, deal_source_id=deal_source_id)
    raw_candidates = provider.propose(deal_source_id=deal_source_id, dimension_ids=dimension_ids)

    observations: list[AnalystObservationV2] = []
    projections: list[AnalystObservationProjectionV2] = []
    evidence: list[ReadinessEvidenceV2] = []
    quarantined: list[QuarantineRecordV2] = []

    def _validate(raw: Any) -> ValidatedObservation:
        return validate_raw_observation(
            raw,
            index=index,
            deal_source_id=deal_source_id,
            accepted_dimensions=accepted_dimensions,
            run_id=run_id,
            analysis_mode=provider.mode,
            input_sha256=input_sha256,
        )

    def _dimension_of(raw: Any) -> str | None:
        try:
            dimension = raw.get("dimension_id") if hasattr(raw, "get") else None
        except Exception:  # noqa: BLE001 - defensive against hostile candidate types
            return None
        return dimension if dimension in _CATALOG_DIMENSIONS else None

    for raw in raw_candidates:
        try:
            validated = _validate(raw)
        except ObservationRejected as first_failure:
            dimension_id = _dimension_of(raw)
            repair_raw = provider.repair(
                deal_source_id=deal_source_id,
                dimension_id=dimension_id,
                reason_code=first_failure.reason_code,
            )
            if repair_raw is None:
                quarantined.append(_quarantine(
                    run_id=run_id, analysis_mode=provider.mode, input_sha256=input_sha256,
                    deal_source_id=deal_source_id, dimension_id=dimension_id,
                    initial_reason=first_failure.reason_code, repair_reason="REPAIR_UNAVAILABLE",
                ))
                continue
            try:
                validated = _validate(repair_raw)
            except ObservationRejected as second_failure:
                quarantined.append(_quarantine(
                    run_id=run_id, analysis_mode=provider.mode, input_sha256=input_sha256,
                    deal_source_id=deal_source_id, dimension_id=_dimension_of(repair_raw) or dimension_id,
                    initial_reason=first_failure.reason_code, repair_reason=second_failure.reason_code,
                ))
                continue

        observations.append(validated.observation)
        projections.append(_projection(validated, analysis_mode=provider.mode, input_sha256=input_sha256))
        evidence.append(evidence_from_validated_observation(
            validated.observation,
            validated_citation_ids=validated.validated_citation_ids,
            incompatibility_receipt_id=validated.incompatibility_receipt_id,
        ))

    return AnalystRunResult(
        input_sha256=input_sha256,
        observations=tuple(observations),
        projections=tuple(projections),
        evidence=tuple(evidence),
        quarantined=tuple(quarantined),
    )


def _quarantine(
    *,
    run_id: str,
    analysis_mode: AnalysisModeV2,
    input_sha256: str,
    deal_source_id: str,
    dimension_id: str | None,
    initial_reason: str,
    repair_reason: str,
) -> QuarantineRecordV2:
    return QuarantineRecordV2(
        schema_version="orchestrator.analyst-quarantine.v2",
        run_id=run_id,
        analysis_mode=analysis_mode,
        input_sha256=input_sha256,
        deal_source_id=deal_source_id,
        dimension_id=dimension_id,  # type: ignore[arg-type]
        initial_reason_code=initial_reason,  # type: ignore[arg-type]
        repair_attempted=True,
        repair_reason_code=repair_reason,  # type: ignore[arg-type]
        applied_to_readiness=False,
    )
