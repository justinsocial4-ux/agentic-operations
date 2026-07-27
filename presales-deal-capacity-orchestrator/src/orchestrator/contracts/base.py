from __future__ import annotations

import json
from datetime import datetime
from typing import Annotated, Any, TypeVar

from pydantic import BaseModel, ConfigDict, StringConstraints

T = TypeVar("T", bound="StrictContract")

Identifier = Annotated[str, StringConstraints(min_length=1, max_length=256, pattern=r"^[A-Za-z0-9][A-Za-z0-9._:%/@+-]*$")]
Sha256 = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]
ExactDecimalString = Annotated[str, StringConstraints(pattern=r"^-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?$")]
CurrencyCode = Annotated[str, StringConstraints(pattern=r"^[A-Z]{3}$")]


def _reject_duplicate_object_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def strict_json_loads(payload: str | bytes | bytearray) -> Any:
    """Decode JSON while rejecting duplicate keys and non-standard constants."""

    def reject_constant(value: str) -> None:
        raise ValueError(f"non-finite JSON number is forbidden: {value}")

    return json.loads(
        payload,
        object_pairs_hook=_reject_duplicate_object_pairs,
        parse_constant=reject_constant,
    )


def require_offset_aware(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timestamp must include a UTC offset")
    return value


class StrictContract(BaseModel):
    model_config = ConfigDict(
        strict=True,
        extra="forbid",
        frozen=True,
        validate_default=True,
        ser_json_inf_nan="null",
    )

    @classmethod
    def model_validate_json(cls: type[T], json_data: str | bytes | bytearray, **kwargs: Any) -> T:
        """Override Pydantic's JSON boundary so duplicate-key rejection is not optional."""
        decoded = strict_json_loads(json_data)
        normalized = json.dumps(decoded, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
        return super().model_validate_json(normalized, **kwargs)

    @classmethod
    def model_validate_json_strict(cls: type[T], payload: str | bytes | bytearray) -> T:
        return cls.model_validate_json(payload)
