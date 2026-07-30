#!/usr/bin/env python3
"""Deterministic helpers extracted from the frozen DQH-02 pilot."""

from __future__ import annotations

import argparse
import json
import math
import re
import unicodedata
from typing import Iterable, Mapping


def normalize_text(value: str) -> str:
    folded = unicodedata.normalize("NFKD", value)
    ascii_value = folded.encode("ascii", "ignore").decode().lower()
    return " ".join(re.sub(r"[^a-z0-9]+", " ", ascii_value).split())


def jaro_similarity(left: str, right: str) -> float:
    if left == right:
        return 1.0
    if not left or not right:
        return 0.0
    distance = max(0, max(len(left), len(right)) // 2 - 1)
    left_used = [False] * len(left)
    right_used = [False] * len(right)
    matches = 0
    for left_index, char in enumerate(left):
        for right_index in range(max(0, left_index - distance), min(len(right), left_index + distance + 1)):
            if right_used[right_index] or char != right[right_index]:
                continue
            left_used[left_index] = True
            right_used[right_index] = True
            matches += 1
            break
    if not matches:
        return 0.0
    left_chars = [left[index] for index, used in enumerate(left_used) if used]
    right_chars = [right[index] for index, used in enumerate(right_used) if used]
    transpositions = sum(a != b for a, b in zip(left_chars, right_chars, strict=True)) / 2
    return (matches / len(left) + matches / len(right) + (matches - transpositions) / matches) / 3


def jaro_winkler(left: str, right: str) -> float:
    left = normalize_text(left)
    right = normalize_text(right)
    jaro = jaro_similarity(left, right)
    prefix = 0
    for a, b in zip(left, right):
        if a != b or prefix == 4:
            break
        prefix += 1
    return round(jaro + prefix * 0.1 * (1 - jaro), 6)


def confidence_tier(confidence: float) -> str:
    if not math.isfinite(confidence) or not 0 <= confidence <= 1:
        raise ValueError("confidence must be between 0 and 1")
    if confidence >= 0.90:
        return "HIGH"
    if confidence >= 0.80:
        return "MEDIUM"
    if confidence >= 0.70:
        return "LOW"
    return "REJECT"


def score_mapping(
    *,
    similarity: float,
    company_context: bool = False,
    frequency: int = 0,
    user_threshold: float = 0.85,
) -> dict[str, object]:
    if not math.isfinite(similarity) or not 0 <= similarity <= 1:
        raise ValueError("similarity must be between 0 and 1")
    if not 0 <= user_threshold <= 1:
        raise ValueError("user threshold must be between 0 and 1")
    if frequency < 0:
        raise ValueError("frequency must be nonnegative")
    base = similarity if similarity >= 0.75 else 0.0
    context_boost = 0.05 if company_context else 0.0
    frequency_boost = 0.05 if frequency >= 100 else 0.0
    confidence = round(min(1.0, base + context_boost + frequency_boost), 2)
    return {
        "confidence": confidence,
        "tier": confidence_tier(confidence),
        "eligible_for_apply": confidence >= user_threshold,
        "auto_map": confidence >= 0.90 and confidence >= user_threshold,
        "components": {
            "base_similarity": base,
            "company_context_boost": context_boost,
            "frequency_boost": frequency_boost,
        },
    }


def bulk_plan(records: Iterable[Mapping[str, object]], user_threshold: float = 0.85) -> dict[str, object]:
    updates: list[dict[str, object]] = []
    skipped: list[dict[str, object]] = []
    for record in records:
        confidence = float(record["confidence"])
        output = dict(record)
        if confidence >= user_threshold:
            output["audit_fields"] = {
                "original_value": record.get("original_value"),
                "normalization_status": "Normalized",
                "confidence_score": confidence,
            }
            updates.append(output)
        else:
            skipped.append(output)
    return {"updates": updates, "skipped": skipped, "requires_explicit_approval": True}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--similarity", type=float, required=True)
    parser.add_argument("--company-context", action="store_true")
    parser.add_argument("--frequency", type=int, default=0)
    parser.add_argument("--user-threshold", type=float, default=0.85)
    args = parser.parse_args(argv)
    result = score_mapping(
        similarity=args.similarity,
        company_context=args.company_context,
        frequency=args.frequency,
        user_threshold=args.user_threshold,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
