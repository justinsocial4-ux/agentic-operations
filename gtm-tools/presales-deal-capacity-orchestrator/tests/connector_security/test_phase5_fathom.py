from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import httpx
import pytest

from orchestrator.contracts.enums import ImplementationProofV1, LiveValidationProofV1
from orchestrator.ingestion.fathom import (
    FathomAdapter,
    FathomContractError,
    FathomMeetingsRequestV1,
    FathomRateLimiter,
    FathomRateLimitError,
    _reject_forbidden_query,
)
from orchestrator.ingestion.transport import (
    LockedHttpClient,
    TransportDenied,
    build_httpx_client,
    validate_vendor_url,
)

ROOT = Path(__file__).resolve().parents[2]
FX = ROOT / "data" / "replay" / "fathom"
NOW = datetime(2026, 8, 3, 9, 0, tzinfo=timezone.utc)
END = datetime(2026, 8, 3, 9, 45, tzinfo=timezone.utc)


def _fixture(name: str) -> dict:
    return json.loads((FX / name).read_text(encoding="utf-8"))


def _adapter(handler, *, limiter: FathomRateLimiter | None = None, sleeper=lambda _: None) -> FathomAdapter:
    raw = build_httpx_client(transport=httpx.MockTransport(handler))
    locked = LockedHttpClient(
        FathomAdapter._allowed_endpoints(), client=raw, sleeper=sleeper, now=lambda: 0,
    )
    return FathomAdapter(api_key="fake-fathom-key-phase5", client=locked, limiter=limiter)


def test_capability_is_get_only_with_no_webhook_or_callback_surface() -> None:
    adapter = _adapter(lambda _: httpx.Response(200, json={"items": []}))
    capability = adapter.capability()
    assert {op.method for op in capability.operations} == {"GET"}
    assert {op.operation_id for op in capability.operations} == {
        "fathom.meetings", "fathom.recording-transcript",
    }
    assert capability.external_writes_supported is False
    assert capability.write_operation_ids == ()
    # No webhook/callback/destination operation exists in the allowlist.
    assert all("webhook" not in op.path_template and "callback" not in op.path_template for op in capability.operations)
    adapter.close()


def test_callback_webhook_and_destination_url_query_keys_are_denied() -> None:
    for key in ("destination_url", "callback", "callback_url", "webhook", "webhook_url"):
        with pytest.raises(FathomContractError, match="forbidden"):
            _reject_forbidden_query({key: "https://attacker.invalid/x"})


def test_meetings_cursor_next_cursor_and_summary_action_items_dropped() -> None:
    adapter = _adapter(lambda _: httpx.Response(200, json=_fixture("meetings-page.json")))
    page = adapter.meetings_page(FathomMeetingsRequestV1(created_after=NOW, created_before=END))
    assert page.next_cursor == "fathom-cursor-page-2"
    assert page.cursor_sha256 is not None
    meeting = page.meetings[0]
    assert meeting.recording_id == "rec-fict-001"
    # Source summary / action items are not carried as evidence.
    assert not hasattr(meeting, "summary")
    assert not hasattr(meeting, "action_items")
    assert "summary" not in json.dumps(meeting.__dict__, default=str)
    adapter.close()


def test_repeated_cursor_is_rejected() -> None:
    adapter = _adapter(lambda _: httpx.Response(200, json=_fixture("meetings-page.json")))
    adapter.meetings_page(FathomMeetingsRequestV1(created_after=NOW))
    with pytest.raises(FathomContractError, match="cyclic"):
        # feeding the same cursor back must be rejected as a cycle
        adapter.meetings_page(FathomMeetingsRequestV1(cursor="fathom-cursor-page-2"))
    adapter.close()


