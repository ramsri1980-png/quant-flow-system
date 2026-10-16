"""Money-units spec (005): typed integer wrappers for _cents/_micros/_mills.

Red tests for tasks 1.1-1.7 (one test per spec scenario).
Sources: SPEC V1 Sec 19.4 / 1.4.13 / 1.4.25, SPEC V2 Sec 19.4.4,
operator ruling RQ-006 (integer-only, round-half-even at display boundary).
"""

import ast
from decimal import ROUND_HALF_EVEN, Decimal
from pathlib import Path

import pytest
from hypothesis import given
from hypothesis import strategies as st

from quantflow.domain.errors import UnitValueError
from quantflow.domain.units import (
    INT64_MAX,
    INT64_MIN,
    MICROS_PER_MILL,
    Micros,
    cents,
    micros,
    micros_to_mills,
    mills,
)

CONSTRUCTORS = [cents, micros, mills]
CONSTRUCTOR_IDS = ["cents", "micros", "mills"]


# 1.1 Golden: construct from int, round-trip exactly
@pytest.mark.parametrize("constructor", CONSTRUCTORS, ids=CONSTRUCTOR_IDS)
@pytest.mark.parametrize("value", [0, 1, -1, 123456789, 2**53, -(2**53)])
def test_construct_from_a_valid_integer(constructor, value):
    assert constructor(value) == value


# 1.2 Boundary/units/sign
@pytest.mark.parametrize("constructor", CONSTRUCTORS, ids=CONSTRUCTOR_IDS)
def test_overflow_at_construction_is_rejected(constructor):
    with pytest.raises(UnitValueError):
        constructor(INT64_MAX + 1)
    with pytest.raises(UnitValueError):
        constructor(INT64_MIN - 1)


@pytest.mark.parametrize("constructor", CONSTRUCTORS, ids=CONSTRUCTOR_IDS)
def test_negative_value_round_trips_unchanged(constructor):
    assert constructor(-987654321) == -987654321


@pytest.mark.parametrize("constructor", CONSTRUCTORS, ids=CONSTRUCTOR_IDS)
def test_float_passed_where_int_is_required(constructor):
    with pytest.raises(TypeError):
        constructor(1.5)


@pytest.mark.parametrize("constructor", CONSTRUCTORS, ids=CONSTRUCTOR_IDS)
def test_bool_is_rejected(constructor):
    with pytest.raises(TypeError):
        constructor(True)
    with pytest.raises(TypeError):
        constructor(False)


# 1.3 Property invariants (hypothesis)
@given(st.integers(min_value=-(2**63), max_value=2**63 - 1))
@pytest.mark.parametrize("constructor", CONSTRUCTORS, ids=CONSTRUCTOR_IDS)
def test_property_any_int64_value_round_trips(constructor, value):
    result = constructor(value)
    assert result == value
    assert isinstance(result, int)


# 1.4 Missing/malformed
@pytest.mark.parametrize("constructor", CONSTRUCTORS, ids=CONSTRUCTOR_IDS)
@pytest.mark.parametrize("bad", [None, "100", Decimal("1.00")], ids=["none", "str", "decimal"])
def test_missing_or_malformed_input_is_rejected(constructor, bad):
    with pytest.raises(TypeError):
        constructor(bad)


# 1.6 Golden: no dollars accessor / no float in domain/units.py (AST scan)
def _units_tree() -> ast.Module:
    module_file = Path(__file__).parents[3] / "src" / "quantflow" / "domain" / "units.py"
    return ast.parse(module_file.read_text())


def test_domain_types_expose_no_dollars_accessor():
    tree = _units_tree()
    function_names = {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}
    assert "to_dollars" not in function_names
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute):
            assert node.attr != "to_dollars"


def test_no_float_literal_or_annotation_in_units_module():
    tree = _units_tree()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert not isinstance(node.value, float), f"float constant at line {node.lineno}"
        if isinstance(node, ast.Name):
            assert node.id != "float", f"float reference at line {node.lineno}"


# 1.7 Golden/boundary: integer unit conversions round half-even (RQ-006)
@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (0, 0),
        (999, 1),
        (1000, 1),
        (1499, 1),
        (1500, 2),  # tie -> even (up)
        (2500, 2),  # tie -> even (down)
        (3500, 4),  # tie -> even (up)
        (-1499, -1),
        (-1500, -2),  # tie -> even (down, away from zero)
        (-2500, -2),  # tie -> even (up, toward zero)
        (-3500, -4),
        # extremes: a float intermediate would corrupt these (proves integer-only)
        (2**63 - 1, 9223372036854776),
        (-(2**63), -9223372036854776),
    ],
)
def test_rounding_is_integer_only_and_half_even(value, expected):
    result = micros_to_mills(Micros(value))
    assert isinstance(result, int)
    assert result == expected


def test_rounding_behavior_is_not_invented_per_formula():
    # The single global rule: deterministic half-even, same result every call.
    assert micros_to_mills(Micros(1500)) == micros_to_mills(Micros(1500)) == 2
    assert micros_to_mills(Micros(2500)) == micros_to_mills(Micros(2500)) == 2


# 1.8 (005a) Fail closed: the converter validates its input like the factories
@pytest.mark.parametrize("bad", [1500.9, 1500.0, True, "1500", None])
def test_micros_to_mills_rejects_non_int(bad):
    with pytest.raises(TypeError):
        micros_to_mills(bad)  # type: ignore[arg-type]


def test_micros_to_mills_rejects_out_of_range():
    with pytest.raises(UnitValueError):
        micros_to_mills(2**63)  # type: ignore[arg-type]


# 005c 7.1: property oracle -- the integer half-even divider must agree with
# Decimal ROUND_HALF_EVEN over the whole signed 64-bit range (proves the
# hand-rolled integer path has no float intermediate and no tie bias).
@given(st.integers(min_value=INT64_MIN, max_value=INT64_MAX))
def test_micros_to_mills_matches_decimal_half_even_oracle(value):
    expected = int(
        (Decimal(value) / Decimal(MICROS_PER_MILL)).quantize(Decimal(1), rounding=ROUND_HALF_EVEN)
    )
    assert micros_to_mills(Micros(value)) == expected


@pytest.mark.parametrize(
    ("micros_in", "mills_out"),
    [
        (0, 0),
        (499, 0),
        (500, 0),
        (501, 1),
        (1499, 1),
        (1500, 2),
        (1501, 2),
        (2500, 2),
        (-500, 0),
        (-501, -1),
        (-1500, -2),
        (-2500, -2),
    ],
)
def test_micros_to_mills_half_even(micros_in, mills_out):
    assert micros_to_mills(micros_in) == mills_out  # type: ignore[arg-type]
