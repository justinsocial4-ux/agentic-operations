from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field, field_validator, model_validator

from .base import Identifier, Sha256, StrictContract, require_offset_aware
from .enums import DataClassificationV1, LaneV1, SourceModeV1

AuthorityRoleV1 = Literal[
    "DEALS_PRIMARY",
    "ROSTER_PRIMARY",
    "CAPACITY_PRIMARY",
    "WORKLOAD_PRIMARY",
    "CONVERSATION_ADDITIVE",
]

CORE_POLICY_FIELDS_BY_LANE: dict[LaneV1, frozenset[str]] = {
    LaneV1.DEAL_PRIORITIZATION: frozenset({
        "horizon_weeks", "readiness_dimensions",
        "required_readiness_subsets_by_request_type", "priority_weights_bp",
        "urgency_breakpoints", "commercial_value_floor", "commercial_value_cap",
        "commercial_currency_basis",
    }),
    LaneV1.ASSIGNMENT_RECOMMENDATION: frozenset({
        "horizon_weeks", "readiness_dimensions",
        "required_readiness_subsets_by_request_type", "priority_weights_bp",
        "urgency_breakpoints", "commercial_value_floor", "commercial_value_cap",
        "commercial_currency_basis", "capacity_unit_minutes",
        "capacity_completeness_window", "utilization_ceiling",
    }),
    LaneV1.CAPACITY_HEATMAP: frozenset({
        "horizon_weeks", "capacity_unit_minutes",
        "capacity_completeness_window", "utilization_ceiling",
    }),
}

ADVANCED_POLICY_FIELDS_BY_LANE: dict[LaneV1, frozenset[str]] = {
    LaneV1.DEAL_PRIORITIZATION: frozenset({
        "priority_weight_bounds", "prohibited_inputs", "prohibited_outputs",
        "export_boundary",
    }),
    LaneV1.ASSIGNMENT_RECOMMENDATION: frozenset({
        "priority_weight_bounds", "skill_catalog", "minimum_working_window_overlap",
        "match_component_weights_bp", "solver_config", "prohibited_inputs",
        "prohibited_outputs", "export_boundary",
    }),
    LaneV1.CAPACITY_HEATMAP: frozenset({
        "skill_catalog", "scenario_boundaries", "prohibited_inputs",
        "prohibited_outputs", "export_boundary",
    }),
}

REQUIRED_AUTHORITY_ROLES_BY_LANE: dict[LaneV1, frozenset[str]] = {
    LaneV1.DEAL_PRIORITIZATION: frozenset({"DEALS_PRIMARY"}),
    LaneV1.ASSIGNMENT_RECOMMENDATION: frozenset({
        "DEALS_PRIMARY", "ROSTER_PRIMARY", "CAPACITY_PRIMARY", "WORKLOAD_PRIMARY",
    }),
    LaneV1.CAPACITY_HEATMAP: frozenset({
        "DEALS_PRIMARY", "ROSTER_PRIMARY", "CAPACITY_PRIMARY", "WORKLOAD_PRIMARY",
    }),
}


class AuthorizationAttestationV1(StrictContract):
    schema_version: Literal["orchestrator.authorization-attestation.v1"]
    authorization_attestation_id: Identifier
    run_id: Identifier
    attestation_text_version: Literal["presales-authority-v1"]
    attestation_text_sha256: Sha256
    source_types: tuple[str, ...] = Field(min_length=1)
    data_classification: DataClassificationV1
    authorized_bounds_sha256: Sha256
    retention_policy_id: Identifier
    actor_role: str = Field(min_length=1, max_length=80)
    attested_at: datetime
    transcript_warning_acknowledged: bool

    @field_validator("attested_at")
    @classmethod
    def attestation_time_is_aware(cls, value: datetime) -> datetime:
        return require_offset_aware(value)

    @model_validator(mode="after")
    def private_transcript_warning_is_required(self) -> "AuthorizationAttestationV1":
        if (
            self.data_classification is DataClassificationV1.AUTHORIZED_PRIVATE_TRANSCRIPT
            and not self.transcript_warning_acknowledged
        ):
            raise ValueError("private transcript warning must be acknowledged before source access")
        return self


