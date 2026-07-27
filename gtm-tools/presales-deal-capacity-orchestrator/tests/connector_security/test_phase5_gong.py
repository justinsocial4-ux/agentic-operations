from __future__ import annotations

import hashlib
import json
import pickle
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx
import pytest

from orchestrator.canonical import canonical_json_bytes
from orchestrator.contracts.adapter import RequestBodyBoundsV1
from orchestrator.contracts.enums import ImplementationProofV1, LiveValidationProofV1
from orchestrator.ingestion.gong import (
    PINNED_ARTIFACT_SHA256,
    PINNED_HOST_SET_SHA256,
    PINNED_OPERATION_IDS,
    GongAdapter,
    GongCapabilityDegraded,
    GongContractError,
    GongPinError,
    GongProactiveLimiter,
    GongRateLimitError,
    validate_gong_request_body,
)
from orchestrator.ingestion.registry import load_gong_capability
from orchestrator.ingestion.transport import (
    AllowedEndpoint,
    EphemeralCredential,
    LockedHttpClient,
    TransportDenied,
    build_httpx_client,
    validate_vendor_url,
)

ROOT = Path(__file__).resolve().parents[2]
FX = ROOT / "data" / "replay" / "gong"
NOW = datetime(2026, 8, 3, 9, 0, tzinfo=timezone.utc)
END = datetime(2026, 8, 3, 10, 0, tzinfo=timezone.utc)
ALL_SCOPES = frozenset({
    "api:calls:read:basic", "api:calls:read:extensive", "api:calls:read:transcript", "api:users:read",
})
CALL_SCOPES = frozenset({
    "api:calls:read:basic", "api:calls:read:extensive", "api:calls:read:transcript",
})


def _fixture(name: str) -> dict:
    return json.loads((FX / name).read_text(encoding="utf-8"))


def _default_handler(request: httpx.Request) -> httpx.Response:
    path = request.url.path
    if path == "/v2/calls":
        return httpx.Response(200, json=_fixture("calls-page.json"))
    if path == "/v2/calls/extensive":
        return httpx.Response(200, json=_fixture("calls-extensive.json"))
    if path == "/v2/calls/transcript":
        return httpx.Response(200, json=_fixture("call-transcript.json"))
    if path == "/v2/users":
        return httpx.Response(200, json=_fixture("users.json"))
    return httpx.Response(404, json={})


def _adapter(
    handler=_default_handler,
    *,
    scopes: frozenset[str] = ALL_SCOPES,
    auth_mode: str = "SESSION_PASTED_BEARER",
    limiter: GongProactiveLimiter | None = None,
    sleeper=lambda _: None,
    capability=None,
) -> GongAdapter:
    cap = capability or load_gong_capability(ROOT)
    endpoints = GongAdapter._build_endpoints(cap)
    raw = build_httpx_client(transport=httpx.MockTransport(handler))
    locked = LockedHttpClient(endpoints, client=raw, sleeper=sleeper, now=lambda: 0)
    return GongAdapter(
        package_root=ROOT, auth_mode=auth_mode, bearer_token="fake-gong-bearer-phase5",
        available_scopes=scopes, capability=cap, client=locked,
        limiter=limiter or GongProactiveLimiter(monotonic=lambda: 0.0, wallclock=lambda: 0.0),
    )


# -- pin / host / operation enforcement --------------------------------------------


def test_phase0_pin_constants_match_the_reviewed_capability() -> None:
    cap = load_gong_capability(ROOT)
    pin = cap.official_artifact
    assert pin.sha256 == PINNED_ARTIFACT_SHA256
    assert pin.approved_host_set_sha256 == PINNED_HOST_SET_SHA256
    assert {o.operation_id for o in cap.operations} == PINNED_OPERATION_IDS
    artifact_bytes = (ROOT / pin.artifact_path).read_bytes()
    assert hashlib.sha256(artifact_bytes).hexdigest() == PINNED_ARTIFACT_SHA256
    host_hash = hashlib.sha256(canonical_json_bytes(list(pin.approved_host_set))).hexdigest()
    assert host_hash == PINNED_HOST_SET_SHA256


