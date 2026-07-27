from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from typing import Any, Protocol

import httpx

from orchestrator.contracts.analyst import AnalysisModeV2
from orchestrator.contracts.base import strict_json_loads
from orchestrator.contracts.records import ConversationSegmentV1
from orchestrator.ingestion.transport import (
    RedirectDenied,
    TransportDenied,
    build_httpx_client,
    validate_caller_headers,
    validate_loopback_url,
)

# Hard maximums mirrored from section 12.3.
MAX_SEGMENT_READS = 24
MAX_MODEL_INPUT_BYTES = 256 * 1024


class AnalystProviderError(RuntimeError):
    """Redacted provider failure. It never embeds transcript text, a URL, or a token."""


class AnalystProvider(Protocol):
    """A mode-specific source of raw observation candidates.

    Every provider returns untrusted raw dicts that MUST pass the mode-agnostic
    validator before any use. A provider never validates, scores, or applies evidence.
    """

    mode: AnalysisModeV2

    def propose(
        self, *, deal_source_id: str, dimension_ids: tuple[str, ...]
    ) -> tuple[dict[str, Any], ...]: ...

    def repair(
        self, *, deal_source_id: str, dimension_id: str | None, reason_code: str
    ) -> dict[str, Any] | None: ...


class ManualCitationProvider:
    """MANUAL_CITATION: the manager enters/selects exact citations. No model runs.

    This is the always-available, no-AI fallback lane. Kevin picks exact quotes; the
    same validator and deterministic readiness rules apply to his entries.
    """

    mode: AnalysisModeV2 = "MANUAL_CITATION"

    def __init__(
        self,
        *,
        entries: Sequence[Mapping[str, Any]],
        repairs: Mapping[str, Mapping[str, Any]] | None = None,
    ) -> None:
        self._entries = tuple(dict(entry) for entry in entries)
        self._repairs = {key: dict(value) for key, value in (repairs or {}).items()}

    def propose(
        self, *, deal_source_id: str, dimension_ids: tuple[str, ...]
    ) -> tuple[dict[str, Any], ...]:
        return tuple(dict(entry) for entry in self._entries)

    def repair(
        self, *, deal_source_id: str, dimension_id: str | None, reason_code: str
    ) -> dict[str, Any] | None:
        if dimension_id is None:
            return None
        entry = self._repairs.get(dimension_id)
        return dict(entry) if entry is not None else None


class RecordedAnalystReplayProvider:
    """RECORDED_ANALYST_REPLAY: hash-bound recorded analyst output. No model runs.

    The recorded fixture is bound to the exact transcript input hash; a mismatch fails
    closed rather than replaying stale output against different evidence.
    """

    mode: AnalysisModeV2 = "RECORDED_ANALYST_REPLAY"

    def __init__(
        self,
        *,
        bound_input_sha256: str,
        recorded_observations: Sequence[Mapping[str, Any]],
        recorded_repairs: Mapping[str, Mapping[str, Any]] | None = None,
    ) -> None:
        self._bound_input_sha256 = bound_input_sha256
        self._recorded = tuple(dict(item) for item in recorded_observations)
        self._repairs = {key: dict(value) for key, value in (recorded_repairs or {}).items()}

    def verify_bound_input(self, input_sha256: str) -> None:
        if input_sha256 != self._bound_input_sha256:
            raise AnalystProviderError("recorded replay is not bound to this transcript input")

    def propose(
        self, *, deal_source_id: str, dimension_ids: tuple[str, ...]
    ) -> tuple[dict[str, Any], ...]:
        return tuple(dict(item) for item in self._recorded)

    def repair(
        self, *, deal_source_id: str, dimension_id: str | None, reason_code: str
    ) -> dict[str, Any] | None:
        if dimension_id is None:
            return None
        entry = self._repairs.get(dimension_id)
        return dict(entry) if entry is not None else None


