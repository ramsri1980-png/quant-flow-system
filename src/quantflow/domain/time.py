"""UTC epoch-ms and bounded duration types (SPEC V1 §19.8.1-19.8.4).

Storage parity: SQLite INTEGER (64-bit), DuckDB BIGINT for epoch columns
(Rule 1); durations are bounded integers validated in code against
DURATION_MS_MAX (Rule 2; RQ-007: no int32 type bound, the column-safe
maximum is enforced at construction). No timezone state lives here -- ET is
display-only (SPEC V1 §19.8.4).
"""

from typing import Literal, NewType

from quantflow.domain.errors import FieldNameError, UnitValueError
from quantflow.domain.units import checked_int

DURATION_MS_MAX = 2**31 - 1

EPOCH_NAME_SUFFIXES = ("_ts", "_at", "_epoch_ms", "_epoch_ns")
DURATION_NAME_SUFFIXES = (
    "latency_ms",
    "staleness_ms",
    "age_ms",
    "duration_ms",
    "response_ms",
)

EpochMs = NewType("EpochMs", int)
DurationMs = NewType("DurationMs", int)

FieldNameKind = Literal["epoch", "duration"]


def epoch_ms(value: object, *, field: str = "epoch_ms") -> EpochMs:
    """Construct a UTC epoch-ms value from validated boundary input."""
    return EpochMs(checked_int(value, field=field))


def duration_ms(value: object, *, field: str = "duration_ms") -> DurationMs:
    """Construct a bounded duration (0..DURATION_MS_MAX) from boundary input."""
    checked = checked_int(value, field=field)
    if checked < 0 or checked > DURATION_MS_MAX:
        raise UnitValueError(f"{field}: {checked} outside 0..DURATION_MS_MAX")
    return DurationMs(checked)


def _has_token_suffix(name: str, suffixes: tuple[str, ...]) -> bool:
    """True when name equals a suffix or ends with "_" + that suffix.

    Token-boundary match: "message_ms" ends with the letters of "age_ms" but
    not on a token boundary, so it is not a duration match (SPEC V1 §19.8.3).
    """
    return any(name == suffix or name.endswith("_" + suffix) for suffix in suffixes)


def _is_epoch_name(name: str) -> bool:
    """True for an epoch name: suffix, "epoch_" prefix, or "_epoch_" token."""
    return name.endswith(EPOCH_NAME_SUFFIXES) or name.startswith("epoch_") or "_epoch_" in name


def field_name_kind(name: str) -> FieldNameKind:
    """Classify a time field name per SPEC V1 §19.8.3 Rules 1-2; else reject."""
    if _is_epoch_name(name):
        return "epoch"
    if _has_token_suffix(name, DURATION_NAME_SUFFIXES):
        return "duration"
    raise FieldNameError(f"{name}: ambiguous time field name; rename per SPEC V1 §19.8.3")
