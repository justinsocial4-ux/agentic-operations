from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import parse_qs

import httpx
import pytest

from orchestrator.canonical import canonical_sha256
from orchestrator.ingestion import salesforce as salesforce_module
from orchestrator.ingestion.salesforce import (
    SalesforceAdapter,
    SalesforceContractError,
    build_explicit_soql,
    incremental_windows,
)
from orchestrator.ingestion.transport import AllowedEndpoint, LockedHttpClient, build_httpx_client
from orchestrator.store import Phase1Store, apply_migrations, connect_database

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "data" / "replay" / "salesforce"
HOST = "synthetic.my.salesforce.com"
BASE = f"https://{HOST}"
VERSION = "v67.0"
BEGIN = datetime(2026, 7, 15, tzinfo=timezone.utc)
END = datetime(2026, 8, 2, tzinfo=timezone.utc)
FIELDS = ("Id", "LastModifiedDate", "Name", "Synthetic_Region__c")


def fixture(name: str) -> bytes:
    return (FIXTURES / name).read_bytes()


def endpoints() -> tuple[AllowedEndpoint, ...]:
    prefix = f"/services/data/{VERSION}"
    return (
        AllowedEndpoint("salesforce.query", "GET", HOST, f"{prefix}/query", True),
        AllowedEndpoint("salesforce.query-page", "GET", HOST, f"{prefix}/query/{{locator}}", True),
        AllowedEndpoint("salesforce.describe", "GET", HOST, f"{prefix}/sobjects/{{object}}/describe", True),
        AllowedEndpoint("salesforce.get-updated", "GET", HOST, f"{prefix}/sobjects/{{object}}/updated", True),
        AllowedEndpoint("salesforce.get-deleted", "GET", HOST, f"{prefix}/sobjects/{{object}}/deleted", True),
        AllowedEndpoint("salesforce.limits", "GET", HOST, f"{prefix}/limits", True),
    )


