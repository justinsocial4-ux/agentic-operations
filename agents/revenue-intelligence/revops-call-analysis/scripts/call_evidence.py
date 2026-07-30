#!/usr/bin/env python3
"""Exact, fail-closed validation for timestamped call evidence."""

from collections import Counter
from decimal import Decimal


REQUIRED_POLICY_FIELDS = (
    "recording_policy_id",
    "analysis_use_policy_id",
    "requester_access_id",
    "redaction_policy_id",
    "retention_policy_id",
    "downstream_use_policy_id",
    "policy_owner",
)

REQUIRED_APPROVAL_FIELDS = (
    "recording_scope_status",
    "analysis_use_status",
    "requester_access_status",
    "redaction_scope_status",
    "retention_handling_status",
    "downstream_use_status",
)


def _nonempty_text(value, name):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value.strip()


def _milliseconds(value, name, allow_zero=True):
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name} must be an integer number of milliseconds")
    if value < 0 or (not allow_zero and value == 0):
        raise ValueError(f"{name} is outside the allowed range")
    return value


def policy_gate(policy):
    if not isinstance(policy, dict):
        raise ValueError("policy must be an object")
    missing = []
    for field in REQUIRED_POLICY_FIELDS:
        value = policy.get(field)
        if not isinstance(value, str) or not value.strip():
            missing.append(field)
    blocked = []
    for field in REQUIRED_APPROVAL_FIELDS:
        value = policy.get(field)
        if not isinstance(value, str) or not value.strip():
            missing.append(field)
        elif value != "APPROVED":
            blocked.append(field)
    if missing:
        status = "POLICY_EVIDENCE_REQUIRED"
    elif blocked:
        status = "POLICY_SCOPE_NOT_APPROVED"
    else:
        status = "POLICY_EVIDENCE_PRESENT"
    return {
        "status": status,
        "missing_fields": missing,
        "blocked_fields": blocked,
    }


def _union_length(intervals):
    if not intervals:
        return 0
    total = 0
    current_begin, current_end = sorted(intervals)[0]
    for begin, end in sorted(intervals)[1:]:
        if begin <= current_end:
            current_end = max(current_end, end)
        else:
            total += current_end - current_begin
            current_begin, current_end = begin, end
    return total + current_end - current_begin


def transcript_receipt(segments, call_duration_ms, approved_speaker_ids):
    duration = _milliseconds(call_duration_ms, "call_duration_ms", allow_zero=False)
    if not isinstance(segments, list):
        raise ValueError("segments must be a list")
    if not isinstance(approved_speaker_ids, (list, tuple, set)):
        raise ValueError("approved_speaker_ids must be a list, tuple, or set")
    approved = {_nonempty_text(item, "approved speaker ID") for item in approved_speaker_ids}

    seen, intervals, speaker_ms = set(), [], Counter()
    uncertain_ms = redacted_ms = 0
    allowed_statuses = {"verified", "uncertain", "redacted"}
    normalized = []
    for row in segments:
        if not isinstance(row, dict):
            raise ValueError("each segment must be an object")
        segment_id = _nonempty_text(row.get("segment_id"), "segment_id")
        if segment_id in seen:
            raise ValueError("segment IDs must be unique")
        speaker_id = _nonempty_text(row.get("speaker_id"), "speaker_id")
        begin = _milliseconds(row.get("start_ms"), "start_ms")
        end = _milliseconds(row.get("end_ms"), "end_ms")
        if begin >= end or end > duration:
            raise ValueError("segment timestamps must satisfy 0 <= start_ms < end_ms <= call_duration_ms")
        text = _nonempty_text(row.get("text"), "text")
        status = row.get("status")
        if status not in allowed_statuses:
            raise ValueError("segment status must be verified, uncertain, or redacted")
        span = end - begin
        if status == "uncertain":
            uncertain_ms += span
        elif status == "redacted":
            redacted_ms += span
        speaker_ms[speaker_id] += span
        intervals.append((begin, end))
        normalized.append({
            "segment_id": segment_id,
            "speaker_id": speaker_id,
            "start_ms": begin,
            "end_ms": end,
            "text": text,
            "status": status,
        })
        seen.add(segment_id)

    union_ms = _union_length(intervals)
    total_segment_ms = sum(end - begin for begin, end in intervals)
    overlap_ms = total_segment_ms - union_ms
    total_speaker_ms = sum(speaker_ms.values())
    unknown = sorted(speaker for speaker in speaker_ms if speaker not in approved)
    shares = {
        speaker: (None if total_speaker_ms == 0 else Decimal(milliseconds) / Decimal(total_speaker_ms))
        for speaker, milliseconds in sorted(speaker_ms.items())
    }
    return {
        "call_duration_ms": duration,
        "segment_count": len(normalized),
        "union_coverage_ms": union_ms,
        "coverage_ratio": Decimal(union_ms) / Decimal(duration),
        "uncovered_ms": duration - union_ms,
        "overlap_ms": overlap_ms,
        "uncertain_segment_ms": uncertain_ms,
        "redacted_segment_ms": redacted_ms,
        "speaker_ms": dict(sorted(speaker_ms.items())),
        "speaker_share_of_segment_time": shares,
        "unknown_speaker_ids": unknown,
        "speaker_status": "SPEAKER_MAPPING_REVIEW" if unknown else "SPEAKER_MAPPING_APPROVED",
        "segments": normalized,
    }


