#!/usr/bin/env python3
"""Deterministic matching helpers for LM-02."""

from __future__ import annotations

import argparse
import json
import math
import re
from typing import Iterable, Mapping


WEIGHTS = {
    "name_similarity": 0.40,
    "domain_match": 0.30,
    "employee_count_match": 0.15,
    "location_match": 0.10,
    "phonetic_match": 0.05,
}

LEGAL_SUFFIXES = {
    "bv",
    "corp",
    "corporation",
    "gmbh",
    "inc",
    "incorporated",
    "llc",
    "limited",
    "ltd",
    "plc",
    "sa",
    "sas",
}


def normalize_company(value: str) -> str:
    tokens = re.sub(r"[^a-z0-9]+", " ", value.lower()).split()
    while tokens and tokens[-1] in LEGAL_SUFFIXES:
        tokens.pop()
    return " ".join(tokens)


def normalize_domain(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"^[a-z]+://", "", value)
    value = value.split("/", 1)[0].split(":", 1)[0]
    return value[4:] if value.startswith("www.") else value


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
        window_begin = max(0, left_index - distance)
        window_end = min(len(right), left_index + distance + 1)
        for right_index in range(window_begin, window_end):
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
    return (
        matches / len(left) + matches / len(right) + (matches - transpositions) / matches
    ) / 3


def jaro_winkler(left: str, right: str) -> float:
    left = normalize_company(left)
    right = normalize_company(right)
    jaro = jaro_similarity(left, right)
    prefix = 0
    for a, b in zip(left, right):
        if a != b or prefix == 4:
            break
        prefix += 1
    return round(jaro + prefix * 0.1 * (1 - jaro), 6)


def soundex(value: str) -> str:
    letters = re.sub(r"[^A-Z]", "", normalize_company(value).upper())
    if not letters:
        return "0000"
    groups = {
        **dict.fromkeys("BFPV", "1"),
        **dict.fromkeys("CGJKQSXZ", "2"),
        **dict.fromkeys("DT", "3"),
        "L": "4",
        **dict.fromkeys("MN", "5"),
        "R": "6",
    }
    first = letters[0]
    previous = groups.get(first, "")
    digits: list[str] = []
    for char in letters[1:]:
        code = groups.get(char, "")
        if code and code != previous:
            digits.append(code)
        previous = code
    return (first + "".join(digits) + "000")[:4]


def employee_count_match(lead_count: float | None, account_count: float | None, tolerance: float = 0.25) -> float:
    if lead_count is None or account_count is None or lead_count <= 0 or account_count <= 0:
        return 0.0
    if not 0 <= tolerance <= 1:
        raise ValueError("tolerance must be between 0 and 1")
    return 1.0 if abs(account_count - lead_count) / lead_count <= tolerance else 0.0


def phonetic_match(lead_company: str, account_company: str) -> float:
    return 0.5 if soundex(lead_company) == soundex(account_company) else 0.0


def _component(value: float, label: str, maximum: float = 1.0) -> float:
    if not math.isfinite(value) or not 0 <= value <= maximum:
        raise ValueError(f"{label} must be between 0 and {maximum}")
    return value


def confidence_bucket(score: float, auto_threshold: float = 90, review_threshold: float = 75) -> str:
    if not 50 <= review_threshold < auto_threshold <= 100:
        raise ValueError("thresholds must satisfy 50 <= review < auto <= 100")
    if score >= auto_threshold:
        return "HIGH"
    if score >= review_threshold:
        return "MEDIUM"
    return "LOW"


def score_match(
    *,
    name_similarity: float,
    domain_match: float,
    employee_count_match: float,
    location_match: float,
    phonetic_match: float,
    auto_threshold: float = 90,
    review_threshold: float = 75,
) -> dict[str, object]:
    components = {
        "name_similarity": _component(name_similarity, "name_similarity"),
        "domain_match": _component(domain_match, "domain_match"),
        "employee_count_match": _component(employee_count_match, "employee_count_match"),
        "location_match": _component(location_match, "location_match"),
        "phonetic_match": _component(phonetic_match, "phonetic_match", 0.5),
    }
    contributions = {key: round(components[key] * WEIGHTS[key] * 100, 4) for key in WEIGHTS}
    score = round(sum(contributions.values()), 2)
    bucket = confidence_bucket(score, auto_threshold, review_threshold)
    action = {"HIGH": "AUTO_ASSOCIATE_AFTER_APPROVAL", "MEDIUM": "REVIEW_QUEUE", "LOW": "MANUAL_LOOKUP"}[bucket]
    return {
        "score": score,
        "bucket": bucket,
        "recommended_action": action,
        "components": components,
        "contributions": contributions,
    }


def rank_candidates(candidates: Iterable[Mapping[str, object]]) -> list[Mapping[str, object]]:
    """Sort scored candidates using the published tie-break order."""
    return sorted(
        candidates,
        key=lambda item: (
            -float(item["score"]),
            -int(bool(item.get("exact_name_match"))),
            -int(bool(item.get("domain_match"))),
            float(item.get("employee_count_delta", math.inf)),
            str(item.get("account_id", "")),
        ),
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    name = commands.add_parser("name", help="calculate Jaro-Winkler and Soundex")
    name.add_argument("--lead", required=True)
    name.add_argument("--account", required=True)

    score = commands.add_parser("score", help="calculate the exact composite score and bucket")
    for field in WEIGHTS:
        score.add_argument(f"--{field.replace('_', '-')}", type=float, required=True)
    score.add_argument("--auto-threshold", type=float, default=90)
    score.add_argument("--review-threshold", type=float, default=75)

    rank = commands.add_parser("rank", help="rank a JSON list of already-scored candidates")
    rank.add_argument("--candidates-json", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "name":
        result: object = {
            "lead_normalized": normalize_company(args.lead),
            "account_normalized": normalize_company(args.account),
            "jaro_winkler": jaro_winkler(args.lead, args.account),
            "lead_soundex": soundex(args.lead),
            "account_soundex": soundex(args.account),
            "phonetic_match": phonetic_match(args.lead, args.account),
        }
    elif args.command == "score":
        result = score_match(
            name_similarity=args.name_similarity,
            domain_match=args.domain_match,
            employee_count_match=args.employee_count_match,
            location_match=args.location_match,
            phonetic_match=args.phonetic_match,
            auto_threshold=args.auto_threshold,
            review_threshold=args.review_threshold,
        )
    else:
        parsed = json.loads(args.candidates_json)
        if not isinstance(parsed, list):
            raise ValueError("candidates JSON must be a list")
        result = rank_candidates(parsed)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
