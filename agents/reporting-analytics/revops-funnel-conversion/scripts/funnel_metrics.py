#!/usr/bin/env python3
"""Deterministic metrics for customer-defined funnel conversion analysis."""

from __future__ import annotations

import math
import statistics
import json


def _count(value: int, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")
    return value


def rate(numerator: int, denominator: int):
    numerator = _count(numerator, "numerator")
    denominator = _count(denominator, "denominator")
    if numerator > denominator:
        raise ValueError("numerator cannot exceed denominator")
    return None if denominator == 0 else numerator / denominator


def wilson_interval(successes: int, total: int, z: float = 1.959963984540054):
    p = rate(successes, total)
    if p is None:
        return None
    if not math.isfinite(z) or z <= 0:
        raise ValueError("z must be positive and finite")
    denom = 1 + z * z / total
    center = (p + z * z / (2 * total)) / denom
    half = z * math.sqrt((p * (1 - p) + z * z / (4 * total)) / total) / denom
    return (center - half, center + half)


def transition_summary(entered: int, mature: int, advanced: int) -> dict:
    entered = _count(entered, "entered")
    mature = _count(mature, "mature")
    advanced = _count(advanced, "advanced")
    if mature > entered:
        raise ValueError("mature cannot exceed entered")
    if advanced > mature:
        raise ValueError("advanced cannot exceed mature")
    value = rate(advanced, mature)
    return {
        "entered": entered,
        "mature": mature,
        "advanced": advanced,
        "pending_not_mature": entered - mature,
        "not_advanced_by_deadline": mature - advanced,
        "conversion_rate": value,
        "wilson95": wilson_interval(advanced, mature),
        "status": "OK" if mature else "INSUFFICIENT_MATURE_COHORT",
    }


def validate_ordered_reach(stage_counts: list) -> bool:
    if not stage_counts:
        raise ValueError("stage_counts cannot be empty")
    checked = [_count(v, "stage_count") for v in stage_counts]
    if any(later > earlier for earlier, later in zip(checked, checked[1:])):
        raise ValueError("ordered reach counts must be non-increasing")
    return True


def compare_rates(current_success: int, current_total: int,
                  baseline_success: int, baseline_total: int) -> dict:
    current = rate(current_success, current_total)
    baseline = rate(baseline_success, baseline_total)
    if current is None or baseline is None:
        return {"status": "INSUFFICIENT_MATURE_COHORT"}
    absolute = current - baseline
    relative = None if baseline == 0 else absolute / baseline
    pooled = (current_success + baseline_success) / (current_total + baseline_total)
    se = math.sqrt(pooled * (1 - pooled) * (1 / current_total + 1 / baseline_total))
    z = 0.0 if se == 0 and absolute == 0 else (math.inf if se == 0 else absolute / se)
    p_value = 0.0 if math.isinf(z) else math.erfc(abs(z) / math.sqrt(2))
    return {
        "status": "OK",
        "current_rate": current,
        "baseline_rate": baseline,
        "absolute_difference": absolute,
        "relative_difference": relative,
        "current_wilson95": wilson_interval(current_success, current_total),
        "baseline_wilson95": wilson_interval(baseline_success, baseline_total),
        "z": z,
        "p_value_two_sided": p_value,
    }


def distribution_summary(values: list) -> dict:
    if not values:
        return {"count": 0, "median": None, "p75": None, "p90": None}
    checked = []
    for value in values:
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
            raise ValueError("distribution values must be non-negative finite numbers")
        checked.append(float(value))
    ordered = sorted(checked)

    def percentile(q: float) -> float:
        index = q * (len(ordered) - 1)
        lo, hi = math.floor(index), math.ceil(index)
        return ordered[lo] if lo == hi else ordered[lo] + (ordered[hi] - ordered[lo]) * (index - lo)

    return {
        "count": len(ordered),
        "median": statistics.median(ordered),
        "p75": percentile(0.75),
        "p90": percentile(0.90),
    }


def target_comparison(observed_rate, target_rate):
    for value, name in ((observed_rate, "observed_rate"), (target_rate, "target_rate")):
        if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value) or not 0 <= value <= 1:
            raise ValueError(f"{name} must be finite and within 0..1")
    return {
        "observed_rate": observed_rate,
        "target_rate": target_rate,
        "difference_percentage_points": (observed_rate - target_rate) * 100,
    }


def _text(value, name):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value.strip()


def _ratio_text(value):
    return None if value is None else format(value, ".6f")


