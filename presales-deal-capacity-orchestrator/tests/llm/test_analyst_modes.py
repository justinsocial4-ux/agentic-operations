from __future__ import annotations

import httpx

from orchestrator.llm.analyst import compute_transcript_input_sha256, run_analyst
from orchestrator.llm.provider import (
    LiveLocalProvider,
    ManualCitationProvider,
    RecordedAnalystReplayProvider,
)

from analyst_fixtures import ACCEPTED_DIMENSIONS, exact_citation, fictional_segments

DEAL = "deal-1"
RUN = "run-modes"
DIMS = ("business-problem", "success-criteria", "security-or-data-requirements", "milestone-date")


def _segments_by_id():
    return {segment.segment_id: segment for segment in fictional_segments()}


def _gold_candidates() -> list[dict]:
    segs = _segments_by_id()
    return [
        {
            "dimension_id": "security-or-data-requirements",
            "state": "SUPPORTED",
            "citations": [exact_citation(segs["seg-a"])],
        },
        {
            "dimension_id": "business-problem",
            "state": "SUPPORTED",
            "citations": [exact_citation(segs["seg-b"])],
        },
        {
            "dimension_id": "success-criteria",
            "state": "CONFLICT",
            "citations": [exact_citation(segs["seg-c"]), exact_citation(segs["seg-d"])],
        },
        {
            "dimension_id": "milestone-date",
            "state": "UNKNOWN",
            "citations": [],
        },
    ]


def _live_provider(candidates: list[dict]) -> LiveLocalProvider:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"observations": candidates})

    client = httpx.Client(trust_env=False, follow_redirects=False, transport=httpx.MockTransport(handler))
    return LiveLocalProvider(
        endpoint_url="http://127.0.0.1:11434/v1/analyze",
        segments=fictional_segments(),
        client=client,
    )


def _run(provider):
    return run_analyst(
        provider=provider,
        segments=fictional_segments(),
        deal_source_id=DEAL,
        accepted_dimensions=ACCEPTED_DIMENSIONS,
        dimension_ids=DIMS,
        run_id=RUN,
    )


def test_three_modes_produce_identical_validated_receipts() -> None:
    candidates = _gold_candidates()
    input_sha = compute_transcript_input_sha256(fictional_segments(), deal_source_id=DEAL)

    live = _run(_live_provider([dict(c) for c in candidates]))
    manual = _run(ManualCitationProvider(entries=[dict(c) for c in candidates]))
    replay = _run(RecordedAnalystReplayProvider(
        bound_input_sha256=input_sha,
        recorded_observations=[dict(c) for c in candidates],
    ))

    # The validator is mode-agnostic: everything is identical except the mode label.
    def _observations_without_mode(result):
        return [o.model_dump(mode="json", exclude={"analysis_mode"}) for o in result.observations]

    assert _observations_without_mode(live) == _observations_without_mode(manual)
    assert _observations_without_mode(manual) == _observations_without_mode(replay)

    # Derived deterministic evidence (the actual decision-bearing artifact) is identical.
    def _evidence(result):
        return [e.model_dump(mode="json") for e in result.evidence]

    assert _evidence(live) == _evidence(manual) == _evidence(replay)

    # And projections match except the mode label.
    def _projections_without_mode(result):
        return [p.model_dump(mode="json", exclude={"analysis_mode"}) for p in result.projections]

    assert _projections_without_mode(live) == _projections_without_mode(manual)
    assert _projections_without_mode(manual) == _projections_without_mode(replay)

    # Each mode stamps its own honest analysis_mode.
    assert {o.analysis_mode for o in live.observations} == {"LIVE_LOCAL"}
    assert {o.analysis_mode for o in manual.observations} == {"MANUAL_CITATION"}
    assert {o.analysis_mode for o in replay.observations} == {"RECORDED_ANALYST_REPLAY"}


def test_recorded_replay_fails_closed_on_wrong_input_hash() -> None:
    import pytest

    from orchestrator.llm.provider import AnalystProviderError

    provider = RecordedAnalystReplayProvider(
        bound_input_sha256="0" * 64,
        recorded_observations=_gold_candidates(),
    )
    with pytest.raises(AnalystProviderError):
        _run(provider)


# -- One repair then quarantine -----------------------------------------------------

class _RepairCountingProvider:
    """A MANUAL_CITATION-shaped provider that records how many repair calls happen."""

    mode = "MANUAL_CITATION"

    def __init__(self, first: dict, repair: dict | None) -> None:
        self._first = first
        self._repair = repair
        self.repair_calls = 0

    def propose(self, *, deal_source_id, dimension_ids):
        return (dict(self._first),)

    def repair(self, *, deal_source_id, dimension_id, reason_code):
        self.repair_calls += 1
        return dict(self._repair) if self._repair is not None else None


def _bad_citation() -> dict:
    seg = _segments_by_id()["seg-a"]
    citation = exact_citation(seg)
    citation["quote"] = "fabricated never-said quote"
    return {
        "dimension_id": "security-or-data-requirements",
        "state": "SUPPORTED",
        "citations": [citation],
    }


def _good_citation() -> dict:
    seg = _segments_by_id()["seg-a"]
    return {
        "dimension_id": "security-or-data-requirements",
        "state": "SUPPORTED",
        "citations": [exact_citation(seg)],
    }


def test_one_repair_recovers_a_valid_citation() -> None:
    provider = _RepairCountingProvider(first=_bad_citation(), repair=_good_citation())
    result = _run(provider)
    assert provider.repair_calls == 1
    assert len(result.observations) == 1
    assert result.quarantined == ()


def test_second_failure_after_one_repair_is_quarantined() -> None:
    provider = _RepairCountingProvider(first=_bad_citation(), repair=_bad_citation())
    result = _run(provider)
    assert provider.repair_calls == 1  # EXACTLY one repair attempt, never a second
    assert result.observations == ()
    assert len(result.quarantined) == 1
    record = result.quarantined[0]
    assert record.initial_reason_code == "QUOTE_TEXT_MISMATCH"
    assert record.repair_reason_code == "QUOTE_TEXT_MISMATCH"
    assert record.repair_attempted is True
    assert record.applied_to_readiness is False
    assert record.dimension_id == "security-or-data-requirements"


def test_missing_repair_is_quarantined_with_repair_unavailable() -> None:
    provider = _RepairCountingProvider(first=_bad_citation(), repair=None)
    result = _run(provider)
    assert provider.repair_calls == 1
    assert len(result.quarantined) == 1
    assert result.quarantined[0].repair_reason_code == "REPAIR_UNAVAILABLE"


def test_quarantined_observation_never_enters_evidence() -> None:
    provider = _RepairCountingProvider(first=_bad_citation(), repair=_bad_citation())
    result = _run(provider)
    assert result.evidence == ()
    assert result.projections == ()


def test_offscope_dimension_quarantines_without_valid_dimension_label() -> None:
    # An injected off-scope dimension cannot be repaired into scope; it quarantines
    # and its dimension label is dropped because the catalog does not recognize it.
    seg = _segments_by_id()["seg-a"]
    bad = {
        "dimension_id": "technical-scope",  # not in accepted PolicyV2 subset
        "state": "SUPPORTED",
        "citations": [exact_citation(seg)],
    }
    provider = _RepairCountingProvider(first=bad, repair=bad)
    result = _run(provider)
    assert len(result.quarantined) == 1
    assert result.quarantined[0].initial_reason_code == "OFF_SCOPE_DIMENSION"
