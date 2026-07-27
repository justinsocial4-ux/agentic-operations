from __future__ import annotations

import hashlib
import re
import time
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Callable
from urllib.parse import urlencode

from orchestrator.canonical import canonical_json_bytes
from orchestrator.contracts.adapter import AdapterCapabilityV1, EndpointCapabilityV1
from orchestrator.contracts.base import strict_json_loads
from orchestrator.contracts.connectors import (
    ConnectorPageV1,
    ConnectorPreflightReceiptV1,
    RateLimitObservationV1,
    SourceFieldMetadataV1,
    SourceSchemaMetadataV1,
)
from orchestrator.contracts.enums import ExecutionModeV1, ImplementationProofV1, LiveValidationProofV1
from orchestrator.contracts.proof import SourceProofInputV1
from orchestrator.ingestion.manifests import opaque_source_instance_id, source_identity_fingerprint
from orchestrator.ingestion.transport import AllowedEndpoint, EphemeralCredential, LockedHttpClient

_CLICKUP_HOST = "api.clickup.com"
_CLICKUP_BASE = "https://api.clickup.com/api/v2"
_MAX_RESPONSE_BYTES = 10 * 1024 * 1024
_TASK_PAGE_SIZE = 100
_PATH_ID = re.compile(r"^[A-Za-z0-9_-]+$")


class ClickUpContractError(ValueError):
    pass


class ClickUpResponseError(RuntimeError):
    pass


class ClickUpRateLimitError(RuntimeError):
    def __init__(self, observation: RateLimitObservationV1, retry_after_seconds: int | None) -> None:
        super().__init__("ClickUp source rate limited")
        self.observation = observation
        self.retry_after_seconds = retry_after_seconds


@dataclass(frozen=True)
class ClickUpTaskReadRequestV1:
    include_closed: bool
    include_subtasks: bool
    include_timl: bool
    selected_custom_field_ids: tuple[str, ...]
    list_id: str | None = None
    team_id: str | None = None
    page_number: int = 0


@dataclass(frozen=True)
class ClickUpSchemaRequestV1:
    list_id: str | None = None
    team_id: str | None = None


class ClickUpMinuteLimiter:
    """Per-adapter session limiter; credentials and token-derived identifiers are never durable."""

    def __init__(self, *, clock: Callable[[], float] = time.monotonic, limit: int = 100) -> None:
        if limit != 100:
            raise ValueError("Phase 4 ClickUp limit is fixed at 100 requests/minute/token")
        self._clock = clock
        self._events: deque[float] = deque()

    def acquire(self) -> None:
        now = self._clock()
        while self._events and now - self._events[0] >= 60:
            self._events.popleft()
        if len(self._events) >= 100:
            raise ClickUpRateLimitError(RateLimitObservationV1(limit=100, remaining=0), 60)
        self._events.append(now)

    @property
    def remaining(self) -> int:
        now = self._clock()
        while self._events and now - self._events[0] >= 60:
            self._events.popleft()
        return 100 - len(self._events)


def parse_clickup_rate_limit(headers: object) -> RateLimitObservationV1 | None:
    def integer(name: str) -> int | None:
        raw = headers.get(name)  # type: ignore[attr-defined]
        if raw is None:
            return None
        try:
            value = int(raw)
        except (TypeError, ValueError):
            return None
        return value if value >= 0 else None

    limit = integer("x-ratelimit-limit")
    remaining = integer("x-ratelimit-remaining")
    reset = integer("x-ratelimit-reset")
    if limit is None and remaining is None and reset is None:
        return None
    return RateLimitObservationV1(limit=limit, remaining=remaining, reset=reset)


def _decode_response(response: object) -> tuple[dict[str, object], str]:
    status = int(getattr(response, "status_code"))
    headers = getattr(response, "headers")
    rate = parse_clickup_rate_limit(headers)
    if status == 429:
        retry_raw = headers.get("retry-after")
        try:
            retry = int(retry_raw) if retry_raw is not None else None
        except ValueError:
            retry = None
        retry = retry if retry is not None and 0 <= retry <= 60 else None
        raise ClickUpRateLimitError(rate or RateLimitObservationV1(), retry)
    if status != 200:
        raise ClickUpResponseError(f"ClickUp read returned HTTP {status}")
    if "application/json" not in headers.get("content-type", "application/json").lower():
        raise ClickUpContractError("ClickUp response content type is not JSON")
    content = bytes(getattr(response, "content"))
    if len(content) > _MAX_RESPONSE_BYTES:
        raise ClickUpContractError("ClickUp response exceeds the byte cap")
    payload = strict_json_loads(content)
    if not isinstance(payload, dict):
        raise ClickUpContractError("ClickUp response must be an object")
    return payload, hashlib.sha256(content).hexdigest()