def adapter(handler) -> tuple[SalesforceAdapter, list[httpx.Request]]:
    seen: list[httpx.Request] = []

    def recording(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return handler(request)

    raw = build_httpx_client(transport=httpx.MockTransport(recording))
    locked = LockedHttpClient(endpoints(), client=raw, sleeper=lambda _: None)
    return SalesforceAdapter(
        instance_url=BASE,
        bearer_token="fake-salesforce-token-phase4",
        api_version=VERSION,
        client=locked,
    ), seen


def json_response(body: bytes, *, limit: str = "api-usage=20/15000") -> httpx.Response:
    return httpx.Response(
        200,
        content=body,
        headers={"content-type": "application/json", "sforce-limit-info": limit},
    )


def test_salesforce_explicit_soql_pagination_projection_and_limit_tracking() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/query"):
            query = parse_qs(request.url.query.decode())["q"][0]
            assert query == build_explicit_soql(object_name="Opportunity", selected_fields=FIELDS)
            assert "FIELDS(" not in query.upper()
            return json_response(fixture("query-page-1.json"))
        return json_response(fixture("query-page-2.json"), limit="api-usage=21/15000")

    source, seen = adapter(handler)
    first = source.query_page(object_name="Opportunity", selected_fields=FIELDS, page_number=0)
    assert first.complete is False and first.next_cursor is not None
    assert first.records[0] == {
        "Id": "006SYNTHETIC001",
        "LastModifiedDate": "2026-08-01T12:00:00Z",
        "Name": "Fictional Deal A",
        "Synthetic_Region__c": "EMEA",
    }
    assert "attributes" not in first.records[0]
    second = source.query_page(
        object_name="Opportunity", selected_fields=FIELDS, cursor=first.next_cursor, page_number=1,
    )
    assert second.complete and second.next_cursor is None
    assert second.rate_limit is not None and second.rate_limit.remaining == 14979
    assert all(request.method == "GET" for request in seen)
    assert all(request.headers["authorization"] == "Bearer fake-salesforce-token-phase4" for request in seen)
    with pytest.raises(SalesforceContractError, match="repeated"):
        source.query_page(object_name="Opportunity", selected_fields=FIELDS, cursor=first.next_cursor, page_number=2)
    source.close()


def test_salesforce_soql_identifiers_and_explicit_fields_fail_closed() -> None:
    for object_name, fields in (
        ("Opportunity WHERE Name != null", FIELDS),
        ("Opportunity", ("Id", "FIELDS(ALL)", "LastModifiedDate")),
        ("Opportunity", ("Id", "Name")),
        ("Opportunity", ("Id", "Id", "LastModifiedDate")),
    ):
        with pytest.raises(SalesforceContractError):
            build_explicit_soql(object_name=object_name, selected_fields=fields)


def test_salesforce_next_records_url_cannot_change_host_path_or_cycle_pretransport() -> None:
    source, seen = adapter(lambda _: pytest.fail("transport should not run"))
    for cursor in (
        "https://lookalike.invalid/services/data/v67.0/query/x",
        f"{BASE}/services/data/v67.0/sobjects/Opportunity/describe",
        f"{BASE}/services/data/v68.0/query/x",
    ):
        with pytest.raises((SalesforceContractError, ValueError)):
            source.query_page(object_name="Opportunity", selected_fields=FIELDS, cursor=cursor)
    assert seen == []
    source.close()


def test_salesforce_describe_is_metadata_only_and_never_auto_maps_custom_fields() -> None:
    source, _ = adapter(lambda _: json_response(fixture("describe-opportunity.json")))
    schema = source.describe("Opportunity")
    custom = next(field for field in schema.fields if field.field_id == "Synthetic_Region__c")
    assert custom.custom is True
    assert schema.mapping_accepted is False
    assert not hasattr(custom, "canonical_field")
    source.close()


def test_salesforce_incremental_windows_are_under_30_days_with_overlap() -> None:
    windows = incremental_windows(BEGIN, END, window_days=7, overlap=timedelta(minutes=5))
    assert windows[0][0] == BEGIN and windows[-1][1] == END
    assert all(upper - lower <= timedelta(days=7) for lower, upper in windows)
    assert all(windows[index][0] == windows[index - 1][1] - timedelta(minutes=5) for index in range(1, len(windows)))
    with pytest.raises(SalesforceContractError, match="30 days"):
        incremental_windows(BEGIN, BEGIN + timedelta(days=31))


def test_salesforce_get_updated_bounds_deduplicates_and_tracks_header() -> None:
    payload = b'{"ids":["006SYNTHETIC001","006SYNTHETIC001","006SYNTHETIC002"]}'
    source, seen = adapter(lambda _: json_response(payload, limit="api-usage=22/15000"))
    ids = source.get_changed_ids(object_name="Opportunity", begin=BEGIN, end=END)
    assert ids == ("006SYNTHETIC001", "006SYNTHETIC002")
    query = parse_qs(seen[0].url.query.decode())
    assert set(query) == {"start", "end"}
    assert source.last_rate_limit is not None and source.last_rate_limit.limit == 15000
    with pytest.raises(SalesforceContractError, match="30 days"):
        source.get_changed_ids(object_name="Opportunity", begin=BEGIN, end=BEGIN + timedelta(days=31))
    assert len(seen) == 1
    source.close()


def test_salesforce_query_rejects_more_than_vendor_2000_record_batch() -> None:
    records = [
        {"Id": f"006SYNTHETIC{index:04d}", "LastModifiedDate": "2026-08-01T12:00:00Z"}
        for index in range(2001)
    ]
    source, _ = adapter(lambda _: json_response(json.dumps({"done": True, "records": records}).encode()))
    with pytest.raises(SalesforceContractError, match="2,000"):
        source.query_page(
            object_name="Opportunity", selected_fields=("Id", "LastModifiedDate"), page_number=0,
        )
    source.close()


def test_salesforce_get_updated_600k_guard_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(salesforce_module, "_MAX_VENDOR_IDS", 2)
    source, _ = adapter(lambda _: json_response(b'{"ids":["id-1","id-2","id-3"]}'))
    with pytest.raises(SalesforceContractError, match="exceed limits"):
        source.get_changed_ids(object_name="Opportunity", begin=BEGIN, end=END)
    source.close()


def test_salesforce_get_updated_incremental_uses_smaller_overlapping_windows_and_deduplicates() -> None:
    payload = b'{"ids":["006SYNTHETIC001","006SYNTHETIC002","006SYNTHETIC001"]}'
    source, seen = adapter(lambda _: json_response(payload))
    ids = source.get_changed_ids_incremental(
        object_name="Opportunity", begin=BEGIN, end=END,
        window_days=7, overlap=timedelta(minutes=5),
    )
    assert ids == ("006SYNTHETIC001", "006SYNTHETIC002")
    assert len(seen) == len(incremental_windows(BEGIN, END, window_days=7, overlap=timedelta(minutes=5)))
    windows = [parse_qs(request.url.query.decode()) for request in seen]
    assert all(window["start"][0] < window["end"][0] for window in windows)
    source.close()


def test_salesforce_get_deleted_receipt_and_incomplete_feed_deletion_unknown() -> None:
    source, _ = adapter(lambda _: json_response(fixture("get-deleted.json")))
    confirmed = source.get_deletion_receipt(
        source_instance_id="src-salesforce-synthetic",
        object_name="Opportunity",
        begin=BEGIN,
        end=END,
        feed_expected_complete=True,
    )
    assert confirmed.deletion_state == "DELETIONS_CONFIRMED"
    assert confirmed.deleted_source_record_ids[0].startswith(
        "urn:orchestrator:salesforce-rest-v1:src-salesforce-synthetic:Opportunity:"
    )
    unknown = source.get_deletion_receipt(
        source_instance_id="src-salesforce-synthetic",
        object_name="Opportunity",
        begin=BEGIN,
        end=END,
        feed_expected_complete=True,
        bounded_read_complete=False,
    )
    assert unknown.deletion_state == "DELETION_UNKNOWN"
    assert unknown.feed_complete is False
    source.close()


def test_deletion_store_tombstones_explicit_ids_and_keeps_unknown_append_only_receipt(tmp_path: Path) -> None:
    source, _ = adapter(lambda _: json_response(fixture("get-deleted.json")))
    complete = source.get_deletion_receipt(
        source_instance_id="src-salesforce-synthetic", object_name="Opportunity",
        begin=BEGIN, end=END, feed_expected_complete=True,
    )
    unknown = source.get_deletion_receipt(
        source_instance_id="src-salesforce-synthetic", object_name="Opportunity",
        begin=BEGIN, end=END, feed_expected_complete=False,
    ).model_copy(update={"deletion_receipt_id": "del-incomplete-synthetic"})
    connection = connect_database(tmp_path / "deletions.sqlite")
    apply_migrations(connection)
    connection.execute(
        "INSERT INTO runs(run_id,lane,state,synthetic,created_at) VALUES (?,?,?,?,?)",
        ("run-del", "DEAL_PRIORITIZATION", "INGESTING", 1, BEGIN.isoformat()),
    )
    manifest = {"source_manifest_id": "sm-del", "run_id": "run-del"}
    connection.execute(
        "INSERT INTO source_manifests(source_manifest_id,run_id,source_instance_id,adapter_id,source_mode,manifest_json,manifest_sha256) VALUES (?,?,?,?,?,?,?)",
        ("sm-del", "run-del", "src-salesforce-synthetic", "salesforce-rest-v1", "MOCK_REPLAY",
         json.dumps(manifest, sort_keys=True), canonical_sha256(manifest)),
    )
    connection.commit()
    store = Phase1Store(connection)
    assert store.persist_deletion_receipt(
        run_id="run-del", source_manifest_id="sm-del", receipt=complete,
        run_policy_id="tombstone-explicit-v1", created_at=END,
    ) == complete.deleted_source_record_ids
    assert store.persist_deletion_receipt(
        run_id="run-del", source_manifest_id="sm-del", receipt=unknown,
        run_policy_id="tombstone-explicit-v1", created_at=END + timedelta(seconds=1),
    ) == unknown.deleted_source_record_ids
    assert connection.execute("SELECT COUNT(*) FROM deletion_receipts").fetchone() == (2,)
    assert connection.execute("SELECT COUNT(*) FROM source_tombstones").fetchone() == (1,)
    assert connection.execute("SELECT COUNT(*) FROM exports").fetchone() == (0,)
    source.close()
    connection.close()


def test_salesforce_capability_and_proof_never_claim_live_validation() -> None:
    source, _ = adapter(lambda _: json_response(fixture("limits.json")))
    capability = source.capability()
    assert {operation.method for operation in capability.operations} == {"GET"}
    assert capability.external_writes_supported is False and capability.write_operation_ids == ()
    proof = source.proof()
    assert proof.implementation_proof == "FULLY_IMPLEMENTED_CONTRACT_TESTED"
    assert proof.live_validation_proof == "NOT_LIVE_VALIDATED"
    source.limits()
    assert source.proof() == proof  # runtime success cannot promote proof
    source.close()


def test_salesforce_official_shape_fixture_manifest_is_hash_bound_and_fake_only() -> None:
    manifest = json.loads((FIXTURES / "fixture-manifest.json").read_text())
    assert manifest["live_network_required"] is False and manifest["credentials"] == "FAKE_ONLY"
    for row in manifest["files"]:
        assert hashlib.sha256((FIXTURES / row["path"]).read_bytes()).hexdigest() == row["sha256"]
