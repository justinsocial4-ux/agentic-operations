"""Verify a fresh checkout/unzip of the package.

Aggregates the mechanical release gates (no network, no credentials, no
production action):

  1. MANIFEST.sha256 exists and matches the current file tree (reproducibility);
  2. the direct+transitive license inventory matches the resolved lock and lists
     no UNKNOWN license (public-license review);
  3. every replay/fictional fixture manifest's recorded hashes match on disk;
  4. the secret/private-data scan passes;
  5. the connector/product no-write scan passes;
  6. the public-doc terminology/claim scan passes.

Exit code is non-zero if any gate fails. Production readiness stays NOT_ASSESSED.

    uv run --frozen python scripts/verify_release.py
"""
from __future__ import annotations

import hashlib
import json
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _normalize(name: str) -> str:
    return name.lower().replace("_", "-")


def check_manifest() -> list[str]:
    from build_release import build_manifest_text  # local import; same scripts dir

    manifest = ROOT / "MANIFEST.sha256"
    if not manifest.exists():
        return ["MANIFEST.sha256 is missing; run scripts/build_release.py"]
    expected = build_manifest_text()
    actual = manifest.read_text(encoding="utf-8")
    if expected != actual:
        return ["MANIFEST.sha256 does not match the current file tree; regenerate with build_release.py"]
    return []


def check_license_inventory() -> list[str]:
    findings: list[str] = []
    lock = tomllib.loads((ROOT / "uv.lock").read_text(encoding="utf-8"))
    locked = {_normalize(p["name"]) for p in lock["package"]}
    locked.discard("presales-deal-capacity-orchestrator")
    inventory = json.loads((ROOT / "config/dependency_licenses_v1.json").read_text())
    rows = {row["name"]: row for row in inventory["packages"]}
    if set(rows) != locked:
        findings.append(f"license inventory drift vs uv.lock: {sorted(set(rows) ^ locked)}")
    for name, row in rows.items():
        if not row["license"] or "UNKNOWN" in row["license"]:
            findings.append(f"unknown license for {name}")
    notices = (ROOT / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8")
    for name in rows:
        if name not in notices:
            findings.append(f"{name} missing from THIRD_PARTY_NOTICES.md")
    return findings


def check_fixture_manifests() -> list[str]:
    findings: list[str] = []
    manifests = list((ROOT / "data").rglob("fixture-manifest.json"))
    manifests += list((ROOT / "data").rglob("manifest.json"))
    for manifest_path in sorted(manifests):
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        files = data.get("files")
        if not isinstance(files, list):
            continue
        base = manifest_path.parent
        for row in files:
            if not isinstance(row, dict):
                continue
            rel = row.get("path")
            expected = row.get("sha256")
            if not rel or not expected:
                continue
            target = base / rel
            if not target.exists():
                findings.append(f"{manifest_path.relative_to(ROOT)}: missing {rel}")
                continue
            actual = hashlib.sha256(target.read_bytes()).hexdigest()
            if actual != expected:
                findings.append(f"{manifest_path.relative_to(ROOT)}: hash mismatch for {rel}")
    return findings


def run_scan(module_name: str) -> list[str]:
    import importlib

    module = importlib.import_module(module_name)
    code = module.main()
    return [] if code == 0 else [f"{module_name} scan failed (exit {code})"]


def main() -> int:
    import sys

    sys.path.insert(0, str(ROOT / "scripts"))
    all_findings: list[str] = []
    for label, findings in (
        ("manifest", check_manifest()),
        ("license-inventory", check_license_inventory()),
        ("fixture-manifests", check_fixture_manifests()),
    ):
        if findings:
            all_findings.extend(f"[{label}] {f}" for f in findings)
        else:
            print(f"[{label}] OK")

    for module_name in ("secret_private_scan", "no_write_scan", "public_doc_terminology_scan"):
        findings = run_scan(module_name)
        if findings:
            all_findings.extend(f"[{module_name}] {f}" for f in findings)
        else:
            print(f"[{module_name}] OK")

    if all_findings:
        print("\nRELEASE VERIFICATION FAILED:")
        for finding in all_findings:
            print(f"  {finding}")
        return 1
    print("\nRelease verification PASSED. Production readiness remains NOT_ASSESSED.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
