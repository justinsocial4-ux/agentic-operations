import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_fictional_manifest_is_frozen_by_sidecar_hash() -> None:
    manifest = ROOT / "data/fictional/v2/manifest.json"
    expected, filename = (ROOT / "data/fictional/v2/manifest.sha256").read_text().split()
    assert filename == "manifest.json"
    assert hashlib.sha256(manifest.read_bytes()).hexdigest() == expected