class LiveLocalProvider:
    """LIVE_LOCAL: a loopback-only local model endpoint.

    Enforced boundaries (section 10.5): loopback host only (127.0.0.1/localhost/[::1]);
    redirects rejected; non-loopback rejected; no credentials; environment proxies,
    `.netrc`, OS credential helpers, and ambient cookies ignored. There is NO remote
    LLM route in v1: this provider is the only network analyst path and it refuses any
    non-loopback URL at construction.
    """

    mode: AnalysisModeV2 = "LIVE_LOCAL"

    def __init__(
        self,
        *,
        endpoint_url: str,
        segments: tuple[ConversationSegmentV1, ...],
        client: httpx.Client | None = None,
        request_headers: Mapping[str, str] | None = None,
    ) -> None:
        # Fails closed on any non-loopback host, IPv4-mapped loopback, or userinfo.
        validate_loopback_url(endpoint_url)
        # No caller-supplied Authorization/Cookie/Proxy/Host header is permitted.
        self._headers = {**validate_caller_headers(request_headers), "content-type": "application/json"}
        self._endpoint_url = endpoint_url
        self._segments = segments
        # trust_env=False, follow_redirects=False, verify=True come from this factory.
        self._client = client or build_httpx_client()

    def close(self) -> None:
        self._client.close()

    def _segment_payload(self, deal_source_id: str) -> list[dict[str, Any]]:
        payload = [
            {
                "conversation_id": segment.conversation_id,
                "segment_id": segment.segment_id,
                "text": segment.text,
                "relative_begin_ms": segment.relative_begin_ms,
                "relative_end_ms": segment.relative_end_ms,
            }
            for segment in self._segments
            if segment.deal_source_id == deal_source_id
        ][:MAX_SEGMENT_READS]
        return payload

    def _post(self, body: dict[str, Any]) -> dict[str, Any]:
        content = json.dumps(body, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        if len(content) > MAX_MODEL_INPUT_BYTES:
            raise AnalystProviderError("local model input exceeds the bounded size")
        self._client.cookies.clear()
        try:
            response = self._client.request(
                "POST",
                self._endpoint_url,
                headers=self._headers,
                content=content,
                follow_redirects=False,
            )
        except (httpx.TimeoutException, httpx.NetworkError, httpx.ProtocolError):
            raise AnalystProviderError("local model request failed") from None
        finally:
            self._client.cookies.clear()
        if 300 <= response.status_code < 400:
            raise RedirectDenied("local model redirect denied")
        if response.status_code != 200:
            raise AnalystProviderError("local model returned a non-success status")
        try:
            decoded = strict_json_loads(response.content)
        except ValueError:
            raise AnalystProviderError("local model returned malformed JSON") from None
        if not isinstance(decoded, dict):
            raise AnalystProviderError("local model response is not an object")
        return decoded

    def propose(
        self, *, deal_source_id: str, dimension_ids: tuple[str, ...]
    ) -> tuple[dict[str, Any], ...]:
        decoded = self._post({
            "task": "extract_observations",
            "deal_source_id": deal_source_id,
            "dimension_ids": list(dimension_ids),
            "segments": self._segment_payload(deal_source_id),
        })
        observations = decoded.get("observations", [])
        if not isinstance(observations, list):
            raise AnalystProviderError("local model observations field is not a list")
        return tuple(item for item in observations if isinstance(item, dict))

    def repair(
        self, *, deal_source_id: str, dimension_id: str | None, reason_code: str
    ) -> dict[str, Any] | None:
        decoded = self._post({
            "task": "repair_observation",
            "deal_source_id": deal_source_id,
            "dimension_id": dimension_id,
            "reason_code": reason_code,
            "segments": self._segment_payload(deal_source_id),
        })
        observation = decoded.get("observation")
        if observation is None:
            return None
        if not isinstance(observation, dict):
            raise AnalystProviderError("local model repair is not an object")
        return observation


__all__ = [
    "AnalystProvider",
    "AnalystProviderError",
    "LiveLocalProvider",
    "ManualCitationProvider",
    "RecordedAnalystReplayProvider",
    "TransportDenied",
]
