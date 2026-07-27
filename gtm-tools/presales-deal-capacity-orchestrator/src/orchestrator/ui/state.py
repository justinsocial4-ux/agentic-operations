"""Pure, testable flow state for the Phase 7 dashboard.

Keeps all decision-free view logic (stages, proof-row rendering, manager
dispositions, inert export) out of the Streamlit script so it can be unit
tested without a browser.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from orchestrator.contracts.enums import LaneV1
from orchestrator.contracts.proof import ExportBundleV2, SerializedSourceProofV1


class LandingPath(StrEnum):
    FICTIONAL_DEMO = "FICTIONAL_DEMO"
    IMPORT = "IMPORT"
    CONNECT = "CONNECT"


class Stage(StrEnum):
    LANDING = "LANDING"
    AUTHORITY = "AUTHORITY"
    SETUP = "SETUP"
    MAPPING = "MAPPING"
    HEALTH = "HEALTH"
    EVIDENCE = "EVIDENCE"
    WALKTHROUGH = "WALKTHROUGH"
    RESULTS = "RESULTS"


class WalkStep(StrEnum):
    """The seven guided walkthrough stages (a–g) in decision order."""

    INTRO = "INTRO"                # a. what we're about to do
    READINESS = "READINESS"        # b. validated readiness dimensions + citations
    PRIORITY = "PRIORITY"          # c. readiness + urgency + value -> priority_bp
    ELIGIBLE = "ELIGIBLE"          # d. manager-approved roster + skills
    ASSIGNMENT = "ASSIGNMENT"      # e. optimal portfolio assignment + why
    CAPACITY = "CAPACITY"          # f. capacity impact + EMEA +25% assumption
    MANAGER = "MANAGER"            # g. engine stops; manager decides; inert export


# The walkthrough is a strict, ordered sequence. It is the DEFAULT experience for
# the fictional demo path; "skip to full results" jumps straight to the compact
# one-shot results view for repeat viewers.
WALKTHROUGH_STEPS: tuple[WalkStep, ...] = (
    WalkStep.INTRO,
    WalkStep.READINESS,
    WalkStep.PRIORITY,
    WalkStep.ELIGIBLE,
    WalkStep.ASSIGNMENT,
    WalkStep.CAPACITY,
    WalkStep.MANAGER,
)


# The three landing paths are the only entry points. Conversation evidence is
# additive, never a landing path and never a standalone lane.
LANDING_PATHS: tuple[LandingPath, ...] = (
    LandingPath.FICTIONAL_DEMO,
    LandingPath.IMPORT,
    LandingPath.CONNECT,
)

# Exactly three output lanes; conversation is not among them.
SELECTABLE_LANES: tuple[LaneV1, ...] = (
    LaneV1.DEAL_PRIORITIZATION,
    LaneV1.ASSIGNMENT_RECOMMENDATION,
    LaneV1.CAPACITY_HEATMAP,
)

# The neutral connect targets. Ordinary buttons, no scary copy.
CONNECT_TARGETS: tuple[str, ...] = ("Salesforce", "ClickUp", "Fathom", "Gong")

DISPOSITION_KINDS: tuple[str, ...] = ("ACCEPT", "OVERRIDE", "REJECT", "DEFER")


@dataclass(frozen=True)
class ProofRow:
    """One expandable per-source proof row for the UI (three separate fields)."""

    source_instance_id: str
    execution_mode: str
    implementation_proof: str
    live_validation_proof: str
    decision_bearing: bool


def proof_rows(bundle: ExportBundleV2) -> tuple[ProofRow, ...]:
    """One row per source in the serializer-derived contributor closure.

    Never collapses sources into one tuple and never re-derives classification.
    """
    rows: list[ProofRow] = []
    for source_id, proof in sorted(bundle.source_proof_by_instance.items()):
        assert isinstance(proof, SerializedSourceProofV1)
        rows.append(ProofRow(
            source_instance_id=source_id,
            execution_mode=proof.execution_mode.value,
            implementation_proof=proof.implementation_proof.value,
            live_validation_proof=proof.live_validation_proof.value,
            decision_bearing=proof.decision_bearing,
        ))
    return tuple(rows)


def run_summary_line(bundle: ExportBundleV2) -> str:
    """Conservative weakest-decision-bearing-source summary text.

    Never uses a strongest-source rule; if any decision-bearing source is
    NOT_LIVE_VALIDATED, the composed run reads NOT_LIVE_VALIDATED.
    """
    summary = bundle.run_proof_summary
    if summary is None:
        return "No decision-bearing source contributed to this run."
    return (
        f"Implementation: {summary.implementation_proof.value} | "
        f"Live validation: {summary.live_validation_proof.value} | "
        f"derivation: {summary.derivation}"
    )


@dataclass
class ManagerDisposition:
    deal_source_id: str
    kind: str  # one of DISPOSITION_KINDS
    override_consultant_source_id: str | None = None
    outside_model_review: bool = False


@dataclass
class FlowState:
    """Session-carried flow state (mirrored into st.session_state by the app)."""

    stage: Stage = Stage.LANDING
    path: LandingPath | None = None
    lane: LaneV1 | None = None
    authority_attested: bool = False
    transcript_ack: bool = False
    core_confirmed: bool = False
    advanced_confirmed: bool = False
    dispositions: dict[str, ManagerDisposition] = field(default_factory=dict)
    export_created: bool = False
    walk_index: int = 0

    # --- transitions -----------------------------------------------------------
    def choose_path(self, path: LandingPath) -> None:
        self.path = path
        if path is LandingPath.FICTIONAL_DEMO:
            # Zero-credential demo skips the authority/import gates and opens the
            # guided walkthrough by default (Kevin sees the reasoning first).
            self.lane = LaneV1.ASSIGNMENT_RECOMMENDATION
            self.walk_index = 0
            self.stage = Stage.WALKTHROUGH
        else:
            self.stage = Stage.AUTHORITY

    # --- walkthrough navigation ------------------------------------------------
    @property
    def current_walk_step(self) -> WalkStep:
        idx = max(0, min(self.walk_index, len(WALKTHROUGH_STEPS) - 1))
        return WALKTHROUGH_STEPS[idx]

    @property
    def is_last_walk_step(self) -> bool:
        return self.walk_index >= len(WALKTHROUGH_STEPS) - 1

    @property
    def is_first_walk_step(self) -> bool:
        return self.walk_index <= 0

    def next_walk(self) -> None:
        if self.walk_index < len(WALKTHROUGH_STEPS) - 1:
            self.walk_index += 1
        else:
            # Past the final narration stage: fall through to full results.
            self.stage = Stage.RESULTS

    def prev_walk(self) -> None:
        if self.walk_index > 0:
            self.walk_index -= 1

    def restart_walk(self) -> None:
        self.walk_index = 0
        self.stage = Stage.WALKTHROUGH

    def skip_to_results(self) -> None:
        self.stage = Stage.RESULTS

    def attest(self, *, transcript_ack: bool) -> None:
        self.authority_attested = True
        self.transcript_ack = transcript_ack
        self.stage = Stage.SETUP

    @property
    def setup_actions_used(self) -> int:
        """At most two confirmation actions per lane, INCLUDING authority."""
        return int(self.core_confirmed) + int(self.advanced_confirmed)

    @property
    def setup_complete(self) -> bool:
        return self.core_confirmed and self.advanced_confirmed

    def confirm_core(self, lane: LaneV1) -> None:
        # One action covering authority + every visible core value.
        self.lane = lane
        self.core_confirmed = True

    def confirm_advanced(self) -> None:
        self.advanced_confirmed = True

    def advance_to_mapping(self) -> None:
        if not self.setup_complete:
            raise ValueError("setup requires both confirmation actions before mapping")
        self.stage = Stage.MAPPING

    def record_disposition(self, disposition: ManagerDisposition) -> None:
        if disposition.kind not in DISPOSITION_KINDS:
            raise ValueError(f"unknown disposition kind: {disposition.kind}")
        self.dispositions[disposition.deal_source_id] = disposition

    def create_export(self) -> None:
        # Inert: only marks that a local recommendation export was produced.
        self.export_created = True

    def reset(self) -> None:
        self.__dict__.update(FlowState().__dict__)