def test_adapter_construction_verifies_pin_and_hosts() -> None:
    adapter = _adapter()
    assert all(e.host == "api.gong.io" for e in adapter._endpoints)
    status = adapter.preflight_status()
    assert status["pinned_artifact_sha256"] == PINNED_ARTIFACT_SHA256
    assert status["approved_host_set"] == ["api.gong.io"]
    adapter.close()


def test_drifted_artifact_hash_is_rejected() -> None:
    cap = load_gong_capability(ROOT)
    drifted = cap.model_copy(update={
        "official_artifact": cap.official_artifact.model_copy(update={"sha256": "0" * 64}),
    })
    with pytest.raises(GongPinError):
        _adapter(capability=drifted)


def test_mutating_post_to_v2_calls_is_not_allowlisted() -> None:
    # addCall (POST /v2/calls) is a mutation; only GET /v2/calls is pinned.
    adapter = _adapter()
    with pytest.raises(TransportDenied):
        adapter._client.request(
            operation_id="addCall", method="POST", url="https://api.gong.io/v2/calls",
            content=b"{}",
        )
    adapter.close()


def test_gong_ssrf_and_non_gong_hosts_denied() -> None:
    for url in (
        "https://api.gong.io.evil.invalid/v2/calls",
        "https://127.0.0.1:8443/v2/calls",
        "http://api.gong.io/v2/calls",
        "https://api.gong.com/v2/calls",
    ):
        with pytest.raises(TransportDenied):
            validate_vendor_url(url, approved_hosts=frozenset({"api.gong.io"}))


# -- auth: pasted-bearer only + redaction ------------------------------------------


def test_only_session_pasted_bearer_or_basic_no_oauth_flow() -> None:
    for bad in ("OAUTH_AUTHORIZATION_CODE", "OAUTH_REFRESH", "BROWSER_OAUTH", "REDIRECT"):
        with pytest.raises(GongContractError, match="no authorization-code"):
            _adapter(auth_mode=bad)


def test_pasted_bearer_credential_is_redacted_and_not_serializable() -> None:
    credential = EphemeralCredential.bearer("fake-gong-bearer-phase5")
    assert "fake-gong-bearer" not in repr(credential)
    with pytest.raises(TypeError, match="cannot be serialized"):
        pickle.dumps(credential)


def test_bearer_is_issued_per_request_and_never_ambient() -> None:
    seen: list[httpx.Request] = []
    adapter = _adapter(lambda r: seen.append(r) or _default_handler(r))
    adapter.list_calls(from_dt=NOW, to_dt=END)
    assert seen[0].headers["authorization"] == "Bearer fake-gong-bearer-phase5"
    assert "authorization" not in adapter._client._client.headers
    adapter.close()


# -- read-by-POST body bounds + hostile bodies -------------------------------------

BOUNDS = RequestBodyBoundsV1(
    allowed_keys=("filter", "contentSelector", "cursor"),
    max_ids=100, max_body_bytes=65_536, max_date_window_days=30,
)


def test_forbidden_body_keys_rejected_top_level_and_nested() -> None:
    for hostile in (
        {"url": "https://x.invalid"},
        {"callback": "x"},
        {"callback_url": "x"},
        {"destination_url": "x"},
        {"webhook": "x"},
        {"filter": {"callIds": ["a"], "webhook": "nested-hostile"}},
        {"filter": {"nested": {"deeper": {"destination_url": "x"}}}},
    ):
        with pytest.raises(GongContractError, match="forbidden"):
            validate_gong_request_body(hostile, BOUNDS)


def test_non_allowlisted_top_level_key_rejected() -> None:
    with pytest.raises(GongContractError, match="not allowlisted"):
        validate_gong_request_body({"filter": {}, "extra": 1}, BOUNDS)


def test_excessive_and_duplicate_call_ids_rejected() -> None:
    with pytest.raises(GongContractError, match="exceed"):
        validate_gong_request_body({"filter": {"callIds": [str(i) for i in range(101)]}}, BOUNDS)
    with pytest.raises(GongContractError, match="duplicate"):
        validate_gong_request_body({"filter": {"callIds": ["a", "a"]}}, BOUNDS)


