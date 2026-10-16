"""005c: generated constants carry a unit/shape suffix (Q3/Q4).

Spec domain-constants scenarios:
- "Constant names encode their unit suffix" (registered set or allowlist)
- "Whole percent points and dimensionless ratios are distinct suffixes"
- "Lane latency cutoffs are named with their millisecond unit"
Sources: 005c brief D1/B1b; ARCH V1 Sec AI.3; conflicts Q3/Q4.
"""

import ast
import re
from pathlib import Path

import pytest

from quantflow.domain import constants

CONSTANTS_MODULE = Path(__file__).parents[3] / "src" / "quantflow" / "domain" / "constants.py"

_UPPER_SNAKE = re.compile(r"^[A-Z][A-Z0-9_]*$")

# Registered unit/shape suffixes (spec "Registered suffix vocabulary").
REGISTERED_SUFFIXES = (
    "_MS",
    "_S",
    "_DAYS",
    "_D",
    "_USD",
    "_CENTS",
    "_MICROS",
    "_MILLS",
    "_MICROCENTS",
    "_BPS",
    "_MB",
    "_PCT",
    "_PPM",
    "_RATIO",
    "_FRAC",
    "_PCTL",
    "_MULT",
    "_COUNT",
    "_SNAPS",
    "_H",
    "_WEIGHT",
)

# Constants whose unit/shape token is mid-name rather than a trailing suffix.
# Each entry carries a reason (spec "Allowlisted constant requires a recorded
# reason"); additions are deliberate, one entry at a time.
ALLOWLIST: dict[str, str] = {
    # greek / risk-scale quantities (ARCH V1 Sec AI.3)
    "MIN_VEGA": "per-contract vega scale; greek quantity",
    "GREEKS_SIGMA_MIN": "implied-vol sigma floor; vol-scale quantity",
    "GREEKS_SIGMA_MAX": "implied-vol sigma ceiling; vol-scale quantity",
    # dimensionless [0,1] ratios (Q2: floats allowed, no unit suffix)
    "DEALER_COVERAGE_MIN": "coverage ratio [0,1]; dimensionless (Q2)",
    "DEALER_R_MIN_FALLBACK": "fallback R ratio [0,1]; dimensionless (Q2)",
    "DEALER_R_FULL_FALLBACK": "full R ratio [0,1]; dimensionless (Q2)",
    "TRACE_SIMILARITY_ALERT": "similarity ratio [0,1]; dimensionless (Q2)",
    "HEDGE_PENALTY_DEFAULT": "hedge penalty ratio [0,1]; dimensionless (Q2)",
    "DELTA_FLOOR_WEIGHT_ADJUST": "weight-adjust fraction [0,1]; dimensionless (Q2)",
    "MIN_VOL_INDEX_COVERAGE": "coverage ratio [0,1]; dimensionless (Q2)",
    "SAFETY_MARGIN": "safety fraction [0,1]; dimensionless (Q2)",
    "ZERO_DTE_MEDIUM_FLOW_STRENGTH_MIN": "flow-strength ratio [0,1]; dimensionless (Q2)",
    "ZERO_DTE_HIGH_CONFLUENCE_MIN": "confluence ratio [0,1]; dimensionless (Q2)",
    "ZERO_DTE_CONFIRMATION_BUFFER_ATR": "ATR multiple; dimensionless (Q2)",
    "ZERO_DTE_VANNA_RELEVANCE_MIN": "vanna relevance ratio [0,1]; dimensionless (Q2)",
    "ZERO_DTE_OPPOSITE_FLOW_LIMIT": "opposite-flow share [0,1]; dimensionless (Q2)",
    "ZERO_DTE_PERCENTILE_FALLBACK_PENALTY": "fallback penalty [0,1]; dimensionless (Q2)",
    # percentile ranks; the _PCTL token is mid-name
    "DEALER_R_PCTL_MIN": "percentile rank; _PCTL token mid-name",
    "DEALER_R_PCTL_FULL": "percentile rank; _PCTL token mid-name",
    # counts and model quantities (unit not one of the registered shapes)
    "LEVEL_THETA": "level-emit price distance; model quantity",
    "LEVEL_EPS": "level-proximity epsilon; model quantity",
    "FLIP_GRID_POINTS": "grid point count",
    "GRID_MAX_POINTS": "grid point count",
    "TRACE_FLAG_COUNT_ALERT": "trace flag count",
    "STAGE4_MIN_N_PER_CELL": "minimum sample count per cell",
    "IVR_HISTORY_REQUIRED_SESSIONS": "required session count",
    "ZERO_DTE_CLUSTER_MIN_EVENTS": "minimum event count",
    "ZERO_DTE_CLUSTER_MIN_STRIKES": "minimum strike count",
    "ZERO_DTE_MEDIUM_EVENT_MIN": "minimum event count",
    "ZERO_DTE_MEDIUM_STRIKE_MIN": "minimum strike count",
    # flow/confluence weights (ARCH V1 Sec AI.3 D.14b); _WEIGHT token mid-name
    "ZERO_DTE_FLOW_WEIGHT_DELTA": "flow weight [0,1] (D.14b)",
    "ZERO_DTE_FLOW_WEIGHT_PREMIUM": "flow weight [0,1] (D.14b)",
    "ZERO_DTE_FLOW_WEIGHT_DIRECTION": "flow weight [0,1] (D.14b)",
    "ZERO_DTE_FLOW_WEIGHT_EVENTS": "flow weight [0,1] (D.14b)",
    "ZERO_DTE_FLOW_WEIGHT_STRIKES": "flow weight [0,1] (D.14b)",
    "ZERO_DTE_CONFLUENCE_WEIGHT_FLOW": "confluence weight [0,1] (D.14b)",
    "ZERO_DTE_CONFLUENCE_WEIGHT_DEALER": "confluence weight [0,1] (D.14b)",
    "ZERO_DTE_CONFLUENCE_WEIGHT_PRICE": "confluence weight [0,1] (D.14b)",
    # unit-scale ratio whose token is _CENT, not the _CENTS quantity suffix
    "THETA_MICROCENTS_PER_CENT": "microcents-per-cent accumulator scale (ARCH V1 Sec AI.3)",
    # lane latency cutoffs; the _MS unit token is mid-name by ARCH naming
    "LANE_LATENCY_CUTOFF_MS_2DTE": "lane latency cutoff (ms); _MS token mid-name",
    "LANE_LATENCY_CUTOFF_MS_SHORT_TACTICAL": "lane latency cutoff (ms); _MS token mid-name",
    "LANE_LATENCY_CUTOFF_MS_SWING": "lane latency cutoff (ms); _MS token mid-name",
    "LANE_LATENCY_CUTOFF_MS_LONGER_HORIZON": "lane latency cutoff (ms); _MS token mid-name",
}

