from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DENIED_NAMES = {".env", ".netrc"}
EXCLUDED_DIR_PARTS = {".venv", ".git", "__pycache__", ".pytest_cache", ".hypothesis"}
# Capture the quoted assignment value so deliberate fake/test placeholders can be
# distinguished from a real leaked credential.
SECRET_PATTERN = re.compile(
    r"(?i)(?:api[_-]?key|client[_-]?secret|refresh[_-]?token|bearer[_-]?token)\s*[:=]\s*['\"]([^'\"]+)['\"]"
)
# Intentionally fake, synthetic, or placeholder values used by replay fixtures
# and contract tests. These are not real secrets by construction.
FAKE_MARKERS = ("fake", "synthetic", "example", "placeholder", "dummy", "test-", "-test", "redacted", "xxxx", "your-", "changeme")


def _value_is_fake(value: str) -> bool:
    lowered = value.lower()
    return any(marker in lowered for marker in FAKE_MARKERS)


def main() -> int:
    findings: list[str] = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or any(part in EXCLUDED_DIR_PARTS for part in path.parts) or path.name.endswith(".pyc"):
            continue
        if path.name in DENIED_NAMES or path.suffix in {".db", ".sqlite", ".log"}:
            findings.append(f"{path.relative_to(ROOT)}: credential/private-state file")
            continue
        if path.stat().st_size <= 2_000_000:
            text = path.read_text(encoding="utf-8", errors="ignore")
            for match in SECRET_PATTERN.finditer(text):
                if not _value_is_fake(match.group(1)):
                    findings.append(f"{path.relative_to(ROOT)}: real-looking secret assignment")
                    break
    if findings:
        print("Secret/private-data scan findings:", *findings, sep="\n")
        return 1
    print("No credential/private-state file pattern detected.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