def test_transcript_route_minimizes_emails_and_never_persists_them() -> None:
    adapter = _adapter(lambda _: httpx.Response(200, json=_fixture("recording-transcript.json")))
    route = adapter.read_transcript_route(
        source_instance_id="src-fathom", recording_id="rec-fict-001",
        native_meeting_id="meet-fict-001", exact_deal_source_id="deal-1",
        started_at=NOW, ended_at=END, route_id="fathom-direct",
        internal_participant_labels=frozenset({"Fictional SC"}),
    )
    serialized = json.dumps([seg.model_dump() for seg in route.segments], default=str)
    assert "buyer@example.invalid" not in serialized
    assert "sc@example.invalid" not in serialized
    assert "@" not in serialized  # no email survives into any segment
    # Role is UNKNOWN unless an internal participant is explicitly confirmed.
    roles = {seg.speaker_ref for seg in route.segments}
    assert roles == {"UNKNOWN", "INTERNAL"}
    labels = {seg.speaker_source_label for seg in route.segments}
    assert labels == {"Fictional Buyer", "Fictional SC"}
    adapter.close()


def test_transcript_translator_ignores_non_allowlisted_response_fields() -> None:
    adapter = _adapter(lambda _: httpx.Response(200, json=_fixture("recording-transcript.json")))
    route = adapter.read_transcript_route(
        source_instance_id="src-fathom", recording_id="rec-fict-001",
        native_meeting_id="meet-fict-001", exact_deal_source_id="deal-1",
        started_at=NOW, ended_at=END, route_id="fathom-direct",
    )
    assert len(route.segments) == 2  # unmapped_future_field ignored, still parses
    adapter.close()


def test_heavy_limiter_enforces_thirty_then_five_per_sixty_seconds() -> None:
    limiter = FathomRateLimiter(clock=lambda: 0.0)
    for _ in range(30):
        limiter.acquire(heavy=True)
    with pytest.raises(FathomRateLimitError) as excinfo:
        limiter.acquire(heavy=True)
    assert excinfo.value.scope == "HEAVY_30_PER_60S"

    tightened = FathomRateLimiter(clock=lambda: 0.0)
    tightened.tighten_heavy_to_five()
    for _ in range(5):
        tightened.acquire(heavy=True)
    with pytest.raises(FathomRateLimitError):
        tightened.acquire(heavy=True)


def test_standard_limiter_enforces_sixty_per_sixty_seconds() -> None:
    limiter = FathomRateLimiter(clock=lambda: 0.0)
    for _ in range(60):
        limiter.acquire(heavy=False)
    with pytest.raises(FathomRateLimitError) as excinfo:
        limiter.acquire(heavy=False)
    assert excinfo.value.scope == "STANDARD_60_PER_60S"


def test_heavy_transcript_honors_bounded_retry_after() -> None:
    calls = {"n": 0}
    sleeps: list[float] = []

    def handler(_: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] == 1:
            return httpx.Response(429, headers={"retry-after": "2"})
        return httpx.Response(200, json=_fixture("recording-transcript.json"))

    adapter = _adapter(handler, sleeper=sleeps.append)
    route = adapter.read_transcript_route(
        source_instance_id="src-fathom", recording_id="rec-fict-001",
        native_meeting_id="meet-fict-001", exact_deal_source_id="deal-1",
        started_at=NOW, ended_at=END, route_id="fathom-direct",
    )
    assert len(route.segments) == 2
    assert sleeps == [2.0]  # bounded Retry-After honored
    adapter.close()


def test_fathom_ssrf_non_allowlisted_host_denied() -> None:
    for url in (
        "https://api.fathom.ai.evil.invalid/external/v1/meetings",
        "https://127.0.0.1/external/v1/meetings",
        "http://api.fathom.ai/external/v1/meetings",
    ):
        with pytest.raises(TransportDenied):
            validate_vendor_url(url, approved_hosts=frozenset({"api.fathom.ai"}))


def test_fathom_proof_is_contract_tested_not_live_validated() -> None:
    proof = FathomAdapter.proof()
    assert proof.implementation_proof is ImplementationProofV1.FULLY_IMPLEMENTED_CONTRACT_TESTED
    assert proof.live_validation_proof is LiveValidationProofV1.NOT_LIVE_VALIDATED
