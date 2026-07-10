#!/usr/bin/env python3
"""Deterministic helpers for the frozen DQH-06 account-hierarchy pilot."""

from __future__ import annotations

import argparse
import json
import math
import re
from collections import defaultdict
from typing import Mapping


LEGAL_SUFFIXES = {
    "bv",
    "corp",
    "corporation",
    "gmbh",
    "inc",
    "incorporated",
    "kk",
    "limited",
    "llc",
    "ltd",
    "plc",
    "pty",
    "sa",
    "sas",
}

WEIGHTS = {
    "email": 0.30,
    "duns": 0.40,
    "name": 0.20,
    "domain": 0.15,
}


def normalize_name(value: str) -> str:
    tokens = re.sub(r"[^a-z0-9]+", " ", value.lower()).split()
    while tokens and tokens[-1] in LEGAL_SUFFIXES:
        tokens.pop()
    return " ".join(tokens)


def jaro_similarity(left: str, right: str) -> float:
    if left == right:
        return 1.0
    if not left or not right:
        return 0.0

    match_distance = max(len(left), len(right)) // 2 - 1
    match_distance = max(0, match_distance)
    left_matches = [False] * len(left)
    right_matches = [False] * len(right)

    matches = 0
    for left_index, char in enumerate(left):
        window_begin = max(0, left_index - match_distance)
        window_end = min(left_index + match_distance + 1, len(right))
        for right_index in range(window_begin, window_end):
            if right_matches[right_index] or char != right[right_index]:
                continue
            left_matches[left_index] = True
            right_matches[right_index] = True
            matches += 1
            break
    if matches == 0:
        return 0.0

    right_chars = [right[index] for index, matched in enumerate(right_matches) if matched]
    left_chars = [left[index] for index, matched in enumerate(left_matches) if matched]
    transpositions = sum(a != b for a, b in zip(left_chars, right_chars, strict=True)) / 2
    return (
        matches / len(left) + matches / len(right) + (matches - transpositions) / matches
    ) / 3


def jaro_winkler(left: str, right: str, scaling: float = 0.1) -> float:
    left = normalize_name(left)
    right = normalize_name(right)
    jaro = jaro_similarity(left, right)
    prefix = 0
    for a, b in zip(left, right):
        if a != b or prefix == 4:
            break
        prefix += 1
    return round(jaro + prefix * scaling * (1 - jaro), 6)


def company_name_signal(parent: str, child: str) -> dict[str, object]:
    normalized_parent = normalize_name(parent)
    normalized_child = normalize_name(child)
    if normalized_parent and normalized_parent in normalized_child:
        return {
            "signal": 0.95,
            "method": "parent_name_contained_in_child",
            "similarity": jaro_winkler(parent, child),
        }
    similarity = jaro_winkler(parent, child)
    return {
        "signal": similarity if similarity >= 0.85 else 0.0,
        "method": "jaro_winkler" if similarity >= 0.85 else "below_threshold",
        "similarity": similarity,
    }


def confidence_tier(score: float) -> str:
    if score >= 95:
        return "auto_link_pending_approval"
    if score >= 85:
        return "review_recommended"
    if score >= 70:
        return "manual_review_required"
    return "discard"


def _signal(value: float, label: str) -> float:
    if not math.isfinite(value) or not 0 <= value <= 1:
        raise ValueError(f"{label} must be between 0 and 1")
    return value


def confidence_score(
    *,
    email: float,
    duns: float,
    name: float,
    domain: float,
    false_positive_adjustment: float = 0.0,
    manual_override: bool = False,
) -> dict[str, object]:
    """Apply the literal non-renormalized pilot formula and cap display at 100."""
    if manual_override:
        return {
            "raw_score": 100.0,
            "score": 100.0,
            "tier": confidence_tier(100),
            "manual_override": True,
            "renormalized": False,
            "weight_total": sum(WEIGHTS.values()),
        }
    signals = {
        "email": _signal(email, "email"),
        "duns": _signal(duns, "duns"),
        "name": _signal(name, "name"),
        "domain": _signal(domain, "domain"),
    }
    if not math.isfinite(false_positive_adjustment) or false_positive_adjustment < 0:
        raise ValueError("false_positive_adjustment must be finite and nonnegative")
    raw_score = round(
        (sum(signals[key] * WEIGHTS[key] for key in WEIGHTS) - false_positive_adjustment) * 100,
        2,
    )
    score = round(min(100.0, max(0.0, raw_score)), 2)
    return {
        "raw_score": raw_score,
        "score": score,
        "tier": confidence_tier(score),
        "manual_override": False,
        "renormalized": False,
        "weight_total": sum(WEIGHTS.values()),
        "signals": signals,
    }


