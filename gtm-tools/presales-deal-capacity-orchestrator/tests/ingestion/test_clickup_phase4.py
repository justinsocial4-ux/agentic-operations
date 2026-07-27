from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import parse_qs

import httpx
import pytest

from orchestrator.ingestion.clickup import (
    ClickUpAdapter,
    ClickUpContractError,
    ClickUpMinuteLimiter,
    ClickUpRateLimitError,
    clickup_absence_deletion_state,
)
from orchestrator.ingestion.transport import AllowedEndpoint, LockedHttpClient, build_httpx_client

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "data" / "replay" / "clickup"
HOST = "api.clickup.com"
BEGIN = datetime(2026, 8, 1, tzinfo=timezone.utc)
END = BEGIN + timedelta(days=7)


def fixture(name: str) -> bytes:
    return (FIXTURES / name).read_bytes()


def endpoints() -> tuple[AllowedEndpoint, ...]:
    return (
        AllowedEndpoint("clickup.workspaces", "GET", HOST, "/api/v2/team", True),
        AllowedEndpoint("clickup.list-tasks", "GET", HOST, "/api/v2/list/{list_id}/task", True),
        AllowedEndpoint("clickup.workspace-tasks", "GET", HOST, "/api/v2/team/{team_id}/task", True),
        AllowedEndpoint("clickup.list-fields", "GET", HOST, "/api/v2/list/{list_id}/field", True),
        AllowedEndpoint("clickup.workspace-fields", "GET", HOST, "/api/v2/team/{team_id}/field", True),
        AllowedEndpoint("clickup.time-entries", "GET", HOST, "/api/v2/team/{team_id}/time_entries", True),
    )