def test_inverted_and_oversized_date_windows_rejected() -> None:
    with pytest.raises(GongContractError, match="inverted"):
        validate_gong_request_body(
            {"filter": {"fromDateTime": "2026-08-10T00:00:00Z", "toDateTime": "2026-08-01T00:00:00Z"}},
            BOUNDS,
        )
    with pytest.raises(GongContractError, match="exceeds the pinned maximum"):
        validate_gong_request_body(
            {"filter": {"fromDateTime": "2026-08-01T00:00:00Z", "toDateTime": "2026-09-15T00:00:00Z"}},
            BOUNDS,
        )


def test_body_byte_overflow_rejected() -> None:
    tight = RequestBodyBoundsV1(
        allowed_keys=("filter",), max_ids=100, max_body_bytes=32, max_date_window_days=30,
    )
    with pytest.raises(GongContractError, match="byte bound"):
        validate_gong_request_body({"filter": {"callIds": [str(i) for i in range(50)]}}, tight)


def test_adapter_generated_extensive_body_is_closed_and_bounded() -> None:
    captured: list[bytes] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/v2/calls/extensive":
            captured.append(request.content)
        return _default_handler(request)

    adapter = _adapter(handler)
    adapter.list_calls_extensive(call_ids=("gong-call-1",), from_dt=NOW, to_dt=END)
    body = json.loads(captured[0])
    assert set(body) <= {"filter", "contentSelector", "cursor"}
    assert "url" not in json.dumps(body) and "webhook" not in json.dumps(body)
    adapter.close()


# -- proactive throttling ----------------------------------------------------------


def test_three_per_second_is_enforced_before_transport() -> None:
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return _default_handler(request)

    limiter = GongProactiveLimiter(monotonic=lambda: 0.0, wallclock=lambda: 0.0)
    adapter = _adapter(handler, limiter=limiter)
    adapter.list_calls(from_dt=NOW, to_dt=END)
    adapter.list_calls(from_dt=NOW, to_dt=END, cursor="c1")
    adapter.list_calls(from_dt=NOW, to_dt=END, cursor="c2")
    before = calls["n"]
    with pytest.raises(GongRateLimitError) as excinfo:
        adapter.list_calls(from_dt=NOW, to_dt=END, cursor="c3")
    assert excinfo.value.scope == "PER_SECOND_3"
    assert calls["n"] == before  # no transport happened on the throttled call
    adapter.close()


def test_ten_thousand_per_day_stops_before_transport() -> None:
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return _default_handler(request)

    ticks = {"t": 0.0}

    def monotonic() -> float:
        ticks["t"] += 1.0  # always outside the 1s window so per-second never trips
        return ticks["t"]

    limiter = GongProactiveLimiter(
        monotonic=monotonic, wallclock=lambda: 0.0, initial_daily_count=9_999,
    )
    adapter = _adapter(handler, limiter=limiter)
    adapter.list_calls(from_dt=NOW, to_dt=END)  # 9,999 -> 10,000
    with pytest.raises(GongRateLimitError) as excinfo:
        adapter.list_calls(from_dt=NOW, to_dt=END, cursor="c1")
    assert excinfo.value.scope == "PER_DAY_10000"
    assert calls["n"] == 1
    adapter.close()


# -- capability degradation --------------------------------------------------------


def test_missing_optional_users_scope_degrades_but_calls_and_transcripts_work() -> None:
    adapter = _adapter(scopes=CALL_SCOPES)
    assert adapter.users_state == "USERS_UNAVAILABLE"
    assert adapter.preflight_status()["users_state"] == "USERS_UNAVAILABLE"
    # calls + transcript reads continue
    calls = adapter.list_calls(from_dt=NOW, to_dt=END)
    assert calls["calls"][0]["id"] == "gong-call-1"
    route = adapter.read_transcript_route(
        source_instance_id="src-gong", call_id="gong-call-1", from_dt=NOW, to_dt=END,
        exact_deal_source_id="deal-1", started_at=NOW, ended_at=END, route_id="direct-gong",
    )
    assert len(route.segments) == 2
    # only the users directory is unavailable
    with pytest.raises(GongCapabilityDegraded):
        adapter.list_users()
    adapter.close()


