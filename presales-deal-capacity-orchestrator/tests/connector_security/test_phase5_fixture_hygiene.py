from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


def _fixture_files() -> list[Path]:
    """Only the declared synthetic replay fixtures; the vendor OpenAPI artifact and its
    review file are vendor-published schema, not participant fixtures."""
    files: list[Path] = []
    for family in ("fathom", "gong"):
        family_dir = ROOT / "data" / "replay" / family
        manifest = json.loads((family_dir / "fixture-manifest.json").read_text())
        files.append(family_dir / "fixture-manifest.json")
        for name in manifest["files"]:
            files.append(family_dir / name)
    return files


def test_no_real_participant_pii_in_phase5_fixtures() -> None:
    for path in _fixture_files():
        text = path.read_text(encoding="utf-8")
        for email in _EMAIL.findall(text):
            # Every synthetic email must be a non-routable .invalid address.
            assert email.endswith(".invalid"), f"non-synthetic email {email} in {path.name}"


def test_replay_manifests_declare_credential_free_no_network_no_pii() -> None:
    for family in ("fathom", "gong"):
        manifest = json.loads((ROOT / "data" / "replay" / family / "fixture-manifest.json").read_text())
        assert manifest["credential_free"] is True
        assert manifest["vendor_network"] is False
        assert manifest["contains_real_participant_pii"] is False
