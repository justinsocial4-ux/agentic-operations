"""Gong read-only client and raw-to-canonical translator (Phase 5).

Gong is READ-ONLY. Only the four Phase 0 pinned operations are reachable:
``listCalls`` (GET /v2/calls), ``listCallsExtensive`` (read-by-POST /v2/calls/extensive),
``getCallTranscripts`` (read-by-POST /v2/calls/transcript), and the optional
``listUsers`` (GET /v2/users). Mutating POST endpoints (for example ``addCall``) are not
in the allowlist. Read-by-POST bodies are adapter-generated, strictly typed, closed, and
size/ID/date bounded; url, callback, destination, and webhook keys are forbidden anywhere in the
body. Proactive throttling (3/sec + 10,000/day) runs before transport; ``Retry-After`` is
an additional reaction. Full transcript text stays in memory only.

v1 OAuth is a session-only PASTED BEARER token. There is no authorization-code, redirect,
refresh-token, or browser OAuth flow in this module.
"""

from __future__ import annotations

import base64
import hashlib
import time
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable

from orchestrator.canonical import canonical_json_bytes
from orchestrator.contracts.adapter import AdapterCapabilityV1, RequestBodyBoundsV1
from orchestrator.contracts.base import strict_json_loads
from orchestrator.contracts.connectors import ConnectorPreflightReceiptV1
from orchestrator.contracts.enums import ExecutionModeV1, ImplementationProofV1, LiveValidationProofV1
from orchestrator.contracts.proof import SourceProofInputV1
from orchestrator.contracts.records import ConversationSegmentV1
from orchestrator.ingestion.manifests import (
    opaque_source_instance_id,
    source_identity_fingerprint,
    stable_source_record_id,
)
from orchestrator.ingestion.registry import load_gong_capability
from orchestrator.ingestion.transcripts import TranscriptRoute
from orchestrator.ingestion.transport import (
    AllowedEndpoint,
    EphemeralCredential,
    LockedHttpClient,
)

_GONG_HOST = "api.gong.io"
_GONG_BASE = "https://api.gong.io"
_MAX_RESPONSE_BYTES = 20 * 1024 * 1024

# Bound Phase 5 code to the exact Phase 0 capability pin. These must never drift.
PINNED_ARTIFACT_SHA256 = "4583f7a19d8f8328e6eb8d85829e1632eda335a9010c0d2f09d9dedeb07b6bd6"
PINNED_HOST_SET_SHA256 = "08d795d7f4d9d1f888caeb437847e09324414003953c6b9d135b87f478224293"
PINNED_OPERATION_IDS = frozenset({"listCalls", "listCallsExtensive", "getCallTranscripts", "listUsers"})

_REQUIRED_SCOPES = frozenset(
    {"api:calls:read:basic", "api:calls:read:extensive", "api:calls:read:transcript"}
)
_OPTIONAL_USERS_SCOPE = "api:users:read"
_PERMITTED_AUTH_MODES = frozenset({"SESSION_PASTED_BEARER", "SESSION_BASIC"})


class GongContractError(ValueError):
    pass


class GongPinError(RuntimeError):
    pass


class GongResponseError(RuntimeError):
    pass


class GongCapabilityDegraded(RuntimeError):
    def __init__(self, state: str) -> None:
        super().__init__(f"Gong capability degraded: {state}")
        self.state = state


class GongRateLimitError(RuntimeError):
    def __init__(self, scope: str) -> None:
        super().__init__("Gong proactive rate limit reached before transport")
        self.scope = scope


