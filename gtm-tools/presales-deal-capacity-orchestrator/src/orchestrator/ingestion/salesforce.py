from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode, urlsplit

from orchestrator.canonical import canonical_json_bytes
from orchestrator.contracts.adapter import AdapterCapabilityV1, EndpointCapabilityV1
from orchestrator.contracts.base import strict_json_loads
from orchestrator.contracts.connectors import (
    ConnectorPageV1,
    ConnectorPreflightReceiptV1,
    DeletionReceiptV1,
    RateLimitObservationV1,
    SourceFieldMetadataV1,
    SourceSchemaMetadataV1,
)
from orchestrator.contracts.enums import ExecutionModeV1, ImplementationProofV1, LiveValidationProofV1
from orchestrator.contracts.proof import SourceProofInputV1
from orchestrator.ingestion.manifests import (
    opaque_source_instance_id,
    source_identity_fingerprint,
    stable_source_record_id,
)
from orchestrator.ingestion.transport import (
    AllowedEndpoint,
    EphemeralCredential,
    LockedHttpClient,
    TransportDenied,
    validate_vendor_url,
)

_IDENTIFIER = re.compile(r"^[A-Za-z][A-Za-z0-9_]*(?:\.[A-Za-z][A-Za-z0-9_]*)*$")
_API_VERSION = re.compile(r"^v[0-9]{2}\.[0-9]$")
_SALESFORCE_SUFFIXES = (".my.salesforce.com", ".salesforce.com")
_MAX_RESPONSE_BYTES = 10 * 1024 * 1024
_MAX_VENDOR_IDS = 600_000


class SalesforceContractError(ValueError):
    pass


class SalesforceResponseError(RuntimeError):
    pass


@dataclass(frozen=True)
class SalesforceReadRequestV1:
    object_name: str
    selected_fields: tuple[str, ...]
    page_number: int = 0


@dataclass(frozen=True)
class SalesforceDeletionRequestV1:
    source_instance_id: str
    object_name: str
    begin: datetime
    end: datetime
    feed_expected_complete: bool
    bounded_read_complete: bool = True


def validate_salesforce_instance_url(instance_url: str) -> tuple[str, str]:
    parsed = urlsplit(instance_url)
    if parsed.query or parsed.fragment or parsed.path not in {"", "/"}:
        raise TransportDenied("Salesforce instance URL must contain only the origin")
    host, path = validate_vendor_url(instance_url, approved_hosts=frozenset({parsed.hostname or ""}))
    if not any(host.endswith(suffix) and host != suffix[1:] for suffix in _SALESFORCE_SUFFIXES):
        raise TransportDenied("Salesforce tenant host is outside the approved suffixes")
    return host, f"https://{host}"


def _identifier(value: str, *, kind: str) -> str:
    if not _IDENTIFIER.fullmatch(value) or "FIELDS" in value.upper():
        raise SalesforceContractError(f"invalid Salesforce {kind} identifier")
    return value


def build_explicit_soql(*, object_name: str, selected_fields: tuple[str, ...]) -> str:
    object_name = _identifier(object_name, kind="object")
    if not selected_fields or len(selected_fields) != len(set(selected_fields)):
        raise SalesforceContractError("SOQL requires a non-empty unique explicit field list")
    fields = tuple(_identifier(field, kind="field") for field in selected_fields)
    if "Id" not in fields or "LastModifiedDate" not in fields:
        raise SalesforceContractError("SOQL field list must explicitly include Id and LastModifiedDate")
    return f"SELECT {', '.join(fields)} FROM {object_name} ORDER BY LastModifiedDate, Id"


