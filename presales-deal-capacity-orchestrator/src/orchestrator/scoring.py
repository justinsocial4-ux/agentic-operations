from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal, ROUND_CEILING, ROUND_HALF_EVEN

from .canonical import canonical_sha256
from .contracts.domain import (
    PriorityBlockedReceiptV2,
    PriorityFeatureV2,
    PriorityReceiptV2,
    ReadinessReceiptV2,
)
from .contracts.policy import PolicyV2
from .contracts.records import DealWorkRequestV2


class OutOfHorizonError(ValueError):
    queue_lane = "OUT_OF_HORIZON"


def _round_half_even(value: Decimal) -> int:
    return int(value.quantize(Decimal("1"), rounding=ROUND_HALF_EVEN))


def due_week_bucket(*, due_time: datetime, as_of: datetime, horizon_weeks: int = 4) -> int:
    if horizon_weeks != 4:
        raise ValueError("v1 supports exactly four weekly buckets")
    if due_time.tzinfo is None or as_of.tzinfo is None:
        raise ValueError("bucket timestamps must be offset-aware")
    elapsed = due_time - as_of
    if elapsed < timedelta(0) or elapsed > timedelta(weeks=4):
        raise OutOfHorizonError("milestone lies outside the literal four-week horizon")
    elapsed_days = int(
        (Decimal(str(elapsed.total_seconds())) / Decimal("86400")).quantize(
            Decimal("1"), rounding=ROUND_CEILING
        )
    )
    return max(1, min(4, (max(elapsed_days, 1) + 6) // 7))


def _commercial_value(
    deal: DealWorkRequestV2,
    policy: PolicyV2,
) -> tuple[Decimal, str, str, str | None] | None:
    assert deal.commercial_amount is not None
    assert deal.commercial_currency is not None
    assert deal.commercial_basis is not None
    expected = policy.commercial_currency_basis
    if deal.commercial_currency == expected.currency and deal.commercial_basis == expected.basis_id:
        return Decimal(deal.commercial_amount), expected.currency, expected.basis_id, None

    approval = deal.corporate_currency_normalization
    lineage = set(deal.lineage_receipt_ids or ())
    if (
        approval is None
        or approval.corporate_currency != expected.currency
        or approval.corporate_basis_id != expected.basis_id
        or not set(approval.source_lineage_receipt_ids).issubset(lineage)
    ):
        return None
    # The source supplied this approved corporate value. No rate or conversion is
    # available in this module and no original amount arithmetic occurs here.
    return (
        Decimal(approval.normalized_amount),
        approval.corporate_currency,
        approval.corporate_basis_id,
        approval.approval_receipt_id,
    )


def score_priority(
    *,
    run_id: str,
    deal: DealWorkRequestV2,
    readiness: ReadinessReceiptV2,
    policy: PolicyV2,
    policy_sha256: str,
    source_manifest_ids: tuple[str, ...],
    mapping_profile_sha256s: tuple[str, ...],
    as_of: datetime,
    created_at: datetime,
) -> PriorityReceiptV2 | PriorityBlockedReceiptV2:
    """Score deal priority without accepting or reading any consultant population."""
    from .contracts.enums import LaneV1

    deal.validate_for_lane(LaneV1.DEAL_PRIORITIZATION)
    source_manifest_ids = tuple(sorted(set(source_manifest_ids)))
    mapping_profile_sha256s = tuple(sorted(set(mapping_profile_sha256s)))
    if canonical_sha256(policy) != policy_sha256:
        raise ValueError("accepted policy hash does not match PolicyV2")
    if (
        readiness.run_id != run_id
        or readiness.deal_source_id != deal.deal_source_id
        or readiness.policy_sha256 != policy_sha256
        or readiness.source_manifest_ids != source_manifest_ids
        or readiness.mapping_profile_sha256s != mapping_profile_sha256s
    ):
        raise ValueError("readiness receipt is outside the frozen run context")

    commercial = _commercial_value(deal, policy)
    if commercial is None:
        return PriorityBlockedReceiptV2(
            schema_version="orchestrator.priority-blocked-receipt.v2",
            run_id=run_id,
            deal_source_id=deal.deal_source_id,
            queue_lane="INPUT_BLOCKED",
            reason_code="CURRENCY_BASIS_MISMATCH",
            priority_receipt_issued=False,
        )
    amount, currency, basis_id, normalization_receipt_id = commercial
    assert deal.milestone_due_time is not None
    bucket = due_week_bucket(due_time=deal.milestone_due_time, as_of=as_of, horizon_weeks=policy.horizon_weeks)

    days_until_due = int(
        (Decimal(str((deal.milestone_due_time - as_of).total_seconds())) / Decimal("86400")).quantize(
            Decimal("1"), rounding=ROUND_CEILING
        )
    )
    urgency_bp = 0
    for breakpoint in sorted(policy.urgency_breakpoints, key=lambda item: item.latest_days_until_due):
        if days_until_due <= breakpoint.latest_days_until_due:
            urgency_bp = breakpoint.feature_bp
            break

    dimensions = {item.dimension_id: item for item in readiness.dimensions}
    if set(dimensions) != set(policy.readiness_dimensions):
        raise ValueError("readiness dimensions do not exactly match accepted PolicyV2")
    supported_count = sum(dimensions[item].state == "SUPPORTED" for item in policy.readiness_dimensions)
    readiness_bp = _round_half_even(
        Decimal(supported_count) * Decimal(10_000) / Decimal(len(policy.readiness_dimensions))
    )

    floor = Decimal(policy.commercial_value_floor)
    cap = Decimal(policy.commercial_value_cap)
    bounded_amount = min(max(amount, floor), cap)
    commercial_bp = _round_half_even((bounded_amount - floor) * Decimal(10_000) / (cap - floor))

    values = (
        ("MILESTONE_URGENCY", urgency_bp, policy.priority_weights_bp.milestone_urgency),
        ("READINESS_EVIDENCE", readiness_bp, policy.priority_weights_bp.readiness_evidence),
        ("COMMERCIAL_VALUE", commercial_bp, policy.priority_weights_bp.commercial_value),
    )
    features = tuple(
        PriorityFeatureV2(
            feature_id=feature_id,
            feature_bp=feature_bp,
            weight_bp=weight_bp,
            weighted_numerator=feature_bp * weight_bp,
        )
        for feature_id, feature_bp, weight_bp in values
    )
    priority_bp = _round_half_even(Decimal(sum(item.weighted_numerator for item in features)) / Decimal(10_000))
    identity_payload = {
        "run_id": run_id,
        "deal_source_id": deal.deal_source_id,
        "readiness_receipt_id": readiness.readiness_receipt_id,
        "bucket": bucket,
        "amount": str(amount),
        "currency": currency,
        "basis_id": basis_id,
        "normalization_receipt_id": normalization_receipt_id,
        "features": features,
        "priority_bp": priority_bp,
        "policy_sha256": policy_sha256,
    }
    return PriorityReceiptV2(
        schema_version="orchestrator.priority-receipt.v2",
        priority_receipt_id=f"priority-{canonical_sha256(identity_payload)[:32]}",
        run_id=run_id,
        policy_sha256=policy_sha256,
        source_manifest_ids=source_manifest_ids,
        mapping_profile_sha256s=mapping_profile_sha256s,
        deal_source_id=deal.deal_source_id,
        readiness_receipt_id=readiness.readiness_receipt_id,
        due_week_bucket=bucket,
        commercial_amount_used=str(amount),
        commercial_currency=currency,
        commercial_basis_id=basis_id,
        normalization_approval_receipt_id=normalization_receipt_id,
        features=features,
        priority_bp=priority_bp,
        rounding="ROUND_HALF_EVEN",
        created_at=created_at,
    )
