#!/usr/bin/env python3
"""Deterministic outbound rate, comparison, and subject-similarity helpers."""

from __future__ import annotations

import math
import re
import unicodedata
from collections import Counter
from typing import Iterable


def _counts(successes: int, total: int) -> None:
    if not isinstance(successes, int) or isinstance(successes, bool) or not isinstance(total, int) or isinstance(total, bool):
        raise ValueError("successes and total must be integers")
    if successes < 0 or total < 0 or successes > total:
        raise ValueError("counts must satisfy 0 <= successes <= total")


def rate_summary(successes: int, total: int, z: float = 1.96) -> dict[str, object]:
    _counts(successes, total)
    if not math.isfinite(z) or z <= 0:
        raise ValueError("z must be a positive finite number")
    if total == 0:
        return {"successes": successes, "total": total, "rate": None, "wilson_low": None, "wilson_high": None}
    p = successes / total
    denominator = 1 + z * z / total
    center = (p + z * z / (2 * total)) / denominator
    margin = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denominator
    return {
        "successes": successes,
        "total": total,
        "rate": round(p, 6),
        "wilson_low": round(max(0.0, center - margin), 6),
        "wilson_high": round(min(1.0, center + margin), 6),
    }


def compare_proportions(success_a: int, total_a: int, success_b: int, total_b: int) -> dict[str, object]:
    _counts(success_a, total_a)
    _counts(success_b, total_b)
    if total_a == 0 or total_b == 0:
        raise ValueError("both comparison denominators must be positive")
    rate_a = success_a / total_a
    rate_b = success_b / total_b
    pooled = (success_a + success_b) / (total_a + total_b)
    standard_error = math.sqrt(pooled * (1 - pooled) * (1 / total_a + 1 / total_b))
    if standard_error == 0:
        z_score = 0.0
        p_value = 1.0
    else:
        z_score = (rate_a - rate_b) / standard_error
        p_value = math.erfc(abs(z_score) / math.sqrt(2))
    return {
        "rate_a": round(rate_a, 6),
        "rate_b": round(rate_b, 6),
        "absolute_difference": round(rate_a - rate_b, 6),
        "relative_lift": None if rate_b == 0 else round((rate_a - rate_b) / rate_b, 6),
        "z_score": round(z_score, 6),
        "p_value_two_sided": round(p_value, 6),
    }


def benjamini_hochberg(p_values: Iterable[float]) -> list[float]:
    values = list(p_values)
    if any(not math.isfinite(value) or not 0 <= value <= 1 for value in values):
        raise ValueError("p-values must be finite numbers from 0 to 1")
    count = len(values)
    ordered = sorted(enumerate(values), key=lambda item: item[1])
    adjusted = [0.0] * count
    running = 1.0
    for reverse_index in range(count - 1, -1, -1):
        original_index, value = ordered[reverse_index]
        rank = reverse_index + 1
        running = min(running, value * count / rank)
        adjusted[original_index] = round(min(1.0, running), 6)
    return adjusted


def normalize_subject(value: str) -> str:
    folded = unicodedata.normalize("NFKD", value)
    ascii_value = folded.encode("ascii", "ignore").decode().lower()
    return " ".join(re.sub(r"[^a-z0-9\[\]]+", " ", ascii_value).split())


def _jaro(left: str, right: str) -> float:
    if left == right:
        return 1.0
    if not left or not right:
        return 0.0
    distance = max(0, max(len(left), len(right)) // 2 - 1)
    left_used = [False] * len(left)
    right_used = [False] * len(right)
    matches = 0
    for index, char in enumerate(left):
        for candidate in range(max(0, index - distance), min(len(right), index + distance + 1)):
            if right_used[candidate] or char != right[candidate]:
                continue
            left_used[index] = True
            right_used[candidate] = True
            matches += 1
            break
    if matches == 0:
        return 0.0
    left_chars = [left[index] for index, used in enumerate(left_used) if used]
    right_chars = [right[index] for index, used in enumerate(right_used) if used]
    transpositions = sum(a != b for a, b in zip(left_chars, right_chars, strict=True)) / 2
    return (matches / len(left) + matches / len(right) + (matches - transpositions) / matches) / 3


def jaro_winkler(left: str, right: str) -> float:
    left = normalize_subject(left)
    right = normalize_subject(right)
    score = _jaro(left, right)
    prefix = 0
    for a, b in zip(left, right):
        if a != b or prefix == 4:
            break
        prefix += 1
    return round(score + prefix * 0.1 * (1 - score), 6)


def cluster_subjects(subjects: Iterable[str], threshold: float = 0.90) -> list[dict[str, object]]:
    if not math.isfinite(threshold) or not 0 <= threshold <= 1:
        raise ValueError("threshold must be between 0 and 1")
    raw = list(subjects)
    normalized = [normalize_subject(value) for value in raw]
    unique = sorted(set(normalized))
    parent = {value: value for value in unique}

    def root(value: str) -> str:
        while parent[value] != value:
            parent[value] = parent[parent[value]]
            value = parent[value]
        return value

    for index, left in enumerate(unique):
        for right in unique[index + 1:]:
            if jaro_winkler(left, right) >= threshold:
                left_root, right_root = root(left), root(right)
                parent[right_root] = left_root

    grouped: dict[str, list[str]] = {}
    for value in unique:
        grouped.setdefault(root(value), []).append(value)
    counts = Counter(normalized)
    results = []
    for variants in grouped.values():
        canonical = sorted(variants, key=lambda value: (-counts[value], -len(value), value))[0]
        original_variants = sorted({value for value, normalized_value in zip(raw, normalized, strict=True) if normalized_value in variants})
        results.append({
            "canonical": canonical,
            "variants": sorted(variants),
            "original_variants": original_variants,
            "touches": sum(counts[value] for value in variants),
            "requires_review": len(original_variants) > 1,
        })
    return sorted(results, key=lambda item: str(item["canonical"]))
