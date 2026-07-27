"""Fathom GET-only conversation read adapter (Phase 5).

Fathom is READ-ONLY: only two allowlisted GET endpoints exist and the async callback
mode and every webhook endpoint are forbidden. Transcript text follows the in-memory
transcript stage in ``transcripts.py``; the adapter never persists full text and never
persists participant emails or names. The free-plan entitlement stays UNKNOWN/CONDITIONAL
and this adapter never claims a no-cost live path.
"""

from __future__ import annotations

import hashlib
import re
import time
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable
from urllib.parse import urlencode

from orchestrator.contracts.adapter import AdapterCapabilityV1, EndpointCapabilityV1
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
from orchestrator.ingestion.transcripts import TranscriptRoute
from orchestrator.ingestion.transport import (
    AllowedEndpoint,
    EphemeralCredential,
    LockedHttpClient,
)

_FATHOM_HOST = "api.fathom.ai"
_FATHOM_BASE = "https://api.fathom.ai"
_MAX_RESPONSE_BYTES = 20 * 1024 * 1024
_RECORDING_ID = re.compile(r"^[A-Za-z0-9_-]{1,128}$")
# Callback, webhook, and destination surfaces are forbidden for the read-only adapter.
_FORBIDDEN_QUERY_KEYS = frozenset(
    {"destination_url", "callback", "callback_url", "webhook", "webhook_url"}
)


class FathomContractError(ValueError):
    pass


class FathomResponseError(RuntimeError):
    pass


class FathomRateLimitError(RuntimeError):
    def __init__(self, scope: str, retry_after_seconds: int | None = None) -> None:
        super().__init__("Fathom source rate limited")
        self.scope = scope
        self.retry_after_seconds = retry_after_seconds


class FathomRateLimiter:
    """Proactive sliding-window limiter.

    Standard requests: 60 / 60s. Heavy requests (recording transcript and any meeting
    request that includes transcript/summary): 30 / 60s, and may be tightened to 5 / 60s
    during elevated activity. ``Retry-After`` is honored by the transport retry path as
    an additional reaction, not the primary control.
    """

    def __init__(
        self,
        *,
        clock: Callable[[], float] = time.monotonic,
        standard_limit: int = 60,
        heavy_limit: int = 30,
    ) -> None:
        if standard_limit != 60 or heavy_limit not in (30, 5):
            raise ValueError("Fathom limits are 60/60s standard and 30 or 5 per 60s heavy")
        self._clock = clock
        self._standard_limit = standard_limit
        self._heavy_limit = heavy_limit
        self._standard: deque[float] = deque()
        self._heavy: deque[float] = deque()

    def tighten_heavy_to_five(self) -> None:
        self._heavy_limit = 5

    def _prune(self, window: deque[float], now: float) -> None:
        while window and now - window[0] >= 60:
            window.popleft()

    def acquire(self, *, heavy: bool) -> None:
        now = self._clock()
        self._prune(self._standard, now)
        if len(self._standard) >= self._standard_limit:
            raise FathomRateLimitError("STANDARD_60_PER_60S", 60)
        if heavy:
            self._prune(self._heavy, now)
            if len(self._heavy) >= self._heavy_limit:
                raise FathomRateLimitError("HEAVY_30_PER_60S", 60)
            self._heavy.append(now)
        self._standard.append(now)

    @property
    def heavy_remaining(self) -> int:
        now = self._clock()
        self._prune(self._heavy, now)
        return self._heavy_limit - len(self._heavy)


@dataclass(frozen=True)
class FathomMeetingsRequestV1:
    created_after: datetime | None = None
    created_before: datetime | None = None
    cursor: str | None = None


def _reject_forbidden_query(params: dict[str, str]) -> dict[str, str]:
    forbidden = sorted(key for key in params if key.lower() in _FORBIDDEN_QUERY_KEYS)
    if forbidden:
        raise FathomContractError(
            f"callback, webhook, or destination query keys are forbidden: {', '.join(forbidden)}"
        )
    return params