class GongProactiveLimiter:
    """Proactive token/window enforcement: at most 3/sec and a durable opaque-source
    daily counter that stops before 10,000/day. A production build binds ``daily_count``
    to the durable per-source checkpoint; contract tests inject the initial count.
    """

    def __init__(
        self,
        *,
        monotonic: Callable[[], float] = time.monotonic,
        wallclock: Callable[[], float] = time.time,
        per_second: int = 3,
        per_day: int = 10_000,
        initial_daily_count: int = 0,
        initial_day: str | None = None,
    ) -> None:
        if per_second != 3 or per_day != 10_000:
            raise ValueError("Gong proactive limits are fixed at 3/sec and 10,000/day")
        self._monotonic = monotonic
        self._wallclock = wallclock
        self._per_second = per_second
        self._per_day = per_day
        self._events: deque[float] = deque()
        self._daily_count = initial_daily_count
        self._day = initial_day if initial_day is not None else self._current_day()

    def _current_day(self) -> str:
        return datetime.fromtimestamp(self._wallclock(), tz=timezone.utc).date().isoformat()

    def acquire(self) -> None:
        now = self._monotonic()
        while self._events and now - self._events[0] >= 1.0:
            self._events.popleft()
        today = self._current_day()
        if today != self._day:
            self._day = today
            self._daily_count = 0
        if self._daily_count >= self._per_day:
            raise GongRateLimitError("PER_DAY_10000")
        if len(self._events) >= self._per_second:
            raise GongRateLimitError("PER_SECOND_3")
        self._events.append(now)
        self._daily_count += 1

    @property
    def daily_count(self) -> int:
        return self._daily_count

    @property
    def per_second_remaining(self) -> int:
        now = self._monotonic()
        while self._events and now - self._events[0] >= 1.0:
            self._events.popleft()
        return self._per_second - len(self._events)


def _deep_reject_forbidden(obj: object, forbidden: frozenset[str]) -> None:
    if isinstance(obj, dict):
        for key, value in obj.items():
            if not isinstance(key, str):
                raise GongContractError("Gong body keys must be strings")
            if key in forbidden:
                raise GongContractError(f"forbidden body key: {key}")
            _deep_reject_forbidden(value, forbidden)
    elif isinstance(obj, (list, tuple)):
        for item in obj:
            _deep_reject_forbidden(item, forbidden)


def _parse_aware(value: str, *, field: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, AttributeError) as exc:
        raise GongContractError(f"invalid Gong {field}") from exc
    if parsed.tzinfo is None:
        raise GongContractError(f"Gong {field} must be offset-aware")
    return parsed


def validate_gong_request_body(body: dict[str, object], bounds: RequestBodyBoundsV1) -> bytes:
    """Enforce the closed, bounded body contract and return canonical bytes.

    Rejects: non-allowlisted top-level keys, forbidden keys anywhere (nested hostile keys),
    excessive/duplicate call IDs, inverted/oversized date windows, and body-byte overflow.
    """
    if not isinstance(body, dict):
        raise GongContractError("Gong request body must be an object")
    forbidden = frozenset(bounds.forbidden_keys)
    allowed = frozenset(bounds.allowed_keys)
    for key in body:
        if key in forbidden:
            raise GongContractError(f"forbidden body key: {key}")
        if key not in allowed:
            raise GongContractError(f"body key is not allowlisted: {key}")
    _deep_reject_forbidden(body, forbidden)

    filter_block = body.get("filter")
    if filter_block is not None:
        if not isinstance(filter_block, dict):
            raise GongContractError("Gong filter must be an object")
        call_ids = filter_block.get("callIds")
        if call_ids is not None:
            if not isinstance(call_ids, (list, tuple)) or any(not isinstance(item, str) for item in call_ids):
                raise GongContractError("callIds must be a list of strings")
            if len(call_ids) > bounds.max_ids:
                raise GongContractError("callIds exceed the pinned maximum")
            if len(call_ids) != len(set(call_ids)):
                raise GongContractError("callIds contain duplicates")
        from_raw = filter_block.get("fromDateTime")
        to_raw = filter_block.get("toDateTime")
        if (from_raw is None) != (to_raw is None):
            raise GongContractError("date window requires both bounds or neither")
        if from_raw is not None and to_raw is not None:
            begin = _parse_aware(str(from_raw), field="fromDateTime")
            end = _parse_aware(str(to_raw), field="toDateTime")
            if begin >= end:
                raise GongContractError("Gong date window is inverted or empty")
            if end - begin > timedelta(days=bounds.max_date_window_days):
                raise GongContractError("Gong date window exceeds the pinned maximum")

    encoded = canonical_json_bytes(body)
    if len(encoded) > bounds.max_body_bytes:
        raise GongContractError("Gong request body exceeds the pinned byte bound")
    return encoded


