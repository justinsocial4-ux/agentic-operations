import pytest
from pydantic import ValidationError

from orchestrator.contracts.adapter import EndpointCapabilityV1, RequestBodyBoundsV1


def test_vendor_capability_rejects_wildcard_ip_and_unclassified_post() -> None:
    for host in ("*.gong.io", "127.0.0.1", "api.gong.io:443"):
        with pytest.raises(ValidationError):
            EndpointCapabilityV1(operation_id="read", method="GET", host=host, path_template="/v2/calls")
    with pytest.raises(ValidationError, match="read-by-POST"):
        EndpointCapabilityV1(operation_id="write", method="POST", host="api.gong.io", path_template="/v2/calls")


def test_read_by_post_requires_closed_bounds() -> None:
    endpoint = EndpointCapabilityV1(
        operation_id="transcript-read", method="POST", host="api.gong.io",
        path_template="/v2/calls/transcript", read_by_post=True,
        body_bounds=RequestBodyBoundsV1(max_ids=100, max_body_bytes=65536, max_date_window_days=30),
    )
    assert endpoint.read_by_post
