from __future__ import annotations

import httpx
import pytest

from orchestrator.ingestion import transport as locked_transport
from orchestrator.ingestion.transport import (
    AllowedEndpoint,
    LockedHttpClient,
    RedirectDenied,
    TransportDenied,
    build_httpx_client,
    validate_loopback_url,
    validate_vendor_url,
)

ENDPOINT = AllowedEndpoint("listCalls", "GET", "api.gong.io", "/v2/calls")


def test_httpx_factory_hard_codes_no_environment_no_redirect_and_tls(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}
    sentinel = object()

    def fake_client(**kwargs: object) -> object:
        captured.update(kwargs)
        return sentinel

    monkeypatch.setattr(locked_transport.httpx, "Client", fake_client)
    assert build_httpx_client() is sentinel
    assert captured["trust_env"] is False
    assert captured["follow_redirects"] is False
    assert captured["verify"] is True


def test_hostile_proxy_environment_is_ignored(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HTTP_PROXY", "http://127.0.0.1:9")
    monkeypatch.setenv("HTTPS_PROXY", "http://127.0.0.1:9")
    monkeypatch.setenv("ALL_PROXY", "http://127.0.0.1:9")
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json={"ok": True})

    raw = build_httpx_client(transport=httpx.MockTransport(handler))
    client = LockedHttpClient((ENDPOINT,), client=raw)
    response = client.request(operation_id="listCalls", method="GET", url="https://api.gong.io/v2/calls")
    assert response.status_code == 200
    assert len(seen) == 1
    assert "proxy-authorization" not in seen[0].headers
    client.close()


def test_netrc_is_not_consulted_or_injected(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    netrc = tmp_path / ".netrc"
    netrc.write_text("machine api.gong.io login synthetic-user password synthetic-password\n")
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("NETRC", str(netrc))
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200)

    client = LockedHttpClient((ENDPOINT,), client=build_httpx_client(transport=httpx.MockTransport(handler)))
    client.request(operation_id="listCalls", method="GET", url="https://api.gong.io/v2/calls")
    assert "authorization" not in seen[0].headers
    client.close()


def test_redirect_is_not_followed_and_is_rejected() -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(302, headers={"location": "https://lookalike.invalid/steal"})

    client = LockedHttpClient((ENDPOINT,), client=build_httpx_client(transport=httpx.MockTransport(handler)))
    with pytest.raises(RedirectDenied):
        client.request(operation_id="listCalls", method="GET", url="https://api.gong.io/v2/calls")
    assert calls == 1
    client.close()


@pytest.mark.parametrize("header", ["Authorization", "Cookie", "Proxy-Authorization", "X-Api-Key", "Host"])
def test_caller_auth_proxy_and_cookie_headers_are_denied_before_transport(header: str) -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(200)

    client = LockedHttpClient((ENDPOINT,), client=build_httpx_client(transport=httpx.MockTransport(handler)))
    with pytest.raises(TransportDenied, match="headers denied"):
        client.request(
            operation_id="listCalls", method="GET", url="https://api.gong.io/v2/calls",
            headers={header: "synthetic-value"},
        )
    assert calls == 0
    client.close()


def test_response_cookie_is_not_sent_on_later_request() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        headers = {"set-cookie": "session=synthetic; Domain=api.gong.io; Path=/"} if len(requests) == 1 else {}
        return httpx.Response(200, headers=headers)

    client = LockedHttpClient((ENDPOINT,), client=build_httpx_client(transport=httpx.MockTransport(handler)))
    for _ in range(2):
        client.request(operation_id="listCalls", method="GET", url="https://api.gong.io/v2/calls")
    assert all("cookie" not in request.headers for request in requests)
    client.close()


@pytest.mark.parametrize(
    "url",
    [
        "https://example.invalid/v1/chat",
        "http://10.0.0.1:8000/v1/chat",
        "http://169.254.169.254/v1/chat",
        "http://[::ffff:127.0.0.1]/v1/chat",
    ],
)
def test_local_model_rejects_non_loopback_and_mapped_addresses(url: str) -> None:
    with pytest.raises(TransportDenied):
        validate_loopback_url(url)


@pytest.mark.parametrize("url", ["http://127.0.0.1:11434/v1/chat", "http://[::1]:11434/v1/chat"])
def test_local_model_accepts_literal_loopback_only(url: str) -> None:
    host, port, path = validate_loopback_url(url)
    assert port == 11434
    assert path == "/v1/chat"
    assert host in {"127.0.0.1", "::1"}


@pytest.mark.parametrize(
    "url",
    [
        "http://api.gong.io/v2/calls",
        "https://api.gong.io:8443/v2/calls",
        "https://api.gong.io.evil.invalid/v2/calls",
        "https://127.0.0.1/v2/calls",
        "https://user@api.gong.io/v2/calls",
        "https://api.gong.io/v2/calls#fragment",
    ],
)
def test_vendor_tls_host_port_and_url_boundaries(url: str) -> None:
    with pytest.raises(TransportDenied):
        validate_vendor_url(url, approved_hosts=frozenset({"api.gong.io"}))


def test_write_method_and_unapproved_operation_fail_before_transport() -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(200)

    client = LockedHttpClient((ENDPOINT,), client=build_httpx_client(transport=httpx.MockTransport(handler)))
    for operation, method in (("addCall", "POST"), ("listCalls", "DELETE")):
        with pytest.raises(TransportDenied, match="tuple"):
            client.request(operation_id=operation, method=method, url="https://api.gong.io/v2/calls")
    assert calls == 0
    client.close()
