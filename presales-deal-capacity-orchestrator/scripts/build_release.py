"""Generate the source/archive manifest for the package.

Writes ``MANIFEST.sha256`` — a deterministic, sorted checksum of every packaged
file — so a fresh clone/unzip can be verified for reproducibility. Volatile,
generated, or non-shipped paths (virtualenv, VCS metadata, caches, local run
state) are excluded. This performs no network, credential, or production action;
production readiness remains NOT_ASSESSED.

    uv run --frozen python scripts/build_release.py
"""
from __future__ import annotations

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "MANIFEST.sha256"

EXCLUDED_DIR_NAMES = {
    ".venv", ".git", "__pycache__", ".pytest_cache", ".hypothesis",
    ".ruff_cache", ".mypy_cache", "node_modules",
}
EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".db", ".sqlite", ".sqlite3", ".log"}
EXCLUDED_NAMES = {"MANIFEST.sha256", ".DS_Store"}


def packaged_files() -> list[Path]:
    files: list[Path] = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(part in EXCLUDED_DIR_NAMES for part in path.relative_to(ROOT).parts):
            continue
        if path.suffix in EXCLUDED_SUFFIXES or path.name in EXCLUDED_NAMES:
            continue
        files.append(path)
    return sorted(files, key=lambda p: p.relative_to(ROOT).as_posix())


def digest(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def build_manifest_text() -> str:
    lines = [f"{digest(path)}  {path.relative_to(ROOT).as_posix()}" for path in packaged_files()]
    return "\n".join(lines) + "\n"


def main() -> None:
    text = build_manifest_text()
    MANIFEST.write_text(text, encoding="utf-8")
    count = text.count("\n")
    print(f"wrote MANIFEST.sha256 with {count} file checksums")


if __name__ == "__main__":
    main()
