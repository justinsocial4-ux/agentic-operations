from __future__ import annotations

import hashlib
import json
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Mapping, TypeAlias

from pydantic import BaseModel

from .contracts.proof import (
    ExportBundleV2,
    RunProofSummaryV1,
    SerializedSourceProofV1,
    SourceProofInputV1,
)
from .contracts.enums import ImplementationProofV1, LiveValidationProofV1

JsonValue: TypeAlias = None | str | bool | int | list["JsonValue"] | dict[str, "JsonValue"]


class CanonicalSerializationError(ValueError):
    pass


def _json_value(value: object) -> JsonValue:
    if isinstance(value, BaseModel):
        return _json_value(value.model_dump(mode="json", by_alias=True, exclude_none=False))
    if isinstance(value, Enum):
        return _json_value(value.value)
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        raise CanonicalSerializationError("floating-point values are forbidden; use exact decimal strings")
    if isinstance(value, Decimal):
        raise CanonicalSerializationError("Decimal must cross contracts as an exact decimal string")
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, (tuple, list)):
        return [_json_value(item) for item in value]
    if isinstance(value, Mapping):
        if any(not isinstance(key, str) for key in value):
            raise CanonicalSerializationError("canonical object keys must be strings")
        return {key: _json_value(item) for key, item in value.items()}
    raise CanonicalSerializationError(f"unsupported canonical type: {type(value).__name__}")


def canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        _json_value(value),
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


class ConsumptionGraph:
    """Phase 0 lineage graph hook. Phase 1 expands edge producers and closure sources."""

    def __init__(self) -> None:
        self._manifested_sources: set[str] = set()
        self._edges: dict[str, set[str]] = defaultdict(set)
        self._decision_roots: set[str] = set()

    def manifest_source(self, source_instance_id: str) -> None:
        self._manifested_sources.add(source_instance_id)

    def record_edge(self, parent: str, child: str) -> None:
        if not parent or not child:
            raise ValueError("lineage graph nodes must be non-empty")
        self._edges[parent].add(child)

    def record_consumption(self, source_instance_id: str, field_id: str) -> None:
        if source_instance_id not in self._manifested_sources:
            raise ValueError("cannot consume an unmanifested source")
        self.record_edge(f"source:{source_instance_id}", f"field:{field_id}")

    def mark_decision_root(self, decision_id: str) -> None:
        self._decision_roots.add(f"decision:{decision_id}")

    @property
    def manifested_sources(self) -> frozenset[str]:
        return frozenset(self._manifested_sources)

    def decision_bearing_sources(self) -> frozenset[str]:
        result: set[str] = set()
        for source in self._manifested_sources:
            start = f"source:{source}"
            queue: deque[str] = deque([start])
            seen = {start}
            while queue:
                node = queue.popleft()
                if node in self._decision_roots:
                    result.add(source)
                    break
                for child in self._edges.get(node, ()):
                    if child not in seen:
                        seen.add(child)
                        queue.append(child)
        return frozenset(result)


@dataclass(frozen=True)
class SourcedDecisionValue:
    source_instance_id: str
    field_id: str
    value: JsonValue


class InstrumentedDecisionInputs:
    """Values are readable only through a session that records their source edge."""

    def __init__(self, values: Mapping[str, SourcedDecisionValue]) -> None:
        self.__values = dict(values)

    def session(self, graph: ConsumptionGraph) -> "DecisionComputation":
        return DecisionComputation(self.__values, graph)


class DecisionComputation:
    def __init__(self, values: Mapping[str, SourcedDecisionValue], graph: ConsumptionGraph) -> None:
        self.__values = values
        self.__graph = graph
        self.__consumed_fields: set[str] = set()

    def read(self, name: str) -> JsonValue:
        sourced = self.__values[name]
        self.__graph.record_consumption(sourced.source_instance_id, sourced.field_id)
        self.__consumed_fields.add(sourced.field_id)
        return sourced.value

    def emit(self, decision_id: str, value: JsonValue) -> JsonValue:
        if not self.__consumed_fields:
            raise ValueError("a decision value cannot be emitted without recorded input consumption")
        for field_id in self.__consumed_fields:
            self.__graph.record_edge(f"field:{field_id}", f"decision:{decision_id}")
        self.__graph.mark_decision_root(decision_id)
        return value


_IMPLEMENTATION_ORDER = {
    ImplementationProofV1.ADAPTER_INTERFACE_ONLY: 0,
    ImplementationProofV1.MOCK_TESTED_ONLY: 1,
    ImplementationProofV1.FULLY_IMPLEMENTED_CONTRACT_TESTED: 2,
}


def build_export_bundle(
    *,
    artifact_id: str,
    payload: object,
    source_proofs: Mapping[str, SourceProofInputV1],
    consumption_graph: ConsumptionGraph,
) -> ExportBundleV2:
    manifested = consumption_graph.manifested_sources
    supplied = frozenset(source_proofs)
    if supplied != manifested:
        missing = sorted(manifested - supplied)
        extra = sorted(supplied - manifested)
        raise ValueError(f"proof closure mismatch; missing={missing}, extra={extra}")

    decision_bearing = consumption_graph.decision_bearing_sources()
    serialized = {
        source_id: SerializedSourceProofV1(
            **proof.model_dump(),
            decision_bearing=source_id in decision_bearing,
        )
        for source_id, proof in sorted(source_proofs.items())
    }

    summary: RunProofSummaryV1 | None = None
    if decision_bearing:
        decision_proofs = [source_proofs[source_id] for source_id in decision_bearing]
        weakest_implementation = min(
            (item.implementation_proof for item in decision_proofs),
            key=_IMPLEMENTATION_ORDER.__getitem__,
        )
        live = (
            LiveValidationProofV1.LIVE_SANDBOX_VALIDATED
            if all(item.live_validation_proof is LiveValidationProofV1.LIVE_SANDBOX_VALIDATED for item in decision_proofs)
            else LiveValidationProofV1.NOT_LIVE_VALIDATED
        )
        summary = RunProofSummaryV1(
            implementation_proof=weakest_implementation,
            live_validation_proof=live,
            derivation="WEAKEST_DECISION_BEARING_SOURCE",
        )

    return ExportBundleV2(
        schema_version="orchestrator.export-bundle.v2",
        artifact_id=artifact_id,
        source_proof_by_instance=serialized,
        run_proof_summary=summary,
        payload_sha256=canonical_sha256(payload),
        execution_authorized=False,
        external_writes_attempted=False,
        assignment_status="RECOMMENDATION_ONLY",
        production_ready=False,
    )