def incremental_windows(
    begin: datetime,
    end: datetime,
    *,
    window_days: int = 7,
    overlap: timedelta = timedelta(minutes=5),
) -> tuple[tuple[datetime, datetime], ...]:
    if begin.tzinfo is None or end.tzinfo is None or begin >= end:
        raise SalesforceContractError("incremental window requires aware increasing timestamps")
    if end - begin > timedelta(days=30):
        raise SalesforceContractError("Get Updated/Get Deleted range exceeds 30 days")
    if not 1 <= window_days < 30 or overlap < timedelta(0) or overlap >= timedelta(days=window_days):
        raise SalesforceContractError("invalid incremental sub-window policy")
    windows: list[tuple[datetime, datetime]] = []
    cursor = begin
    while cursor < end:
        upper = min(cursor + timedelta(days=window_days), end)
        windows.append((cursor, upper))
        if upper == end:
            break
        cursor = upper - overlap
    return tuple(windows)


def _utc_parameter(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def parse_sforce_limit_info(value: str | None) -> RateLimitObservationV1 | None:
    if value is None:
        return None
    match = re.search(r"(?:^|;)\s*api-usage=(\d+)/(\d+)", value, re.IGNORECASE)
    if match is None:
        return RateLimitObservationV1(raw_sforce_limit_info=value[:500])
    used, limit = (int(match.group(1)), int(match.group(2)))
    return RateLimitObservationV1(
        limit=limit,
        remaining=max(limit - used, 0),
        raw_sforce_limit_info=value[:500],
    )


def _decode_response(response: object) -> tuple[dict[str, object], str]:
    status = int(getattr(response, "status_code"))
    if status != 200:
        raise SalesforceResponseError(f"Salesforce read returned HTTP {status}")
    headers = getattr(response, "headers")
    if "application/json" not in headers.get("content-type", "application/json").lower():
        raise SalesforceContractError("Salesforce response content type is not JSON")
    content = bytes(getattr(response, "content"))
    if len(content) > _MAX_RESPONSE_BYTES:
        raise SalesforceContractError("Salesforce response exceeds the byte cap")
    payload = strict_json_loads(content)
    if not isinstance(payload, dict):
        raise SalesforceContractError("Salesforce response must be an object")
    return payload, hashlib.sha256(content).hexdigest()


class SalesforceAdapter:
    adapter_id = "salesforce-rest-v1"

    def __init__(
        self,
        *,
        instance_url: str,
        bearer_token: str,
        api_version: str,
        client: LockedHttpClient | None = None,
    ) -> None:
        if not _API_VERSION.fullmatch(api_version):
            raise SalesforceContractError("Salesforce API version must have the form vXX.X")
        self.host, self.base_url = validate_salesforce_instance_url(instance_url)
        self.api_version = api_version
        self._credential = EphemeralCredential.bearer(bearer_token)
        self._endpoints = self._allowed_endpoints()
        self._client = client or LockedHttpClient(self._endpoints)
        self._seen_cursors: set[str] = set()
        self.last_rate_limit: RateLimitObservationV1 | None = None

    def _allowed_endpoints(self) -> tuple[AllowedEndpoint, ...]:
        prefix = f"/services/data/{self.api_version}"
        return (
            AllowedEndpoint("salesforce.query", "GET", self.host, f"{prefix}/query", True),
            AllowedEndpoint("salesforce.query-page", "GET", self.host, f"{prefix}/query/{{locator}}", True),
            AllowedEndpoint("salesforce.describe", "GET", self.host, f"{prefix}/sobjects/{{object}}/describe", True),
            AllowedEndpoint("salesforce.get-updated", "GET", self.host, f"{prefix}/sobjects/{{object}}/updated", True),
            AllowedEndpoint("salesforce.get-deleted", "GET", self.host, f"{prefix}/sobjects/{{object}}/deleted", True),
            AllowedEndpoint("salesforce.limits", "GET", self.host, f"{prefix}/limits", True),
        )

    def close(self) -> None:
        self._client.close()

    def capability(self) -> AdapterCapabilityV1:
        return AdapterCapabilityV1(
            schema_version="orchestrator.adapter-capability.v1",
            adapter_id=self.adapter_id,
            package_version="0.0.1",
            source_api_family="Salesforce REST API",
            source_api_version=self.api_version,
            source_kinds=("DEAL", "ROSTER"),
            object_kinds=("Opportunity", "User", "CUSTOM_OBJECT"),
            permitted_authentication_modes=("SESSION_PASTED_BEARER",),
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
            supported_cursor_semantics=("NEXT_RECORDS_URL_MEMORY_ONLY", "HIGH_WATER_WITH_OVERLAP"),
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

    def preflight(self, *, non_secret_org_id: str, source_instance_id: str | None = None) -> ConnectorPreflightReceiptV1:
        fingerprint = source_identity_fingerprint(adapter_id=self.adapter_id, non_secret_source_identity=non_secret_org_id)
        resolved_id = source_instance_id or opaque_source_instance_id(
            adapter_id=self.adapter_id, identity_fingerprint=fingerprint,
        )
        return ConnectorPreflightReceiptV1(
            schema_version="orchestrator.connector-preflight.v1",
            adapter_id=self.adapter_id,
            source_instance_id=resolved_id,
            source_identity_fingerprint=fingerprint,
            auth_mode="SESSION_PASTED_BEARER",
            permitted_operation_ids=tuple(item.operation_id for item in self._endpoints),
        )

    def _get(self, operation_id: str, url: str) -> object:
        response = self._client.request_with_retry(
            operation_id=operation_id,
            method="GET",
            url=url,
            credential=self._credential,
            headers={"Accept": "application/json"},
        )
        self.last_rate_limit = parse_sforce_limit_info(response.headers.get("sforce-limit-info"))
        return response

    def describe(self, object_name: str) -> SourceSchemaMetadataV1:
        object_name = _identifier(object_name, kind="object")
        response = self._get(
            "salesforce.describe",
            f"{self.base_url}/services/data/{self.api_version}/sobjects/{object_name}/describe",
        )
        payload, _ = _decode_response(response)
        raw_fields = payload.get("fields")
        if not isinstance(raw_fields, list):
            raise SalesforceContractError("describe response is missing fields")
        fields: list[SourceFieldMetadataV1] = []
        for raw in raw_fields:
            if not isinstance(raw, dict) or not isinstance(raw.get("name"), str) or not isinstance(raw.get("type"), str):
                raise SalesforceContractError("describe field has an invalid shape")
            name = _identifier(raw["name"], kind="field")
            fields.append(SourceFieldMetadataV1(
                field_id=name,
                label=raw.get("label") if isinstance(raw.get("label"), str) else None,
                source_type=raw["type"],
                custom=bool(raw.get("custom", name.endswith("__c"))),
            ))
        fields_tuple = tuple(sorted(fields, key=lambda item: item.field_id))
        return SourceSchemaMetadataV1(
            schema_version="orchestrator.source-schema-metadata.v1",
            adapter_id=self.adapter_id,
            object_kind=object_name,
            fields=fields_tuple,
            schema_sha256=hashlib.sha256(canonical_json_bytes(fields_tuple)).hexdigest(),
        )

    def query_page(
        self,
        *,
        object_name: str,
        selected_fields: tuple[str, ...],
        cursor: str | None = None,
        page_number: int = 0,
    ) -> ConnectorPageV1:
        soql = build_explicit_soql(object_name=object_name, selected_fields=selected_fields)
        prefix = f"/services/data/{self.api_version}/query"
        if cursor is None:
            url = f"{self.base_url}{prefix}?{urlencode({'q': soql})}"
            operation_id = "salesforce.query"
        else:
            parsed = urlsplit(cursor)
            cursor_url = f"{self.base_url}{cursor}" if not parsed.scheme and cursor.startswith("/") else cursor
            host, path = validate_vendor_url(cursor_url, approved_hosts=frozenset({self.host}))
            if host != self.host or not re.fullmatch(re.escape(prefix) + r"/[A-Za-z0-9_-]+", path):
                raise SalesforceContractError("nextRecordsUrl changed the confirmed query origin/path")
            digest = hashlib.sha256(cursor_url.encode()).hexdigest()
            if digest in self._seen_cursors:
                raise SalesforceContractError("repeated or cyclic nextRecordsUrl")
            self._seen_cursors.add(digest)
            url = cursor_url
            operation_id = "salesforce.query-page"
        response = self._get(operation_id, url)
        payload, response_hash = _decode_response(response)
        records = payload.get("records")
        if not isinstance(records, list) or len(records) > 2_000:
            raise SalesforceContractError("query records must be a list capped at 2,000")
        allowed = set(selected_fields)
        filtered: list[dict[str, object]] = []
        high_water: datetime | None = None
        for record in records:
            if not isinstance(record, dict) or not isinstance(record.get("Id"), str):
                raise SalesforceContractError("query record is missing a string Id")
            projected = {key: value for key, value in record.items() if key in allowed}
            if set(projected) != (set(record) & allowed):
                raise AssertionError("selected-field projection failed")
            modified = projected.get("LastModifiedDate")
            if not isinstance(modified, str):
                raise SalesforceContractError("record is missing LastModifiedDate")
            try:
                modified_at = datetime.fromisoformat(modified.replace("Z", "+00:00"))
            except ValueError as exc:
                raise SalesforceContractError("invalid LastModifiedDate") from exc
            high_water = modified_at if high_water is None else max(high_water, modified_at)
            filtered.append(projected)
        next_cursor = payload.get("nextRecordsUrl")
        if next_cursor is not None and not isinstance(next_cursor, str):
            raise SalesforceContractError("nextRecordsUrl must be a string")
        done = payload.get("done")
        if not isinstance(done, bool) or done == (next_cursor is not None):
            raise SalesforceContractError("query done/cursor state is inconsistent")
        if not records and next_cursor is not None:
            raise SalesforceContractError("empty page with nextRecordsUrl is forbidden")
        cursor_hash = hashlib.sha256(next_cursor.encode()).hexdigest() if next_cursor else None
        return ConnectorPageV1(
            schema_version="orchestrator.connector-page.v1",
            adapter_id=self.adapter_id,
            object_kind=object_name,
            records=tuple(filtered),
            page_number=page_number,
            next_cursor=next_cursor,
            cursor_sha256=cursor_hash,
            response_sha256=response_hash,
            high_water_mark=high_water,
            complete=done,
            completeness="COMPLETE" if done else "BOUNDED_PARTIAL",
            rate_limit=self.last_rate_limit,
        )

    def read_page(
        self,
        request: SalesforceReadRequestV1,
        cursor: str | None = None,
    ) -> ConnectorPageV1:
        return self.query_page(
            object_name=request.object_name,
            selected_fields=request.selected_fields,
            cursor=cursor,
            page_number=request.page_number,
        )

    def preview(self, request: SalesforceReadRequestV1) -> ConnectorPageV1:
        page = self.read_page(request, None)
        truncated = len(page.records) > 100
        return page.model_copy(update={
            "records": page.records[:100],
            "complete": page.complete and not truncated,
            "completeness": "BOUNDED_PARTIAL" if truncated else page.completeness,
        })

    def get_changed_ids(
        self,
        *,
        object_name: str,
        begin: datetime,
        end: datetime,
    ) -> tuple[str, ...]:
        _identifier(object_name, kind="object")
        incremental_windows(begin, end, window_days=29, overlap=timedelta(0))
        query = urlencode({"start": _utc_parameter(begin), "end": _utc_parameter(end)})
        response = self._get(
            "salesforce.get-updated",
            f"{self.base_url}/services/data/{self.api_version}/sobjects/{object_name}/updated?{query}",
        )
        payload, _ = _decode_response(response)
        ids = payload.get("ids")
        if not isinstance(ids, list) or len(ids) > _MAX_VENDOR_IDS or any(not isinstance(item, str) for item in ids):
            raise SalesforceContractError("Get Updated IDs exceed limits or have invalid shape")
        return tuple(dict.fromkeys(ids))

    def get_changed_ids_incremental(
        self,
        *,
        object_name: str,
        begin: datetime,
        end: datetime,
        window_days: int = 7,
        overlap: timedelta = timedelta(minutes=5),
    ) -> tuple[str, ...]:
        """Read smaller overlapping windows and deduplicate stable native IDs in first-seen order."""
        deduplicated: dict[str, None] = {}
        for lower, upper in incremental_windows(
            begin, end, window_days=window_days, overlap=overlap,
        ):
            for native_id in self.get_changed_ids(object_name=object_name, begin=lower, end=upper):
                deduplicated.setdefault(native_id, None)
                if len(deduplicated) > _MAX_VENDOR_IDS:
                    raise SalesforceContractError("aggregate Get Updated IDs exceed 600,000")
        return tuple(deduplicated)

    def get_deletion_receipt(
        self,
        *,
        source_instance_id: str,
        object_name: str,
        begin: datetime,
        end: datetime,
        feed_expected_complete: bool,
        bounded_read_complete: bool = True,
    ) -> DeletionReceiptV1:
        _identifier(object_name, kind="object")
        incremental_windows(begin, end, window_days=29, overlap=timedelta(0))
        query = urlencode({"start": _utc_parameter(begin), "end": _utc_parameter(end)})
        response = self._get(
            "salesforce.get-deleted",
            f"{self.base_url}/services/data/{self.api_version}/sobjects/{object_name}/deleted?{query}",
        )
        payload, response_hash = _decode_response(response)
        rows = payload.get("deletedRecords")
        if not isinstance(rows, list) or len(rows) > _MAX_VENDOR_IDS:
            raise SalesforceContractError("Get Deleted rows exceed limits or have invalid shape")
        native_ids: list[str] = []
        for row in rows:
            if not isinstance(row, dict) or not isinstance(row.get("id"), str):
                raise SalesforceContractError("Get Deleted row is missing id")
            native_ids.append(row["id"])
        def coverage_time(name: str) -> datetime | None:
            raw = payload.get(name)
            if not isinstance(raw, str):
                return None
            try:
                parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            except ValueError:
                return None
            return parsed if parsed.tzinfo is not None else None

        earliest = coverage_time("earliestDateAvailable")
        latest = coverage_time("latestDateCovered")
        coverage_complete = earliest is not None and latest is not None and earliest <= begin and latest >= end
        ids = tuple(
            stable_source_record_id(
                adapter_id=self.adapter_id,
                source_instance_id=source_instance_id,
                object_kind=object_name,
                native_id=native_id,
            )
            for native_id in dict.fromkeys(native_ids)
        )
        complete = feed_expected_complete and bounded_read_complete and coverage_complete
        receipt_digest = hashlib.sha256(canonical_json_bytes({
            "source": source_instance_id,
            "object": object_name,
            "begin": begin,
            "end": end,
            "ids": ids,
            "response": response_hash,
        })).hexdigest()
        return DeletionReceiptV1(
            schema_version="orchestrator.deletion-receipt.v1",
            deletion_receipt_id=f"del-{receipt_digest[:32]}",
            adapter_id=self.adapter_id,
            source_instance_id=source_instance_id,
            object_kind=object_name,
            window_begin=begin,
            window_end=end,
            deleted_source_record_ids=ids,
            feed_complete=complete,
            deletion_state="DELETIONS_CONFIRMED" if complete else "DELETION_UNKNOWN",
            response_sha256=response_hash,
        )

    def deletion_page(
        self,
        request: SalesforceDeletionRequestV1,
        cursor: str | None = None,
    ) -> DeletionReceiptV1:
        if cursor is not None:
            raise SalesforceContractError("Salesforce deletion cursor is unsupported for one bounded window")
        return self.get_deletion_receipt(
            source_instance_id=request.source_instance_id,
            object_name=request.object_name,
            begin=request.begin,
            end=request.end,
            feed_expected_complete=request.feed_expected_complete,
            bounded_read_complete=request.bounded_read_complete,
        )

    def limits(self) -> dict[str, object]:
        response = self._get("salesforce.limits", f"{self.base_url}/services/data/{self.api_version}/limits")
        payload, _ = _decode_response(response)
        return payload