def test_missing_required_scope_is_a_hard_error() -> None:
    with pytest.raises(GongContractError, match="required"):
        _adapter(scopes=frozenset({"api:calls:read:basic"}))


# -- idempotent-retry designation --------------------------------------------------


def test_all_pinned_operations_are_designated_idempotent_retryable() -> None:
    cap = load_gong_capability(ROOT)
    assert all(op.idempotent_retryable for op in cap.operations)


def test_undesignated_read_by_post_never_retries() -> None:
    calls = {"n": 0}

    def handler(_: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(429, headers={"retry-after": "1"})

    endpoint = AllowedEndpoint(
        "gong.nonidempotent", "POST", "api.gong.io", "/v2/calls/transcript", idempotent_retryable=False,
    )
    raw = build_httpx_client(transport=httpx.MockTransport(handler))
    client = LockedHttpClient((endpoint,), client=raw, sleeper=lambda _: None, now=lambda: 0)
    response = client.request_with_retry(
        operation_id="gong.nonidempotent", method="POST", url="https://api.gong.io/v2/calls/transcript",
        content=b"{}",
    )
    assert response.status_code == 429
    assert calls["n"] == 1  # no retry for an undesignated read-by-POST
    client.close()


# -- translation forward-compat + malformed ----------------------------------------


def test_translator_ignores_non_allowlisted_response_fields() -> None:
    adapter = _adapter()
    calls = adapter.list_calls(from_dt=NOW, to_dt=END)
    row = calls["calls"][0]
    assert set(row).issubset({"id", "started", "duration", "title"})
    assert "unmapped_future_field" not in row
    adapter.close()


def test_malformed_responses_fail_visibly() -> None:
    def missing_calls(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"records": {}})

    adapter = _adapter(missing_calls)
    with pytest.raises(GongContractError, match="missing calls"):
        adapter.list_calls(from_dt=NOW, to_dt=END)
    adapter.close()

    def bad_transcript(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/v2/calls/extensive":
            return httpx.Response(200, json=_fixture("calls-extensive.json"))
        return httpx.Response(200, json={"callTranscripts": [{"callId": "gong-call-1", "transcript": "not-a-list"}]})

    adapter2 = _adapter(bad_transcript)
    with pytest.raises(GongContractError):
        adapter2.read_transcript_route(
            source_instance_id="src", call_id="gong-call-1", from_dt=NOW, to_dt=END,
            exact_deal_source_id="deal-1", started_at=NOW, ended_at=END, route_id="r",
        )
    adapter2.close()


def test_transcript_translation_assigns_party_roles() -> None:
    adapter = _adapter()
    route = adapter.read_transcript_route(
        source_instance_id="src-gong", call_id="gong-call-1", from_dt=NOW, to_dt=END,
        exact_deal_source_id="deal-1", started_at=NOW, ended_at=END, route_id="direct-gong",
    )
    roles = [seg.speaker_ref for seg in route.segments]
    assert roles == ["CUSTOMER", "INTERNAL"]
    serialized = json.dumps([seg.model_dump() for seg in route.segments], default=str)
    assert "@" not in serialized  # no email persists into segments
    adapter.close()


def test_gong_proof_is_contract_tested_not_live_validated() -> None:
    proof = GongAdapter.proof()
    assert proof.implementation_proof is ImplementationProofV1.FULLY_IMPLEMENTED_CONTRACT_TESTED
    assert proof.live_validation_proof is LiveValidationProofV1.NOT_LIVE_VALIDATED


def test_list_date_window_over_thirty_days_rejected() -> None:
    adapter = _adapter()
    with pytest.raises(GongContractError, match="30 days"):
        adapter.list_calls(from_dt=NOW, to_dt=NOW + timedelta(days=31))
    adapter.close()
