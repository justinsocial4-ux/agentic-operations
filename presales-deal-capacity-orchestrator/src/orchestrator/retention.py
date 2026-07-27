from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, Literal

from pydantic import Field, field_validator, model_validator

from .contracts.base import Identifier, Sha256, StrictContract, require_offset_aware


class RetentionError(RuntimeError):
    pass


class RetainedCitedExcerptV1(StrictContract):
    schema_version: Literal["orchestrator.retained-cited-excerpt.v1"]
    excerpt_id: Identifier
    conversation_origin_id: Identifier
    excerpt: str = Field(min_length=1, max_length=4096)
    quote_sha256: Sha256
    char_begin: int = Field(ge=0)
    char_end: int = Field(gt=0)
    expires_at: datetime
    retention_approved_at: datetime

    @field_validator("expires_at", "retention_approved_at")
    @classmethod
    def aware_times(cls, value: datetime) -> datetime:
        return require_offset_aware(value)

    @model_validator(mode="after")
    def validate_excerpt(self) -> "RetainedCitedExcerptV1":
        import hashlib

        if self.char_begin >= self.char_end or self.char_end - self.char_begin != len(self.excerpt):
            raise ValueError("excerpt offsets do not match the exact retained excerpt")
        if hashlib.sha256(self.excerpt.encode("utf-8")).hexdigest() != self.quote_sha256:
            raise ValueError("retained excerpt hash mismatch")
        if self.expires_at <= self.retention_approved_at:
            raise ValueError("retained excerpt must have a bounded future expiry")
        return self


@dataclass(frozen=True)
class SentinelMatch:
    path: Path
    byte_offset: int


def scan_artifacts_for_sentinel(paths: Iterable[Path], sentinel: str) -> tuple[SentinelMatch, ...]:
    needle = sentinel.encode("utf-8")
    if not needle:
        raise ValueError("sentinel cannot be empty")
    matches: list[SentinelMatch] = []
    files: list[Path] = []
    for path in paths:
        if path.is_dir():
            files.extend(item for item in path.rglob("*") if item.is_file())
        elif path.is_file():
            files.append(path)
    for path in files:
        try:
            payload = path.read_bytes()
        except OSError as exc:
            raise RetentionError(f"artifact could not be scanned: {path.name}") from exc
        offset = payload.find(needle)
        if offset >= 0:
            matches.append(SentinelMatch(path, offset))
    return tuple(matches)


def write_metadata_only_crash_artifact(
    path: Path,
    *,
    occurred_at: datetime,
    reason_code: str,
    run_id: str | None,
) -> None:
    """Write no exception message, traceback, locals, request body, or buffer."""
    if path.exists() or path.is_symlink():
        raise RetentionError("crash artifact destination must be new")
    payload = {
        "schema_version": "orchestrator.crash-metadata.v1",
        "occurred_at": occurred_at.isoformat(),
        "reason_code": reason_code,
        "run_id": run_id,
        "locals_captured": False,
        "request_body_captured": False,
    }
    descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_NOFOLLOW", 0), 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, sort_keys=True, separators=(",", ":"))


def delete_expired_app_files(
    *,
    app_data_root: Path,
    items: Iterable[tuple[Path, datetime]],
    now: datetime,
) -> tuple[Path, ...]:
    root = app_data_root.resolve(strict=True)
    deleted: list[Path] = []
    for path, expires_at in items:
        if expires_at > now:
            continue
        candidate = path.resolve(strict=True)
        try:
            candidate.relative_to(root)
        except ValueError as exc:
            raise RetentionError("retention item escapes app-owned data root") from exc
        if path.is_symlink() or not candidate.is_file():
            raise RetentionError("retention deletion permits only app-owned regular files")
        candidate.unlink()
        deleted.append(candidate)
    return tuple(deleted)
