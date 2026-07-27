from __future__ import annotations

import json
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def normalize(name: str) -> str:
    return name.lower().replace("_", "-")


def test_every_locked_direct_and_transitive_dependency_has_a_known_license() -> None:
    lock = tomllib.loads((ROOT / "uv.lock").read_text())
    locked = {normalize(package["name"]) for package in lock["package"]}
    locked.remove("presales-deal-capacity-orchestrator")
    inventory = json.loads((ROOT / "config/dependency_licenses_v1.json").read_text())
    rows = inventory["packages"]
    assert {row["name"] for row in rows} == locked
    assert all(row["license"] and "UNKNOWN" not in row["license"] for row in rows)
    assert {row["name"] for row in rows if row["scope"] == "DIRECT_RUNTIME"} == {"httpx", "ortools", "pydantic", "streamlit"}
    assert {row["name"] for row in rows if row["scope"] == "DIRECT_TEST"} == {"hypothesis", "pytest"}


def test_fallback_requirements_are_exact_and_hash_locked() -> None:
    text = (ROOT / "requirements.lock").read_text()
    requirement_lines = [line for line in text.splitlines() if line and not line.startswith((" ", "#"))]
    assert requirement_lines
    assert all("==" in line and line.endswith("\\") for line in requirement_lines)
    assert text.count("--hash=sha256:") >= len(requirement_lines)
