#!/usr/bin/env python3
"""Deterministic helpers extracted from the frozen DQH-01 pilot."""

from __future__ import annotations

import argparse
import json
import math
import re
import unicodedata
from typing import Mapping


WEIGHTS = {"email": 0.35, "phone": 0.35, "name": 0.20, "company": 0.10}


def _signal(value: float, label: str) -> float:
    if not math.isfinite(value) or not 0 <= value <= 1:
        raise ValueError(f"{label} signal must be between 0 and 1")
    return value


def confidence_tier(score: float) -> str:
    if not math.isfinite(score) or not 0 <= score <= 100:
        raise ValueError("score must be between 0 and 100")
    if score >= 95:
        return "SAFE_AUTO_MERGE"
    if score >= 85:
        return "REVIEW_RECOMMENDED"
    if score >= 70:
        return "MANUAL_REVIEW"
    return "DO_NOT_MERGE"


def score_pair(*, email: float, phone: float, name: float, company: float) -> dict[str, object]:
    signals = {
        "email": _signal(email, "email"),
        "phone": _signal(phone, "phone"),
        "name": _signal(name, "name"),
        "company": _signal(company, "company"),
    }
    contributions = {key: round(signals[key] * WEIGHTS[key] * 100, 4) for key in WEIGHTS}
    score = round(sum(contributions.values()), 2)
    return {"score": score, "tier": confidence_tier(score), "contributions": contributions}


def normalize_name(value: str) -> str:
    folded = unicodedata.normalize("NFKD", value)
    return " ".join(re.sub(r"[^a-z0-9]+", " ", folded.encode("ascii", "ignore").decode().lower()).split())


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
    left = normalize_name(left)
    right = normalize_name(right)
    jaro = jaro_similarity(left, right)
    prefix = 0
    for a, b in zip(left, right):
        if a != b or prefix == 4:
            break
        prefix += 1
    return round(jaro + prefix * 0.1 * (1 - jaro), 6)


def metaphone(value: str) -> str:
    """Small deterministic classic-Metaphone implementation for pilot comparisons."""
    word = re.sub(r"[^A-Z]", "", normalize_name(value).upper())
    if not word:
        return ""
    for prefix, replacement in (("KN", "N"), ("GN", "N"), ("PN", "N"), ("AE", "E"), ("WR", "R"), ("WH", "W")):
        if word.startswith(prefix):
            word = replacement + word[2:]
            break
    if word.startswith("X"):
        word = "S" + word[1:]
    output: list[str] = []
    index = 0
    vowels = "AEIOU"
    while index < len(word):
        char = word[index]
        previous = word[index - 1] if index else ""
        following = word[index + 1] if index + 1 < len(word) else ""
        pair = word[index:index + 2]
        if char == previous and char != "C":
            index += 1
            continue
        if char in vowels:
            if index == 0:
                output.append(char)
        elif char in "BFPV":
            output.append("F" if char in "FV" else char)
        elif char in "DT":
            output.append("0" if pair == "TH" else "T")
        elif char == "C":
            output.append("X" if pair == "CH" or following in "IEY" else "K")
        elif char in "GJ":
            output.append("J" if char == "J" or following in "IEY" else "K")
        elif char == "H":
            if previous not in "CSPTG" and following in vowels:
                output.append("H")
        elif char in "KQ":
            output.append("K")
        elif char == "X":
            output.extend(("K", "S"))
        elif char == "Z":
            output.append("S")
        elif char not in "WY":
            output.append(char)
        index += 2 if pair in {"CH", "TH"} else 1
    return "".join(output)


def choose_master(record_a: Mapping[str, object], record_b: Mapping[str, object]) -> dict[str, str]:
    for field in ("verified_email", "verified_phone"):
        left = bool(record_a.get(field, False))
        right = bool(record_b.get(field, False))
        if left != right:
            return {"master": "A" if left else "B", "reason": field}
    activity_a = int(record_a.get("activities_90d", 0))
    activity_b = int(record_b.get("activities_90d", 0))
    if activity_a >= 10 and activity_b < 5:
        return {"master": "A", "reason": "activity_count"}
    if activity_b >= 10 and activity_a < 5:
        return {"master": "B", "reason": "activity_count"}
    created_a = float(record_a.get("created_epoch_days", 0))
    created_b = float(record_b.get("created_epoch_days", 0))
    if abs(created_a - created_b) >= 30:
        return {"master": "A" if created_a < created_b else "B", "reason": "creation_date"}
    complete_a = float(record_a.get("completeness", 0))
    complete_b = float(record_b.get("completeness", 0))
    if complete_a != complete_b:
        return {"master": "A" if complete_a > complete_b else "B", "reason": "completeness"}
    modified_a = float(record_a.get("modified_epoch", 0))
    modified_b = float(record_b.get("modified_epoch", 0))
    if modified_a != modified_b:
        return {"master": "A" if modified_a > modified_b else "B", "reason": "last_modified"}
    return {"master": "A", "reason": "stable_input_order"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    score = commands.add_parser("score")
    for name in WEIGHTS:
        score.add_argument(f"--{name}", type=float, required=True)
    names = commands.add_parser("names")
    names.add_argument("--left", required=True)
    names.add_argument("--right", required=True)
    master = commands.add_parser("master")
    master.add_argument("--record-a-json", required=True)
    master.add_argument("--record-b-json", required=True)
    args = parser.parse_args(argv)
    if args.command == "score":
        result: object = score_pair(email=args.email, phone=args.phone, name=args.name, company=args.company)
    elif args.command == "names":
        result = {"jaro_winkler": jaro_winkler(args.left, args.right), "left_metaphone": metaphone(args.left), "right_metaphone": metaphone(args.right)}
    else:
        result = choose_master(json.loads(args.record_a_json), json.loads(args.record_b_json))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
