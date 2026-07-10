#!/usr/bin/env python3
"""Deterministic helpers for mature-cohort MQL-to-SQL analysis."""

from __future__ import annotations

import math
import statistics
from collections import Counter


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


def summarize_funnel(total_mql: int, mature: int, converted: int, rejected: int,
                     unresolved: int, other: int = 0) -> dict:
    values = {k: _count(v, k) for k, v in {
        "total_mql": total_mql, "mature": mature, "converted": converted,
        "rejected": rejected, "unresolved": unresolved, "other": other,
    }.items()}
    if values["mature"] > values["total_mql"]:
        raise ValueError("mature cannot exceed total_mql")
    if values["converted"] + values["rejected"] + values["unresolved"] + values["other"] != values["mature"]:
        raise ValueError("mature outcomes must reconcile exactly")
    pending = values["total_mql"] - values["mature"]
    result = {**values, "pending_not_mature": pending}
    for key in ("converted", "rejected", "unresolved", "other"):
        result[f"{key}_rate"] = rate(values[key], values["mature"])
        result[f"{key}_wilson95"] = wilson_interval(values[key], values["mature"])
    result["status"] = "OK" if values["mature"] else "INSUFFICIENT_MATURE_COHORT"
    return result


def compare_rates(current_success: int, current_total: int,
                  prior_success: int, prior_total: int) -> dict:
    current = rate(current_success, current_total)
    prior = rate(prior_success, prior_total)
    if current is None or prior is None:
        return {"status": "INSUFFICIENT_MATURE_COHORT"}
    absolute = current - prior
    relative = None if prior == 0 else absolute / prior
    pooled = (current_success + prior_success) / (current_total + prior_total)
    se = math.sqrt(pooled * (1 - pooled) * (1 / current_total + 1 / prior_total))
    z = 0.0 if se == 0 and absolute == 0 else (math.inf if se == 0 else absolute / se)
    p_value = 0.0 if math.isinf(z) else math.erfc(abs(z) / math.sqrt(2))
    return {
        "status": "OK", "current_rate": current, "prior_rate": prior,
        "absolute_difference": absolute, "relative_difference": relative,
        "current_wilson95": wilson_interval(current_success, current_total),
        "prior_wilson95": wilson_interval(prior_success, prior_total),
        "z": z, "p_value_two_sided": p_value,
    }


def rejection_summary(reasons: list, total_rejections: int) -> dict:
    total_rejections = _count(total_rejections, "total_rejections")
    if len(reasons) > total_rejections:
        raise ValueError("captured reasons cannot exceed total rejections")
    cleaned = [str(r).strip() for r in reasons if r is not None and str(r).strip()]
    if len(cleaned) != len(reasons):
        raise ValueError("reasons must be non-empty captured values")
    counts = Counter(cleaned)
    captured = len(cleaned)
    rows = []
    for reason, count in sorted(counts.items(), key=lambda x: (-x[1], x[0])):
        rows.append({
            "reason": reason, "count": count,
            "share_all_rejections": rate(count, total_rejections),
            "share_captured_reasons": rate(count, captured),
        })
    return {
        "total_rejections": total_rejections, "captured_reasons": captured,
        "unknown_reason": total_rejections - captured,
        "capture_rate": rate(captured, total_rejections), "rows": rows,
    }


def velocity_summary(days_to_sql: list) -> dict:
    if not days_to_sql:
        return {"count": 0, "median_days": None, "p75_days": None}
    values = []
    for value in days_to_sql:
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
            raise ValueError("velocity values must be non-negative finite numbers")
        values.append(float(value))
    ordered = sorted(values)
    index = 0.75 * (len(ordered) - 1)
    lo, hi = math.floor(index), math.ceil(index)
    p75 = ordered[lo] if lo == hi else ordered[lo] + (ordered[hi] - ordered[lo]) * (index - lo)
    return {"count": len(ordered), "median_days": statistics.median(ordered), "p75_days": p75}