@dataclass(frozen=True)
class GongPartyV1:
    speaker_id: str
    role: str  # CUSTOMER | INTERNAL | UNKNOWN
    minimized_name: str | None  # in-memory only; never persisted


def _affiliation_to_role(affiliation: object) -> str:
    if isinstance(affiliation, str):
        normalized = affiliation.strip().lower()
        if normalized == "internal":
            return "INTERNAL"
        if normalized == "external":
            return "CUSTOMER"
    return "UNKNOWN"


class GongAdapter:
    adapter_id = "gong-api-v2"

    def __init__(
        self,
        *,
        package_root: Path,
        auth_mode: str,
        bearer_token: str | None = None,
        access_key: str | None = None,
        access_key_secret: str | None = None,
        available_scopes: frozenset[str],
        capability: AdapterCapabilityV1 | None = None,
        client: LockedHttpClient | None = None,
        limiter: GongProactiveLimiter | None = None,
    ) -> None:
        if auth_mode not in _PERMITTED_AUTH_MODES:
            raise GongContractError(
                "Gong v1 supports only SESSION_PASTED_BEARER or SESSION_BASIC; "
                "no authorization-code, redirect, or refresh OAuth flow exists"
            )
        self._capability = capability or load_gong_capability(package_root)
        self._verify_pin(package_root, self._capability)
        self._endpoints = self._build_endpoints(self._capability)
        self._body_bounds = {
            operation.operation_id: operation.body_bounds
            for operation in self._capability.operations
            if operation.body_bounds is not None
        }
        self.auth_mode = auth_mode
        self._credential = self._build_credential(
            auth_mode, bearer_token, access_key, access_key_secret
        )
        missing_required = _REQUIRED_SCOPES - available_scopes
        if missing_required:
            raise GongContractError(
                "missing required Gong read scopes for calls/transcripts"
            )
        self.users_state = "USERS_AVAILABLE" if _OPTIONAL_USERS_SCOPE in available_scopes else "USERS_UNAVAILABLE"
        self._available_scopes = frozenset(available_scopes)
        self._client = client or LockedHttpClient(self._endpoints)
        self._limiter = limiter or GongProactiveLimiter()
        self._seen_cursors: set[str] = set()

    # -- pin + endpoint construction ------------------------------------------------

    def _verify_pin(self, package_root: Path, capability: AdapterCapabilityV1) -> None:
        if capability.adapter_id != self.adapter_id:
            raise GongPinError("capability is not the pinned Gong adapter")
        pin = capability.official_artifact
        if pin is None:
            raise GongPinError("Gong capability is missing its reviewed official artifact pin")
        artifact_bytes = (package_root / pin.artifact_path).read_bytes()
        if hashlib.sha256(artifact_bytes).hexdigest() != pin.sha256:
            raise GongPinError("Gong official artifact hash does not match the pin")
        if pin.sha256 != PINNED_ARTIFACT_SHA256:
            raise GongPinError("Gong artifact pin drifted from the Phase 0 hash")
        host_hash = hashlib.sha256(canonical_json_bytes(list(pin.approved_host_set))).hexdigest()
        if host_hash != pin.approved_host_set_sha256 or pin.approved_host_set_sha256 != PINNED_HOST_SET_SHA256:
            raise GongPinError("Gong approved host-set hash drifted from the Phase 0 pin")
        operations = [
            {"operation_id": o.operation_id, "method": o.method, "path": o.path_template}
            for o in capability.operations
        ]
        if hashlib.sha256(canonical_json_bytes(operations)).hexdigest() != pin.operation_ids_sha256:
            raise GongPinError("Gong operation-IDs hash does not match the pin")
        if {o.operation_id for o in capability.operations} != PINNED_OPERATION_IDS:
            raise GongPinError("Gong operation set drifted from the four pinned operations")
        for operation in capability.operations:
            if operation.host != _GONG_HOST or operation.host not in pin.approved_host_set:
                raise GongPinError("Gong operation host is outside the approved host set")
        if capability.external_writes_supported is not False or capability.write_operation_ids != ():
            raise GongPinError("Gong capability must declare no external writes")

    @staticmethod
    def _build_endpoints(capability: AdapterCapabilityV1) -> tuple[AllowedEndpoint, ...]:
        return tuple(
            AllowedEndpoint(
                operation.operation_id,
                operation.method,
                operation.host,
                operation.path_template,
                operation.idempotent_retryable,
            )
            for operation in capability.operations
        )

    @staticmethod
    def _build_credential(
        auth_mode: str,
        bearer_token: str | None,
        access_key: str | None,
        access_key_secret: str | None,
    ) -> EphemeralCredential:
        if auth_mode == "SESSION_PASTED_BEARER":
            if not bearer_token:
                raise GongContractError("pasted bearer auth requires a session token")
            return EphemeralCredential.bearer(bearer_token)
        if not access_key or not access_key_secret:
            raise GongContractError("Basic auth requires an access key and secret")
        encoded = base64.b64encode(f"{access_key}:{access_key_secret}".encode()).decode()
        return EphemeralCredential.authorization_value(f"Basic {encoded}")

    def close(self) -> None:
        self._client.close()

    # -- capability / proof / preflight --------------------------------------------

    def capability(self) -> AdapterCapabilityV1:
        return self._capability

    @staticmethod
    def proof() -> SourceProofInputV1:
        return SourceProofInputV1(
            execution_mode=ExecutionModeV1.DIRECT_CONNECTOR_ENABLED,
            implementation_proof=ImplementationProofV1.FULLY_IMPLEMENTED_CONTRACT_TESTED,
            live_validation_proof=LiveValidationProofV1.NOT_LIVE_VALIDATED,
        )

    def preflight(self, *, non_secret_workspace_id: str) -> ConnectorPreflightReceiptV1:
        fingerprint = source_identity_fingerprint(
            adapter_id=self.adapter_id, non_secret_source_identity=non_secret_workspace_id,
        )
        return ConnectorPreflightReceiptV1(
            schema_version="orchestrator.connector-preflight.v1",
            adapter_id=self.adapter_id,
            source_instance_id=opaque_source_instance_id(
                adapter_id=self.adapter_id, identity_fingerprint=fingerprint,
            ),
            source_identity_fingerprint=fingerprint,
            auth_mode=self.auth_mode,
            permitted_operation_ids=tuple(item.operation_id for item in self._endpoints),
        )

    def preflight_status(self) -> dict[str, object]:
        """Non-secret preflight surface: auth mode, pinned capability, users degradation,
        and the remaining local request budget. No credential or token is included."""
        pin = self._capability.official_artifact
        return {
            "auth_mode": self.auth_mode,
            "pinned_artifact_sha256": pin.sha256 if pin else None,
            "approved_host_set": list(pin.approved_host_set) if pin else [],
            "permitted_operation_ids": sorted(o.operation_id for o in self._endpoints),
            "users_state": self.users_state,
            "required_scopes_satisfied": _REQUIRED_SCOPES.issubset(self._available_scopes),
            "remaining_daily_requests": self._limiter._per_day - self._limiter.daily_count,
            "per_second_remaining": self._limiter.per_second_remaining,
        }

    # -- transport helpers ---------------------------------------------------------

    def _decode(self, response: object) -> tuple[dict[str, object], str]:
        status = int(getattr(response, "status_code"))
        headers = getattr(response, "headers")
        if status != 200:
            raise GongResponseError(f"Gong read returned HTTP {status}")
        if "application/json" not in headers.get("content-type", "application/json").lower():
            raise GongContractError("Gong response content type is not JSON")
        content = bytes(getattr(response, "content"))
        if len(content) > _MAX_RESPONSE_BYTES:
            raise GongContractError("Gong response exceeds the byte cap")
        payload = strict_json_loads(content)
        if not isinstance(payload, dict):
            raise GongContractError("Gong response must be an object")
        return payload, hashlib.sha256(content).hexdigest()

    def _get(self, operation_id: str, url: str) -> object:
        self._limiter.acquire()
        return self._client.request_with_retry(
            operation_id=operation_id,
            method="GET",
            url=url,
            credential=self._credential,
            headers={"Accept": "application/json"},
        )

    def _post_read(self, operation_id: str, url: str, body: bytes) -> object:
        self._limiter.acquire()
        return self._client.request_with_retry(
            operation_id=operation_id,
            method="POST",
            url=url,
            credential=self._credential,
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            content=body,
        )

    def _track_cursor(self, cursor: object) -> str | None:
        if cursor is None:
            return None
        if not isinstance(cursor, str) or not cursor:
            raise GongContractError("Gong cursor must be a non-empty string")
        digest = hashlib.sha256(cursor.encode()).hexdigest()
        if digest in self._seen_cursors:
            raise GongContractError("repeated or cyclic Gong cursor")
        self._seen_cursors.add(digest)
        return cursor

    # -- read operations -----------------------------------------------------------

    def list_calls(
        self,
        *,
        from_dt: datetime,
        to_dt: datetime,
        cursor: str | None = None,
    ) -> dict[str, object]:
        if from_dt.tzinfo is None or to_dt.tzinfo is None or from_dt >= to_dt:
            raise GongContractError("listCalls requires an aware increasing window")
        if to_dt - from_dt > timedelta(days=30):
            raise GongContractError("listCalls window exceeds 30 days")
        params = [
            ("fromDateTime", from_dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")),
            ("toDateTime", to_dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")),
        ]
        if cursor is not None:
            self._track_cursor(cursor)
            params.append(("cursor", cursor))
        from urllib.parse import urlencode

        response = self._get("listCalls", f"{_GONG_BASE}/v2/calls?{urlencode(params)}")
        payload, response_hash = self._decode(response)
        raw_calls = payload.get("calls")
        if not isinstance(raw_calls, list):
            raise GongContractError("listCalls response is missing calls")
        calls: list[dict[str, object]] = []
        for raw in raw_calls:
            if not isinstance(raw, dict) or not isinstance(raw.get("id"), str):
                raise GongContractError("Gong call is missing a string id")
            # Ignore non-allowlisted response fields (forward-compat).
            calls.append({key: raw[key] for key in ("id", "started", "duration", "title") if key in raw})
        return {
            "calls": tuple(calls),
            "next_cursor": self._extract_cursor(payload),
            "response_sha256": response_hash,
        }

    @staticmethod
    def _extract_cursor(payload: dict[str, object]) -> str | None:
        records = payload.get("records")
        if records is None:
            return None
        if not isinstance(records, dict):
            raise GongContractError("Gong records block must be an object")
        cursor = records.get("cursor")
        if cursor is not None and not isinstance(cursor, str):
            raise GongContractError("Gong records.cursor must be a string")
        return cursor

    def list_calls_extensive(
        self,
        *,
        call_ids: tuple[str, ...],
        from_dt: datetime,
        to_dt: datetime,
        cursor: str | None = None,
        expose_parties: bool = True,
    ) -> tuple[GongParsedCallV1, ...]:
        body: dict[str, object] = {
            "filter": {
                "fromDateTime": from_dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
                "toDateTime": to_dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
                "callIds": list(call_ids),
            },
            "contentSelector": {"exposedFields": {"parties": bool(expose_parties)}},
        }
        if cursor is not None:
            self._track_cursor(cursor)
            body["cursor"] = cursor
        bounds = self._body_bounds["listCallsExtensive"]
        encoded = validate_gong_request_body(body, bounds)
        response = self._post_read("listCallsExtensive", f"{_GONG_BASE}/v2/calls/extensive", encoded)
        payload, _ = self._decode(response)
        raw_calls = payload.get("calls")
        if not isinstance(raw_calls, list):
            raise GongContractError("extensive-call response is missing calls")
        return tuple(self._parse_extensive_call(raw) for raw in raw_calls)

    @staticmethod
    def _parse_extensive_call(raw: object) -> "GongParsedCallV1":
        if not isinstance(raw, dict):
            raise GongContractError("extensive call must be an object")
        meta = raw.get("metaData")
        if not isinstance(meta, dict) or not isinstance(meta.get("id"), str):
            raise GongContractError("extensive call is missing metaData.id")
        raw_parties = raw.get("parties", [])
        if not isinstance(raw_parties, list):
            raise GongContractError("extensive call parties must be a list")
        parties: list[GongPartyV1] = []
        for party in raw_parties:
            if not isinstance(party, dict) or not isinstance(party.get("speakerId"), str):
                # A party without a speakerId cannot map to transcript speakers; skip it.
                continue
            name = party.get("name")
            minimized = name[:200] if isinstance(name, str) else None
            # party.emailAddress is intentionally never retained.
            parties.append(GongPartyV1(
                speaker_id=party["speakerId"],
                role=_affiliation_to_role(party.get("affiliation")),
                minimized_name=minimized,
            ))
        return GongParsedCallV1(call_id=meta["id"], parties=tuple(parties))

    def get_call_transcripts(
        self,
        *,
        call_ids: tuple[str, ...],
        from_dt: datetime,
        to_dt: datetime,
        cursor: str | None = None,
    ) -> tuple[dict[str, object], ...]:
        body: dict[str, object] = {
            "filter": {
                "fromDateTime": from_dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
                "toDateTime": to_dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
                "callIds": list(call_ids),
            },
        }
        if cursor is not None:
            self._track_cursor(cursor)
            body["cursor"] = cursor
        bounds = self._body_bounds["getCallTranscripts"]
        encoded = validate_gong_request_body(body, bounds)
        response = self._post_read("getCallTranscripts", f"{_GONG_BASE}/v2/calls/transcript", encoded)
        payload, _ = self._decode(response)
        raw = payload.get("callTranscripts")
        if not isinstance(raw, list):
            raise GongContractError("transcript response is missing callTranscripts")
        return tuple(raw)

    def list_users(self, *, cursor: str | None = None) -> tuple[dict[str, object], ...]:
        if self.users_state != "USERS_AVAILABLE":
            raise GongCapabilityDegraded("USERS_UNAVAILABLE")
        from urllib.parse import urlencode

        url = f"{_GONG_BASE}/v2/users"
        if cursor is not None:
            self._track_cursor(cursor)
            url = f"{url}?{urlencode([('cursor', cursor)])}"
        response = self._get("listUsers", url)
        payload, _ = self._decode(response)
        raw_users = payload.get("users")
        if not isinstance(raw_users, list):
            raise GongContractError("listUsers response is missing users")
        users: list[dict[str, object]] = []
        for user in raw_users:
            if not isinstance(user, dict) or not isinstance(user.get("id"), str):
                raise GongContractError("Gong user is missing a string id")
            # Only opaque id + role-relevant fields; emails/names are never persisted.
            users.append({key: user[key] for key in ("id", "active") if key in user})
        return tuple(users)

    # -- transcript translation to ephemeral route ---------------------------------

    def read_transcript_route(
        self,
        *,
        source_instance_id: str,
        call_id: str,
        from_dt: datetime,
        to_dt: datetime,
        exact_deal_source_id: str,
        started_at: datetime,
        ended_at: datetime,
        route_id: str,
    ) -> TranscriptRoute:
        """Translate one Gong call transcript into an ephemeral TranscriptRoute.

        Speaker roles come from extensive-call party affiliation (available with
        api:calls:read:extensive). Missing optional api:users:read only removes the
        user-directory enrichment; call and transcript reads continue.
        """
        extensive = self.list_calls_extensive(
            call_ids=(call_id,), from_dt=from_dt, to_dt=to_dt, expose_parties=True,
        )
        party_by_speaker: dict[str, GongPartyV1] = {}
        for call in extensive:
            if call.call_id == call_id:
                party_by_speaker = {party.speaker_id: party for party in call.parties}
                break
        transcripts = self.get_call_transcripts(call_ids=(call_id,), from_dt=from_dt, to_dt=to_dt)
        target = None
        for entry in transcripts:
            if isinstance(entry, dict) and entry.get("callId") == call_id:
                target = entry
                break
        if target is None:
            raise GongContractError("Gong transcript response did not include the requested call")
        raw_transcript = target.get("transcript")
        if not isinstance(raw_transcript, list) or not raw_transcript:
            raise GongContractError("Gong transcript is empty")
        segments: list[ConversationSegmentV1] = []
        seq = 0
        for monologue in raw_transcript:
            if not isinstance(monologue, dict):
                raise GongContractError("Gong transcript monologue must be an object")
            speaker_id = monologue.get("speakerId")
            party = party_by_speaker.get(speaker_id) if isinstance(speaker_id, str) else None
            role = party.role if party is not None else "UNKNOWN"
            label = party.minimized_name if party is not None else None
            sentences = monologue.get("sentences")
            if not isinstance(sentences, list):
                raise GongContractError("Gong monologue sentences must be a list")
            for sentence in sentences:
                if not isinstance(sentence, dict):
                    raise GongContractError("Gong sentence must be an object")
                text = sentence.get("text")
                start = sentence.get("start")
                end = sentence.get("end", start)
                if not isinstance(text, str) or not text:
                    raise GongContractError("Gong sentence is missing text")
                if not isinstance(start, int) or isinstance(start, bool) or start < 0:
                    raise GongContractError("Gong sentence start offset is invalid")
                if not isinstance(end, int) or isinstance(end, bool) or end < start:
                    raise GongContractError("Gong sentence end offset is invalid")
                segment_native = f"{call_id}-seg-{seq}"
                segments.append(ConversationSegmentV1(
                    schema_version="orchestrator.conversation-segment.v1",
                    conversation_id=call_id,
                    deal_source_id=exact_deal_source_id,
                    segment_id=segment_native,
                    speaker_ref=role,
                    speaker_source_label=label,
                    occurred_at=started_at,
                    relative_begin_ms=start,
                    relative_end_ms=end,
                    text=text,
                    source_record_id=stable_source_record_id(
                        adapter_id=self.adapter_id,
                        source_instance_id=source_instance_id,
                        object_kind="TRANSCRIPT",
                        native_id=segment_native,
                    ),
                    text_sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(),
                    lineage_receipt_id=f"lin-gong-{call_id}-{seq}",
                ))
                seq += 1
        if not segments:
            raise GongContractError("Gong transcript produced no segments")
        return TranscriptRoute(
            route_id=route_id,
            route_kind="DIRECT_CONNECTOR",
            source_manifest_id=source_instance_id,
            origin_family="GONG",
            native_call_or_meeting_id=call_id,
            deal_source_id=exact_deal_source_id,
            started_at=started_at,
            ended_at=ended_at,
            segments=tuple(segments),
        )


@dataclass(frozen=True)
class GongParsedCallV1:
    call_id: str
    parties: tuple[GongPartyV1, ...]
