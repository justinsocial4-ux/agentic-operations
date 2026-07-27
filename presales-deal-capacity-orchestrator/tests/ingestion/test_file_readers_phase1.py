from __future__ import annotations

import json
from pathlib import Path

import pytest

from orchestrator.contracts.enums import SnapshotSemanticsV1
from orchestrator.ingestion.deletions import DeletionReconciliationError, reconcile_file_deletions
from orchestrator.ingestion.file_readers import (
    FileImportError,
    FileImportProofChecklist,
    FileReadBounds,
    bounded_preview,
    contract_tested_file_import_proof,
    read_csv_file,
    read_json_file,
)


def test_csv_json_readers_require_attestation_and_bound_preview(tmp_path: Path) -> None:
    csv_path = tmp_path / "records.csv"
    csv_path.write_text("id,private,note\n1,secret," + "x" * 250 + "\n", encoding="utf-8")
    with pytest.raises(FileImportError, match="attestation"):
        read_csv_file(csv_path, authorization_attestation_id="")
    result = read_csv_file(
        csv_path, authorization_attestation_id="att-fictional", selected_field_ids=("id", "private", "note")
    )
    preview = bounded_preview(result, row_limit=1, redacted_field_ids=("private",))
    assert preview.rows[0]["private"] == "[REDACTED]"
    assert len(preview.rows[0]["note"] or "") == 200

    json_path = tmp_path / "records.json"
    json_path.write_text(json.dumps([{"id": "1", "ignored": "not selected"}]), encoding="utf-8")
    parsed = read_json_file(
        json_path, authorization_attestation_id="att-fictional", selected_field_ids=("id",)
    )
    assert parsed.rows == ({"id": "1"},)


@pytest.mark.parametrize(
    "name,payload,reader",
    [
        ("bad.csv", 'a,b\n"unterminated,b\n', read_csv_file),
        ("width.csv", "a,b\n1\n", read_csv_file),
        ("duplicate.csv", "a,a\n1,2\n", read_csv_file),
        ("bad.json", "{not-json", read_json_file),
        ("duplicate.json", '[{"id":"1","id":"2"}]', read_json_file),
        ("shape.json", '{"records":[],"extra":true}', read_json_file),
    ],
)
def test_malformed_files_fail_closed(tmp_path: Path, name: str, payload: str, reader: object) -> None:
    path = tmp_path / name
    path.write_text(payload, encoding="utf-8")
    with pytest.raises(FileImportError):
        reader(path, authorization_attestation_id="att-fictional")  # type: ignore[operator]


def test_encoding_cell_row_and_file_bounds(tmp_path: Path) -> None:
    invalid = tmp_path / "invalid.csv"
    invalid.write_bytes(b"id\n\xff\n")
    with pytest.raises(FileImportError, match="UTF-8"):
        read_csv_file(invalid, authorization_attestation_id="att")

    oversized = tmp_path / "oversized.csv"
    oversized.write_text("id\n" + "x" * 20 + "\n", encoding="utf-8")
    with pytest.raises(FileImportError, match="cell"):
        read_csv_file(
            oversized, authorization_attestation_id="att",
            bounds=FileReadBounds(max_rows=2, max_bytes=100, max_cell_bytes=10),
        )

    rows = tmp_path / "rows.csv"
    rows.write_text("id\n1\n2\n", encoding="utf-8")
    partial = read_csv_file(
        rows, authorization_attestation_id="att",
        bounds=FileReadBounds(max_rows=1, max_bytes=100, max_cell_bytes=20),
    )
    assert not partial.complete and partial.stopped_reason == "ROW_BOUND_REACHED"


def test_full_snapshot_and_delta_deletion_semantics_are_explicit() -> None:
    with pytest.raises(DeletionReconciliationError, match="requires confirmation"):
        reconcile_file_deletions(
            snapshot_semantics=SnapshotSemanticsV1.FULL_SNAPSHOT,
            previous_source_record_ids=frozenset({"a", "b"}), current_source_record_ids=frozenset({"a"}),
        )
    full = reconcile_file_deletions(
        snapshot_semantics=SnapshotSemanticsV1.FULL_SNAPSHOT,
        previous_source_record_ids=frozenset({"a", "b"}), current_source_record_ids=frozenset({"a"}),
        confirmed_same_source_profile_population=True,
    )
    assert full.tombstoned_source_record_ids == ("b",)
    delta = reconcile_file_deletions(
        snapshot_semantics=SnapshotSemanticsV1.BOUNDED_DELTA,
        previous_source_record_ids=frozenset({"a", "b"}), current_source_record_ids=frozenset({"a"}),
    )
    assert delta.tombstoned_source_record_ids == ()


def test_file_import_proof_requires_every_contract_test_category() -> None:
    proof = contract_tested_file_import_proof()
    assert proof.implementation_proof == "FULLY_IMPLEMENTED_CONTRACT_TESTED"
    with pytest.raises(FileImportError, match="not earned"):
        FileImportProofChecklist(True, True, True, True, True, False).proof()