def annotation_receipt(annotations, segments, approved_category_ids):
    if not isinstance(annotations, list):
        raise ValueError("annotations must be a list")
    if not isinstance(segments, list):
        raise ValueError("segments must be a list")
    if not isinstance(approved_category_ids, (list, tuple, set)):
        raise ValueError("approved_category_ids must be a list, tuple, or set")
    approved = {_nonempty_text(item, "approved category ID") for item in approved_category_ids}
    segment_index = {}
    for segment in segments:
        if not isinstance(segment, dict):
            raise ValueError("each segment must be an object")
        segment_id = _nonempty_text(segment.get("segment_id"), "segment_id")
        if segment_id in segment_index:
            raise ValueError("segment IDs must be unique")
        segment_index[segment_id] = segment

    allowed_review = {"MODEL_CANDIDATE", "HUMAN_VERIFIED", "REJECTED"}
    seen, by_category, verified_by_category, by_review = set(), Counter(), Counter(), Counter()
    normalized = []
    for row in annotations:
        if not isinstance(row, dict):
            raise ValueError("each annotation must be an object")
        annotation_id = _nonempty_text(row.get("annotation_id"), "annotation_id")
        if annotation_id in seen:
            raise ValueError("annotation IDs must be unique")
        segment_id = _nonempty_text(row.get("segment_id"), "segment_id")
        if segment_id not in segment_index:
            raise ValueError("annotation segment_id does not exist")
        category_id = _nonempty_text(row.get("category_id"), "category_id")
        if category_id not in approved:
            raise ValueError("TAXONOMY_REQUIRED")
        speaker_id = _nonempty_text(row.get("speaker_id"), "speaker_id")
        if speaker_id != segment_index[segment_id].get("speaker_id"):
            raise ValueError("annotation speaker_id must match the segment")
        quote = _nonempty_text(row.get("quote"), "quote")
        segment_text = _nonempty_text(segment_index[segment_id].get("text"), "segment text")
        segment_status = segment_index[segment_id].get("status")
        if segment_status == "redacted":
            raise ValueError("redacted segments cannot support annotations")
        if quote not in segment_text:
            raise ValueError("annotation quote must be an exact substring of segment text")
        review_status = row.get("review_status")
        if review_status not in allowed_review:
            raise ValueError("annotation review_status is invalid")
        reviewer_id = row.get("reviewer_id")
        if review_status in {"HUMAN_VERIFIED", "REJECTED"}:
            reviewer_id = _nonempty_text(reviewer_id, "reviewer_id")
        elif reviewer_id is not None:
            reviewer_id = _nonempty_text(reviewer_id, "reviewer_id")
        by_category[category_id] += 1
        if review_status == "HUMAN_VERIFIED":
            if segment_status != "verified":
                raise ValueError("human-verified annotations require a verified segment")
            verified_by_category[category_id] += 1
        by_review[review_status] += 1
        normalized.append({
            "annotation_id": annotation_id,
            "segment_id": segment_id,
            "category_id": category_id,
            "speaker_id": speaker_id,
            "quote": quote,
            "review_status": review_status,
            "reviewer_id": reviewer_id,
        })
        seen.add(annotation_id)

    return {
        "annotation_count": len(normalized),
        "counts_by_category": dict(sorted(by_category.items())),
        "human_verified_counts_by_category": dict(sorted(verified_by_category.items())),
        "counts_by_review_status": dict(sorted(by_review.items())),
        "status": "ANNOTATION_REVIEW_REQUIRED" if by_review["MODEL_CANDIDATE"] else "ANNOTATIONS_REVIEWED",
        "annotations": normalized,
    }
