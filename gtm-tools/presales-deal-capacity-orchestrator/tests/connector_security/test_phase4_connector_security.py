from __future__ import annotations

import json
import pickle
from pathlib import Path

import httpx
import pytest

from orchestrator.contracts.connectors import ConnectorPageV1
from orchestrator.ingestion.salesforce import validate_salesforce_instance_url
from orchestrator.ingestion.transport import (
    AllowedEndpoint,
    EphemeralCredential,
    LockedHttpClient,
    RedirectDenied,
    TransportDenied,
    build_httpx_client,
    validate_public_dns_evidence,
    validate_vendor_url,
)

ENDPOINT = AllowedEndpoint(
    "synthetic.read", "GET", "api.clickup.com", "/api/v2/team", idempotent_retryable=True,
)


def locked(handler, *, sleeper=lambda _: None) -> LockedHttpClient:
    raw = build_httpx_client(transport=httpx.MockTransport(handler))
    return LockedHttpClient((ENDPOINT,), client=raw, sleeper=sleeper, now=lambda: 0)


def test_session_credential_is_explicitly_issued_redacted_and_not_ambient() -> None:
    seen: list[httpx.Request] = []
    client = locked(lambda request: seen.append(request) or httpx.Response(200, json={}))
    credential = EphemeralCredential.authorization_value("fake-clickup-token-phase4")
    assert "fake-clickup" not in repr(credential)
    with pytest.raises(TypeError, match="cannot be serialized"):
        pickle.dumps(credential)
    client.request(
        operation_id="synthetic.read", method="GET", url="https://api.clickup.com/api/v2/team",
        credential=credential,
    )
    assert seen[0].headers["authorization"] == "fake-clickup-token-phase4"
    assert "authorization" not in client._client.headers  # no ambient client-level credential
    client.close()


def test_saarland_style_cross_domain_redirect_is_denied_without_forwarding() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(307, headers={"location": "https://www.saarland.de/credential-capture"})

    client = locked(handler)
    with pytest.raises(RedirectDenied):
        client.request(
            operation_id="synthetic.read", method="GET", url="https://api.clickup.com/api/v2/team",
            credential=EphemeralCredential.authorization_value("fake-only"),
        )
    assert len(seen) == 1
    client.close()


@pytest.mark.parametrize(
    "url",
    [
        "file:///private/synthetic-token",
        "gopher://api.clickup.com/api/v2/team",
        "https://localhost/api/v2/team",
        "https://169.254.169.254/api/v2/team",
        "https://api.clickup.com.evil.invalid/api/v2/team",
        "https://арi.clickup.com/api/v2/team",
    ],
)
def test_ssrf_and_local_file_urls_are_denied(url: str) -> None:
    with pytest.raises(TransportDenied):
        validate_vendor_url(url, approved_hosts=frozenset({"api.clickup.com"}))


@pytest.mark.parametrize(
    "url",
    [
        "https://evil.invalid",
        "https://synthetic.my.salesforce.com.evil.invalid",
        "https://127.0.0.1",
        "file:///tmp/source",
        "https://user@synthetic.my.salesforce.com",
    ],
)
def test_salesforce_instance_ssrf_denial(url: str) -> None:
    with pytest.raises(TransportDenied):
        validate_salesforce_instance_url(url)


def test_dns_private_link_local_multicast_and_rebinding_evidence_is_denied() -> None:
    for addresses in (["127.0.0.1"], ["10.0.0.8"], ["169.254.1.1"], ["224.0.0.1"]):
        with pytest.raises(TransportDenied):
            validate_public_dns_evidence(addresses)
    assert validate_public_dns_evidence(["8.8.8.8"], ["8.8.8.8"]) == ("8.8.8.8",)
    with pytest.raises(TransportDenied, match="rebinding"):
        validate_public_dns_evidence(["8.8.8.8"], ["1.1.1.1"])


def test_locked_client_rejects_ambient_default_auth_header() -> None:
    raw = build_httpx_client(transport=httpx.MockTransport(lambda _: httpx.Response(200)))
    raw.headers["Authorization"] = "ambient-fake"
    with pytest.raises(TransportDenied, match="ambient"):
        LockedHttpClient((ENDPOINT,), client=raw)
    raw.close()


def test_get_body_and_caller_auth_header_are_denied_before_mock_transport() -> None:
    calls = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(200)

    client = locked(handler)
    with pytest.raises(TransportDenied, match="bodies"):
        client.request(
            operation_id="synthetic.read", method="GET", url="https://api.clickup.com/api/v2/team",
            content=b'{"callback":"file:///tmp/no"}',
        )
    with pytest.raises(TransportDenied, match="headers denied"):
        client.request(
            operation_id="synthetic.read", method="GET", url="https://api.clickup.com/api/v2/team",
            headers={"Authorization": "ambient-fake"},
        )
    assert calls == 0
    client.close()


def test_retry_is_bounded_to_four_and_honors_only_bounded_retry_after() -> None:
    calls = 0
    sleeps: list[float] = []

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(429, headers={"retry-after": "999999"})

    client = locked(handler, sleeper=sleeps.append)
    response = client.request_with_retry(
        operation_id="synthetic.read", method="GET", url="https://api.clickup.com/api/v2/team",
    )
    assert response.status_code == 429
    assert calls == 4
    assert sleeps == [1.0, 2.0, 4.0]
    assert len(client.last_retry_trace) == 3
    client.close()


def test_checkpoint_projection_contains_cursor_hash_but_not_vendor_cursor_value() -> None:
    page = ConnectorPageV1(
        schema_version="orchestrator.connector-page.v1",
        adapter_id="clickup-api-v2",
        object_kind="TASK",
        records=(),
        page_number=0,
        next_cursor="opaque-vendor-page-value",
        cursor_sha256="d" * 64,
        response_sha256="e" * 64,
        high_water_mark=None,
        complete=False,
        completeness="BOUNDED_PARTIAL",
    )
    durable = page.durable_checkpoint_projection()
    encoded = json.dumps(durable, default=str)
    assert "opaque-vendor-page-value" not in encoded
    assert durable["cursor_sha256"] == "d" * 64