def check_cycle(
    parent_by_child: Mapping[str, str | None],
    child: str,
    proposed_parent: str,
    max_depth: int = 10,
) -> dict[str, object]:
    if max_depth < 1:
        raise ValueError("max_depth must be at least 1")
    links = dict(parent_by_child)
    links[child] = proposed_parent
    path = [child]
    current = child

    while True:
        parent = links.get(current)
        if parent is None:
            return {"circular": False, "depth": len(path) - 1, "path": path, "reason": "root_found"}
        if parent == current:
            return {"circular": True, "depth": len(path), "path": path + [parent], "reason": "self_reference"}
        if parent in path:
            return {"circular": True, "depth": len(path), "path": path + [parent], "reason": "loop_detected"}
        path.append(parent)
        if len(path) - 1 > max_depth:
            return {"circular": True, "depth": len(path) - 1, "path": path, "reason": "depth_exceeded"}
        current = parent


def _validate_existing_links(parent_by_child: Mapping[str, str | None], max_depth: int = 10) -> None:
    for child, parent in parent_by_child.items():
        if parent is None:
            continue
        result = check_cycle(parent_by_child, child, parent, max_depth=max_depth)
        if result["circular"]:
            raise ValueError(f"invalid hierarchy at {child}: {result['reason']}")


def build_forest(parent_by_child: Mapping[str, str | None], max_depth: int = 10) -> list[dict[str, object]]:
    _validate_existing_links(parent_by_child, max_depth=max_depth)
    nodes = set(parent_by_child)
    nodes.update(parent for parent in parent_by_child.values() if parent is not None)
    children: dict[str, list[str]] = defaultdict(list)
    for child, parent in parent_by_child.items():
        if parent is not None:
            children[parent].append(child)
    roots = sorted(node for node in nodes if parent_by_child.get(node) is None)

    def branch(node: str) -> dict[str, object]:
        return {"account": node, "children": [branch(child) for child in sorted(children[node])]}

    return [branch(root) for root in roots]


def _links(value: str) -> dict[str, str | None]:
    parsed = json.loads(value)
    if not isinstance(parsed, dict) or any(
        not isinstance(key, str) or (parent is not None and not isinstance(parent, str))
        for key, parent in parsed.items()
    ):
        raise ValueError("links JSON must be an object of child to parent-or-null")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    name = commands.add_parser("name", help="calculate the pilot company-name signal")
    name.add_argument("--parent", required=True)
    name.add_argument("--child", required=True)

    score = commands.add_parser("score", help="apply the literal pilot confidence formula")
    for signal in WEIGHTS:
        score.add_argument(f"--{signal}", type=float, required=True)
    score.add_argument("--false-positive-adjustment", type=float, default=0.0)
    score.add_argument("--manual-override", action="store_true")

    cycle = commands.add_parser("cycle", help="check a proposed link for a loop or excess depth")
    cycle.add_argument("--links-json", required=True)
    cycle.add_argument("--child", required=True)
    cycle.add_argument("--parent", required=True)
    cycle.add_argument("--max-depth", type=int, default=10)

    tree = commands.add_parser("tree", help="build a stable hierarchy forest from child-parent links")
    tree.add_argument("--links-json", required=True)
    tree.add_argument("--max-depth", type=int, default=10)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "name":
        result: object = company_name_signal(args.parent, args.child)
    elif args.command == "score":
        result = confidence_score(
            email=args.email,
            duns=args.duns,
            name=args.name,
            domain=args.domain,
            false_positive_adjustment=args.false_positive_adjustment,
            manual_override=args.manual_override,
        )
    elif args.command == "cycle":
        result = check_cycle(_links(args.links_json), args.child, args.parent, args.max_depth)
    else:
        result = build_forest(_links(args.links_json), args.max_depth)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
