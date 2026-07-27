from __future__ import annotations

import httpx
import pytest

from orchestrator.ingestion.transport import RedirectDenied, TransportDenied
from orchestrator.llm.provider import (
    AnalystProviderError,
    LiveLocalProvider,
)

from analyst_fixtures import exact_citation, fictional_segments

DEAL = "deal-1"


def _segments_by_id():
    return {segment.segment_id: segment for segment in fictional_segments()}


def _mock_client(handler) -> httpx.Client:
    return httpx.Client(
        trust_env=False,
        follow_redirects=False,
        transport=httpx.MockTransport(handler),
    )


def test_loopback_endpoint_accepts_valid_local_model_response() -> None:
    seg = _segments_by_id()["seg-a"]

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.host in {"127.0.0.1", "localhost"}
        # No credentials must ever be attached.
        assert "authorization" not in {k.lower() for k in request.headers}
        assert "cookie" not in {k.lower() for k in request.headers}
        return httpx.Response(200, json={"observations": [{
            "dimension_id": "security-or-data-requirements",
            "state": "SUPPORTED",
            "citations": [exact_citation(seg)],
        }]})

    provider = LiveLocalProvider(
        endpoint_url="http://127.0.0.1:11434/v1/analyze",
        segments=fictional_segments(),
        client=_mock_client(handler),
    )
    candidates = provider.propose(deal_source_id=DEAL, dimension_ids=("security-or-data-requirements",))
    provider.close()
    assert len(candidates) == 1
    assert candidates[0]["dimension_id"] == "security-or-data-requirements"


@pytest.mark.parametrize("url", [
    "http://93.184.216.34/v1/analyze",       # public IP literal
    "http://model.example.com/v1/analyze",   # remote host
    "http://10.0.0.5/v1/analyze",            # private but non-loopback
    "http://[::ffff:127.0.0.1]/v1/analyze",  # IPv4-mapped loopback
    "http://user:pass@127.0.0.1/v1/analyze", # userinfo
])
def test_non_loopback_endpoint_rejected_at_construction(url: str) -> None:
    with pytest.raises(TransportDenied):
        LiveLocalProvider(endpoint_url=url, segments=fictional_segments())


def test_loopback_ipv6_accepted() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"observations": []})

    provider = LiveLocalProvider(
        endpoint_url="http://[::1]:11434/v1/analyze",
        segments=fictional_segments(),
        client=_mock_client(handler),
    )
    assert provider.propose(deal_source_id=DEAL, dimension_ids=()) == ()
    provider.close()


def test_redirect_response_rejected() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(302, headers={"location": "http://evil.example.com/"})

    provider = LiveLocalProvider(
        endpoint_url="http://127.0.0.1:11434/v1/analyze",
        segments=fictional_segments(),
        client=_mock_client(handler),
    )
    with pytest.raises(RedirectDenied):
        provider.propose(deal_source_id=DEAL, dimension_ids=())
    provider.close()


def test_caller_authorization_header_rejected() -> None:
    with pytest.raises(TransportDenied):
        LiveLocalProvider(
            endpoint_url="http://127.0.0.1:11434/v1/analyze",
            segments=fictional_segments(),
            request_headers={"Authorization": "Bearer secret"},
        )


def test_caller_cookie_header_rejected() -> None:
    with pytest.raises(TransportDenied):
        LiveLocalProvider(
            endpoint_url="http://127.0.0.1:11434/v1/analyze",
            segments=fictional_segments(),
            request_headers={"Cookie": "session=abc"},
        )


def test_provider_does_not_follow_redirects_or_trust_env() -> None:
    # The default client factory must never trust environment proxies or follow redirects.
    provider = LiveLocalProvider(
        endpoint_url="http://127.0.0.1:11434/v1/analyze",
        segments=fictional_segments(),
    )
    assert provider._client.follow_redirects is False
    assert provider._client.trust_env is False
    provider.close()


def test_non_success_status_raises_provider_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={})

    provider = LiveLocalProvider(
        endpoint_url="http://127.0.0.1:11434/v1/analyze",
        segments=fictional_segments(),
        client=_mock_client(handler),
    )
    with pytest.raises(AnalystProviderError):
        provider.propose(deal_source_id=DEAL, dimension_ids=())
    provider.close()


def test_no_remote_llm_route_exists_in_module() -> None:
    # There is only ONE network analyst provider and it is loopback-only. No remote
    # provider class, base URL, or endpoint constant may appear in the module.
    import inspect

    import orchestrator.llm.provider as provider_module

    source = inspect.getsource(provider_module)
    for banned in ("openai.com", "anthropic.com", "api.", "https://", "REMOTE"):
        assert banned not in source, f"unexpected remote-route token: {banned}"
    # The only provider that touches the network validates a loopback URL.
    assert "validate_loopback_url" in source


def test_bounded_model_input_and_segment_read_cap() -> None:
    # Section 12.3: <= 24 segment reads and <= 256 KiB model input per call.
    from analyst_fixtures import make_segment
    from orchestrator.llm.provider import MAX_MODEL_INPUT_BYTES, MAX_SEGMENT_READS

    big_text = "x" * 20_000  # ~20 KiB each; 30 of them blows the 256 KiB ceiling
    segments = tuple(
        make_segment(segment_id=f"seg-big-{i}", text=big_text + str(i), begin_ms=i * 1000, end_ms=i * 1000 + 500)
        for i in range(30)
    )

    def handler(request: httpx.Request) -> httpx.Response:  # pragma: no cover - never reached
        return httpx.Response(200, json={"observations": []})

    provider = LiveLocalProvider(
        endpoint_url="http://127.0.0.1:11434/v1/analyze",
        segments=segments,
        client=_mock_client(handler),
    )
    # The segment payload is capped at 24 reads; even so the bounded body ceiling holds.
    assert MAX_SEGMENT_READS == 24
    assert MAX_MODEL_INPUT_BYTES == 256 * 1024
    with pytest.raises(AnalystProviderError):
        provider.propose(deal_source_id=DEAL, dimension_ids=())
    provider.close()


def test_malformed_json_from_local_model_rejected() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=b"{not json")

    provider = LiveLocalProvider(
        endpoint_url="http://127.0.0.1:11434/v1/analyze",
        segments=fictional_segments(),
        client=_mock_client(handler),
    )
    with pytest.raises(AnalystProviderError):
        provider.propose(deal_source_id=DEAL, dimension_ids=())
    provider.close()
