"""Phase 8 packaging gates: docs, scans, sample profiles, and manifest."""
from __future__ import annotations

import importlib
import sys
from pathlib import Path

from orchestrator.contracts.mapping import MappingProfileV1
from orchestrator.mapping.profiles import mapping_profile_payload_hash, scan_mapping_profile

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"


def _load(module_name: str):
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))
    return importlib.import_module(module_name)


def test_public_doc_terminology_scan_finds_no_overclaim() -> None:
    assert _load("public_doc_terminology_scan").main() == 0


def test_secret_private_scan_passes() -> None:
    assert _load("secret_private_scan").main() == 0


def test_no_write_scan_passes() -> None:
    assert _load("no_write_scan").main() == 0


def test_recruiter_acceptance_passes_headless() -> None:
    assert _load("recruiter_acceptance").main() == 0


def test_sample_mapping_profiles_are_valid_credential_free_and_hash_bound() -> None:
    profile_dir = ROOT / "config" / "mapping_profiles"
    profiles = sorted(profile_dir.glob("*.json"))
    assert profiles, "expected at least one sample mapping profile"
    for path in profiles:
        profile = MappingProfileV1.model_validate_json_strict(path.read_text(encoding="utf-8"))
        # Fails closed on any value/secret and on a hash mismatch.
        scan_mapping_profile(profile)
        assert profile.canonical_profile_sha256 == mapping_profile_payload_hash(profile)


def test_required_phase8_public_artifacts_exist() -> None:
    for rel in (
        "README.md",
        "DISCLAIMER.md",
        "SECURITY.md",
        "PRIVACY.md",
        "LICENSE",
        "THIRD_PARTY_NOTICES.md",
        "MANIFEST.sha256",
        "run_demo.sh",
        "run_demo.command",
        "docs/recruiter-playbook.md",
        "config/mapping_profiles/README.md",
        ".github/workflows/ci.yml",
    ):
        assert (ROOT / rel).is_file(), f"missing packaged artifact: {rel}"


def test_license_is_marked_provisional() -> None:
    text = (ROOT / "LICENSE").read_text(encoding="utf-8")
    assert "PROVISIONAL" in text
    assert "MIT License" in text


def test_manifest_matches_current_tree() -> None:
    build = _load("build_release")
    manifest = ROOT / "MANIFEST.sha256"
    assert manifest.exists()
    assert build.build_manifest_text() == manifest.read_text(encoding="utf-8"), (
        "MANIFEST.sha256 is stale; regenerate with scripts/build_release.py"
    )