class SourceSlotSelectionV1(StrictContract):
    """Authority selected before preflight; no source instance ID exists here."""

    source_slot_id: Identifier
    authority_role: AuthorityRoleV1
    adapter_id: Identifier
    source_mode: SourceModeV1
    expected_non_secret_identity_fingerprint: Sha256 | None = None


class FieldAcceptanceV1(StrictContract):
    field_name: str = Field(min_length=1)
    value_sha256: Sha256
    acceptance: Literal["DIRECT", "GROUPED"]


class ConfirmationActionV1(StrictContract):
    action_number: Literal[1, 2]
    action_kind: Literal["AUTHORITY_AND_CORE", "ADVANCED_REVIEWED_DEFAULTS"]


class RunSetupAcceptanceV1(StrictContract):
    """Complete single-screen gate with authority folded into at most two actions."""

    schema_version: Literal["orchestrator.run-setup-acceptance.v1"]
    run_id: Identifier
    lane: LaneV1
    actor: str = Field(min_length=1, max_length=80)
    accepted_at: datetime
    authority_confirmed: Literal[True]
    source_slots: tuple[SourceSlotSelectionV1, ...] = Field(min_length=1)
    authority_binding_sha256: Sha256
    core_field_acceptances: tuple[FieldAcceptanceV1, ...] = Field(min_length=1)
    advanced_field_acceptances: tuple[FieldAcceptanceV1, ...] = Field(min_length=1)
    actions: tuple[ConfirmationActionV1, ...] = Field(min_length=2, max_length=2)
    second_setup_screen: Literal[False]

    @field_validator("accepted_at")
    @classmethod
    def aware_time(cls, value: datetime) -> datetime:
        return require_offset_aware(value)

    @model_validator(mode="after")
    def enforce_complete_interaction(self) -> "RunSetupAcceptanceV1":
        expected_actions = [(1, "AUTHORITY_AND_CORE"), (2, "ADVANCED_REVIEWED_DEFAULTS")]
        actual_actions = [(action.action_number, action.action_kind) for action in self.actions]
        if actual_actions != expected_actions:
            raise ValueError("run setup must use authority+core then Advanced in two total actions")

        core_names = [item.field_name for item in self.core_field_acceptances]
        advanced_names = [item.field_name for item in self.advanced_field_acceptances]
        if len(core_names) != len(set(core_names)) or set(core_names) != CORE_POLICY_FIELDS_BY_LANE[self.lane]:
            raise ValueError("core policy acceptance inventory is incomplete or duplicated")
        if len(advanced_names) != len(set(advanced_names)) or set(advanced_names) != ADVANCED_POLICY_FIELDS_BY_LANE[self.lane]:
            raise ValueError("Advanced policy acceptance inventory is incomplete or duplicated")
        if any(item.acceptance != "DIRECT" for item in self.core_field_acceptances):
            raise ValueError("core fields require per-field direct records from the one core action")
        if any(item.acceptance != "GROUPED" for item in self.advanced_field_acceptances):
            raise ValueError("Advanced fields require grouped records from the one Advanced action")

        slots = [(item.source_slot_id, item.authority_role) for item in self.source_slots]
        if len(slots) != len(set(slots)):
            raise ValueError("source slot/role pairs must be unique")
        authority_roles = [item.authority_role for item in self.source_slots if item.authority_role != "CONVERSATION_ADDITIVE"]
        if len(authority_roles) != len(set(authority_roles)):
            raise ValueError("each consumed population requires exactly one authoritative source slot")
        roles = {item.authority_role for item in self.source_slots}
        required_roles = REQUIRED_AUTHORITY_ROLES_BY_LANE[self.lane]
        if not required_roles.issubset(roles):
            raise ValueError(f"source authority roles incomplete: {sorted(required_roles - roles)}")
        if "CONVERSATION_ADDITIVE" in roles and self.lane is LaneV1.CAPACITY_HEATMAP:
            raise ValueError("conversation evidence cannot attach to Capacity/heatmap")
        return self
