from __future__ import annotations

import json
from pathlib import Path

import httpx

from orchestrator.llm.analyst import run_analyst
from orchestrator.llm.digest import build_analyst_digest
from orchestrator.llm.provider import LiveLocalProvider, ManualCitationProvider
from orchestrator.retention import scan_artifacts_for_sentinel

from analyst_fixtures import (
    ACCEPTED_DIMENSIONS,
    PHASE6_SENTINEL,
    exact_citation,
    fictional_segments,
)
from datetime import datetime, timezone

DEAL = "deal-1"
RUN = "run-sentinel"
NOW = datetime(2026, 8, 3, 12, 0, tzinfo=timezone.utc)


def _segments_by_id():
    return {segment.segment_id: segment for segment in fictional_segments()}


def _candidates():
    segs = _segments_by_id()
    # Cite the sentinel-bearing segment so a naive persistence path would leak it.
    return [
        {"dimension_id": "security-or-data-requirements", "state": "SUPPORTED",
         "citations": [exact_citation(segs["seg-a"])]},
        {"dimension_id": "business-problem", "state": "SUPPORTED",
         "citations": [exact_citation(segs["seg-e"])]},  # seg-e IS the sentinel text
    ]


def test_analyst_run_persists_no_full_transcript_text(tmp_path: Path) -> None:
    # Sanity: the sentinel really is present in the in-memory evidence.
    assert any(PHASE6_SENTINEL in s.text for s in fictional_segments())

    provider = ManualCitationProvider(entries=_candidates())
    result = run_analyst(
        provider=provider, segments=fictional_segments(), deal_source_id=DEAL,
        accepted_dimensions=ACCEPTED_DIMENSIONS,
        dimension_ids=("security-or-data-requirements", "business-problem"), run_id=RUN,
    )
    digest = build_analyst_digest(
        run_id=RUN, deal_source_id=DEAL, policy_sha256="d" * 64,
        analysis_mode="MANUAL_CITATION", projections=result.projections,
        quarantined=result.quarantined, created_at=NOW,
    )

    # Serialize every durable Phase 6 artifact to an app-owned directory.
    app_dir = tmp_path / "app"
    app_dir.mkdir()
    (app_dir / "observations.json").write_text(
        json.dumps([p.model_dump(mode="json") for p in result.projections]), encoding="utf-8")
    (app_dir / "evidence.json").write_text(
        json.dumps([e.model_dump(mode="json") for e in result.evidence]), encoding="utf-8")
    (app_dir / "digest.json").write_text(
        json.dumps(digest.model_dump(mode="json")), encoding="utf-8")
    (app_dir / "quarantine.json").write_text(
        json.dumps([q.model_dump(mode="json") for q in result.quarantined]), encoding="utf-8")

    # The full transcript text (sentinel) must appear in NONE of the durable artifacts.
    matches = scan_artifacts_for_sentinel((app_dir,), PHASE6_SENTINEL)
    assert matches == (), f"full transcript text leaked into durable artifacts: {matches}"

    # Durable projections carry only hashes/offsets — proof the sentinel-bearing
    # citation was reduced to metadata, not text.
    sentinel_projection = next(p for p in result.projections if p.dimension_id == "business-problem")
    assert all("quote" not in c.model_dump(mode="json") for c in sentinel_projection.citations)


def test_live_local_sends_text_only_over_loopback_and_nothing_persists(tmp_path: Path) -> None:
    seg = _segments_by_id()["seg-e"]  # sentinel-bearing
    captured_bodies: list[bytes] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured_bodies.append(request.content)  # in-memory only, loopback host
        assert request.url.host == "127.0.0.1"
        return httpx.Response(200, json={"observations": [{
            "dimension_id": "business-problem", "state": "SUPPORTED",
            "citations": [exact_citation(seg)],
        }]})

    client = httpx.Client(trust_env=False, follow_redirects=False, transport=httpx.MockTransport(handler))
    provider = LiveLocalProvider(
        endpoint_url="http://127.0.0.1:11434/v1/analyze",
        segments=fictional_segments(), client=client,
    )
    result = run_analyst(
        provider=provider, segments=fictional_segments(), deal_source_id=DEAL,
        accepted_dimensions=ACCEPTED_DIMENSIONS,
        dimension_ids=("business-problem",), run_id=RUN,
    )
    provider.close()

    # The local model DID receive segment text (that is the loopback-only design), but
    # only over loopback and only in-memory.
    assert any(PHASE6_SENTINEL.encode("utf-8") in body for body in captured_bodies)

    # Nothing durable is written by the run; the durable projection is text-free.
    app_dir = tmp_path / "app"
    app_dir.mkdir()
    (app_dir / "projections.json").write_text(
        json.dumps([p.model_dump(mode="json") for p in result.projections]), encoding="utf-8")
    assert scan_artifacts_for_sentinel((app_dir,), PHASE6_SENTINEL) == ()
