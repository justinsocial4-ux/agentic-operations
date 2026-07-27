"""Terminology / claim scan over every public-facing document.

Fails if any forbidden marketing/overclaim phrase appears in the README, the
notices, the threat model, the recruiter playbook, the launcher scripts, or any
sample-data README. Reuses the exact forbidden-term list the Phase 7 UI scanner
enforces, so the whole package speaks one proof-qualified vocabulary.
"""
from __future__ import annotations

from pathlib import Path

from orchestrator.ui.copy import scan_text

ROOT = Path(__file__).resolve().parents[1]

# Explicit top-level public docs.
TOP_LEVEL = (
    "README.md",
    "DISCLAIMER.md",
    "SECURITY.md",
    "PRIVACY.md",
    "THREAT_MODEL.md",
    "THIRD_PARTY_NOTICES.md",
    "run_demo.sh",
    "run_demo.command",
)

# Globs for the rest of the public-facing surface.
GLOBS = (
    "docs/**/*.md",
    "config/**/*.md",
    "data/**/*.md",
)


def _targets() -> list[Path]:
    paths: list[Path] = [ROOT / name for name in TOP_LEVEL]
    for pattern in GLOBS:
        paths.extend(sorted(ROOT.glob(pattern)))
    return [p for p in paths if p.is_file()]


def main() -> int:
    offenders: dict[str, tuple[str, ...]] = {}
    for path in _targets():
        hits = scan_text(path.read_text(encoding="utf-8"))
        if hits:
            offenders[str(path.relative_to(ROOT))] = hits
    if offenders:
        print("Overclaim wording in public docs:")
        for name, hits in sorted(offenders.items()):
            print(f"  {name}: {sorted(set(hits))}")
        return 1
    print(f"No overclaim wording in {len(_targets())} public-facing documents.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
