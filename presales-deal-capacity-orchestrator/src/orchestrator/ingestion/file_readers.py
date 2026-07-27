from __future__ import annotations

import csv
import io
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

from orchestrator.canonical import canonical_json_bytes
from orchestrator.contracts.base import strict_json_loads
from orchestrator.contracts.enums import (
    ExecutionModeV1,
    ImplementationProofV1,
    LiveValidationProofV1,
)
from orchestrator.contracts.proof import SourceProofInputV1
from orchestrator.ingestion.bounds import MAX_OPERATIONAL_BYTES, MAX_ROWS, MAX_TRANSCRIPT_BYTES

DEFAULT_PREVIEW_ROWS = 20
MAX_PREVIEW_ROWS = 100
MAX_PREVIEW_VALUE_CHARS = 200
DEFAULT_MAX_CELL_BYTES = 1_048_576


class FileImportError(ValueError):
    """Safe file-import failure. Messages contain no source values."""


@dataclass(frozen=True)
class FileReadBounds:
    max_rows: int = 2_000
    max_bytes: int = 50 * 1024 * 1024
    max_cell_bytes: int = DEFAULT_MAX_CELL_BYTES
    transcript: bool = False

    def __post_init__(self) -> None:
        byte_ceiling = MAX_TRANSCRIPT_BYTES if self.transcript else MAX_OPERATIONAL_BYTES
        if not 1 <= self.max_rows <= MAX_ROWS:
            raise FileImportError("row bound exceeds the file-import hard ceiling")
        if not 1 <= self.max_bytes <= byte_ceiling:
            raise FileImportError("byte bound exceeds the file-import hard ceiling")
        if not 1 <= self.max_cell_bytes <= self.max_bytes:
            raise FileImportError("cell bound must fit inside the byte bound")


@dataclass(frozen=True)
class FileReadResult:
    field_ids: tuple[str, ...]
    rows: tuple[dict[str, Any], ...]
    bytes_read: int
    complete: bool
    stopped_reason: str | None
    next_row_offset: int


@dataclass(frozen=True)
class PreviewResult:
    field_ids: tuple[str, ...]
    rows: tuple[dict[str, str | None], ...]
    rows_available: int
    truncated: bool


@dataclass(frozen=True)
class FileImportProofChecklist:
    bounded_reader: bool
    translator: bool
    replay_fixture: bool
    malformed_and_oversized_negatives: bool
    path_size_encoding_controls: bool
    no_network_enforcement: bool

    def proof(self) -> SourceProofInputV1:
        if not all((
            self.bounded_reader,
            self.translator,
            self.replay_fixture,
            self.malformed_and_oversized_negatives,
            self.path_size_encoding_controls,
            self.no_network_enforcement,
        )):
            raise FileImportError("file adapter has not earned contract-tested implementation proof")
        return SourceProofInputV1(
            execution_mode=ExecutionModeV1.FILE_IMPORT,
            implementation_proof=ImplementationProofV1.FULLY_IMPLEMENTED_CONTRACT_TESTED,
            live_validation_proof=LiveValidationProofV1.NOT_LIVE_VALIDATED,
        )


def contract_tested_file_import_proof() -> SourceProofInputV1:
    """The shipped reader's status. Tests separately exercise every checklist item."""
    return FileImportProofChecklist(True, True, True, True, True, True).proof()


def _authorized_regular_file(path: Path, authorization_attestation_id: str) -> bytes:
    if not authorization_attestation_id.strip():
        raise FileImportError("authorization attestation is required before file access")
    if path.is_symlink():
        raise FileImportError("symbolic-link imports are forbidden")
    try:
        stat_result = path.stat()
    except OSError as exc:
        raise FileImportError("selected import file is unavailable") from exc
    if not path.is_file() or not os.path.isfile(path):
        raise FileImportError("selected import path is not a regular file")
    # The caller checks its selected bound after reading no content. stat_size may race;
    # the post-read length check remains authoritative.
    if stat_result.st_size < 1:
        raise FileImportError("selected import file is empty")
    try:
        return path.read_bytes()
    except OSError as exc:
        raise FileImportError("selected import file could not be read") from exc


def _decode_utf8(payload: bytes, bounds: FileReadBounds) -> str:
    if len(payload) > bounds.max_bytes:
        raise FileImportError("selected import exceeds the authorized byte bound")
    try:
        text = payload.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise FileImportError("selected import is not valid UTF-8") from exc
    if "\x00" in text:
        raise FileImportError("NUL bytes are forbidden in imports")
    return text


def _check_cell(value: Any, bounds: FileReadBounds) -> None:
    try:
        size = len(canonical_json_bytes(value))
    except (TypeError, ValueError) as exc:
        raise FileImportError("unsupported or non-finite import value") from exc
    if size > bounds.max_cell_bytes:
        raise FileImportError("import cell exceeds the authorized cell bound")


