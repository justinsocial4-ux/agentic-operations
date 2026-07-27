from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any

from orchestrator.contracts.mapping import MappingRuleV1


class ConversionError(ValueError):
    pass


def _crosswalk(rule: MappingRuleV1) -> dict[str, str]:
    return {entry.source_value: entry.canonical_value for entry in rule.crosswalk}


def _scalar(value: Any) -> str:
    if not isinstance(value, (str, int, bool)) or isinstance(value, float):
        raise ConversionError("conversion requires a scalar string/integer/boolean")
    return str(value)


def convert_value(value: Any, rule: MappingRuleV1) -> Any:
    """Apply one closed, deterministic conversion. No conversion supplies defaults."""
    conversion = rule.conversion_id
    if conversion == "IDENTITY":
        return value
    if conversion == "TRIM":
        return _scalar(value).strip()
    if conversion in {"ENUM_CROSSWALK", "EXACT_ID_CROSSWALK"}:
        table = _crosswalk(rule)
        key = _scalar(value)
        if key not in table:
            raise ConversionError("source value has no exact approved crosswalk entry")
        return table[key]
    if conversion == "ISO_TIMESTAMP":
        raw = _scalar(value)
        try:
            parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ConversionError("invalid ISO timestamp") from exc
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise ConversionError("ISO timestamp requires an explicit offset")
        return parsed.isoformat()
    if conversion == "EPOCH_MS_TIMESTAMP":
        raw = _scalar(value)
        try:
            milliseconds = int(raw)
        except ValueError as exc:
            raise ConversionError("epoch milliseconds must be an integer") from exc
        try:
            return datetime.fromtimestamp(milliseconds / 1000, timezone.utc).isoformat()
        except (OverflowError, OSError, ValueError) as exc:
            raise ConversionError("epoch milliseconds are outside the supported range") from exc
    if conversion == "DECIMAL_CURRENCY":
        raw = _scalar(value)
        if raw.strip() != raw or any(character in raw for character in ",$_"):
            raise ConversionError("currency amount must be a plain exact decimal")
        try:
            decimal = Decimal(raw)
        except InvalidOperation as exc:
            raise ConversionError("invalid exact decimal") from exc
        if not decimal.is_finite():
            raise ConversionError("non-finite decimals are forbidden")
        rendered = format(decimal, "f")
        if rendered.startswith("+"):
            rendered = rendered[1:]
        return rendered
    if conversion == "EFFORT_MINUTES_TO_UNITS":
        raw = _scalar(value)
        try:
            minutes = int(raw)
        except ValueError as exc:
            raise ConversionError("effort minutes must be an integer") from exc
        if minutes < 0 or minutes % 30:
            raise ConversionError("effort minutes must be non-negative whole 30-minute units")
        return minutes // 30
    if conversion == "BOOLEAN":
        raw = _scalar(value).strip().lower()
        if raw in {"true", "1", "yes"}:
            return True
        if raw in {"false", "0", "no"}:
            return False
        raise ConversionError("boolean requires an explicit true/false value")
    if conversion == "LIST_SPLIT":
        if not isinstance(value, str):
            raise ConversionError("list split requires text")
        delimiter = rule.list_delimiter
        if delimiter is None:
            raise ConversionError("list split requires an approved delimiter")
        items = tuple(item.strip() for item in value.split(delimiter))
        if any(not item for item in items):
            raise ConversionError("list split produced an empty item")
        return items
    raise ConversionError("unknown conversion")
