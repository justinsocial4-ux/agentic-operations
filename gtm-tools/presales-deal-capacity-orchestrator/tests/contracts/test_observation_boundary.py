import pytest
from pydantic import ValidationError

from orchestrator.contracts.records import AnalystObservationV2

BASE = {
    "schema_version": "orchestrator.analyst-observation.v2",
    "run_id": "run-1",
    "analysis_mode": "RECORDED_ANALYST_REPLAY",
    "input_sha256": "a" * 64,
    "deal_source_id": "deal-1",
    "dimension_id": "success-criteria",
    "state": "UNKNOWN",
    "citations": (),
}


def test_observation_rejects_consultant_fit_and_win_rate_fields() -> None:
    for forbidden in ("consultant_id", "candidate_score", "individual_win_rate", "sentiment"):
        with pytest.raises(ValidationError):
            AnalystObservationV2.model_validate({**BASE, forbidden: "forbidden"})


def test_supported_requires_exact_citation_shape() -> None:
    with pytest.raises(ValidationError, match="SUPPORTED requires"):
        AnalystObservationV2.model_validate({**BASE, "state": "SUPPORTED"})