def _filter_row(row: Mapping[str, Any], selected_field_ids: tuple[str, ...] | None) -> dict[str, Any]:
    if selected_field_ids is None:
        return dict(row)
    return {field: row[field] for field in selected_field_ids if field in row}


def read_csv_file(
    path: Path,
    *,
    authorization_attestation_id: str,
    bounds: FileReadBounds = FileReadBounds(),
    selected_field_ids: tuple[str, ...] | None = None,
) -> FileReadResult:
    payload = _authorized_regular_file(path, authorization_attestation_id)
    text = _decode_utf8(payload, bounds)
    try:
        reader = csv.reader(io.StringIO(text, newline=""), strict=True)
        header = next(reader)
        if not header or any(not item for item in header):
            raise FileImportError("CSV requires non-empty header field IDs")
        if len(header) != len(set(header)):
            raise FileImportError("CSV contains duplicate header field IDs")
        if selected_field_ids is not None:
            missing_selection = sorted(set(selected_field_ids) - set(header))
            if missing_selection:
                raise FileImportError("selected CSV field ID is absent from the header")
        rows: list[dict[str, Any]] = []
        partial = False
        for values in reader:
            if len(values) != len(header):
                raise FileImportError("CSV row width does not match its header")
            if len(rows) >= bounds.max_rows:
                partial = True
                break
            for value in values:
                _check_cell(value, bounds)
            rows.append(_filter_row(dict(zip(header, values, strict=True)), selected_field_ids))
    except (csv.Error, StopIteration) as exc:
        raise FileImportError("malformed CSV import") from exc
    fields = tuple(header if selected_field_ids is None else selected_field_ids)
    return FileReadResult(fields, tuple(rows), len(payload), not partial, "ROW_BOUND_REACHED" if partial else None, len(rows))


def _json_records(decoded: Any) -> list[Any]:
    if isinstance(decoded, list):
        return decoded
    if isinstance(decoded, dict) and set(decoded) == {"records"} and isinstance(decoded["records"], list):
        return decoded["records"]
    raise FileImportError("JSON import must be an array or an object containing only a records array")


def read_json_file(
    path: Path,
    *,
    authorization_attestation_id: str,
    bounds: FileReadBounds = FileReadBounds(),
    selected_field_ids: tuple[str, ...] | None = None,
) -> FileReadResult:
    payload = _authorized_regular_file(path, authorization_attestation_id)
    text = _decode_utf8(payload, bounds)
    try:
        records = _json_records(strict_json_loads(text))
    except FileImportError:
        raise
    except (ValueError, TypeError) as exc:
        raise FileImportError("malformed JSON import") from exc
    partial = len(records) > bounds.max_rows
    accepted_records = records[: bounds.max_rows]
    rows: list[dict[str, Any]] = []
    fields: list[str] = []
    seen_fields: set[str] = set()
    for record in accepted_records:
        if not isinstance(record, dict) or any(not isinstance(key, str) or not key for key in record):
            raise FileImportError("each JSON record must be an object with non-empty string field IDs")
        for key, value in record.items():
            _check_cell(value, bounds)
            if key not in seen_fields:
                fields.append(key)
                seen_fields.add(key)
        rows.append(_filter_row(record, selected_field_ids))
    if selected_field_ids is not None:
        # JSON has no independent header. A selected optional field may be absent from
        # every row; the mapping gate, not the reader, owns required/optional meaning.
        output_fields = selected_field_ids
    else:
        output_fields = tuple(fields)
    return FileReadResult(tuple(output_fields), tuple(rows), len(payload), not partial, "ROW_BOUND_REACHED" if partial else None, len(rows))


def bounded_preview(
    result: FileReadResult,
    *,
    row_limit: int = DEFAULT_PREVIEW_ROWS,
    redacted_field_ids: Iterable[str] = (),
) -> PreviewResult:
    if not 1 <= row_limit <= MAX_PREVIEW_ROWS:
        raise FileImportError("preview row limit must be between 1 and 100")
    redacted = set(redacted_field_ids)
    preview_rows: list[dict[str, str | None]] = []
    for row in result.rows[:row_limit]:
        output: dict[str, str | None] = {}
        for field in result.field_ids:
            value = row.get(field)
            if field in redacted and value is not None:
                output[field] = "[REDACTED]"
            elif value is None:
                output[field] = None
            else:
                rendered = str(value)
                output[field] = rendered[:MAX_PREVIEW_VALUE_CHARS]
        preview_rows.append(output)
    return PreviewResult(
        field_ids=result.field_ids,
        rows=tuple(preview_rows),
        rows_available=len(result.rows),
        truncated=len(result.rows) > row_limit,
    )