def _utc_parameter(value: datetime) -> str:
    if value.tzinfo is None:
        raise FathomContractError("Fathom date filters require an aware timestamp")
    return value.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _decode_response(response: object) -> tuple[dict[str, object], str]:
    status = int(getattr(response, "status_code"))
    headers = getattr(response, "headers")
    if status == 429:
        retry_raw = headers.get("retry-after")
        try:
            retry = int(retry_raw) if retry_raw is not None else None
        except ValueError:
            retry = None
        raise FathomRateLimitError("HTTP_429", retry)
    if status != 200:
        raise FathomResponseError(f"Fathom read returned HTTP {status}")
    if "application/json" not in headers.get("content-type", "application/json").lower():
        raise FathomContractError("Fathom response content type is not JSON")
    content = bytes(getattr(response, "content"))
    if len(content) > _MAX_RESPONSE_BYTES:
        raise FathomContractError("Fathom response exceeds the byte cap")
    payload = strict_json_loads(content)
    if not isinstance(payload, dict):
        raise FathomContractError("Fathom response must be an object")
    return payload, hashlib.sha256(content).hexdigest()


@dataclass(frozen=True)
class FathomMeetingSummaryV1:
    """Minimized meeting listing. Source summary/action items are deliberately dropped:
    they are not transcript evidence and cannot satisfy readiness dimensions."""

    meeting_id: str
    recording_id: str
    title: str | None
    started_at: datetime
    ended_at: datetime


@dataclass(frozen=True)
class FathomMeetingsPage:
    meetings: tuple[FathomMeetingSummaryV1, ...]
    next_cursor: str | None
    cursor_sha256: str | None
    response_sha256: str


