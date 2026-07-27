from __future__ import annotations

import hashlib
from datetime import datetime, timezone

from orchestrator.contracts.records import ConversationSegmentV1

NOW = datetime(2026, 8, 3, 9, 0, tzinfo=timezone.utc)

# Fictional catalog subset accepted by the fixture PolicyV2.
ACCEPTED_DIMENSIONS = frozenset({
    "business-problem",
    "success-criteria",
    "security-or-data-requirements",
    "milestone-date",
})

# A unique full-transcript phrase that must appear NOWHERE durable.
PHASE6_SENTINEL = "PHASE6_SENTINEL synthetic residency success criteria 9c3e7f verbatim"


def make_segment(
    *,
    segment_id: str,
    text: str,
    conversation_id: str = "conv-101",
    deal_source_id: str = "deal-1",
    begin_ms: int = 0,
    end_ms: int = 5000,
) -> ConversationSegmentV1:
    return ConversationSegmentV1(
        schema_version="orchestrator.conversation-segment.v1",
        conversation_id=conversation_id,
        deal_source_id=deal_source_id,
        segment_id=segment_id,
        speaker_ref="CUSTOMER",
        speaker_source_label=None,
        occurred_at=NOW,
        relative_begin_ms=begin_ms,
        relative_end_ms=end_ms,
        text=text,
        source_record_id=f"src-{segment_id}",
        text_sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(),
        lineage_receipt_id=f"lin-{segment_id}",
    )


def fictional_segments() -> tuple[ConversationSegmentV1, ...]:
    """A coherent fictional deal transcript with explicit gold statements.

    The sentinel phrase is embedded so the persistence sentinel scan has something to
    hunt for; only exact cited excerpts and hashes may ever leave process memory.
    """
    return (
        make_segment(
            segment_id="seg-a",
            text="Approval requires EU data residency.",
            begin_ms=0,
            end_ms=4000,
        ),
        make_segment(
            segment_id="seg-b",
            text="We must cut onboarding time in half this quarter.",
            begin_ms=4000,
            end_ms=9000,
        ),
        make_segment(
            segment_id="seg-c",
            text="Success means a signed pilot by the 30th.",
            begin_ms=9000,
            end_ms=13000,
        ),
        make_segment(
            segment_id="seg-d",
            text="Actually success is just a demo, no pilot needed.",
            begin_ms=13000,
            end_ms=17000,
        ),
        make_segment(
            segment_id="seg-e",
            text=PHASE6_SENTINEL,
            begin_ms=17000,
            end_ms=21000,
        ),
    )


def exact_citation(segment: ConversationSegmentV1, *, quote: str | None = None) -> dict:
    """Build a valid exact citation dict for the whole segment text (or a substring)."""
    text = segment.text
    if quote is None:
        quote = text
        begin, end = 0, len(text)
    else:
        begin = text.index(quote)
        end = begin + len(quote)
    return {
        "conversation_id": segment.conversation_id,
        "segment_id": segment.segment_id,
        "quote": quote,
        "char_begin": begin,
        "char_end": end,
        "text_sha256": segment.text_sha256,
        "relative_begin_ms": segment.relative_begin_ms,
    }