def adapter(handler, *, limiter: ClickUpMinuteLimiter | None = None) -> tuple[ClickUpAdapter, list[httpx.Request]]:
    seen: list[httpx.Request] = []

    def recording(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return handler(request)

    raw = build_httpx_client(transport=httpx.MockTransport(recording))
    locked = LockedHttpClient(endpoints(), client=raw, sleeper=lambda _: None)
    return ClickUpAdapter(
        token="fake-clickup-token-phase4",
        client=locked,
        limiter=limiter,
    ), seen


def response(body: bytes, *, status: int = 200, headers: dict[str, str] | None = None) -> httpx.Response:
    base_headers = {
        "content-type": "application/json",
        "x-ratelimit-limit": "100",
        "x-ratelimit-remaining": "99",
        "x-ratelimit-reset": "1785585660",
    }
    base_headers.update(headers or {})
    return httpx.Response(status, content=body, headers=base_headers)


def test_clickup_workspace_preflight_binds_authorized_workspace_and_session_auth() -> None:
    source, seen = adapter(lambda _: response(fixture("authorized-workspaces.json")))
    receipt = source.preflight(expected_team_id="team-synthetic-001")
    assert receipt.source_instance_id.startswith("src-")
    assert receipt.credential_persisted is False
    assert seen[0].url.path == "/api/v2/team"
    assert seen[0].headers["authorization"] == "fake-clickup-token-phase4"
    with pytest.raises(ClickUpContractError, match="binding"):
        source.preflight(expected_team_id="different-team")
    source.close()


def test_clickup_zero_based_pagination_flags_home_list_warning_and_custom_field_ids() -> None:
    source, seen = adapter(lambda _: response(fixture("tasks-page.json")))
    page = source.task_page(
        page=0,
        include_closed=True,
        include_subtasks=False,
        include_timl=False,
        selected_custom_field_ids=("field-skill-id",),
        list_id="list-synthetic-001",
    )
    query = parse_qs(seen[0].url.query.decode())
    assert query == {
        "page": ["0"], "include_closed": ["true"], "subtasks": ["false"], "include_timl": ["false"],
    }
    assert page.complete is True
    assert page.warnings == ("HOME_LIST_TASK_VISIBILITY_INCOMPLETE",)
    assert page.records[0]["custom_fields"] == [
        {"id": "field-skill-id", "type": "short_text", "value": "security"}
    ]
    assert "Display Label Must Not Map" not in json.dumps(page.records)
    assert page.rate_limit is not None and page.rate_limit.limit == 100
    with pytest.raises(ClickUpContractError, match="zero-based"):
        source.task_page(
            page=-1, include_closed=False, include_subtasks=False, include_timl=True,
            selected_custom_field_ids=(), list_id="list-synthetic-001",
        )
    source.close()


def test_clickup_exact_100_rows_produces_next_zero_based_page_cursor_and_hash_only_checkpoint() -> None:
    tasks = [
        {"id": f"task-{index:03d}", "date_updated": "1785585600000", "custom_fields": []}
        for index in range(100)
    ]
    source, _ = adapter(lambda _: response(json.dumps({"tasks": tasks}).encode()))
    page = source.task_page(
        page=0, include_closed=False, include_subtasks=True, include_timl=True,
        selected_custom_field_ids=(), team_id="team-synthetic-001",
    )
    assert len(page.records) == 100 and page.next_cursor == "1" and page.complete is False
    durable = page.durable_checkpoint_projection()
    assert "next_cursor" not in durable and durable["cursor_sha256"] == hashlib.sha256(b"1").hexdigest()
    source.close()


def test_clickup_attachment_url_is_ignored_and_cannot_become_a_request() -> None:
    body = json.dumps({"tasks": [{
        "id": "task-ssrf-synthetic",
        "date_updated": "1785585600000",
        "custom_fields": [],
        "attachments": [{"url": "http://169.254.169.254/latest/meta-data"}],
    }]}).encode()
    source, seen = adapter(lambda _: response(body))
    page = source.task_page(
        page=0, include_closed=False, include_subtasks=False, include_timl=True,
        selected_custom_field_ids=(), list_id="list-synthetic-001",
    )
    assert "attachments" not in page.records[0]
    assert len(seen) == 1 and seen[0].url.host == "api.clickup.com"
    source.close()


def test_clickup_rejects_task_page_over_vendor_100_row_cap() -> None:
    tasks = [{"id": f"task-{index:03d}", "custom_fields": []} for index in range(101)]
    source, _ = adapter(lambda _: response(json.dumps({"tasks": tasks}).encode()))
    with pytest.raises(ClickUpContractError, match="at most 100"):
        source.task_page(
            page=0, include_closed=False, include_subtasks=False, include_timl=True,
            selected_custom_field_ids=(), list_id="list-synthetic-001",
        )
    source.close()


def test_clickup_custom_field_metadata_keeps_id_authoritative_and_unmapped() -> None:
    source, _ = adapter(lambda _: response(fixture("custom-fields.json")))
    schema = source.describe_custom_fields(list_id="list-synthetic-001")
    assert [field.field_id for field in schema.fields] == ["field-capacity-id", "field-skill-id"]
    assert schema.mapping_accepted is False
    assert all(not hasattr(field, "canonical_field") for field in schema.fields)
    source.close()


def test_clickup_time_entry_bounds_and_running_negative_duration_conflict() -> None:
    source, _ = adapter(lambda _: response(fixture("time-entries.json")))
    entries = source.time_entries(
        team_id="team-synthetic-001", begin=BEGIN, end=END, assignee_id="101",
    )
    assert entries[0]["duration"] == "3600000"
    with pytest.raises(ClickUpContractError, match="30 days"):
        source.time_entries(team_id="team-synthetic-001", begin=BEGIN, end=BEGIN + timedelta(days=31))
    source.close()

    running = b'{"data":[{"id":"time-running-synthetic","duration":"-1785585600000"}]}'
    running_source, _ = adapter(lambda _: response(running))
    with pytest.raises(ClickUpContractError, match="RUNNING_TIME_ENTRY_CONFLICT"):
        running_source.time_entries(team_id="team-synthetic-001", begin=BEGIN, end=END)
    running_source.close()


def test_clickup_proactive_100_per_minute_limit_stops_before_transport() -> None:
    clock_value = [0.0]
    limiter = ClickUpMinuteLimiter(clock=lambda: clock_value[0])
    source, seen = adapter(lambda _: response(fixture("authorized-workspaces.json")), limiter=limiter)
    for _ in range(100):
        source.authorized_workspaces()
    with pytest.raises(ClickUpRateLimitError) as caught:
        source.authorized_workspaces()
    assert len(seen) == 100
    assert caught.value.observation.limit == 100 and caught.value.observation.remaining == 0
    clock_value[0] = 60.0
    source.authorized_workspaces()
    assert len(seen) == 101
    source.close()


def test_clickup_429_tracks_limit_remaining_reset_and_bounded_retry_after() -> None:
    source, _ = adapter(lambda _: response(
        b'{"err":"rate limited"}', status=429,
        headers={"x-ratelimit-remaining": "0", "retry-after": "12"},
    ))
    with pytest.raises(ClickUpRateLimitError) as caught:
        source.authorized_workspaces()
    assert caught.value.observation.limit == 100
    assert caught.value.observation.remaining == 0
    assert caught.value.observation.reset == 1785585660
    assert caught.value.retry_after_seconds == 12
    source.close()


def test_clickup_absence_never_infers_deletion_and_flags_are_required_booleans() -> None:
    assert clickup_absence_deletion_state() == "DELETION_UNKNOWN"
    source, seen = adapter(lambda _: response(fixture("tasks-page.json")))
    with pytest.raises(TypeError):
        source.task_page(  # type: ignore[arg-type]
            page=0, include_closed=None, include_subtasks=False, include_timl=False,
            selected_custom_field_ids=(), list_id="list-synthetic-001",
        )
    assert seen == []
    source.close()


def test_clickup_capability_and_proof_are_get_only_contract_tested_not_live() -> None:
    source, _ = adapter(lambda _: response(fixture("authorized-workspaces.json")))
    capability = source.capability()
    assert {operation.method for operation in capability.operations} == {"GET"}
    assert capability.external_writes_supported is False and capability.write_operation_ids == ()
    proof = source.proof()
    source.authorized_workspaces()
    assert proof == source.proof()
    assert proof.implementation_proof == "FULLY_IMPLEMENTED_CONTRACT_TESTED"
    assert proof.live_validation_proof == "NOT_LIVE_VALIDATED"
    source.close()


def test_clickup_official_shape_fixture_manifest_is_hash_bound_fake_and_offline() -> None:
    manifest = json.loads((FIXTURES / "fixture-manifest.json").read_text())
    assert manifest["live_network_required"] is False and manifest["credentials"] == "FAKE_ONLY"
    for row in manifest["files"]:
        assert hashlib.sha256((FIXTURES / row["path"]).read_bytes()).hexdigest() == row["sha256"]
