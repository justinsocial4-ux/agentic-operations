from __future__ import annotations

import ipaddress
from typing import Annotated, Literal

from pydantic import Field, StringConstraints, model_validator

from .base import Identifier, Sha256, StrictContract

HostName = Annotated[str, StringConstraints(min_length=1, max_length=253, to_lower=True)]
PathTemplate = Annotated[str, StringConstraints(pattern=r"^/[^?#]*$")]


class RequestBodyBoundsV1(StrictContract):
    allowed_keys: tuple[str, ...] = ()
    forbidden_keys: tuple[str, ...] = (
        "url",
        "callback",
        "callback_url",
        "destination_url",
        "webhook",
    )
    max_ids: int = Field(ge=1, le=100)
    max_body_bytes: int = Field(ge=1, le=65_536)
    max_date_window_days: int = Field(ge=1, le=30)


class EndpointCapabilityV1(StrictContract):
    operation_id: Identifier
    method: Literal["GET", "POST"]
    host: HostName
    path_template: PathTemplate
    read_by_post: bool = False
    idempotent_retryable: bool = False
    body_bounds: RequestBodyBoundsV1 | None = None

    @model_validator(mode="after")
    def deny_unsafe_shape(self) -> "EndpointCapabilityV1":
        if "*" in self.host or ":" in self.host or self.host.endswith("."):
            raise ValueError("host must be an exact DNS hostname without wildcard, port, or trailing dot")
        try:
            ipaddress.ip_address(self.host)
        except ValueError:
            pass
        else:
            raise ValueError("IP literals are forbidden for vendor capabilities")
        if self.method == "POST" and not self.read_by_post:
            raise ValueError("POST is permitted only when explicitly classified read-by-POST")
        if self.read_by_post and self.method != "POST":
            raise ValueError("read_by_post is valid only for POST")
        if self.method == "POST" and self.body_bounds is None:
            raise ValueError("read-by-POST requires closed body bounds")
        if self.method == "GET" and self.body_bounds is not None:
            raise ValueError("GET capability cannot define a request body")
        return self


class OfficialArtifactPinV1(StrictContract):
    retrieval_url: str = Field(pattern=r"^https://")
    retrieved_at: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    version_parameter: str
    openapi_version: str
    api_version: str
    sha256: Sha256
    artifact_path: str
    artifact_declared_servers: tuple[str, ...]
    rejected_declared_servers: tuple[str, ...] = ()
    approved_host_set: tuple[HostName, ...]
    approved_host_set_sha256: Sha256
    operation_ids_sha256: Sha256
    manual_review_status: Literal["APPROVED_WITH_REJECTED_GENERATED_SERVERS", "APPROVED"]


class AdapterCapabilityV1(StrictContract):
    schema_version: Literal["orchestrator.adapter-capability.v1"]
    adapter_id: Identifier
    package_version: str
    source_api_family: str
    source_api_version: str
    source_kinds: tuple[str, ...] = Field(min_length=1)
    object_kinds: tuple[str, ...] = Field(min_length=1)
    permitted_authentication_modes: tuple[str, ...]
    operations: tuple[EndpointCapabilityV1, ...]
    official_artifact: OfficialArtifactPinV1 | None = None
    supported_cursor_semantics: tuple[str, ...] = ()
    schema_discovery_supported: bool
    transcript_available: bool
    external_writes_supported: Literal[False]
    write_operation_ids: tuple[()] = ()

    @model_validator(mode="after")
    def unique_read_only_operations(self) -> "AdapterCapabilityV1":
        operation_ids = [operation.operation_id for operation in self.operations]
        tuples = [(o.method, o.host, o.path_template) for o in self.operations]
        if len(operation_ids) != len(set(operation_ids)):
            raise ValueError("operation IDs must be unique")
        if len(tuples) != len(set(tuples)):
            raise ValueError("method/host/path capability tuples must be unique")
        if self.adapter_id == "gong-api-v2" and self.official_artifact is None:
            raise ValueError("Gong capability requires a reviewed official artifact pin")
        return self
