"""Integer money/price unit types for the decision path (SPEC V1 §19.4).

No float may enter the decision path (SPEC V2 §19.4.6: DOUBLE is analysis
only); dollars conversion is forbidden in this module (RQ-006: rounding is
integer-only, round-half-even at the display boundary). Construction validates
the signed 64-bit range (SQLite INTEGER 64-bit / DuckDB BIGINT per
SPEC V2 §19.4.4) and rejects bool/float/non-int inputs fail-closed.
"""

from typing import NewType

from quantflow.domain.errors import UnitValueError

INT64_MIN = -(2**63)
INT64_MAX = 2**63 - 1

MICROS_PER_MILL = 1000

Cents = NewType("Cents", int)
Micros = NewType("Micros", int)
Mills = NewType("Mills", int)


def checked_int(value: object, *, field: str) -> int:
    """Validate a boundary integer: int only (bool rejected), signed 64-bit."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field}: expected int, got {type(value).__name__}")
    if not INT64_MIN <= value <= INT64_MAX:
        raise UnitValueError(f"{field}: {value} outside signed 64-bit range")
    return value


def cents(value: object, *, field: str = "cents") -> Cents:
    """Construct a _cents option-price value from validated boundary input."""
    return Cents(checked_int(value, field=field))


def micros(value: object, *, field: str = "micros") -> Micros:
    """Construct a _micros underlying/index price from validated boundary input."""
    return Micros(checked_int(value, field=field))


def mills(value: object, *, field: str = "mills") -> Mills:
    """Construct a _mills strike/level value from validated boundary input."""
    return Mills(checked_int(value, field=field))


def _round_half_even_div(numerator: int, denominator: int) -> int:
    """Exact integer division rounding ties to even; no float intermediate."""
    quotient, remainder = divmod(numerator, denominator)
    twice_remainder = 2 * remainder
    if twice_remainder > denominator or (twice_remainder == denominator and quotient % 2 != 0):
        quotient += 1
    return quotient


def micros_to_mills(value: Micros) -> Mills:
    """Convert _micros to _mills rounding half to even (RQ-006, integer-only).

    The input is validated like the factories: a float, bool or out-of-range
    value is rejected rather than silently truncated (fail closed).
    """
    checked = checked_int(value, field="micros")
    return Mills(_round_half_even_div(checked, MICROS_PER_MILL))
