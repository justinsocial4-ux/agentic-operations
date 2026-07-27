from __future__ import annotations

import json
from pathlib import Path

from orchestrator.contracts.adapter import AdapterCapabilityV1

CAPABILITY_IDS = frozenset({"gong-api-v2", "salesforce-rest-v1", "clickup-api-v2"})


def load_gong_capability(package_root: Path) -> AdapterCapabilityV1:
    """Load the reviewed Phase 0 capability; this does not instantiate transport."""
    config = (package_root / "config" / "connector_security_v1.json").read_text(encoding="utf-8")
    payload = json.loads(config)
    return AdapterCapabilityV1.model_validate_json_strict(json.dumps(payload["gong_capability"]))
