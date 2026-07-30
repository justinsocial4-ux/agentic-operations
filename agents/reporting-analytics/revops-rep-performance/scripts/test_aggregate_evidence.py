#!/usr/bin/env python3
"""Adversarial tests for anonymous aggregate evidence review."""

from __future__ import annotations

import copy
import io
import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from aggregate_evidence import (  # noqa: E402
    EvidenceError,
    main,
    render_review_output,
    review_aggregate_evidence,
)


def fixture() -> dict:
    return {
        "review_id": "review-ra05",
        "policy": {
            "policy_id": "policy-ra05",
            "version": "v1.0",
            "policy_authority_id": "authority-a",
            "human_reviewer_id": "reviewer-a",
            "privacy_approval_id": "privacy-approval-a",
            "workforce_approval_id": "workforce-approval-a",
            "notice_receipt_id": "notice-receipt-a",
            "approved_purpose": "anonymous_aggregate_descriptive_review",
            "approved_cohort_dimension": "team-cohort",
            "allowed_metric_codes": ["calls_logged", "active_pipeline_amount"],
            "allowed_aggregation_rule_ids": ["aggregation-calls-v1", "aggregation-pipeline-v1"],
            "minimum_group_size": 5,
            "cutoff_at": "2026-07-11T12:00:00Z",
            "effective_from": "2026-07-01T00:00:00Z",
            "effective_to": "2026-07-31T23:59:59Z",
            "authorized_recipient_ids": ["recipient-a"],
            "retention_rule_id": "retention-a",
            "correction_path_id": "correction-a",
            "prohibited_uses": [
                "causal_or_predictive_claim",
                "coaching_recommendation",
                "compensation_action",
                "crm_write",
                "customer_action",
                "employment_action",
                "individual_worker_analysis",
                "message_or_alert",
                "quota_action",
                "territory_action",
                "worker_ranking",
                "worker_scoring",
            ],
        },
        "declared_source_ids": ["source-a"],
        "sources": [
            {
                "source_id": "source-a",
                "system_code": "approved-export",
                "schema_version": "schema-v1",
                "authorization_id": "authorization-a",
                "population_receipt_id": "population-a",
                "observed_at": "2026-07-11T10:00:00Z",
                "captured_at": "2026-07-11T11:00:00Z",
                "declared_cell_ids": ["cell-a1", "cell-a2", "cell-b1", "cell-b2", "cell-money"],
            }
        ],
        "declared_cohort_ids": ["cohort-a", "cohort-b"],
        "cohorts": [
            {
                "cohort_id": "cohort-a",
                "dimension_code": "team-cohort",
                "member_count": 12,
                "population_receipt_id": "cohort-population-a",
                "anonymity_receipt_id": "anonymity-a",
            },
            {
                "cohort_id": "cohort-b",
                "dimension_code": "team-cohort",
                "member_count": 2,
                "population_receipt_id": "cohort-population-b",
                "anonymity_receipt_id": "anonymity-b",
            },
        ],
        "declared_period_ids": ["period-previous", "period-current"],
        "periods": [
            {
                "period_id": "period-previous",
                "begin_at": "2026-06-23T00:00:00Z",
                "end_at": "2026-06-30T00:00:00Z",
            },
            {
                "period_id": "period-current",
                "begin_at": "2026-07-01T00:00:00Z",
                "end_at": "2026-07-08T00:00:00Z",
            },
        ],
        "declared_cell_ids": ["cell-a1", "cell-a2", "cell-b1", "cell-b2", "cell-money"],
        "cells": [
            {
                "cell_id": "cell-a1",
                "source_id": "source-a",
                "cohort_id": "cohort-a",
                "period_id": "period-previous",
                "metric_code": "calls_logged",
                "value": "10",
                "unit": "count",
                "currency": None,
                "amount_basis": None,
                "aggregation_rule_id": "aggregation-calls-v1",
            },
            {
                "cell_id": "cell-a2",
                "source_id": "source-a",
                "cohort_id": "cohort-a",
                "period_id": "period-current",
                "metric_code": "calls_logged",
                "value": "17",
                "unit": "count",
                "currency": None,
                "amount_basis": None,
                "aggregation_rule_id": "aggregation-calls-v1",
            },
            {
                "cell_id": "cell-b1",
                "source_id": "source-a",
                "cohort_id": "cohort-b",
                "period_id": "period-previous",
                "metric_code": "calls_logged",
                "value": "4",
                "unit": "count",
                "currency": None,
                "amount_basis": None,
                "aggregation_rule_id": "aggregation-calls-v1",
            },
            {
                "cell_id": "cell-b2",
                "source_id": "source-a",
                "cohort_id": "cohort-b",
                "period_id": "period-current",
                "metric_code": "calls_logged",
                "value": "9",
                "unit": "count",
                "currency": None,
                "amount_basis": None,
                "aggregation_rule_id": "aggregation-calls-v1",
            },
            {
                "cell_id": "cell-money",
                "source_id": "source-a",
                "cohort_id": "cohort-a",
                "period_id": "period-current",
                "metric_code": "active_pipeline_amount",
                "value": "100.25",
                "unit": "money",
                "currency": "USD",
                "amount_basis": "unweighted-booked-currency",
                "aggregation_rule_id": "aggregation-pipeline-v1",
            },
        ],
        "declared_comparison_ids": ["comparison-a", "comparison-b"],
        "comparisons": [
            {
                "comparison_id": "comparison-a",
                "current_cell_id": "cell-a2",
                "previous_cell_id": "cell-a1",
            },
            {
                "comparison_id": "comparison-b",
                "current_cell_id": "cell-b2",
                "previous_cell_id": "cell-b1",
            },
        ],
    }