class FathomAdapter:
    adapter_id = "fathom-api-v1"

    def __init__(
        self,
        *,
        api_key: str,
        client: LockedHttpClient | None = None,
        limiter: FathomRateLimiter | None = None,
    ) -> None:
        # v1 uses a session-only user API key (X-Api-Key). OAuth is documented but not
        # implemented in v1: there is no authorization-code, redirect, or refresh path.
        self._credential = EphemeralCredential(header_name="X-Api-Key", header_value=api_key)
        self._endpoints = self._allowed_endpoints()
        self._client = client or LockedHttpClient(self._endpoints)
        self._limiter = limiter or FathomRateLimiter()
        self._seen_cursors: set[str] = set()

    @staticmethod
    def _allowed_endpoints() -> tuple[AllowedEndpoint, ...]:
        return (
            AllowedEndpoint("fathom.meetings", "GET", _FATHOM_HOST, "/external/v1/meetings", True),
            AllowedEndpoint(
                "fathom.recording-transcript",
                "GET",
                _FATHOM_HOST,
                "/external/v1/recordings/{recording_id}/transcript",
                True,
            ),
        )

    def close(self) -> None:
        self._client.close()

    def capability(self) -> AdapterCapabilityV1:
        return AdapterCapabilityV1(
            schema_version="orchestrator.adapter-capability.v1",
            adapter_id=self.adapter_id,
            package_version="0.0.1",
            source_api_family="Fathom API",
            source_api_version="external/v1",
            source_kinds=("CONVERSATION",),
            object_kinds=("MEETING", "RECORDING_TRANSCRIPT"),
            permitted_authentication_modes=("SESSION_API_KEY",),
            operations=tuple(
                EndpointCapabilityV1(
                    operation_id=item.operation_id,
                    method="GET",
                    host=item.host,
                    path_template=item.path_template,
                    idempotent_retryable=True,
                )
                for item in self._endpoints
            ),
            supported_cursor_semantics=("OPAQUE_SOURCE_SCOPED",),
            schema_discovery_supported=False,
            transcript_available=True,
            external_writes_supported=False,
            write_operation_ids=(),
        )

    @staticmethod
    def proof() -> SourceProofInputV1:
        # Contract-tested only; live validation and free-plan entitlement remain unproven.
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
            auth_mode="SESSION_API_KEY",
            permitted_operation_ids=tuple(item.operation_id for item in self._endpoints),
        )

    def _get(self, operation_id: str, url: str, *, heavy: bool) -> object:
        self._limiter.acquire(heavy=heavy)
        return self._client.request_with_retry(
            operation_id=operation_id,
            method="GET",
            url=url,
            credential=self._credential,
            headers={"Accept": "application/json"},
        )

    def meetings_page(self, request: FathomMeetingsRequestV1) -> FathomMeetingsPage:
        params: dict[str, str] = {}
        if request.created_after is not None:
            params["created_after"] = _utc_parameter(request.created_after)
        if request.created_before is not None:
            params["created_before"] = _utc_parameter(request.created_before)
        if request.cursor is not None:
            params["cursor"] = request.cursor
        # include_transcript is deliberately never sent: OAuth apps and this adapter fetch
        # transcripts only from the recording transcript endpoint.
        _reject_forbidden_query(params)
        url = f"{_FATHOM_BASE}/external/v1/meetings"
        if params:
            url = f"{url}?{urlencode(params)}"
        response = self._get("fathom.meetings", url, heavy=False)
        payload, response_hash = _decode_response(response)
        items = payload.get("items")
        if not isinstance(items, list):
            raise FathomContractError("Fathom meetings response is missing items")
        meetings: list[FathomMeetingSummaryV1] = []
        for item in items:
            meetings.append(self._parse_meeting(item))
        next_cursor = payload.get("next_cursor")
        if next_cursor is not None and not isinstance(next_cursor, str):
            raise FathomContractError("Fathom next_cursor must be a string")
        if not items and next_cursor is not None:
            raise FathomContractError("empty page with a next_cursor is forbidden")
        if next_cursor is not None:
            digest = hashlib.sha256(next_cursor.encode()).hexdigest()
            if digest in self._seen_cursors or next_cursor == request.cursor:
                raise FathomContractError("repeated or cyclic Fathom cursor")
            self._seen_cursors.add(digest)
        return FathomMeetingsPage(
            meetings=tuple(meetings),
            next_cursor=next_cursor,
            cursor_sha256=hashlib.sha256(next_cursor.encode()).hexdigest() if next_cursor else None,
            response_sha256=response_hash,
        )

    @staticmethod
    def _aware(value: object, *, field: str) -> datetime:
        if not isinstance(value, str):
            raise FathomContractError(f"Fathom meeting is missing {field}")
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise FathomContractError(f"invalid Fathom {field}") from exc
        if parsed.tzinfo is None:
            raise FathomContractError(f"Fathom {field} must be offset-aware")
        return parsed

    def _parse_meeting(self, item: object) -> FathomMeetingSummaryV1:
        if not isinstance(item, dict):
            raise FathomContractError("Fathom meeting must be an object")
        meeting_id = item.get("id")
        recording = item.get("recording")
        if not isinstance(meeting_id, str) or not meeting_id:
            raise FathomContractError("Fathom meeting is missing a string id")
        if not isinstance(recording, dict) or not isinstance(recording.get("id"), str):
            raise FathomContractError("Fathom meeting is missing a recording id")
        started = self._aware(item.get("started_at"), field="started_at")
        ended = self._aware(item.get("ended_at"), field="ended_at")
        if started > ended:
            raise FathomContractError("Fathom meeting interval is inverted")
        title = item.get("title") if isinstance(item.get("title"), str) else None
        # summary / action_items are intentionally ignored: not transcript evidence.
        return FathomMeetingSummaryV1(
            meeting_id=meeting_id,
            recording_id=recording["id"],
            title=title,
            started_at=started,
            ended_at=ended,
        )

    def read_transcript_route(
        self,
        *,
        source_instance_id: str,
        recording_id: str,
        native_meeting_id: str,
        exact_deal_source_id: str,
        started_at: datetime,
        ended_at: datetime,
        route_id: str,
        internal_participant_labels: frozenset[str] = frozenset(),
    ) -> TranscriptRoute:
        """Fetch and translate a recording transcript into an ephemeral TranscriptRoute.

        The transcript endpoint is HEAVY. Participant emails are read into memory for
        role inference only and never enter a returned segment or any durable record.
        """
        if not _RECORDING_ID.fullmatch(recording_id):
            raise FathomContractError("invalid Fathom recording id")
        url = f"{_FATHOM_BASE}/external/v1/recordings/{recording_id}/transcript"
        response = self._get("fathom.recording-transcript", url, heavy=True)
        payload, _ = _decode_response(response)
        raw_segments = payload.get("segments")
        if not isinstance(raw_segments, list) or not raw_segments:
            raise FathomContractError("Fathom transcript is missing segments")
        segments: list[ConversationSegmentV1] = []
        for index, raw in enumerate(raw_segments):
            segments.append(self._translate_segment(
                raw,
                index=index,
                source_instance_id=source_instance_id,
                recording_id=recording_id,
                exact_deal_source_id=exact_deal_source_id,
                occurred_at=started_at,
                internal_participant_labels=internal_participant_labels,
            ))
        return TranscriptRoute(
            route_id=route_id,
            route_kind="DIRECT_CONNECTOR",
            source_manifest_id=source_instance_id,
            origin_family="FATHOM",
            native_call_or_meeting_id=native_meeting_id,
            deal_source_id=exact_deal_source_id,
            started_at=started_at,
            ended_at=ended_at,
            segments=tuple(segments),
        )

    def _translate_segment(
        self,
        raw: object,
        *,
        index: int,
        source_instance_id: str,
        recording_id: str,
        exact_deal_source_id: str,
        occurred_at: datetime,
        internal_participant_labels: frozenset[str],
    ) -> ConversationSegmentV1:
        if not isinstance(raw, dict):
            raise FathomContractError("Fathom transcript segment must be an object")
        text = raw.get("text")
        offset = raw.get("relative_timestamp_ms")
        speaker = raw.get("speaker")
        if not isinstance(text, str) or not text:
            raise FathomContractError("Fathom transcript segment is missing text")
        if not isinstance(offset, int) or isinstance(offset, bool) or offset < 0:
            raise FathomContractError("Fathom transcript relative timestamp is invalid")
        display_name = None
        if isinstance(speaker, dict):
            candidate = speaker.get("display_name")
            display_name = candidate if isinstance(candidate, str) else None
            # speaker.email is read but deliberately never carried into the segment.
        # Role is UNKNOWN unless the source explicitly marks an internal participant.
        if display_name is not None and display_name in internal_participant_labels:
            speaker_ref = "INTERNAL"
        else:
            speaker_ref = "UNKNOWN"
        minimized_label = display_name[:200] if display_name is not None else None
        segment_native = f"{recording_id}-seg-{index}"
        return ConversationSegmentV1(
            schema_version="orchestrator.conversation-segment.v1",
            conversation_id=recording_id,
            deal_source_id=exact_deal_source_id,
            segment_id=segment_native,
            speaker_ref=speaker_ref,
            speaker_source_label=minimized_label,
            occurred_at=occurred_at,
            relative_begin_ms=offset,
            relative_end_ms=offset,
            text=text,
            source_record_id=stable_source_record_id(
                adapter_id=self.adapter_id,
                source_instance_id=source_instance_id,
                object_kind="RECORDING_TRANSCRIPT",
                native_id=segment_native,
            ),
            text_sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(),
            lineage_receipt_id=f"lin-fathom-{recording_id}-{index}",
        )
