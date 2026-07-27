from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field

from orchestrator.canonical import canonical_sha256
from orchestrator.contracts.base import Identifier, Sha256, StrictContract
from orchestrator.contracts.enums import DataClassificationV1, SourceModeV1
from orchestrator.contracts.manifest import SourceManifestV1
from orchestrator.contracts.policy import PolicyV2
from orchestrator.contracts.setup import (
    ADVANCED_POLICY_FIELDS_BY_LANE,
    AuthorizationAttestationV1,
    CORE_POLICY_FIELDS_BY_LANE,
    ConfirmationActionV1,
    FieldAcceptanceV1,
    RunSetupAcceptanceV1,
    SourceSlotSelectionV1,
)


class SetupGateError(ValueError):
    pass


AUTHORIZATION_ATTESTATION_TEXT = (
    "I am authorized to access and process the selected exports/account data for this local evaluation; "
    "I selected the minimum necessary fields and time range; I understand transcripts may contain customer, "
    "employee, or sensitive private information; and this tool produces recommendations only and does not "
    "replace my organization's privacy, legal, security, or staffing approvals."
)


def build_authorization_attestation(
    *,
    authorization_attestation_id: str,
    run_id: str,
    source_types: tuple[str, ...],
    data_classification: DataClassificationV1,
    authorized_bounds: object,
    retention_policy_id: str,
    actor_role: str,
    attested_at: datetime,
    transcript_warning_acknowledged: bool,
) -> AuthorizationAttestationV1:
    return AuthorizationAttestationV1(
        schema_version="orchestrator.authorization-attestation.v1",
        authorization_attestation_id=authorization_attestation_id,
        run_id=run_id,
        attestation_text_version="presales-authority-v1",
        attestation_text_sha256=canonical_sha256(AUTHORIZATION_ATTESTATION_TEXT),
        source_types=source_types,
        data_classification=data_classification,
        authorized_bounds_sha256=canonical_sha256(authorized_bounds),
        retention_policy_id=retention_policy_id,
        actor_role=actor_role,
        attested_at=attested_at,
        transcript_warning_acknowledged=transcript_warning_acknowledged,
    )


class PostPreflightIdentityV1(StrictContract):
    adapter_id: Identifier
    source_mode: SourceModeV1
    authority_role: Literal[
        "DEALS_PRIMARY", "ROSTER_PRIMARY", "CAPACITY_PRIMARY",
        "WORKLOAD_PRIMARY", "CONVERSATION_ADDITIVE",
    ]
    actual_non_secret_identity_fingerprint: Sha256


class BoundSourceAuthorityV1(StrictContract):
    source_slot_id: Identifier
    authority_role: str
    source_manifest_id: Identifier
    source_instance_id: Identifier
    binding_sha256: Sha256


def _field_hash(policy: PolicyV2, field_name: str) -> str:
    return canonical_sha256(getattr(policy, field_name))


def build_run_setup_acceptance(
    *,
    run_id: str,
    lane: object,
    actor: str,
    accepted_at: datetime,
    policy: PolicyV2,
    source_slots: tuple[SourceSlotSelectionV1, ...],
    authority_and_core_confirmed: bool,
    advanced_confirmed: bool,
) -> RunSetupAcceptanceV1:
    """Represent the two buttons on the one setup screen; there are no per-field actions."""
    if not authority_and_core_confirmed:
        raise SetupGateError("authority and every visible core value require confirmation")
    if not advanced_confirmed:
        raise SetupGateError("Advanced reviewed defaults require confirmation")
    # Literal typing already rejects every other horizon; this explicit check documents
    # that it is displayed/hash-bound but never edited or defaulted by this function.
    if policy.horizon_weeks != 4:
        raise SetupGateError("the confirm-only v1 horizon must be four weeks")
    core = tuple(
        FieldAcceptanceV1(field_name=name, value_sha256=_field_hash(policy, name), acceptance="DIRECT")
        for name in sorted(CORE_POLICY_FIELDS_BY_LANE[lane])
    )
    advanced = tuple(
        FieldAcceptanceV1(field_name=name, value_sha256=_field_hash(policy, name), acceptance="GROUPED")
        for name in sorted(ADVANCED_POLICY_FIELDS_BY_LANE[lane])
    )
    return RunSetupAcceptanceV1(
        schema_version="orchestrator.run-setup-acceptance.v1",
        run_id=run_id,
        lane=lane,
        actor=actor,
        accepted_at=accepted_at,
        authority_confirmed=True,
        source_slots=source_slots,
        authority_binding_sha256=canonical_sha256(source_slots),
        core_field_acceptances=core,
        advanced_field_acceptances=advanced,
        actions=(
            ConfirmationActionV1(action_number=1, action_kind="AUTHORITY_AND_CORE"),
            ConfirmationActionV1(action_number=2, action_kind="ADVANCED_REVIEWED_DEFAULTS"),
        ),
        second_setup_screen=False,
    )


def validate_current_setup(
    receipt: RunSetupAcceptanceV1,
    *,
    policy: PolicyV2,
    source_slots: tuple[SourceSlotSelectionV1, ...],
) -> None:
    if receipt.authority_binding_sha256 != canonical_sha256(source_slots) or receipt.source_slots != source_slots:
        raise SetupGateError("source authority changed after setup acceptance")
    for item in (*receipt.core_field_acceptances, *receipt.advanced_field_acceptances):
        if item.value_sha256 != _field_hash(policy, item.field_name):
            raise SetupGateError(f"policy acceptance invalidated for field {item.field_name}")


def bind_post_preflight_manifest(
    *,
    receipt: RunSetupAcceptanceV1,
    source_slot_id: str,
    manifest: SourceManifestV1,
    identity: PostPreflightIdentityV1,
) -> BoundSourceAuthorityV1:
    slots = [slot for slot in receipt.source_slots if slot.source_slot_id == source_slot_id]
    if len(slots) != 1:
        raise SetupGateError("source slot is not uniquely confirmed")
    slot = slots[0]
    manifest_binding = [binding for binding in manifest.authority_bindings if binding.source_slot_id == source_slot_id]
    matches = (
        manifest.run_id == receipt.run_id
        and manifest.adapter_id == slot.adapter_id == identity.adapter_id
        and manifest.source_mode is slot.source_mode is identity.source_mode
        and slot.authority_role == identity.authority_role
        and len(manifest_binding) == 1
        and manifest_binding[0].authority_role == slot.authority_role
        and (
            slot.expected_non_secret_identity_fingerprint is None
            or slot.expected_non_secret_identity_fingerprint == identity.actual_non_secret_identity_fingerprint
        )
    )
    if not matches:
        raise SetupGateError("SOURCE_SLOT_IDENTITY_MISMATCH")
    payload = {
        "source_slot_id": slot.source_slot_id,
        "authority_role": slot.authority_role,
        "source_manifest_id": manifest.source_manifest_id,
        "source_instance_id": manifest.source_instance_id,
        "actual_identity_fingerprint": identity.actual_non_secret_identity_fingerprint,
    }
    return BoundSourceAuthorityV1(
        source_slot_id=slot.source_slot_id,
        authority_role=slot.authority_role,
        source_manifest_id=manifest.source_manifest_id,
        source_instance_id=manifest.source_instance_id,
        binding_sha256=canonical_sha256(payload),
    )