LANE_LATENCY_EXPECTED = {
    "LANE_LATENCY_CUTOFF_MS_2DTE": 3000,
    "LANE_LATENCY_CUTOFF_MS_SHORT_TACTICAL": 5000,
    "LANE_LATENCY_CUTOFF_MS_SWING": 10000,
    "LANE_LATENCY_CUTOFF_MS_LONGER_HORIZON": 30000,
}

RENAMED_RATIO_CONSTANTS = [
    "SPX_FALSE_CROSS_TOLERANCE_RATIO",
    "SPX_APPROACHING_RATIO",
    "SPX_APPROACHING_RETREAT_RATIO",
    "SPX_CONFIRMATION_BUFFER_RATIO",
    "GAMMA_FLIP_AGREEMENT_RATIO",
    "WALL_PROXIMITY_RATIO",
    "ZERO_DTE_CONFIRMATION_BUFFER_RATIO",
    "ZERO_DTE_MEDIUM_MIN_COVERAGE_RATIO",
    "STRUCTURE_STOP_MIN_RATIO",
    "PAPER_DEPTH_PARTICIPATION_RATIO",
    "PAYOFF_KERNEL_MAX_INVALID_RATIO",
]


def _module_level_constants(source: str) -> dict[str, object]:
    """Module-level UPPER_SNAKE value assignments (excludes *_APPROVAL_PENDING)."""
    values: dict[str, object] = {}
    for node in ast.parse(source).body:
        target: ast.expr | None = None
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            target = node.target
        if not isinstance(target, ast.Name):
            continue
        name = target.id
        if not _UPPER_SNAKE.match(name) or name.endswith("_APPROVAL_PENDING"):
            continue
        try:
            values[name] = ast.literal_eval(node.value)
        except ValueError:
            continue
    return values


def _suffix_violations(values: dict[str, object], allowlist: dict[str, str]) -> list[str]:
    """Names with no registered suffix and no allowlist entry, sorted."""
    return sorted(
        name for name in values if not name.endswith(REGISTERED_SUFFIXES) and name not in allowlist
    )


def _generated_values() -> dict[str, object]:
    return _module_level_constants(CONSTANTS_MODULE.read_text())


# 2.1 / 3.2: the fraction-valued *_PCT constants were renamed to *_RATIO
def test_fraction_valued_pct_constants_are_renamed_to_ratio():
    assert constants.SPX_FALSE_CROSS_TOLERANCE_RATIO == 0.0015
    assert not hasattr(constants, "SPX_FALSE_CROSS_TOLERANCE_PCT")
    for name in RENAMED_RATIO_CONSTANTS:
        assert hasattr(constants, name), name


# 3.2: lane latency cutoffs renamed with their millisecond unit
def test_lane_latency_constants_carry_ms_suffix_and_values():
    for name, value in LANE_LATENCY_EXPECTED.items():
        assert getattr(constants, name) == value, name
    for bare in ("TACTICAL_2DTE", "SHORT_TACTICAL", "SWING", "LONGER_HORIZON"):
        assert not hasattr(constants, bare), bare


# 2.1: no fraction-valued *_PCT constant remains
def test_no_fraction_valued_pct_constant_remains():
    offenders = {
        name: value
        for name, value in _generated_values().items()
        if name.endswith("_PCT") and isinstance(value, float) and 0.0 < value < 1.0
    }
    assert offenders == {}


# 3.3: every generated constant is registered or explicitly allowlisted
def test_every_constant_ends_in_a_registered_suffix_or_is_allowlisted():
    violations = _suffix_violations(_generated_values(), ALLOWLIST)
    assert violations == [], violations


# 3.1: allowlist entries all carry a reason
def test_allowlist_entries_carry_a_reason():
    assert all(reason.strip() for reason in ALLOWLIST.values())


# 3.1: a deliberately-bad constant fails the lint
def test_lint_flags_a_deliberately_bad_constant():
    values = _module_level_constants('"""bad."""\nMY_INVENTED_THRESHOLD = 2\n')
    violations = _suffix_violations(values, ALLOWLIST)
    assert violations == ["MY_INVENTED_THRESHOLD"], violations


def test_lint_accepts_a_registered_suffix():
    values = _module_level_constants("OPERATION_TIMEOUT_MS = 500\n")
    assert _suffix_violations(values, ALLOWLIST) == []


@pytest.mark.parametrize("suffix", REGISTERED_SUFFIXES)
def test_registered_suffixes_are_recognized(suffix):
    values = {f"INVENTED{suffix}": 1}
    assert _suffix_violations(values, ALLOWLIST) == []
