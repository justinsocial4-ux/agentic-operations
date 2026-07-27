"""Deterministic, credential-free fictional demo run for the Phase 7 dashboard.

This module composes the already-verified deterministic domain (readiness,
scoring, capacity, eligibility, fit, optimizer, alternatives, capacity heatmap,
EMEA scenario, and fact-bound digest) over a tiny frozen fictional dataset.

No credentials, no network, no real accounts, and no real LLM are used. Every
source proof row is FICTIONAL_REPLAY / FULLY_IMPLEMENTED_CONTRACT_TESTED /
NOT_LIVE_VALIDATED so the conservative run summary reads NOT_LIVE_VALIDATED.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from pathlib import Path
from typing import Callable, Literal

from orchestrator.alternatives import build_assignment_recommendation
from orchestrator.canonical import (
    ConsumptionGraph,
    InstrumentedDecisionInputs,
    SourcedDecisionValue,
    build_export_bundle,
    canonical_sha256,
)
from orchestrator.capacity import compute_capacity_heatmap, compute_weekly_capacity
from orchestrator.contracts.domain import (
    ExactEvidenceCitationV2,
    ReadinessEvidenceV2,
)
from orchestrator.contracts.enums import (
    ExecutionModeV1,
    ImplementationProofV1,
    LaneV1,
    LiveValidationProofV1,
    SourceModeV1,
)
from orchestrator.contracts.phase3 import (
    CapacityDemandV1,
    PortfolioDealV1,
    PortfolioPairV1,
    PortfolioProblemV1,
)
from orchestrator.contracts.policy import PolicyV2
from orchestrator.contracts.proof import SourceProofInputV1
from orchestrator.contracts.records import (
    CapacityAvailabilityV1,
    ConsultantV2,
    DealWorkRequestV2,
    SkillAssertionV1,
    WorkloadCommitmentV1,
)
from orchestrator.contracts.setup import SourceSlotSelectionV1
from orchestrator.digest import build_leadership_digest
from orchestrator.eligibility import compute_consultant_fit, evaluate_eligibility
from orchestrator.optimizer import solve_portfolio
from orchestrator.readiness import compute_readiness
from orchestrator.scenario import run_emea_capacity_scenario
from orchestrator.scoring import score_priority
from orchestrator.setup_gate import build_run_setup_acceptance

ROOT = Path(__file__).resolve().parents[3]
RUN_ID = "run-fictional-demo"
NOW = datetime(2026, 8, 3, 9, tzinfo=timezone.utc)
_HASH = "d" * 64

# Fictional source instances. All are FICTIONAL_REPLAY replay fixtures.
SOURCE_MANIFEST_IDS = ("demo-capacity", "demo-conversation", "demo-deals", "demo-roster")
MAPPINGS = (_HASH,)


def demo_policy() -> PolicyV2:
    return PolicyV2.model_validate_json_strict((ROOT / "config/demo_policy_v2.json").read_text())


def _fictional_proof() -> SourceProofInputV1:
    return SourceProofInputV1(
        execution_mode=ExecutionModeV1.FICTIONAL_REPLAY,
        implementation_proof=ImplementationProofV1.FULLY_IMPLEMENTED_CONTRACT_TESTED,
        live_validation_proof=LiveValidationProofV1.NOT_LIVE_VALIDATED,
    )


def _citation(dimension: str, suffix: str = "1") -> ExactEvidenceCitationV2:
    digest = hashlib.sha256(f"{dimension}-{suffix}".encode()).hexdigest()
    return ExactEvidenceCitationV2(
        citation_id=f"citation-{dimension}-{suffix}",
        source_record_id=f"source-{dimension}-{suffix}",
        conversation_id="conversation-1",
        segment_id=f"segment-{dimension}-{suffix}",
        excerpt_sha256=digest,
        char_begin=0,
        char_end=16,
        relative_begin_ms=120,
        exact_match_validated=True,
    )


def _deal(deal_id: str, work_id: str, amount: str, *, attach_conversation: bool) -> DealWorkRequestV2:
    return DealWorkRequestV2.model_validate({
        "schema_version": "orchestrator.deal-work-request.v2",
        "work_request_id": work_id,
        "deal_source_id": deal_id,
        "region_source_value": "EMEA",
        "region_id": "EMEA",
        "request_type": "DEMO_REQUEST",
        "milestone_type": "POC",
        "milestone_due_time": NOW + timedelta(days=6),
        "effort_units": 10,
        "commercial_amount": amount,
        "commercial_currency": "USD",
        "commercial_basis": "demo-corporate-bookings-v1",
        "required_skill_ids": ("security", "integration"),
        "required_languages": ("en",),
        "required_working_window_overlap_minutes": 120,
        "structured_evidence_references": ("evidence-1",),
        "conversation_ids": ("conversation-1",) if attach_conversation else (),
        "source_freshness": NOW,
        "lineage_receipt_ids": ("lineage-deal",),
    })


def _consultant(consultant_id: str) -> ConsultantV2:
    return ConsultantV2.model_validate({
        "schema_version": "orchestrator.consultant.v2",
        "consultant_source_id": consultant_id,
        "active_eligibility": True,
        "supported_region_ids": ("EMEA",),
        "time_zone": "Europe/London",
        "working_windows": ("09:00-17:00",),
        "languages": ("en",),
        "manager_approved_skill_ids": ("security", "integration"),
        "policy_receipt_ids": ("manager-skill-policy-1",),
    })


def _skills(consultant_id: str) -> tuple[SkillAssertionV1, ...]:
    return tuple(SkillAssertionV1(
        schema_version="orchestrator.skill-assertion.v1",
        consultant_source_id=consultant_id,
        skill_id=skill_id,
        level=3,
        policy_owner="manager",
        effective_begin=NOW - timedelta(days=1),
        source_receipt_id=f"skill-receipt-{consultant_id}-{skill_id}",
    ) for skill_id in ("security", "integration"))


def _capacity(consultant: ConsultantV2, policy: PolicyV2, policy_sha256: str, *, scheduled: int):
    availability = tuple(CapacityAvailabilityV1(
        schema_version="orchestrator.capacity-availability.v1",
        consultant_source_id=consultant.consultant_source_id,
        week_bucket=week,
        scheduled_units=scheduled,
        time_off_reduction_units=0,
        source_as_of=NOW,
        completeness_state="COMPLETE",
        lineage_receipt_ids=(f"capacity-lineage-{week}",),
    ) for week in range(1, 5))
    workloads = tuple(WorkloadCommitmentV1(
        schema_version="orchestrator.workload-commitment.v1",
        consultant_source_id=consultant.consultant_source_id,
        source_work_id=f"active-{week}",
        week_bucket=week,
        committed_units=5,
        due_time=NOW + timedelta(days=week),
        status="ACTIVE",
        lineage_receipt_ids=(f"work-lineage-{week}",),
    ) for week in range(1, 5))
    return compute_weekly_capacity(
        run_id=RUN_ID,
        consultant=consultant,
        availability=availability,
        workloads=workloads,
        workload_population_complete=True,
        active_workload_statuses=frozenset({"ACTIVE"}),
        policy=policy,
        policy_sha256=policy_sha256,
        source_manifest_ids=SOURCE_MANIFEST_IDS,
        mapping_profile_sha256s=MAPPINGS,
        created_at=NOW,
    )


def _readiness_evidence(policy: PolicyV2, *, transcript_dimension: str | None) -> tuple[ReadinessEvidenceV2, ...]:
    evidence = []
    for dimension in policy.readiness_dimensions:
        is_transcript = dimension == transcript_dimension
        evidence.append(ReadinessEvidenceV2(
            dimension_id=dimension,
            state="SUPPORTED",
            provenance="TRANSCRIPT" if is_transcript else "STRUCTURED",
            citations=(_citation(dimension),),
        ))
    return tuple(evidence)


@dataclass(frozen=True)
class ConsultantSummary:
    """Read-only view of a manager-approved consultant for the walkthrough.

    Carries only manager-approved facts (skills, region, availability). It never
    carries call-text-derived signal; the roster is the pool the optimizer may
    draw from, established outside any conversation.
    """

    consultant_source_id: str
    supported_region_ids: tuple[str, ...]
    languages: tuple[str, ...]
    manager_approved_skill_ids: tuple[str, ...]
    skill_levels: tuple[tuple[str, int], ...]


@dataclass(frozen=True)
class ConversationAttachment:
    """Additive-only conversation evidence bound to an exact deal crosswalk."""

    deal_source_id: str
    conversation_id: str
    dimension_id: str
    provenance: str  # always "TRANSCRIPT"
    is_standalone_lane: bool  # always False


DemoPipelineStage = Literal[
    "fixtures", "readiness", "priority", "eligibility", "solver", "scenario", "done",
]


@dataclass(frozen=True)
class DemoPipelineEvent:
    """Read-only UI observation emitted after a real composition stage completes."""

    stage: DemoPipelineStage
    artifacts: tuple[object, ...]


DemoPipelineObserver = Callable[[DemoPipelineEvent], None]


@dataclass(frozen=True)
class DemoRun:
    lane: LaneV1
    policy: PolicyV2
    policy_sha256: str
    # Deal prioritization
    priority_queue: tuple  # tuple[PriorityReceiptV2, ...] sorted by priority desc
    readiness_by_deal: dict
    # Assignment
    assignment_recommendation: object | None
    solver_receipt: object | None
    # Capacity
    capacity_cells: tuple
    scenario_comparison: object | None
    digest: object | None
    # Proof
    export_bundle: object
    conversation_attachment: ConversationAttachment | None
    # Manager-approved roster (walkthrough "who is allowed to help" stage)
    roster: tuple[ConsultantSummary, ...] = ()


def _compose_demo_run(
    lane: LaneV1,
    observer: DemoPipelineObserver | None = None,
) -> DemoRun:
    """Compose the deterministic run, optionally exposing read-only UI events."""

    def observe(stage: DemoPipelineStage, *artifacts: object) -> None:
        if observer is not None:
            observer(DemoPipelineEvent(stage=stage, artifacts=artifacts))

    policy = demo_policy()
    policy_sha256 = canonical_sha256(policy)

    deals = (
        _deal("deal-emea-alpha", "work-alpha", "200000.00", attach_conversation=True),
        _deal("deal-emea-bravo", "work-bravo", "480000.00", attach_conversation=False),
    )
    consultants = (_consultant("consultant-lyra"), _consultant("consultant-vega"))
    observe("fixtures", deals, consultants)
    capacities = {
        c.consultant_source_id: _capacity(c, policy, policy_sha256, scheduled=40)
        for c in consultants
    }

    readiness_by_deal = {}
    priorities = {}
    for deal in deals:
        readiness = compute_readiness(
            run_id=RUN_ID,
            deal=deal,
            policy=policy,
            policy_sha256=policy_sha256,
            source_manifest_ids=SOURCE_MANIFEST_IDS,
            mapping_profile_sha256s=MAPPINGS,
            evidence=_readiness_evidence(
                policy,
                transcript_dimension="success-criteria" if deal.conversation_ids else None,
            ),
            created_at=NOW,
        )
        observe("readiness", readiness)
        priority = score_priority(
            run_id=RUN_ID,
            deal=deal,
            readiness=readiness,
            policy=policy,
            policy_sha256=policy_sha256,
            source_manifest_ids=SOURCE_MANIFEST_IDS,
            mapping_profile_sha256s=MAPPINGS,
            as_of=NOW,
            created_at=NOW,
        )
        readiness_by_deal[deal.deal_source_id] = readiness
        priorities[deal.deal_source_id] = priority
        observe("priority", priority)

    priority_queue = tuple(sorted(
        priorities.values(),
        key=lambda item: (-item.priority_bp, item.deal_source_id),
    ))

    # Assignment lane: build the portfolio problem and solve it.
    portfolio_deals = tuple(
        PortfolioDealV1(priority=priorities[deal.deal_source_id], effort_units=10)
        for deal in deals
    )
    pairs = []
    for deal in deals:
        for consultant in consultants:
            capacity = capacities[consultant.consultant_source_id]
            eligibility = evaluate_eligibility(
                run_id=RUN_ID,
                deal=deal,
                readiness=readiness_by_deal[deal.deal_source_id],
                priority=priorities[deal.deal_source_id],
                consultant=consultant,
                skill_assertions=_skills(consultant.consultant_source_id),
                capacity=capacity,
                policy=policy,
                policy_sha256=policy_sha256,
                source_manifest_ids=SOURCE_MANIFEST_IDS,
                mapping_profile_sha256s=MAPPINGS,
                as_of=NOW,
                created_at=NOW,
            )
            fit = None
            if eligibility.eligible:
                fit = compute_consultant_fit(
                    deal=deal,
                    consultant=consultant,
                    priority=priorities[deal.deal_source_id],
                    eligibility=eligibility,
                    skill_assertions=_skills(consultant.consultant_source_id),
                    capacity=capacity,
                    policy=policy,
                    as_of=NOW,
                    created_at=NOW,
                )
            pairs.append(PortfolioPairV1(eligibility=eligibility, fit=fit))
            observe("eligibility", eligibility)

    problem = PortfolioProblemV1(
        schema_version="orchestrator.portfolio-problem.v1",
        run_id=RUN_ID,
        policy_sha256=policy_sha256,
        deals=portfolio_deals,
        pairs=tuple(pairs),
        capacities=tuple(capacities[c.consultant_source_id] for c in consultants),
    )
    solver_receipt = solve_portfolio(problem=problem, policy=policy, created_at=NOW)
    assignment = build_assignment_recommendation(
        problem=problem, policy=policy, solver_receipt=solver_receipt, created_at=NOW,
    )
    observe("solver", problem, solver_receipt, assignment)

    # Capacity/heatmap lane and EMEA scenario.
    demands = tuple(
        CapacityDemandV1(
            deal_source_id=deal.deal_source_id,
            region_id="EMEA",
            required_skill_ids=("security", "integration"),
            due_week_bucket=1,
            effort_units=10,
        )
        for deal in deals
    )
    capacity_cells = compute_capacity_heatmap(
        run_id=RUN_ID,
        demands=demands,
        consultants=consultants,
        capacities=tuple(capacities.values()),
        policy=policy,
        policy_sha256=policy_sha256,
        source_manifest_ids=SOURCE_MANIFEST_IDS,
        mapping_profile_sha256s=MAPPINGS,
    )
    heatmap_setup = build_run_setup_acceptance(
        run_id=RUN_ID,
        lane=LaneV1.CAPACITY_HEATMAP,
        actor="fictional-manager",
        accepted_at=NOW,
        policy=policy,
        source_slots=tuple(SourceSlotSelectionV1(
            source_slot_id=f"slot-{role.lower()}",
            authority_role=role,
            adapter_id="fictional-adapter",
            source_mode=SourceModeV1.FICTIONAL,
        ) for role in ("DEALS_PRIMARY", "ROSTER_PRIMARY", "CAPACITY_PRIMARY", "WORKLOAD_PRIMARY")),
        authority_and_core_confirmed=True,
        advanced_confirmed=True,
    )
    scenario_comparison = run_emea_capacity_scenario(
        run_id=RUN_ID,
        demands=demands,
        consultants=consultants,
        capacities=tuple(capacities.values()),
        policy=policy,
        policy_sha256=policy_sha256,
        source_manifest_ids=SOURCE_MANIFEST_IDS,
        mapping_profile_sha256s=MAPPINGS,
        setup_acceptance=heatmap_setup,
        created_at=NOW,
    )
    digest = build_leadership_digest(
        solver_receipt=solver_receipt,
        scenario_comparison=scenario_comparison,
        created_at=NOW,
    )
    observe("scenario", scenario_comparison)

    # Proof closure: instrument decision reads so each fictional source is
    # recorded as decision-bearing, then derive the conservative run summary.
    graph = ConsumptionGraph()
    for source_id in SOURCE_MANIFEST_IDS:
        graph.manifest_source(source_id)
    inputs = InstrumentedDecisionInputs({
        "deal": SourcedDecisionValue("demo-deals", "deal.priority_bp", priority_queue[0].priority_bp),
        "roster": SourcedDecisionValue("demo-roster", "consultant.eligibility", "eligible"),
        "capacity": SourcedDecisionValue("demo-capacity", "capacity.free_units", 30),
        "conversation": SourcedDecisionValue(
            "demo-conversation", "readiness.coverage", "success-criteria",
        ),
    })
    session = inputs.session(graph)
    session.emit("priority", session.read("deal"))
    session.emit("assignment", (session.read("roster"), session.read("capacity")))
    session.emit("readiness-coverage", session.read("conversation"))
    export_bundle = build_export_bundle(
        artifact_id="fictional-demo-export",
        payload={"status": "RECOMMENDATION_ONLY", "lane": lane.value},
        source_proofs={source_id: _fictional_proof() for source_id in SOURCE_MANIFEST_IDS},
        consumption_graph=graph,
    )

    conversation_attachment = ConversationAttachment(
        deal_source_id="deal-emea-alpha",
        conversation_id="conversation-1",
        dimension_id="success-criteria",
        provenance="TRANSCRIPT",
        is_standalone_lane=False,
    )

    roster = tuple(
        ConsultantSummary(
            consultant_source_id=c.consultant_source_id,
            supported_region_ids=tuple(c.supported_region_ids),
            languages=tuple(c.languages),
            manager_approved_skill_ids=tuple(c.manager_approved_skill_ids),
            skill_levels=tuple(
                (s.skill_id, s.level) for s in _skills(c.consultant_source_id)
            ),
        )
        for c in consultants
    )

    demo_run = DemoRun(
        lane=lane,
        policy=policy,
        policy_sha256=policy_sha256,
        priority_queue=priority_queue,
        readiness_by_deal=readiness_by_deal,
        assignment_recommendation=assignment,
        solver_receipt=solver_receipt,
        capacity_cells=capacity_cells,
        scenario_comparison=scenario_comparison,
        digest=digest,
        export_bundle=export_bundle,
        conversation_attachment=conversation_attachment,
        roster=roster,
    )
    observe("done", demo_run)
    return demo_run


@lru_cache(maxsize=None)
def build_demo_run(lane: LaneV1 = LaneV1.ASSIGNMENT_RECOMMENDATION) -> DemoRun:
    """Return the cached deterministic fictional run used by study views."""
    return _compose_demo_run(lane)


def run_demo_pipeline(
    lane: LaneV1 = LaneV1.ASSIGNMENT_RECOMMENDATION,
    *,
    observer: DemoPipelineObserver | None = None,
) -> DemoRun:
    """Execute a fresh real demo composition while exposing UI-only stage events.

    This deliberately bypasses the study-view cache. Observation is read-only;
    it does not alter engine inputs, receipts, ordering, or output.
    """
    return _compose_demo_run(lane, observer)
