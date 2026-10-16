"""Epoch-clock spec (005): epoch-ms/duration types and the naming rule.

Tasks 2.1, 2.2, 2.5 (one test per spec scenario).
Sources: SPEC V1 Sec 19.8.1-19.8.4 Rules 1-2; operator ruling RQ-007
(BIGINT/64-bit parity with a validated DURATION_MS_MAX in code).
"""

import dataclasses
from pathlib import Path

import pytest

from quantflow.domain.errors import FieldNameError, UnitValueError
from quantflow.domain.time import (
    DURATION_MS_MAX,
    EPOCH_MS_MAX,
    EPOCH_MS_MIN,
    duration_ms,
    epoch_ms,
    field_name_kind,
)

INT64_MAX = 2**63 - 1
INT64_MIN = -(2**63)


# 2.1 Golden: EpochMs constructs from int, round-trips exactly
def test_construct_epoch_ms_from_int():
    assert epoch_ms(1729012345678) == 1729012345678
    assert epoch_ms(EPOCH_MS_MIN) == EPOCH_MS_MIN
    assert epoch_ms(EPOCH_MS_MAX) == EPOCH_MS_MAX


@pytest.mark.parametrize("bad", [1.5, "100", None], ids=["float", "str", "none"])
def test_epoch_ms_rejects_non_int(bad):
    with pytest.raises(TypeError):
        epoch_ms(bad)


def test_epoch_ms_rejects_out_of_int64():
    with pytest.raises(UnitValueError):
        epoch_ms(INT64_MAX + 1)
    with pytest.raises(UnitValueError):
        epoch_ms(INT64_MIN - 1)


def test_epoch_ms_rejects_bool():
    # bool is an int subclass; it must be rejected like any other wrong type
    # (units.checked_int raises TypeError).
    with pytest.raises(TypeError):
        epoch_ms(True)


def test_duration_ms_rejects_bool():
    with pytest.raises(TypeError):
        duration_ms(False)


# 005b Q8: plausible operational range [EPOCH_MS_MIN, EPOCH_MS_MAX]
# (2010-01-01T00:00:00Z..2060-01-01T00:00:00Z), inclusive, enforced at
# construction; catches seconds/micros silently passed as ms.
def test_epoch_ms_bounds_match_the_spec_dates():
    assert EPOCH_MS_MIN == 1262304000000  # 2010-01-01T00:00:00Z
    assert EPOCH_MS_MAX == 2840140800000  # 2060-01-01T00:00:00Z


def test_seconds_passed_as_ms_are_rejected():
    # Plausible seconds-since-epoch (2023-11-14) is below the ms floor.
    with pytest.raises(UnitValueError, match="below EPOCH_MS_MIN"):
        epoch_ms(1_700_000_000)


def test_micros_passed_as_ms_are_rejected():
    # Plausible micros-since-epoch exceeds the ms ceiling.
    with pytest.raises(UnitValueError, match="above EPOCH_MS_MAX"):
        epoch_ms(1_700_000_000_000_000)


def test_epoch_ms_range_edges_are_inclusive():
    assert epoch_ms(EPOCH_MS_MIN) == EPOCH_MS_MIN
    assert epoch_ms(EPOCH_MS_MAX) == EPOCH_MS_MAX
    with pytest.raises(UnitValueError, match="below EPOCH_MS_MIN"):
        epoch_ms(EPOCH_MS_MIN - 1)
    with pytest.raises(UnitValueError, match="above EPOCH_MS_MAX"):
        epoch_ms(EPOCH_MS_MAX + 1)


def test_duration_ms_max_is_the_column_safe_bound():
    # RQ-007: validated maximum in code, anchored to the DuckDB INTEGER
    # (32-bit) duration column bound, SPEC V1 Sec 19.8.3 Rule 2.
    assert DURATION_MS_MAX == 2**31 - 1


def test_duration_ms_accepts_zero_and_max():
    assert duration_ms(0) == 0
    assert duration_ms(DURATION_MS_MAX) == DURATION_MS_MAX


def test_duration_ms_rejects_negative():
    with pytest.raises(UnitValueError):
        duration_ms(-1)


def test_duration_ms_rejects_above_max():
    with pytest.raises(UnitValueError):
        duration_ms(DURATION_MS_MAX + 1)


@pytest.mark.parametrize("bad", [1.5, "10", None], ids=["float", "str", "none"])
def test_duration_ms_rejects_non_int(bad):
    with pytest.raises(TypeError):
        duration_ms(bad)


# 2.2 Duplicate/idempotency: naming rule exercised on synthetic classes
@dataclasses.dataclass(frozen=True, slots=True)
class RecognizedNames:
    observed_ts: int
    created_at: int
    cursor_epoch_ms: int
    fetch_staleness_ms: int
    wait_duration_ms: int


@dataclasses.dataclass(frozen=True, slots=True)
class AmbiguousName:
    elapsed_ms_wait: int


def test_naming_rule_passes_on_recognized_names():
    for field in dataclasses.fields(RecognizedNames):
        assert field_name_kind(field.name) in {"epoch", "duration"}


def test_naming_rule_fails_on_ambiguous_ms_name():
    for field in dataclasses.fields(AmbiguousName):
        with pytest.raises(FieldNameError):
            field_name_kind(field.name)


# 005a 1.4: a duration suffix matches only on a token boundary (equal, or
# "_" + suffix). Names that merely end in the letters of a suffix are
# ambiguous and must be rejected, not silently classified.
@pytest.mark.parametrize(
    "name",
    ["message_ms", "image_ms", "package_ms", "voltage_ms", "elapsed_ms_wait"],
)
def test_names_that_only_look_like_durations_are_rejected(name):
    with pytest.raises(FieldNameError):
        field_name_kind(name)


@pytest.mark.parametrize(
    "name",
    [
        "age_ms",
        "quote_age_ms",
        "latency_ms",
        "feed_staleness_ms",
        "call_duration_ms",
        "response_ms",
    ],
)
def test_duration_names(name):
    assert field_name_kind(name) == "duration"


@pytest.mark.parametrize(
    "name",
    ["created_at", "bar_ts", "event_epoch_ms", "epoch_ms", "epoch_ms_wait"],
)
def test_epoch_names(name):
    assert field_name_kind(name) == "epoch"


# 005b Q13 (design D3): a name matching BOTH an epoch and a duration
# pattern is ambiguous and raises -- silent precedence is not permitted
# (it is what let epoch_latency_ms through in 005a).
@pytest.mark.parametrize(
    "name",
    ["epoch_latency_ms", "fetch_epoch_staleness_ms", "poll_epoch_age_ms", "epoch_duration_ms"],
)
def test_names_matching_both_patterns_are_rejected(name):
    with pytest.raises(FieldNameError, match="epoch and duration"):
        field_name_kind(name)


# 2.5 Golden: no timezone state; ET rendering stays outside domain//kernels
def test_epoch_and_duration_types_carry_no_timezone_attribute():
    for value in [epoch_ms(1729012345678), duration_ms(60_000)]:
        assert not hasattr(value, "tzinfo")
        assert not hasattr(value, "utcoffset")


def test_no_et_rendering_helper_in_domain_or_kernels():
    root = Path(__file__).parents[3] / "src" / "quantflow"
    for package in ("domain", "kernels"):
        for path in (root / package).rglob("*.py"):
            source = path.read_text()
            assert "ZoneInfo" not in source, path
            assert "zoneinfo" not in source, path
            assert "America/New_York" not in source, path