def build_funnel_report(*, report_id, policy_id, cutoff, stages, reach_counts, transition_rows):
    """Build one exact, read-only report for the supplied ordered funnel evidence."""
    report_id = _text(report_id, "report_id")
    policy_id = _text(policy_id, "policy_id")
    cutoff = _text(cutoff, "cutoff")
    if not isinstance(stages, list) or len(stages) < 2:
        raise ValueError("stages must contain at least two ordered names")
    stages = [_text(value, "stage") for value in stages]
    if len(stages) != len(set(stages)):
        raise ValueError("stages must be unique")
    if not isinstance(reach_counts, list) or len(reach_counts) != len(stages):
        raise ValueError("reach_counts must align exactly with stages")
    reach_counts = [_count(value, "reach_count") for value in reach_counts]
    validate_ordered_reach(reach_counts)
    if not isinstance(transition_rows, list) or len(transition_rows) != len(stages) - 1:
        raise ValueError("transition_rows must cover every adjacent stage pair")

    reach = []
    anchored = reach_counts[0]
    for stage, count in zip(stages, reach_counts):
        reach.append({"stage": stage, "ordered_reach_count": count, "anchored_share": _ratio_text(rate(count, anchored))})

    transitions = []
    for index, row in enumerate(transition_rows):
        if not isinstance(row, dict):
            raise ValueError("each transition row must be an object")
        required = {"from_stage", "to_stage", "entered", "mature", "advanced"}
        if set(row) != required:
            raise ValueError("transition rows require only from_stage, to_stage, entered, mature, and advanced")
        from_stage = _text(row["from_stage"], "from_stage")
        to_stage = _text(row["to_stage"], "to_stage")
        if (from_stage, to_stage) != (stages[index], stages[index + 1]):
            raise ValueError("transition rows must match adjacent ordered stages")
        summary = transition_summary(row["entered"], row["mature"], row["advanced"])
        if summary["entered"] != reach_counts[index] or summary["advanced"] != reach_counts[index + 1]:
            raise ValueError("transition counts must reconcile to ordered reach")
        interval = summary["wilson95"]
        transitions.append({
            "from_stage": from_stage,
            "to_stage": to_stage,
            "entered_count_source": from_stage,
            "mature": summary["mature"],
            "advanced_count_source": to_stage,
            "pending_not_mature": summary["pending_not_mature"],
            "not_advanced_by_deadline": summary["not_advanced_by_deadline"],
            "conversion_rate": _ratio_text(summary["conversion_rate"]),
            "wilson95": None if interval is None else [_ratio_text(interval[0]), _ratio_text(interval[1])],
            "state": "NO_MATURE_EPISODES" if summary["mature"] == 0 else "OBSERVED",
        })

    observed = [row for row in transitions if row["conversion_rate"] is not None]
    minimum = None if not observed else min(observed, key=lambda row: (float(row["conversion_rate"]), row["from_stage"], row["to_stage"]))
    minimum_receipt = None if minimum is None else {
        "from_stage": minimum["from_stage"],
        "to_stage": minimum["to_stage"],
        "transition_value_source": "transitions",
        "interpretation": "OBSERVATION_ONLY",
        "bottleneck_state": "TARGET_NOT_APPROVED",
    }
    return {
        "report_id": report_id,
        "policy_id": policy_id,
        "cutoff": cutoff,
        "funnel_reach": reach,
        "transitions": transitions,
        "minimum_point_estimate": minimum_receipt,
        "end_to_end_conversion": {"state": "POLICY_REQUIRED", "reason_code": "END_TO_END_WINDOW_AND_MATURE_DENOMINATOR_REQUIRED"},
        "unavailable_analyses": [
            {"analysis": "bottleneck_verdict", "state": "TARGET_NOT_APPROVED"},
            {"analysis": "completed_dwell", "state": "DWELL_UNAVAILABLE"},
            {"analysis": "current_age", "state": "SOURCE_REQUIRED"},
            {"analysis": "period_or_segment_comparison", "state": "INCOMPARABLE_COHORTS"},
            {"analysis": "revenue_or_exposure", "state": "SOURCE_REQUIRED"},
        ],
        "human_review_questions": [
            "Approve an end-to-end observation window before evaluating a future independent cohort.",
            "Supply stage-entry and exit evidence for dwell or current-age review.",
            "Supply frozen dimensions and a comparable cohort before segment or period comparison.",
            "Approve any target and decision rule prospectively; do not apply it to this inspected cohort.",
        ],
        "validation": {
            "ordered_reach_non_increasing": True,
            "transition_rows_reconcile": True,
            "pending_excluded_from_denominators": True,
            "reach_counts_not_reprinted_in_transition_rows": True,
            "minimum_metric_not_reprinted": True,
            "cross_transition_interval_comparison_performed": False,
            "adequacy_label_applied": False,
            "external_write_performed": False,
        },
        "action_authorized": False,
        "boundary": "NO CRM / STAGE / ROUTING / SCORING / STAFFING / WORKFLOW ACTION",
    }


def render_funnel_json(report):
    if not isinstance(report, dict):
        raise ValueError("report must be an object")
    return json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)
