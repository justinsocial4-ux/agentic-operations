from pathlib import Path

from orchestrator.ingestion.registry import CAPABILITY_IDS, load_gong_capability

ROOT = Path(__file__).resolve().parents[2]


def test_registry_exposes_reviewed_capability_without_instantiating_transport() -> None:
    capability = load_gong_capability(ROOT)
    assert capability.adapter_id in CAPABILITY_IDS
    assert {"salesforce-rest-v1", "clickup-api-v2"}.issubset(CAPABILITY_IDS)
    assert capability.external_writes_supported is False