class AggregateEvidenceTests(unittest.TestCase):
    def review(self, document: dict | None = None) -> dict:
        return review_aggregate_evidence(fixture() if document is None else document)

    def assert_rejected(self, document: dict) -> None:
        with self.assertRaises(EvidenceError):
            self.review(document)

    def test_happy_path_status(self):
        result = self.review()
        self.assertEqual(result["status"], "HUMAN_REVIEW_REQUIRED")
        self.assertFalse(result["action_boundary"]["action_authorized"])

    def test_reviewable_cell_value_is_preserved(self):
        result = self.review()
        cells = {row["cell_id"]: row for row in result["cell_receipts"]}
        self.assertEqual(cells["cell-money"]["value"], "100.25")

    def test_signed_delta_is_exact(self):
        result = self.review()
        comparisons = {row["comparison_id"]: row for row in result["comparison_receipts"]}
        self.assertEqual(comparisons["comparison-a"]["signed_delta"], "7")

    def test_small_cohort_is_suppressed(self):
        result = self.review()
        cohorts = {row["cohort_id"]: row for row in result["cohort_receipts"]}
        self.assertEqual(cohorts["cohort-b"]["status"], "SUPPRESSED")

    def test_suppressed_cells_emit_no_values(self):
        result = self.review()
        suppressed = [row for row in result["cell_receipts"] if row["cohort_id"] == "cohort-b"]
        self.assertTrue(suppressed)
        self.assertTrue(all("value" not in row for row in suppressed))

    def test_suppressed_comparison_emits_no_delta(self):
        result = self.review()
        row = next(item for item in result["comparison_receipts"] if item["comparison_id"] == "comparison-b")
        self.assertEqual(row["status"], "SUPPRESSED")
        self.assertNotIn("signed_delta", row)

    def test_renderer_is_exact_json_with_newline(self):
        rendered = render_review_output(self.review())
        self.assertTrue(rendered.startswith("{"))
        self.assertTrue(rendered.endswith("}\n"))
        self.assertEqual(rendered, json.dumps(json.loads(rendered), sort_keys=True, separators=(",", ":")) + "\n")

    def test_renderer_has_no_markdown(self):
        rendered = render_review_output(self.review())
        self.assertNotIn("```", rendered)
        self.assertNotIn("# ", rendered)

    def test_unsuppressed_input_value_occurs_once(self):
        rendered = render_review_output(self.review())
        self.assertEqual(rendered.count('"value":"100.25"'), 1)

    def test_delta_occurs_once(self):
        rendered = render_review_output(self.review())
        self.assertEqual(rendered.count('"signed_delta":"7"'), 1)

    def test_input_order_does_not_change_output(self):
        first = fixture()
        second = fixture()
        for key in ("sources", "cohorts", "periods", "cells", "comparisons"):
            second[key].reverse()
        self.assertEqual(render_review_output(self.review(first)), render_review_output(self.review(second)))

    def test_unknown_top_level_key_fails(self):
        document = fixture()
        document["extra"] = "x"
        self.assert_rejected(document)

    def test_missing_top_level_key_fails(self):
        document = fixture()
        del document["comparisons"]
        self.assert_rejected(document)

    def test_declared_source_population_mismatch_fails(self):
        document = fixture()
        document["declared_source_ids"] = ["source-other"]
        self.assert_rejected(document)

    def test_declared_cohort_population_mismatch_fails(self):
        document = fixture()
        document["declared_cohort_ids"].append("cohort-extra")
        self.assert_rejected(document)

    def test_declared_period_population_mismatch_fails(self):
        document = fixture()
        document["declared_period_ids"].pop()
        self.assert_rejected(document)

    def test_declared_cell_population_mismatch_fails(self):
        document = fixture()
        document["declared_cell_ids"].pop()
        self.assert_rejected(document)

    def test_declared_comparison_population_mismatch_fails(self):
        document = fixture()
        document["declared_comparison_ids"] = []
        self.assert_rejected(document)

    def test_duplicate_declared_id_fails(self):
        document = fixture()
        document["declared_cell_ids"].append("cell-a1")
        self.assert_rejected(document)

    def test_duplicate_record_fails(self):
        document = fixture()
        document["cells"].append(copy.deepcopy(document["cells"][0]))
        self.assert_rejected(document)

    def test_invalid_review_identifier_fails(self):
        document = fixture()
        document["review_id"] = "bad value"
        self.assert_rejected(document)

    def test_wrong_purpose_fails(self):
        document = fixture()
        document["policy"]["approved_purpose"] = "worker_scorecard"
        self.assert_rejected(document)

    def test_policy_not_yet_effective_fails(self):
        document = fixture()
        document["policy"]["effective_from"] = "2026-07-12T00:00:00Z"
        self.assert_rejected(document)

    def test_expired_policy_fails(self):
        document = fixture()
        document["policy"]["effective_to"] = "2026-07-10T00:00:00Z"
        self.assert_rejected(document)

    def test_naive_policy_timestamp_fails(self):
        document = fixture()
        document["policy"]["cutoff_at"] = "2026-07-11T12:00:00"
        self.assert_rejected(document)

    def test_zero_minimum_group_fails(self):
        document = fixture()
        document["policy"]["minimum_group_size"] = 0
        self.assert_rejected(document)

    def test_boolean_minimum_group_fails(self):
        document = fixture()
        document["policy"]["minimum_group_size"] = True
        self.assert_rejected(document)

    def test_unsupported_allowed_metric_fails(self):
        document = fixture()
        document["policy"]["allowed_metric_codes"].append("worker_score")
        self.assert_rejected(document)

    def test_duplicate_allowed_metric_fails(self):
        document = fixture()
        document["policy"]["allowed_metric_codes"].append("calls_logged")
        self.assert_rejected(document)

    def test_unapproved_aggregation_rule_fails(self):
        document = fixture()
        document["cells"][0]["aggregation_rule_id"] = "aggregation-unapproved"
        self.assert_rejected(document)

    def test_duplicate_aggregation_rule_fails(self):
        document = fixture()
        document["policy"]["allowed_aggregation_rule_ids"].append("aggregation-calls-v1")
        self.assert_rejected(document)

    def test_missing_privacy_approval_fails(self):
        document = fixture()
        del document["policy"]["privacy_approval_id"]
        self.assert_rejected(document)

    def test_missing_workforce_approval_fails(self):
        document = fixture()
        del document["policy"]["workforce_approval_id"]
        self.assert_rejected(document)

    def test_missing_notice_receipt_fails(self):
        document = fixture()
        del document["policy"]["notice_receipt_id"]
        self.assert_rejected(document)

    def test_missing_prohibited_use_fails(self):
        document = fixture()
        document["policy"]["prohibited_uses"].pop()
        self.assert_rejected(document)

    def test_extra_prohibited_use_fails(self):
        document = fixture()
        document["policy"]["prohibited_uses"].append("extra-use")
        self.assert_rejected(document)

    def test_wrong_cohort_dimension_fails(self):
        document = fixture()
        document["cohorts"][0]["dimension_code"] = "region-cohort"
        self.assert_rejected(document)

    def test_zero_member_count_fails(self):
        document = fixture()
        document["cohorts"][0]["member_count"] = 0
        self.assert_rejected(document)

    def test_missing_anonymity_receipt_fails(self):
        document = fixture()
        del document["cohorts"][0]["anonymity_receipt_id"]
        self.assert_rejected(document)

    def test_source_observed_after_capture_fails(self):
        document = fixture()
        document["sources"][0]["observed_at"] = "2026-07-11T11:30:00Z"
        self.assert_rejected(document)

    def test_source_capture_after_cutoff_fails(self):
        document = fixture()
        document["sources"][0]["captured_at"] = "2026-07-11T12:30:00Z"
        self.assert_rejected(document)

    def test_source_observation_before_period_end_fails(self):
        document = fixture()
        document["sources"][0]["observed_at"] = "2026-07-07T23:00:00Z"
        document["sources"][0]["captured_at"] = "2026-07-08T01:00:00Z"
        self.assert_rejected(document)

    def test_source_cell_population_mismatch_fails(self):
        document = fixture()
        document["sources"][0]["declared_cell_ids"].pop()
        self.assert_rejected(document)

    def test_period_end_after_cutoff_fails(self):
        document = fixture()
        document["periods"][1]["end_at"] = "2026-07-12T00:00:00Z"
        self.assert_rejected(document)

    def test_period_reversed_fails(self):
        document = fixture()
        document["periods"][1]["begin_at"] = "2026-07-09T00:00:00Z"
        self.assert_rejected(document)

    def test_unknown_source_reference_fails(self):
        document = fixture()
        document["cells"][0]["source_id"] = "source-missing"
        self.assert_rejected(document)

    def test_unknown_cohort_reference_fails(self):
        document = fixture()
        document["cells"][0]["cohort_id"] = "cohort-missing"
        self.assert_rejected(document)

    def test_unknown_period_reference_fails(self):
        document = fixture()
        document["cells"][0]["period_id"] = "period-missing"
        self.assert_rejected(document)

    def test_cell_metric_not_allowed_fails(self):
        document = fixture()
        document["cells"][0]["metric_code"] = "meetings_occurred"
        self.assert_rejected(document)

    def test_wrong_metric_unit_fails(self):
        document = fixture()
        document["cells"][0]["unit"] = "money"
        self.assert_rejected(document)

    def test_float_value_fails(self):
        document = fixture()
        document["cells"][0]["value"] = 10.0
        self.assert_rejected(document)

    def test_negative_value_fails(self):
        document = fixture()
        document["cells"][0]["value"] = "-1"
        self.assert_rejected(document)

    def test_fractional_count_fails(self):
        document = fixture()
        document["cells"][0]["value"] = "1.5"
        self.assert_rejected(document)

    def test_nonfinite_value_fails(self):
        document = fixture()
        document["cells"][0]["value"] = "NaN"
        self.assert_rejected(document)

    def test_whitespace_decimal_fails(self):
        document = fixture()
        document["cells"][0]["value"] = " 10"
        self.assert_rejected(document)

    def test_count_with_currency_fails(self):
        document = fixture()
        document["cells"][0]["currency"] = "USD"
        self.assert_rejected(document)

    def test_money_without_currency_fails(self):
        document = fixture()
        document["cells"][4]["currency"] = None
        self.assert_rejected(document)

    def test_money_without_amount_basis_fails(self):
        document = fixture()
        document["cells"][4]["amount_basis"] = None
        self.assert_rejected(document)

    def test_same_cell_comparison_fails(self):
        document = fixture()
        document["comparisons"][0]["previous_cell_id"] = "cell-a2"
        self.assert_rejected(document)

    def test_unknown_comparison_cell_fails(self):
        document = fixture()
        document["comparisons"][0]["current_cell_id"] = "cell-missing"
        self.assert_rejected(document)

    def test_mixed_cohort_comparison_fails(self):
        document = fixture()
        document["comparisons"][0]["previous_cell_id"] = "cell-b1"
        self.assert_rejected(document)

    def test_mixed_metric_comparison_fails(self):
        document = fixture()
        document["comparisons"][0]["current_cell_id"] = "cell-money"
        self.assert_rejected(document)

    def test_unequal_duration_comparison_fails(self):
        document = fixture()
        document["periods"][0]["begin_at"] = "2026-06-24T00:00:00Z"
        self.assert_rejected(document)

    def test_overlapping_periods_fail(self):
        document = fixture()
        document["periods"][0]["end_at"] = "2026-07-03T00:00:00Z"
        document["periods"][0]["begin_at"] = "2026-06-26T00:00:00Z"
        self.assert_rejected(document)

    def test_empty_comparison_population_is_allowed(self):
        document = fixture()
        document["declared_comparison_ids"] = []
        document["comparisons"] = []
        result = self.review(document)
        self.assertEqual(result["comparison_receipts"], [])

    def test_cli_stdin_success(self):
        stdin_before = sys.stdin
        try:
            sys.stdin = io.StringIO(json.dumps(fixture()))
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                code = main([])
        finally:
            sys.stdin = stdin_before
        self.assertEqual(code, 0)
        self.assertTrue(buffer.getvalue().endswith("}\n"))

    def test_cli_file_success(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "document.json"
            path.write_text(json.dumps(fixture()), encoding="utf-8")
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                code = main([str(path)])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(buffer.getvalue())["status"], "HUMAN_REVIEW_REQUIRED")

    def test_cli_invalid_json_fails(self):
        stdin_before = sys.stdin
        try:
            sys.stdin = io.StringIO("{")
            error = io.StringIO()
            with redirect_stderr(error):
                code = main([])
        finally:
            sys.stdin = stdin_before
        self.assertEqual(code, 1)
        self.assertIn("ERROR:", error.getvalue())

    def test_cli_too_many_arguments_fails(self):
        error = io.StringIO()
        with redirect_stderr(error):
            code = main(["one", "two"])
        self.assertEqual(code, 2)

    def test_subprocess_output_matches_library(self):
        completed = subprocess.run(
            [sys.executable, str(SCRIPT_DIR / "aggregate_evidence.py")],
            input=json.dumps(fixture()),
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(completed.stdout, render_review_output(self.review()))


def _add_forbidden_key_test(key: str, index: int) -> None:
    def test(self: AggregateEvidenceTests) -> None:
        document = fixture()
        document[key] = "opaque-value"
        self.assert_rejected(document)

    setattr(AggregateEvidenceTests, f"test_forbidden_key_{index:02d}_{key}", test)


for _index, _key in enumerate(
    [
        "rep_id",
        "worker_id",
        "employee_code",
        "first_name",
        "email_address",
        "phone",
        "job_title",
        "quota",
        "attainment",
        "salary",
        "performance_score",
        "health_status",
        "leave_status",
        "protected_trait",
        "recording_url",
        "transcript_text",
    ],
    1,
):
    _add_forbidden_key_test(_key, _index)


if __name__ == "__main__":
    unittest.main(verbosity=2)
