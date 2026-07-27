from __future__ import annotations

import json
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIRECT_RUNTIME = {"httpx", "ortools", "pydantic", "streamlit"}
DIRECT_TEST = {"hypothesis", "pytest"}
LICENSES = {
    "absl-py": "Apache-2.0", "altair": "BSD-3-Clause", "annotated-types": "MIT",
    "anyio": "MIT", "attrs": "MIT", "blinker": "MIT", "certifi": "MPL-2.0",
    "charset-normalizer": "MIT", "click": "BSD-3-Clause", "colorama": "BSD-3-Clause",
    "gitdb": "BSD-3-Clause", "gitpython": "BSD-3-Clause", "h11": "MIT",
    "httpcore": "BSD-3-Clause", "httptools": "MIT", "httpx": "BSD-3-Clause",
    "hypothesis": "MPL-2.0", "idna": "BSD-3-Clause", "immutabledict": "MIT",
    "iniconfig": "MIT", "itsdangerous": "BSD-3-Clause", "jinja2": "BSD-3-Clause",
    "jsonschema": "MIT", "jsonschema-specifications": "MIT", "markupsafe": "BSD-3-Clause",
    "narwhals": "MIT", "numpy": "BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0",
    "ortools": "Apache-2.0", "packaging": "Apache-2.0 OR BSD-2-Clause",
    "pandas": "BSD-3-Clause", "pillow": "MIT-CMU", "pluggy": "MIT",
    "protobuf": "BSD-3-Clause", "pyarrow": "Apache-2.0", "pydantic": "MIT",
    "pydantic-core": "MIT", "pydeck": "Apache-2.0", "pygments": "BSD-2-Clause",
    "pytest": "MIT", "python-dateutil": "Apache-2.0 OR BSD-3-Clause",
    "python-multipart": "Apache-2.0", "referencing": "MIT", "requests": "Apache-2.0",
    "rpds-py": "MIT", "six": "MIT", "smmap": "BSD-3-Clause",
    "sortedcontainers": "Apache-2.0", "starlette": "BSD-3-Clause",
    "streamlit": "Apache-2.0", "tenacity": "Apache-2.0", "toml": "MIT",
    "typing-extensions": "PSF-2.0", "typing-inspection": "MIT", "tzdata": "Apache-2.0",
    "urllib3": "MIT", "uvicorn": "BSD-3-Clause", "watchdog": "Apache-2.0",
    "websockets": "BSD-3-Clause",
}


def normalize(name: str) -> str:
    return name.lower().replace("_", "-")


def main() -> None:
    lock = tomllib.loads((ROOT / "uv.lock").read_text(encoding="utf-8"))
    rows = []
    for package in lock["package"]:
        name = normalize(package["name"])
        if name == "presales-deal-capacity-orchestrator":
            continue
        if name not in LICENSES:
            raise SystemExit(f"unknown dependency license: {name}")
        scope = "DIRECT_RUNTIME" if name in DIRECT_RUNTIME else "DIRECT_TEST" if name in DIRECT_TEST else "TRANSITIVE"
        rows.append({"name": name, "version": package["version"], "scope": scope, "license": LICENSES[name]})
    rows.sort(key=lambda row: row["name"])
    inventory = {
        "schema_version": "orchestrator.dependency-license-inventory.v1",
        "source": "uv.lock",
        "packages": rows,
    }
    (ROOT / "config" / "dependency_licenses_v1.json").write_text(
        json.dumps(inventory, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    lines = [
        "# Third-Party Notices", "",
        "Generated from the resolved `uv.lock`. License identifiers were normalized from package metadata/license files; review full upstream license texts before publication.", "",
        "| Package | Version | Scope | License |", "|---|---:|---|---|",
    ]
    lines.extend(f"| {r['name']} | {r['version']} | {r['scope']} | {r['license']} |" for r in rows)
    lines.extend(["", "SQLite is used through Python's standard library and is public domain.", ""])
    (ROOT / "THIRD_PARTY_NOTICES.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
