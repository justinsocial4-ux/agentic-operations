from __future__ import annotations

import inspect
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from orchestrator.contracts.analyst import (
    AnalystDigestFactV2,
    AnalystDigestV2,
    AnalystObservationProjectionV2,
    AnalystProjectionCitationV2,
    QuarantineRecordV2,
)
from orchestrator.contracts.records import AnalystObservationV2
from orchestrator.llm.analyst import run_analyst
from orchestrator.llm.digest import build_analyst_digest
from orchestrator.llm.provider import ManualCitationProvider

from analyst_fixtures import ACCEPTED_DIMENSIONS, exact_citation, fictional_segments

DEAL = "deal-1"
RUN = "run-digest"
POLICY_SHA = "c" * 64
NOW = datetime(2026, 8, 3, 12, 0, tzinfo=timezone.utc)

# Fields the analyst output must NEVER carry.
FORBIDDEN_FIELDS = (
    "consultant_id", "consultant_fit", "candidate", "candidate_score", "employee_id",
    "employee_score", "sentiment", "emotion", "intent", "authority", "performance",
    "coaching", "probability", "confidence", "severity", "score", "assignment", "action",
    "authorization", "individual_win_rate",
)


def _segments_by_id():
    return {segment.segment_id: segment for segment in fictional_segments()}


def _gold_run():
    segs = _segments_by_id()
    provider = ManualCitationProvider(entries=[
        {"dimension_id": "security-or-data-requirements", "state": "SUPPORTED",
         "citations": [exact_citation(segs["seg-a"])]},
        {"dimension_id": "success-criteria", "state": "CONFLICT",
         "citations": [exact_citation(segs["seg-c"]), exact_citation(segs["seg-d"])]},
        {"dimension_id": "milestone-date", "state": "UNKNOWN", "citations": []},
    ])
    return run_analyst(
        provider=provider, segments=fictional_segments(), deal_source_id=DEAL,
        accepted_dimensions=ACCEPTED_DIMENSIONS,
        dimension_ids=("security-or-data-requirements", "success-criteria", "milestone-date"),
        run_id=RUN,
    )


def test_digest_states_only_validator_proven_facts() -> None:
    result = _gold_run()
    digest = build_analyst_digest(
        run_id=RUN, deal_source_id=DEAL, policy_sha256=POLICY_SHA,
        analysis_mode="MANUAL_CITATION", projections=result.projections,
        quarantined=result.quarantined, created_at=NOW,
    )
    assert digest.generation_mode == "VALIDATOR_FACT_BOUND"
    assert digest.production_readiness == "NOT_ASSESSED"
    assert digest.recommendation_only is True
    states = {fact.dimension_id: fact.state for fact in digest.facts}
    assert states == {
        "security-or-data-requirements": "SUPPORTED",
        "success-criteria": "CONFLICT",
        "milestone-date": "UNKNOWN",
    }
    # Every SUPPORTED/CONFLICT fact references exact citation hashes; UNKNOWN references none.
    for fact in digest.facts:
        if fact.state == "UNKNOWN":
            assert fact.citation_excerpt_ids == ()
        else:
            assert fact.citation_excerpt_ids
            assert len(fact.citation_excerpt_ids) == len(fact.citation_sha256s)


def test_digest_statements_contain_no_inference_language() -> None:
    result = _gold_run()
    digest = build_analyst_digest(
        run_id=RUN, deal_source_id=DEAL, policy_sha256=POLICY_SHA,
        analysis_mode="MANUAL_CITATION", projections=result.projections,
        quarantined=result.quarantined, created_at=NOW,
    )
    banned = ("sentiment", "feel", "happy", "angry", "intent", "authority",
              "performance", "recommend assigning", "should assign", "best consultant")
    for fact in digest.facts:
        lowered = fact.statement.lower()
        for token in banned:
            assert token not in lowered, f"digest leaked inference token: {token}"


def test_projection_carries_no_quote_text() -> None:
    result = _gold_run()
    for projection in result.projections:
        dumped = projection.model_dump(mode="json")
        assert "quote" not in dumped
        for citation in dumped["citations"]:
            assert "quote" not in citation
            assert "text" not in citation
            # Only hashes/offsets/ids survive.
            assert set(citation) == {
                "excerpt_id", "conversation_id", "segment_id", "quote_sha256",
                "segment_text_sha256", "char_begin", "char_end", "relative_begin_ms",
            }


@pytest.mark.parametrize("model", [
    AnalystObservationV2, AnalystObservationProjectionV2, AnalystProjectionCitationV2,
    AnalystDigestFactV2, AnalystDigestV2, QuarantineRecordV2,
])
def test_analyst_contracts_have_no_consultant_or_scoring_field(model) -> None:
    field_names = set(model.model_fields)
    for forbidden in FORBIDDEN_FIELDS:
        assert forbidden not in field_names, f"{model.__name__} exposes forbidden field {forbidden}"


def test_projection_rejects_injected_consultant_fit_field() -> None:
    result = _gold_run()
    good = result.projections[0].model_dump(mode="json")
    for forbidden in ("consultant_fit", "candidate_score", "sentiment", "action"):
        with pytest.raises(ValidationError):
            AnalystObservationProjectionV2.model_validate({**good, forbidden: "x"})


def test_llm_module_source_never_scores_or_selects_consultants() -> None:
    import orchestrator.llm.analyst as analyst_mod
    import orchestrator.llm.digest as digest_mod
    import orchestrator.llm.provider as provider_mod
    import orchestrator.llm.validator as validator_mod

    for module in (analyst_mod, digest_mod, provider_mod, validator_mod):
        source = inspect.getsource(module).lower()
        for banned in ("consultant_fit", "candidate_score", "employee_score",
                       "assign(", "win_rate", "sentiment_score"):
            assert banned not in source, f"{module.__name__} references {banned}"
