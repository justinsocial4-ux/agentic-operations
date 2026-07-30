#!/usr/bin/env python3
"""Build a verified, deterministic .skill archive for the agent factory.

The archive keeps the established project layout:

    <skill-name>/SKILL.md
    <skill-name>/references/...
    <skill-name>/scripts/...

All non-hidden bundled files are included recursively. The command fails closed
when required references are absent or the finished archive differs from the
source tree.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path


SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
FIXED_ZIP_TIME = (1980, 1, 1, 0, 0, 0)
IGNORED_NAMES = {".DS_Store", "Icon\r"}


class PackagingError(RuntimeError):
    """Raised when an input skill cannot be safely packaged."""


@dataclass(frozen=True)
class SkillMetadata:
    name: str
    description: str


def _strip_yaml_scalar(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1].strip()
    return value


def read_metadata(skill_md: Path) -> SkillMetadata:
    """Read the required top-level name and description frontmatter fields."""
    try:
        lines = skill_md.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError as exc:
        raise PackagingError(f"missing required file: {skill_md}") from exc

    if not lines or lines[0].strip() != "---":
        raise PackagingError("SKILL.md must begin with YAML frontmatter")

    try:
        end = next(index for index, line in enumerate(lines[1:], start=1) if line.strip() == "---")
    except StopIteration as exc:
        raise PackagingError("SKILL.md frontmatter has no closing ---") from exc

    fields: dict[str, str] = {}
    for line in lines[1:end]:
        if not line or line[0].isspace() or ":" not in line:
            continue
        key, value = line.split(":", 1)
        if key in {"name", "description"}:
            fields[key] = _strip_yaml_scalar(value)

    name = fields.get("name", "")
    description = fields.get("description", "")
    if not name:
        raise PackagingError("SKILL.md frontmatter is missing a non-empty name")
    if not SLUG_RE.fullmatch(name):
        raise PackagingError(f"skill name must be a lowercase hyphenated slug: {name!r}")
    if not description:
        raise PackagingError("SKILL.md frontmatter is missing a non-empty description")
    return SkillMetadata(name=name, description=description)


def _ignored(relative_path: Path) -> bool:
    return any(part.startswith(".") or part in IGNORED_NAMES or part == "__pycache__" for part in relative_path.parts)


def collect_files(skill_dir: Path) -> list[Path]:
    """Return stable, recursively collected bundle files and reject symlinks."""
    files: list[Path] = []
    for path in skill_dir.rglob("*"):
        relative = path.relative_to(skill_dir)
        if _ignored(relative):
            continue
        if path.is_symlink():
            raise PackagingError(f"symlinks are not allowed in skill bundles: {relative}")
        if path.is_file() and path.suffix != ".skill" and path.suffix != ".pyc":
            files.append(path)
    return sorted(files, key=lambda path: path.relative_to(skill_dir).as_posix())


def validate_inputs(skill_dir: Path, require_references: bool = True) -> tuple[SkillMetadata, list[Path]]:
    if not skill_dir.is_dir():
        raise PackagingError(f"skill path is not a directory: {skill_dir}")

    metadata = read_metadata(skill_dir / "SKILL.md")
    files = collect_files(skill_dir)
    relative_files = {path.relative_to(skill_dir).as_posix() for path in files}

    if "SKILL.md" not in relative_files:
        raise PackagingError("SKILL.md was not collected")
    if require_references and not any(name.startswith("references/") for name in relative_files):
        raise PackagingError("references/ must contain at least one bundled file")
    return metadata, files


def _zip_info(archive_name: str, source: Path) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(archive_name, FIXED_ZIP_TIME)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.create_system = 3
    mode = 0o755 if os.access(source, os.X_OK) else 0o644
    info.external_attr = (mode & 0xFFFF) << 16
    return info


def verify_archive(archive: Path, skill_name: str, source_files: list[Path], skill_dir: Path) -> list[str]:
    """Prove the archive has exactly the expected members and intact bytes."""
    expected = [f"{skill_name}/{path.relative_to(skill_dir).as_posix()}" for path in source_files]
    with zipfile.ZipFile(archive, "r") as bundle:
        actual = bundle.namelist()
        if actual != expected:
            raise PackagingError(f"archive member mismatch: expected {expected!r}, got {actual!r}")
        bad_member = bundle.testzip()
        if bad_member:
            raise PackagingError(f"archive CRC verification failed for {bad_member}")
        for path, member in zip(source_files, expected, strict=True):
            if bundle.read(member) != path.read_bytes():
                raise PackagingError(f"archive content differs from source: {member}")
    return expected


def package_skill(
    skill_dir: Path,
    output_dir: Path,
    *,
    force: bool = False,
    require_references: bool = True,
) -> tuple[Path, list[str]]:
    """Package one skill atomically and return the archive plus verified members."""
    skill_dir = skill_dir.resolve()
    metadata, source_files = validate_inputs(skill_dir, require_references=require_references)
    output_dir.mkdir(parents=True, exist_ok=True)
    archive = output_dir.resolve() / f"{metadata.name}.skill"
    if archive.exists() and not force:
        raise PackagingError(f"output already exists; pass --force to replace it: {archive}")

    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(prefix=f".{metadata.name}.", suffix=".skill", dir=output_dir, delete=False) as temp:
            temp_path = Path(temp.name)
        with zipfile.ZipFile(temp_path, "w") as bundle:
            for source in source_files:
                relative = source.relative_to(skill_dir).as_posix()
                member = f"{metadata.name}/{relative}"
                bundle.writestr(_zip_info(member, source), source.read_bytes())
        members = verify_archive(temp_path, metadata.name, source_files, skill_dir)
        os.replace(temp_path, archive)
        temp_path = None
        return archive, members
    finally:
        if temp_path and temp_path.exists():
            temp_path.unlink()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Package and verify one agent-factory skill.")
    parser.add_argument("skill_dir", type=Path, help="source skill directory")
    parser.add_argument("output_dir", type=Path, nargs="?", default=Path("_build/dist"), help="archive output directory")
    parser.add_argument("--force", action="store_true", help="atomically replace an existing archive")
    parser.add_argument(
        "--allow-missing-references",
        action="store_true",
        help="permit a skill without references (not allowed by this factory's final gate)",
    )
    parser.add_argument("--list", action="store_true", help="print verified archive members")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        archive, members = package_skill(
            args.skill_dir,
            args.output_dir,
            force=args.force,
            require_references=not args.allow_missing_references,
        )
    except (OSError, PackagingError, zipfile.BadZipFile) as exc:
        print(f"PACKAGING FAILED: {exc}", file=sys.stderr)
        return 1

    print(f"PACKAGING PASSED: {archive}")
    if args.list:
        for member in members:
            print(member)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