def _path_id(value: str, *, kind: str) -> str:
    if not _PATH_ID.fullmatch(value):
        raise ClickUpContractError(f"invalid ClickUp {kind} ID")
    return value


def clickup_absence_deletion_state() -> str:
    """Task/list absence is never deletion evidence under ClickUp visibility semantics."""
    return "DELETION_UNKNOWN"


class ClickUpAdapter:
    adapter_id = "clickup-api-v2"

    def __init__(
        self,
        *,
        token: str,
        auth_mode: str = "SESSION_PERSONAL_TOKEN",
        client: LockedHttpClient | None = None,
        limiter: ClickUpMinuteLimiter | None = None,
    ) -> None:
        if auth_mode not in {"SESSION_PERSONAL_TOKEN", "SESSION_OAUTH_TOKEN"}:
            raise ClickUpContractError("unsupported ClickUp session auth mode")
        self.auth_mode = auth_mode
        self._credential = EphemeralCredential.authorization_value(token)
        self._endpoints = self._allowed_endpoints()
        self._client = client or LockedHttpClient(self._endpoints)
        self._limiter = limiter or ClickUpMinuteLimiter()
        self.last_rate_limit: RateLimitObservationV1 | None = None

    @staticmethod
    def _allowed_endpoints() -> tuple[AllowedEndpoint, ...]:
        return (
            AllowedEndpoint("clickup.workspaces", "GET", _CLICKUP_HOST, "/api/v2/team", True),
            AllowedEndpoint("clickup.list-tasks", "GET", _CLICKUP_HOST, "/api/v2/list/{list_id}/task", True),
            AllowedEndpoint("clickup.workspace-tasks", "GET", _CLICKUP_HOST, "/api/v2/team/{team_id}/task", True),
            AllowedEndpoint("clickup.list-fields", "GET", _CLICKUP_HOST, "/api/v2/list/{list_id}/field", True),
            AllowedEndpoint("clickup.workspace-fields", "GET", _CLICKUP_HOST, "/api/v2/team/{team_id}/field", True),
            AllowedEndpoint("clickup.time-entries", "GET", _CLICKUP_HOST, "/api/v2/team/{team_id}/time_entries", True),
        )

    def close(self) -> None:
        self._client.close()

    def capability(self) -> AdapterCapabilityV1:
        return AdapterCapabilityV1(
            schema_version="orchestrator.adapter-capability.v1",
            adapter_id=self.adapter_id,
            package_version="0.0.1",
            source_api_family="ClickUp API",
            source_api_version="v2",
            source_kinds=("ROSTER", "WORKLOAD", "CAPACITY"),
            object_kinds=("WORKSPACE", "TASK", "CUSTOM_FIELD", "TIME_ENTRY"),
            permitted_authentication_modes=("SESSION_PERSONAL_TOKEN", "SESSION_OAUTH_TOKEN"),
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
            supported_cursor_semantics=("ZERO_BASED_PAGE_MEMORY_ONLY", "HIGH_WATER_WITH_OVERLAP"),
            schema_discovery_supported=True,
            transcript_available=False,
            external_writes_supported=False,
            write_operation_ids=(),
        )

    @staticmethod
    def proof() -> SourceProofInputV1:
        return SourceProofInputV1(
            execution_mode=ExecutionModeV1.DIRECT_CONNECTOR_ENABLED,
            implementation_proof=ImplementationProofV1.FULLY_IMPLEMENTED_CONTRACT_TESTED,
            live_validation_proof=LiveValidationProofV1.NOT_LIVE_VALIDATED,
        )

    def _get(self, operation_id: str, url: str) -> object:
        self._limiter.acquire()
        response = self._client.request(
            operation_id=operation_id,
            method="GET",
            url=url,
            credential=self._credential,
            headers={"Accept": "application/json"},
        )
        self.last_rate_limit = parse_clickup_rate_limit(response.headers)
        return response

    def authorized_workspaces(self) -> tuple[dict[str, object], ...]:
        response = self._get("clickup.workspaces", f"{_CLICKUP_BASE}/team")
        payload, _ = _decode_response(response)
        teams = payload.get("teams")
        if not isinstance(teams, list):
            raise ClickUpContractError("authorized workspace response is missing teams")
        result: list[dict[str, object]] = []
        for team in teams:
            if not isinstance(team, dict) or not isinstance(team.get("id"), str):
                raise ClickUpContractError("authorized workspace is missing a string id")
            result.append({key: value for key, value in team.items() if key in {"id", "members"}})
        return tuple(result)

    def preflight(self, *, expected_team_id: str) -> ConnectorPreflightReceiptV1:
        _path_id(expected_team_id, kind="workspace")
        workspaces = self.authorized_workspaces()
        if expected_team_id not in {item["id"] for item in workspaces}:
            raise ClickUpContractError("authorized workspace binding mismatch")
        fingerprint = source_identity_fingerprint(
            adapter_id=self.adapter_id, non_secret_source_identity=expected_team_id,
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

    def describe_custom_fields(
        self,
        *,
        list_id: str | None = None,
        team_id: str | None = None,
    ) -> SourceSchemaMetadataV1:
        if (list_id is None) == (team_id is None):
            raise ClickUpContractError("choose exactly one custom-field metadata scope")
        if list_id is not None:
            _path_id(list_id, kind="list")
            operation = "clickup.list-fields"
            object_kind = f"LIST:{list_id}"
            url = f"{_CLICKUP_BASE}/list/{list_id}/field"
        else:
            assert team_id is not None
            _path_id(team_id, kind="workspace")
            operation = "clickup.workspace-fields"
            object_kind = f"TEAM:{team_id}"
            url = f"{_CLICKUP_BASE}/team/{team_id}/field"
        response = self._get(operation, url)
        payload, _ = _decode_response(response)
        raw_fields = payload.get("fields")
        if not isinstance(raw_fields, list):
            raise ClickUpContractError("custom-field response is missing fields")
        fields: list[SourceFieldMetadataV1] = []
        for raw in raw_fields:
            if not isinstance(raw, dict) or not isinstance(raw.get("id"), str) or not isinstance(raw.get("type"), str):
                raise ClickUpContractError("custom field has an invalid shape")
            fields.append(SourceFieldMetadataV1(
                field_id=raw["id"],
                label=raw.get("name") if isinstance(raw.get("name"), str) else None,
                source_type=raw["type"],
                custom=True,
            ))
        fields_tuple = tuple(sorted(fields, key=lambda item: item.field_id))
        return SourceSchemaMetadataV1(
            schema_version="orchestrator.source-schema-metadata.v1",
            adapter_id=self.adapter_id,
            object_kind=object_kind,
            fields=fields_tuple,
            schema_sha256=hashlib.sha256(canonical_json_bytes(fields_tuple)).hexdigest(),
        )

    def describe(self, request: ClickUpSchemaRequestV1) -> SourceSchemaMetadataV1:
        return self.describe_custom_fields(list_id=request.list_id, team_id=request.team_id)

    def task_page(
        self,
        *,
        page: int,
        include_closed: bool,
        include_subtasks: bool,
        include_timl: bool,
        selected_custom_field_ids: tuple[str, ...],
        list_id: str | None = None,
        team_id: str | None = None,
    ) -> ConnectorPageV1:
        if page < 0:
            raise ClickUpContractError("ClickUp page is zero-based and non-negative")
        if not all(type(flag) is bool for flag in (include_closed, include_subtasks, include_timl)):
            raise TypeError("ClickUp visibility flags must be explicit booleans")
        if (list_id is None) == (team_id is None):
            raise ClickUpContractError("choose exactly one task scope")
        if len(selected_custom_field_ids) != len(set(selected_custom_field_ids)):
            raise ClickUpContractError("custom field IDs must be unique")
        params = {
            "page": str(page),
            "include_closed": str(include_closed).lower(),
            "subtasks": str(include_subtasks).lower(),
            "include_timl": str(include_timl).lower(),
        }
        if list_id is not None:
            _path_id(list_id, kind="list")
            operation = "clickup.list-tasks"
            url = f"{_CLICKUP_BASE}/list/{list_id}/task?{urlencode(params)}"
        else:
            assert team_id is not None
            _path_id(team_id, kind="workspace")
            operation = "clickup.workspace-tasks"
            url = f"{_CLICKUP_BASE}/team/{team_id}/task?{urlencode(params)}"
        response = self._get(operation, url)
        payload, response_hash = _decode_response(response)
        tasks = payload.get("tasks")
        if not isinstance(tasks, list) or len(tasks) > _TASK_PAGE_SIZE:
            raise ClickUpContractError("task page must contain at most 100 rows")
        selected = set(selected_custom_field_ids)
        projected: list[dict[str, object]] = []
        high_water: datetime | None = None
        for task in tasks:
            if not isinstance(task, dict) or not isinstance(task.get("id"), str):
                raise ClickUpContractError("task is missing a string id")
            raw_custom = task.get("custom_fields", [])
            if not isinstance(raw_custom, list):
                raise ClickUpContractError("task custom_fields must be a list")
            custom_fields: list[dict[str, object]] = []
            for field in raw_custom:
                if not isinstance(field, dict) or not isinstance(field.get("id"), str):
                    raise ClickUpContractError("task custom field is missing an id")
                if field["id"] in selected:
                    custom_fields.append({key: value for key, value in field.items() if key in {"id", "value", "type"}})
            row = {key: value for key, value in task.items() if key in {
                "id", "status", "date_updated", "assignees", "list", "parent",
            }}
            row["custom_fields"] = custom_fields
            modified = task.get("date_updated")
            if modified is not None:
                try:
                    modified_at = datetime.fromtimestamp(int(modified) / 1000, tz=timezone.utc)
                except (TypeError, ValueError, OverflowError) as exc:
                    raise ClickUpContractError("task date_updated is invalid") from exc
                high_water = modified_at if high_water is None else max(high_water, modified_at)
            projected.append(row)
        complete = len(tasks) < _TASK_PAGE_SIZE
        next_cursor = None if complete else str(page + 1)
        warnings = () if include_timl else ("HOME_LIST_TASK_VISIBILITY_INCOMPLETE",)
        return ConnectorPageV1(
            schema_version="orchestrator.connector-page.v1",
            adapter_id=self.adapter_id,
            object_kind="TASK",
            records=tuple(projected),
            page_number=page,
            next_cursor=next_cursor,
            cursor_sha256=hashlib.sha256(next_cursor.encode()).hexdigest() if next_cursor else None,
            response_sha256=response_hash,
            high_water_mark=high_water,
            complete=complete,
            completeness="COMPLETE" if complete else "BOUNDED_PARTIAL",
            warnings=warnings,
            rate_limit=self.last_rate_limit,
        )

    def read_page(
        self,
        request: ClickUpTaskReadRequestV1,
        cursor: str | None = None,
    ) -> ConnectorPageV1:
        if cursor is None:
            page_number = request.page_number
        else:
            if not cursor.isdigit():
                raise ClickUpContractError("ClickUp page cursor must be an opaque decimal page token")
            page_number = int(cursor)
        return self.task_page(
            page=page_number,
            include_closed=request.include_closed,
            include_subtasks=request.include_subtasks,
            include_timl=request.include_timl,
            selected_custom_field_ids=request.selected_custom_field_ids,
            list_id=request.list_id,
            team_id=request.team_id,
        )

    def preview(self, request: ClickUpTaskReadRequestV1) -> ConnectorPageV1:
        return self.read_page(request, None)

    def deletion_page(self, request: object, cursor: str | None = None) -> str:
        if cursor is not None:
            raise ClickUpContractError("ClickUp has no deletion-feed cursor")
        return clickup_absence_deletion_state()

    def time_entries(
        self,
        *,
        team_id: str,
        begin: datetime,
        end: datetime,
        assignee_id: str | None = None,
    ) -> tuple[dict[str, object], ...]:
        _path_id(team_id, kind="workspace")
        if assignee_id is not None:
            _path_id(assignee_id, kind="assignee")
        if begin.tzinfo is None or end.tzinfo is None or begin >= end or end - begin > timedelta(days=30):
            raise ClickUpContractError("time-entry range must be aware, increasing, and at most 30 days")
        params = {
            "start_date": str(int(begin.timestamp() * 1000)),
            "end_date": str(int(end.timestamp() * 1000)),
        }
        if assignee_id is not None:
            params["assignee"] = assignee_id
        response = self._get(
            "clickup.time-entries",
            f"{_CLICKUP_BASE}/team/{team_id}/time_entries?{urlencode(params)}",
        )
        payload, _ = _decode_response(response)
        data = payload.get("data")
        if not isinstance(data, list):
            raise ClickUpContractError("time-entry response is missing data")
        result: list[dict[str, object]] = []
        for entry in data:
            if not isinstance(entry, dict) or not isinstance(entry.get("id"), str):
                raise ClickUpContractError("time entry is missing a string id")
            try:
                duration = int(entry.get("duration"))
            except (TypeError, ValueError) as exc:
                raise ClickUpContractError("time entry duration is invalid") from exc
            if duration < 0:
                raise ClickUpContractError("RUNNING_TIME_ENTRY_CONFLICT")
            result.append({key: value for key, value in entry.items() if key in {
                "id", "duration", "start", "end", "assignee", "task",
            }})
        return tuple(result)
