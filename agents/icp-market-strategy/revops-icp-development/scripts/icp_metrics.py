#!/usr/bin/env python3
"""Exact descriptive metrics for ICP segment reviews."""

from decimal import Decimal
from math import isfinite, sqrt


def _count(value, name):
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")
    return value


def _positive_finite(value, name):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a positive finite number")
    value = float(value)
    if not isfinite(value) or value <= 0:
        raise ValueError(f"{name} must be a positive finite number")
    return value


def segment_metrics(won, lost, other=0, baseline_won=None, baseline_total=None, z=1.959963984540054):
    won, lost, other = _count(won, "won"), _count(lost, "lost"), _count(other, "other")
    z = _positive_finite(z, "z")
    rate_denominator = won + lost
    total = won + lost + other
    if rate_denominator == 0:
        return {
            "won": won,
            "lost": lost,
            "other": other,
            "total": total,
            "rate_denominator": 0,
            "win_rate": None,
            "difference_pp": None,
            "wilson": None,
        }
    rate = won / rate_denominator
    denominator = 1 + z * z / rate_denominator
    center = (rate + z * z / (2 * rate_denominator)) / denominator
    margin = z * sqrt(
        (rate * (1 - rate) + z * z / (4 * rate_denominator)) / rate_denominator
    ) / denominator
    difference = None
    if baseline_won is not None or baseline_total is not None:
        bw, bt = _count(baseline_won, "baseline_won"), _count(baseline_total, "baseline_total")
        if bt == 0 or bw > bt:
            raise ValueError("baseline counts are invalid")
        difference = (rate - bw / bt) * 100
    return {
        "won": won,
        "lost": lost,
        "other": other,
        "total": total,
        "rate_denominator": rate_denominator,
        "win_rate": rate,
        "difference_pp": difference,
        "wilson": (max(0.0, center - margin), min(1.0, center + margin)),
    }


def coverage(known, eligible):
    known, eligible = _count(known, "known"), _count(eligible, "eligible")
    if known > eligible: raise ValueError("coverage counts are invalid")
    return None if eligible == 0 else Decimal(known) / Decimal(eligible)
