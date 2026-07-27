from __future__ import annotations

import hashlib
import unicodedata
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from pydantic import ValidationError

from orchestrator.canonical import canonical_sha256
from orchestrator.contracts.analyst import AnalysisModeV2, QuarantineReasonCodeV2
from orchestrator.contracts.records import AnalystObservationV2, ConversationSegmentV1

# The exact keys a mode may submit per observation. Anything else (sentiment,
# consultant_id, confidence, score, action, authority, ...) is rejected as an
# untrusted injected field, never silently dropped.
_ALLOWED_RAW_OBSERVATION_KEYS = frozenset({"dimension_id", "state", "citations", "deal_source_id"})


class ObservationRejected(ValueError):
    """A validation failure carrying a stable reason code and no transcript text."""

    def __init__(self, reason_code: QuarantineReasonCodeV2) -> None:
        super().__init__(reason_code)
        self.reason_code: QuarantineReasonCodeV2 = reason_code


@dataclass(frozen=True)
class ValidatedObservation:
    observation: AnalystObservationV2
    validated_citation_ids: frozenset[str]
    incompatibility_receipt_id: str | None
    citation_excerpt_ids: tuple[str, ...]
    citation_quote_sha256s: tuple[str, ...]
    citation_segment_text_sha256s: tuple[str, ...]


def _normalize(text: str) -> str:
    return unicodedata.normalize("NFC", text.replace("\r\n", "\n").replace("\r", "\n"))


def build_segment_index(
    segments: tuple[ConversationSegmentV1, ...], *, deal_source_id: str
) -> dict[tuple[str, str], ConversationSegmentV1]:
    """Build the in-memory citation lookup for one deal. Segments never persist."""
    index: dict[tuple[str, str], ConversationSegmentV1] = {}
    for segment in segments:
        if segment.deal_source_id != deal_source_id:
            continue
        index[(segment.conversation_id, segment.segment_id)] = segment
    return index


def _citation_id(citation: Any) -> str:
    return f"citation-{canonical_sha256(citation.model_dump(mode='json'))[:24]}"


def _map_validation_error(exc: ValidationError) -> QuarantineReasonCodeV2:
    for error in exc.errors():
        if error.get("type") == "extra_forbidden":
            return "UNKNOWN_FIELD"
        message = str(error.get("msg", ""))
        if "SUPPORTED requires" in message:
            return "MISSING_CITATION"
        if "CONFLICT requires" in message:
            return "INSUFFICIENT_CONFLICT_CITATIONS"
        if "UNKNOWN must not" in message:
            return "UNKNOWN_WITH_CITATION"
    return "MALFORMED_PAYLOAD"


def validate_raw_observation(
    raw: Mapping[str, Any],
    *,
    index: Mapping[tuple[str, str], ConversationSegmentV1],
    deal_source_id: str,
    accepted_dimensions: frozenset[str],
    run_id: str,
    analysis_mode: AnalysisModeV2,
    input_sha256: str,
) -> ValidatedObservation:
    """Mode-agnostic strict validator.

    Validates IDs, exact normalized substring + offset, hashes, source/deal scope,
    and timestamps. Rejects off-scope dimensions, injected fields, and prompt-injection
    style extra keys. SUPPORTED needs >=1 exact citation, CONFLICT needs >=2 distinct
    incompatible exact citations, UNKNOWN carries none and is not an absence assertion.
    The citation contributes no bonus beyond satisfying its deterministic dimension state.
    """
    if not isinstance(raw, Mapping):
        raise ObservationRejected("MALFORMED_PAYLOAD")

    unknown = set(raw) - _ALLOWED_RAW_OBSERVATION_KEYS
    if unknown:
        # Sentiment/consultant/score/action/authority demands land here.
        raise ObservationRejected("UNKNOWN_FIELD")

    if "deal_source_id" in raw and raw["deal_source_id"] != deal_source_id:
        raise ObservationRejected("DEAL_SCOPE_MISMATCH")

    # Providers emit JSON lists; strict contracts require tuples. Coerce the container
    # shape only (list/tuple of dicts). Any other shape fails validation as malformed.
    raw_citations = raw.get("citations", ())
    if isinstance(raw_citations, (list, tuple)):
        citations: Any = tuple(
            tuple(item) if isinstance(item, list) else item for item in raw_citations
        )
    else:
        citations = raw_citations

    candidate: dict[str, Any] = {
        "schema_version": "orchestrator.analyst-observation.v2",
        "run_id": run_id,
        "analysis_mode": analysis_mode,
        "input_sha256": input_sha256,
        "deal_source_id": deal_source_id,
        "dimension_id": raw.get("dimension_id"),
        "state": raw.get("state"),
        "citations": citations,
    }
    try:
        observation = AnalystObservationV2.model_validate(candidate)
    except ValidationError as exc:
        raise ObservationRejected(_map_validation_error(exc)) from None

    if observation.dimension_id not in accepted_dimensions:
        # LLM-created / off-catalog / off-policy dimensions are refused.
        raise ObservationRejected("OFF_SCOPE_DIMENSION")

    citation_ids: list[str] = []
    excerpt_ids: list[str] = []
    quote_sha256s: list[str] = []
    segment_text_sha256s: list[str] = []
    statement_keys: set[tuple[str, int, int]] = set()

    for citation in observation.citations:
        segment = index.get((citation.conversation_id, citation.segment_id))
        if segment is None:
            raise ObservationRejected("UNKNOWN_SEGMENT")
        if segment.deal_source_id != deal_source_id:
            raise ObservationRejected("CROSS_DEAL_CITATION")
        if citation.char_end > len(segment.text):
            raise ObservationRejected("QUOTE_OFFSET_MISMATCH")
        exact_slice = segment.text[citation.char_begin:citation.char_end]
        if exact_slice != citation.quote or _normalize(exact_slice) != _normalize(citation.quote):
            raise ObservationRejected("QUOTE_TEXT_MISMATCH")
        if citation.text_sha256 != segment.text_sha256:
            raise ObservationRejected("SEGMENT_HASH_MISMATCH")
        if not (segment.relative_begin_ms <= citation.relative_begin_ms <= segment.relative_end_ms):
            raise ObservationRejected("TIMESTAMP_OUT_OF_BOUNDS")

        statement_key = (citation.segment_id, citation.char_begin, citation.char_end)
        statement_keys.add(statement_key)
        citation_ids.append(_citation_id(citation))
        quote_sha256 = hashlib.sha256(citation.quote.encode("utf-8")).hexdigest()
        excerpt_ids.append(f"excerpt-{quote_sha256[:32]}")
        quote_sha256s.append(quote_sha256)
        segment_text_sha256s.append(segment.text_sha256)

    if observation.state == "CONFLICT" and len(statement_keys) < 2:
        # Two identical citations cannot prove incompatible explicit statements.
        raise ObservationRejected("INSUFFICIENT_CONFLICT_CITATIONS")

    incompatibility_receipt_id: str | None = None
    if observation.state == "CONFLICT":
        incompatibility_receipt_id = "incompat-" + canonical_sha256({
            "deal_source_id": deal_source_id,
            "dimension_id": observation.dimension_id,
            "statement_keys": sorted(statement_keys),
        })[:24]

    return ValidatedObservation(
        observation=observation,
        validated_citation_ids=frozenset(citation_ids),
        incompatibility_receipt_id=incompatibility_receipt_id,
        citation_excerpt_ids=tuple(excerpt_ids),
        citation_quote_sha256s=tuple(quote_sha256s),
        citation_segment_text_sha256s=tuple(segment_text_sha256s),
    )
