"""Phase 8 gate: credential-free mixed-source Assignment acceptance.

One end-to-end contract/replay run that composes three source-specific adapters
purely from checked-in official-shape replay fixtures, with fake credentials and
``httpx.MockTransport`` (no vendor network, no real accounts, no private data):

* Salesforce replay -> the decision-bearing deal population;
* ClickUp replay    -> the decision-bearing roster/capacity population;
* Gong replay       -> additive exact-deal-crosswalk conversation evidence that
  can only satisfy a cited readiness dimension and never picks/scores anyone.

The run emits a source-indexed proof map (one three-field row per source
instance) plus the conservative, serializer-derived
``WEAKEST_DECISION_BEARING_SOURCE`` run label. Because every contributor is
``NOT_LIVE_VALIDATED``, the composed run label stays ``NOT_LIVE_VALIDATED``:
runtime success over replay fixtures never promotes proof.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx

from orchestrator.canonical import (
    ConsumptionGraph,
    InstrumentedDecisionInputs,
    SourcedDecisionValue,
    build_export_bundle,
)
from orchestrator.ingestion.clickup import ClickUpAdapter
from orchestrator.ingestion.gong import GongAdapter
from orchestrator.ingestion.registry import load_gong_capability
from orchestrator.ingestion.salesforce import SalesforceAdapter
from orchestrator.ingestion.transport import (
    AllowedEndpoint,
    LockedHttpClient,
    build_httpx_client,
)

ROOT = Path(__file__).resolve().parents[2]
SF_FX = ROOT / "data" / "replay" / "salesforce"
CU_FX = ROOT / "data" / "replay" / "clickup"
GO_FX = ROOT / "data" / "replay" / "gong"

SF_HOST = "synthetic.my.salesforce.com"
SF_VERSION = "v67.0"
SF_FIELDS = ("Id", "LastModifiedDate", "Name", "Synthetic_Region__c")
CU_HOST = "api.clickup.com"
NOW = datetime(2026, 8, 3, 9, 0, tzinfo=timezone.utc)
WINDOW_END = NOW + timedelta(hours=2)
ALL_GONG_SCOPES = frozenset({
    "api:calls:read:basic", "api:calls:read:extensive", "api:calls:read:transcript", "api:users:read",
})


# -- Salesforce replay: decision-bearing deal population -----------------------


def _salesforce_endpoints() -> tuple[AllowedEndpoint, ...]:
    prefix = f"/services/data/{SF_VERSION}"
    return (
        AllowedEndpoint("salesforce.query", "GET", SF_HOST, f"{prefix}/query", True),
        AllowedEndpoint("salesforce.query-page", "GET", SF_HOST, f"{prefix}/query/{{locator}}", True),
    )


def _salesforce_adapter() -> tuple[SalesforceAdapter, list[httpx.Request]]:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        body = (SF_FX / ("query-page-1.json" if request.url.path.endswith("/query") else "query-page-2.json")).read_bytes()
        return httpx.Response(
            200,
            content=body,
            headers={"content-type": "application/json", "sforce-limit-info": "api-usage=20/15000"},
        )

    raw = build_httpx_client(transport=httpx.MockTransport(handler))
    locked = LockedHttpClient(_salesforce_endpoints(), client=raw, sleeper=lambda _: None)
    return SalesforceAdapter(
        instance_url=f"https://{SF_HOST}",
        bearer_token="fake-salesforce-token-phase8",
        api_version=SF_VERSION,
        client=locked,
    ), seen


# -- ClickUp replay: decision-bearing roster/capacity population ---------------


def _clickup_endpoints() -> tuple[AllowedEndpoint, ...]:
    return (
        AllowedEndpoint("clickup.workspaces", "GET", CU_HOST, "/api/v2/team", True),
        AllowedEndpoint("clickup.list-tasks", "GET", CU_HOST, "/api/v2/list/{list_id}/task", True),
    )


def _clickup_adapter() -> tuple[ClickUpAdapter, list[httpx.Request]]:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(
            200,
            content=(CU_FX / "tasks-page.json").read_bytes(),
            headers={
                "content-type": "application/json",
                "x-ratelimit-limit": "100",
                "x-ratelimit-remaining": "99",
                "x-ratelimit-reset": "1785585660",
            },
        )

    raw = build_httpx_client(transport=httpx.MockTransport(handler))
    locked = LockedHttpClient(_clickup_endpoints(), client=raw, sleeper=lambda _: None)
    return ClickUpAdapter(token="fake-clickup-token-phase8", client=locked), seen


# -- Gong replay: additive exact-crosswalk conversation evidence ---------------


def _gong_adapter() -> tuple[GongAdapter, list[httpx.Request]]:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        path = request.url.path
        if path == "/v2/calls":
            return httpx.Response(200, json=json.loads((GO_FX / "calls-page.json").read_text()))
        if path == "/v2/calls/extensive":
            return httpx.Response(200, json=json.loads((GO_FX / "calls-extensive.json").read_text()))
        if path == "/v2/calls/transcript":
            return httpx.Response(200, json=json.loads((GO_FX / "call-transcript.json").read_text()))
        if path == "/v2/users":
            return httpx.Response(200, json=json.loads((GO_FX / "users.json").read_text()))
        return httpx.Response(404, json={})

    cap = load_gong_capability(ROOT)
    endpoints = GongAdapter._build_endpoints(cap)
    raw = build_httpx_client(transport=httpx.MockTransport(handler))
    locked = LockedHttpClient(endpoints, client=raw, sleeper=lambda _: None, now=lambda: 0)
    from orchestrator.ingestion.gong import GongProactiveLimiter

    adapter = GongAdapter(
        package_root=ROOT,
        auth_mode="SESSION_PASTED_BEARER",
        bearer_token="fake-gong-bearer-phase8",
        available_scopes=ALL_GONG_SCOPES,
        capability=cap,
        client=locked,
        limiter=GongProactiveLimiter(monotonic=lambda: 0.0, wallclock=lambda: 0.0),
    )
    return adapter, seen


def test_credential_free_mixed_source_assignment_replay_run_emits_conservative_proof_map() -> None:
    exact_deal_source_id = "006SYNTHETIC001"

    # 1. Salesforce replay -> deal population (credential-free, replay only).
    sf, sf_seen = _salesforce_adapter()
    first = sf.query_page(object_name="Opportunity", selected_fields=SF_FIELDS, page_number=0)
    assert first.records[0]["Id"] == exact_deal_source_id
    assert all(request.method == "GET" for request in sf_seen)
    assert all(
        request.headers["authorization"] == "Bearer fake-salesforce-token-phase8"
        for request in sf_seen
    )
    sf.close()

    # 2. ClickUp replay -> roster/capacity population (credential-free, replay only).
    cu, cu_seen = _clickup_adapter()
    tasks = cu.task_page(
        page=0,
        include_closed=True,
        include_subtasks=False,
        include_timl=False,
        selected_custom_field_ids=("field-skill-id",),
        list_id="list-synthetic-001",
    )
    assert tasks.records and tasks.complete is True
    assert all(request.method == "GET" for request in cu_seen)
    cu.close()

    # 3. Gong replay -> additive exact-deal-crosswalk conversation evidence.
    go, go_seen = _gong_adapter()
    route = go.read_transcript_route(
        source_instance_id="src-gong-synthetic",
        call_id="gong-call-1",
        from_dt=NOW,
        to_dt=WINDOW_END,
        exact_deal_source_id=exact_deal_source_id,
        started_at=NOW,
        ended_at=WINDOW_END,
        route_id="route-gong-phase8",
    )
    # The conversation is bound to the exact deal crosswalk and never names a consultant.
    assert route.origin_family == "GONG"
    assert all(segment.deal_source_id == exact_deal_source_id for segment in route.segments)
    assert all(request.method in {"GET", "POST"} for request in go_seen)
    go.close()

    # 4. Compose the source-indexed proof map. Salesforce (deal) and ClickUp
    # (roster + capacity) are decision-bearing for the assignment; Gong evidence
    # is decision-bearing only on the cited readiness-coverage path that feeds
    # priority -> assignment, never on consultant selection.
    graph = ConsumptionGraph()
    for source_id in ("src-salesforce", "src-clickup", "src-gong-synthetic"):
        graph.manifest_source(source_id)
    inputs = InstrumentedDecisionInputs({
        "deal": SourcedDecisionValue("src-salesforce", "deal.id", exact_deal_source_id),
        "roster": SourcedDecisionValue("src-clickup", "consultant.eligibility", "eligible"),
        "capacity": SourcedDecisionValue("src-clickup", "capacity.units", 20),
        "conversation": SourcedDecisionValue(
            "src-gong-synthetic", "readiness.coverage", route.segments[0].deal_source_id,
        ),
    })
    session = inputs.session(graph)
    session.emit("readiness-coverage", session.read("conversation"))
    session.emit("priority", session.read("deal"))
    session.emit("assignment", (session.read("roster"), session.read("capacity")))

    bundle = build_export_bundle(
        artifact_id="phase8-mixed-source-assignment",
        payload={"status": "RECOMMENDATION_ONLY", "lane": "ASSIGNMENT_RECOMMENDATION"},
        source_proofs={
            "src-salesforce": SalesforceAdapter.proof(),
            "src-clickup": ClickUpAdapter.proof(),
            "src-gong-synthetic": GongAdapter.proof(),
        },
        consumption_graph=graph,
    )

    # Source-indexed proof map: one three-field row per source instance, no
    # collapse and no strongest-source rule.
    assert set(bundle.source_proof_by_instance) == {"src-salesforce", "src-clickup", "src-gong-synthetic"}
    for row in bundle.source_proof_by_instance.values():
        assert row.decision_bearing is True
        assert row.implementation_proof == "FULLY_IMPLEMENTED_CONTRACT_TESTED"
        assert row.live_validation_proof == "NOT_LIVE_VALIDATED"

    # Conservative run label from the weakest decision-bearing source.
    assert bundle.run_proof_summary is not None
    assert bundle.run_proof_summary.derivation == "WEAKEST_DECISION_BEARING_SOURCE"
    assert bundle.run_proof_summary.live_validation_proof == "NOT_LIVE_VALIDATED"
    assert bundle.run_proof_summary.implementation_proof == "FULLY_IMPLEMENTED_CONTRACT_TESTED"

    # Inert, recommendation-only, no external writes anywhere in the package.
    assert bundle.assignment_status == "RECOMMENDATION_ONLY"
    assert bundle.execution_authorized is False
    assert bundle.external_writes_attempted is False
    assert bundle.production_ready is False
