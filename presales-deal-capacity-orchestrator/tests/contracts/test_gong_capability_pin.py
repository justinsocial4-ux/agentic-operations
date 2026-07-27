from __future__ import annotations

import hashlib
import json
from pathlib import Path

from orchestrator.canonical import canonical_json_bytes
from orchestrator.contracts.adapter import AdapterCapabilityV1

ROOT = Path(__file__).resolve().parents[2]


def test_gong_official_artifact_host_and_operations_are_hash_bound() -> None:
    config = json.loads((ROOT / "config/connector_security_v1.json").read_text())
    capability = AdapterCapabilityV1.model_validate_json_strict(json.dumps(config["gong_capability"]))
    pin = capability.official_artifact
    assert pin is not None
    artifact_bytes = (ROOT / pin.artifact_path).read_bytes()
    assert hashlib.sha256(artifact_bytes).hexdigest() == pin.sha256
    artifact = json.loads(artifact_bytes)
    assert artifact["openapi"] == pin.openapi_version
    assert artifact["info"]["version"] == pin.api_version
    assert tuple(server["url"] for server in artifact["servers"]) == pin.artifact_declared_servers
    assert "https://127.0.0.1:8443" in pin.rejected_declared_servers
    assert pin.approved_host_set == ("api.gong.io",)
    assert hashlib.sha256(canonical_json_bytes(list(pin.approved_host_set))).hexdigest() == pin.approved_host_set_sha256

    operations = [
        {"operation_id": operation.operation_id, "method": operation.method, "path": operation.path_template}
        for operation in capability.operations
    ]
    assert hashlib.sha256(canonical_json_bytes(operations)).hexdigest() == pin.operation_ids_sha256
    for operation in capability.operations:
        spec_operation = artifact["paths"][operation.path_template][operation.method.lower()]
        assert spec_operation["operationId"] == operation.operation_id
    assert all(operation.operation_id != "addCall" for operation in capability.operations)
    assert capability.external_writes_supported is False
    assert capability.write_operation_ids == ()
