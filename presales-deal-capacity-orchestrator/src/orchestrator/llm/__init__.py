"""Local evidence analyst (Phase 6).

Three v1 private-data modes share ONE mode-agnostic validator: LIVE_LOCAL (loopback-only
local model), RECORDED_ANALYST_REPLAY (hash-bound recorded output), and MANUAL_CITATION
(manager-entered exact citations). No remote LLM route exists in v1; the local model's
storage/log/cache behavior is the owner's responsibility, not an app-enforced boundary.
The app enforces only loopback-only LIVE_LOCAL transport and the absence of any remote route.
"""

from .analyst import AnalystRunResult, compute_transcript_input_sha256, run_analyst
from .digest import build_analyst_digest
from .provider import (
    AnalystProvider,
    AnalystProviderError,
    LiveLocalProvider,
    ManualCitationProvider,
    RecordedAnalystReplayProvider,
)
from .validator import ObservationRejected, ValidatedObservation, validate_raw_observation

__all__ = [
    "AnalystProvider",
    "AnalystProviderError",
    "AnalystRunResult",
    "LiveLocalProvider",
    "ManualCitationProvider",
    "ObservationRejected",
    "RecordedAnalystReplayProvider",
    "ValidatedObservation",
    "build_analyst_digest",
    "compute_transcript_input_sha256",
    "run_analyst",
    "validate_raw_observation",
]
