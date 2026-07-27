from __future__ import annotations

import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src" / "orchestrator"
CONNECTORS = SOURCE / "ingestion"

# Broad product-source claim scan. Local SQLite/retention removal is deliberately
# reviewed by its own tests and is not a vendor mutation surface.
FORBIDDEN_PRODUCT_SURFACE = re.compile(
    r"/webhooks?\b|create[_-]?(task|message|assignment)|(?:send|upload)[_-]?(message|file)",
    re.IGNORECASE,
)
ALLOWED_PRODUCT_FILES = {
    SOURCE / "store.py",
    SOURCE / "retention.py",
}
CONNECTOR_FILES = {
    CONNECTORS / "transport.py",
    CONNECTORS / "salesforce.py",
    CONNECTORS / "clickup.py",
}
MUTATING_HTTP_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})
MUTATOR_CALL_NAMES = frozenset({"post", "put", "patch", "delete", "create", "upload", "send", "assign"})
MUTATING_PATH_SEGMENTS = frozenset({
    "webhook", "webhooks", "create", "update", "upload", "send", "assign", "comment", "comments",
})
READ_SEMANTIC_PATH_SEGMENTS = frozenset({"updated", "deleted"})  # Salesforce GET resources.


def connector_ast_findings(path: Path) -> list[str]:
    findings: list[str] = []
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            value = node.value
            if value.upper() in MUTATING_HTTP_METHODS:
                findings.append(f"{path.name}:{node.lineno}: mutating HTTP method literal {value!r}")
            if value.startswith("/"):
                segments = {segment.lower() for segment in value.split("/") if segment}
                denied = (segments & MUTATING_PATH_SEGMENTS) - READ_SEMANTIC_PATH_SEGMENTS
                if denied:
                    findings.append(f"{path.name}:{node.lineno}: vendor mutation path segment {sorted(denied)!r}")
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr.lower() in MUTATOR_CALL_NAMES:
                findings.append(f"{path.name}:{node.lineno}: mutator-like SDK/HTTP call {node.func.attr}()")
    return findings


def main() -> int:
    findings: list[str] = []
    for path in SOURCE.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if path not in ALLOWED_PRODUCT_FILES and FORBIDDEN_PRODUCT_SURFACE.search(text):
            findings.append(f"{path.relative_to(ROOT)}: potential product mutation surface")
    for path in sorted(CONNECTOR_FILES):
        findings.extend(connector_ast_findings(path))
    if findings:
        print("Potential write surface:", *findings, sep="\n")
        return 1
    print("No connector HTTP/SDK mutation surface detected; Salesforce updated/deleted are GET-only read resources.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
