NOTE: This change covers Parts 1, 2, and 4 only. Part 3 (open questions)
is deferred to a separate change (005b) and will not be recorded here.
005a Domain hardening (review fixes for 005)

Epic: E0 setup | Depends: 005 (archived) | Blockers: none for Part 1; Part 3 items need operator answers Use: /opsx-propose @openspec/prompts/005a-domain-hardening.md Capabilities (modified, not new): money-units, epoch-clock, domain-enums Sources: 005 review of src/quantflow/domain/{units,time,enums,constants}.py, src/quantflow/adapters/clock.py, tests/unit/test_wall_clock_scan.py, openspec/specs/{money-units,epoch-clock}/spec.md

    Save this file as openspec/prompts/005a-domain-hardening.md and run the Use: line above. The code snippets were written from reading the files on GitHub. They have NOT been executed. Adapt them to the existing test conventions and run the full suite after each item.

Process

    Do NOT edit the archived change openspec/changes/archive/2026-10-16-005-domain-types-units-clock/.
    Spec edits happen as deltas in this new change, not by editing openspec/specs/** directly.
    Classify every item as RESOLVED_FROM_SOURCE / PROPOSED / BLOCKED. Part 1 = PROPOSED (implement). Part 3 = BLOCKED (record, do not implement).
    Tests first (AGENTS rule 12). One item per commit. Keep domain/** coverage at or above 95%.
    Part 3 items: append each to openspec/conflicts-and-gaps.md under "Open questions" and stop on them. Do not invent thresholds, names or formulas (AGENTS rule 11).
    Do not hand-edit src/quantflow/domain/constants.py (generated). Fix scripts/gen_constants.py if a constants change is ever approved.
    Do not touch docs/reference/CURRENT, applied migrations, or /data.
    Tool routing per AGENTS rules 17-18 (harness-tools.*).

Part 1: Implement now
1.1 micros_to_mills must validate its input (HIGH)

File: src/quantflow/domain/units.py

Problem: micros_to_mills calls int(value) with no validation. A float silently truncates (micros_to_mills(1500.9)returns Mills(2)), bool passes, and out-of-range values pass. This breaks "float is rejected" and fail-closed.

Fix:
python

def micros_to_mills(value: Micros) -> Mills:
    """Convert _micros to _mills rounding half to even (RQ-006, integer-only)."""
    checked = checked_int(value, field="micros")
    return Mills(_round_half_even_div(checked, MICROS_PER_MILL))

Tests (add to tests/unit/domain/test_units.py):
python

import pytest
from quantflow.domain.errors import UnitValueError
from quantflow.domain.units import micros_to_mills

@pytest.mark.parametrize("bad", [1500.9, 1500.0, True, "1500", None])
def test_micros_to_mills_rejects_non_int(bad):
    with pytest.raises(TypeError):
        micros_to_mills(bad)  # type: ignore[arg-type]

def test_micros_to_mills_rejects_out_of_range():
    with pytest.raises(UnitValueError):
        micros_to_mills(2**63)  # type: ignore[arg-type]

@pytest.mark.parametrize(
    ("micros_in", "mills_out"),
    [(0, 0), (499, 0), (500, 0), (501, 1), (1499, 1), (1500, 2), (1501, 2),
     (2500, 2), (-500, 0), (-501, -1), (-1500, -2), (-2500, -2)],
)
def test_micros_to_mills_half_even(micros_in, mills_out):
    assert micros_to_mills(micros_in) == mills_out  # type: ignore[arg-type]

Done when: the new tests pass and no other test changed.
1.2 Ban direct construction of unit wrappers; fix SystemClock (HIGH)

Files: new tests/unit/test_direct_unit_construction.py; src/quantflow/adapters/clock.py

Problem: Cents, Micros, Mills, EpochMs, DurationMs are typing.NewType, which is a runtime no-op. Cents(1.5), Cents(True) and Micros(2**70) all succeed. Only the factories (cents(), micros(), mills(), epoch_ms(), duration_ms()) validate. SystemClock.now_ms already calls EpochMs(...) directly.

Chosen default (proceed unless the operator answers Q1 differently): keep NewType, make the factories the only sanctioned constructors, and enforce that with an AST test.

Fix 1: src/quantflow/adapters/clock.py
python

import time

from quantflow.domain.time import EpochMs, epoch_ms


class SystemClock:
    """Concrete Clock reading the OS clock; wired at the application edge."""

    def now_ms(self) -> EpochMs:
        """Current UTC epoch ms (integer, no float). NOTE: time_ns is not monotonic."""
        return epoch_ms(time.time_ns() // 1_000_000, field="now_ms")

Fix 2: new test file
python

"""Direct NewType construction of unit wrappers is banned outside units.py/time.py."""

import ast
from pathlib import Path

SRC_ROOT = Path(__file__).parents[2] / "src" / "quantflow"
WRAPPER_NAMES = {"Cents", "Micros", "Mills", "EpochMs", "DurationMs"}
ALLOWED_FILES = {
    SRC_ROOT / "domain" / "units.py",
    SRC_ROOT / "domain" / "time.py",
}


def find_direct_wrapper_calls(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(), filename=str(path))
    found: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                name: str | None = func.id
            elif isinstance(func, ast.Attribute):
                name = func.attr
            else:
                name = None
            if name in WRAPPER_NAMES:
                found.append(
                    f"{path}:{node.lineno} direct {name}(...); use the validating factory"
                )
    return found


def test_no_direct_wrapper_construction_in_src():
    violations: list[str] = []
    for path in sorted(SRC_ROOT.rglob("*.py")):
        if path in ALLOWED_FILES or "__pycache__" in path.parts:
            continue
        violations.extend(find_direct_wrapper_calls(path))
    assert violations == []


def test_scan_detects_deliberately_bad_fixture(tmp_path):
    bad = tmp_path / "bad_fixture.py"
    bad.write_text(
        "from quantflow.domain.units import Cents\n"
        "import quantflow.domain.time as t\n"
        "x = Cents(1.5)\n"
        "y = t.EpochMs(-1)\n"
    )
    assert len(find_direct_wrapper_calls(bad)) == 2

Known limit (document in the test docstring): typing.cast(Cents, x) is not detected.

Done when: the scan passes on src/, the fixture test passes, and tests/unit/test_clock.py still passes. If any other src/ file calls a wrapper directly, replace it with the factory.
1.3 Pin enum vocabulary behaviour (HIGH)

File: tests/unit/domain/test_enums.py (add tests; do not change enums.py)

Problem: the 005 brief says "same enum literal in two vocabularies → test fails", but ClusterState and EpisodeStatelegitimately share ACTIVE, RETRACTED, EXPIRED (SPEC V2 §19.2). The seed scenario cannot be literally true. What must hold is that the types never bridge.

Tests:
python

import pytest
from quantflow.domain.enums import ClusterGrade, ClusterState, EpisodeState
from quantflow.domain.errors import VocabularyError


def _values(enum_cls):
    return {m.value for m in enum_cls}


def test_overlap_is_exactly_the_documented_shared_literals():
    assert _values(ClusterState) & _values(EpisodeState) == {"ACTIVE", "RETRACTED", "EXPIRED"}


def test_grade_is_disjoint_from_both_state_vocabularies():
    assert _values(ClusterGrade).isdisjoint(_values(ClusterState))
    assert _values(ClusterGrade).isdisjoint(_values(EpisodeState))


def test_basic_is_a_grade_only():
    assert "BASIC" in _values(ClusterGrade)
    with pytest.raises(VocabularyError):
        ClusterState("BASIC")
    with pytest.raises(VocabularyError):
        EpisodeState("BASIC")


def test_shared_literals_never_compare_equal_across_types():
    assert ClusterState.ACTIVE != EpisodeState.ACTIVE
    assert ClusterState.ACTIVE.value == EpisodeState.ACTIVE.value  # documents the overlap


def test_members_do_not_coerce_across_vocabularies():
    with pytest.raises(VocabularyError):
        ClusterState(EpisodeState.ACTIVE)
    with pytest.raises(VocabularyError):
        EpisodeState(ClusterState.ACTIVE)


@pytest.mark.parametrize("lit", ["FORMING", "UPGRADED", "REVERSED"])
def test_episode_only_literals_rejected_by_cluster_state(lit):
    with pytest.raises(VocabularyError):
        ClusterState(lit)


@pytest.mark.parametrize("lit", ["ACTIVE", "active", "Basic", ""])
def test_grade_rejects_unknown_and_case_mangled(lit):
    with pytest.raises(VocabularyError):
        ClusterGrade(lit)

Done when: all pass. Add the spec delta in Part 2 (domain-enums) so the wording matches.
1.4 Token-boundary matching in the naming rule (MEDIUM)

File: src/quantflow/domain/time.py; tests in tests/unit/domain/test_time.py

Problem: field_name_kind uses bare endswith, so message_ms, image_ms and package_ms are classified as durations because they end with age_ms. It also uses a loose "epoch_" in name substring test.

Fix:
python

def _has_token_suffix(name: str, suffixes: tuple[str, ...]) -> bool:
    return any(name == s or name.endswith("_" + s) for s in suffixes)


def _is_epoch_name(name: str) -> bool:
    return (
        name.endswith(EPOCH_NAME_SUFFIXES)
        or name.startswith("epoch_")
        or "_epoch_" in name
    )


def field_name_kind(name: str) -> FieldNameKind:
    """Classify a time field name per SPEC V1 §19.8.3 Rules 1-2; else reject."""
    if _is_epoch_name(name):
        return "epoch"
    if _has_token_suffix(name, DURATION_NAME_SUFFIXES):
        return "duration"
    raise FieldNameError(f"{name}: ambiguous time field name; rename per SPEC V1 §19.8.3")

Tests:
python

@pytest.mark.parametrize("name", ["message_ms", "image_ms", "package_ms", "voltage_ms", "elapsed_ms_wait"])
def test_names_that_only_look_like_durations_are_rejected(name):
    with pytest.raises(FieldNameError):
        field_name_kind(name)


@pytest.mark.parametrize("name", ["age_ms", "quote_age_ms", "latency_ms", "feed_staleness_ms", "call_duration_ms", "response_ms"])
def test_duration_names(name):
    assert field_name_kind(name) == "duration"


@pytest.mark.parametrize("name", ["created_at", "bar_ts", "event_epoch_ms", "epoch_ms", "epoch_ms_wait"])
def test_epoch_names(name):
    assert field_name_kind(name) == "epoch"

Done when: the new tests pass and existing naming tests still pass. If an existing test relied on the loose matching, report it in "Open questions" instead of weakening the new tests.
1.5 Harden the wall-clock AST scan (MEDIUM)

File: tests/unit/test_wall_clock_scan.py

Changes:

    Extend the banned call names:

python

BANNED_CALL_NAMES = {
    "now", "utcnow", "today", "monotonic", "time",
    "time_ns", "monotonic_ns", "perf_counter", "perf_counter_ns",
    "process_time", "process_time_ns", "urandom",
}
BANNED_MODULES = {"time", "datetime", "secrets"}

    Ban relative imports in domain/** and kernels/**. This prevents from .time import x (module name time) from being falsely flagged, and stops relative paths reaching adapters. Insert this branch BEFORE the existing elif isinstance(node, ast.ImportFrom) and node.module: branch:

python

        elif isinstance(node, ast.ImportFrom) and node.level > 0:
            violations.append(
                f"{path}:{node.lineno} relative import "
                "(use absolute quantflow.* imports in domain/kernels)"
            )

    Add fixtures:

python

def test_scan_detects_additional_clock_calls(tmp_path):
    bad = tmp_path / "bad_fixture.py"
    bad.write_text(
        "def f(c):\n"
        "    return c.time_ns() + c.perf_counter() + c.monotonic_ns() + c.process_time()\n"
    )
    assert len(find_wall_clock_violations(bad)) == 4


def test_scan_detects_relative_imports(tmp_path):
    bad = tmp_path / "bad_fixture.py"
    bad.write_text("from . import x\nfrom ..adapters import clock\n")
    assert len(find_wall_clock_violations(bad)) == 2


def test_scan_detects_secrets_import(tmp_path):
    bad = tmp_path / "bad_fixture.py"
    bad.write_text("import secrets\n")
    assert len(find_wall_clock_violations(bad)) == 1

Accepted trade-off (add a comment in the test): generic names like .time() and .today() flag any method with that name. That is intentional fail-closed behaviour.

Not changed here: random and uuid (see Q12).

Done when: the scan passes on current domain/ and kernels/. If a current file uses a relative import, convert it to an absolute import.
Part 2: Spec deltas for this change (wording only, no behaviour beyond Part 1)

Write these as delta specs under the new change's specs/<capability>/spec.md.

money-units (modify "Typed integer unit wrappers"): replace "constructible only from integers" with: "Unit values SHALL be created only through the validating factory functions (cents, micros, mills). Direct NewType construction is prohibited outside domain/units.py and domain/time.py and is enforced by an AST test. Factories SHALL reject non-int, bool, and out-of-signed-64-bit inputs." Add scenario: "Unit conversion functions validate input" (WHEN micros_to_mills receives a float or bool, THEN a type error is raised).

money-units (modify "Dollars only at formula boundaries"): split the rounding sentence into two clear rules: (a) integer unit conversions inside the domain (e.g. micros to mills) use integer-only round-half-even; (b) any dollars figure for display is produced at the presentation boundary, also round-half-even. Remove the single "÷1e6" phrasing for cents and mills, which do not scale by 1e6.

epoch-clock (modify "Epoch vs duration naming rule"): add: "A * in these patterns means an underscore-delimited prefix; a name matches a duration suffix only if it equals the suffix or ends with _ plus the suffix." Add scenarios for message_ms(rejected) and quote_age_ms (duration).

domain-enums (modify the disjointness requirement): define it as: "Vocabularies are disjoint as types: members never compare equal across vocabularies and never coerce across them. cluster_grade shares no literal with the other two. cluster_state and episode_state share exactly ACTIVE, RETRACTED, EXPIRED (SPEC V2 §19.2); BASIC is a grade only." Replace the "same literal in two vocabularies fails" scenario with the tests in 1.3.
Part 3: Open questions (record only; do NOT implement)

Append each to openspec/conflicts-and-gaps.md. Recommended option first.

    Q1 Wrapper strategy. Default in 1.2 is factory-only plus AST ban. Alternative: make wrappers int subclasses with a validating __new__ (also needs arithmetic rules so Cents + Micros raises). Confirm.
    Q2 Floats in constants.py. Thresholds like DEALER_COVERAGE_MIN = 0.80, SPX_*_PCT, weights, and MIN_VEGAare floats, but AGENTS rule 2 says no floats in the decision path. Options: declare them analysis-side only, or restate as integers (for example ppm) via an ARCH V1 §AI.3 amendment.
    Q3 _PCT semantics. SPX_FALSE_CROSS_TOLERANCE_PCT = 0.0015 is a fraction, but BUDGET_FLOW_ALERT_RESERVE_PCT = 60 and BUDGET_PREMARKET_BORROW_PCT = 20 are percent points. A 0.60 vs 60 confusion is possible. Needs an ARCH amendment to normalize the names.
    Q4 Unitless constants. TACTICAL_2DTE = 3000, SHORT_TACTICAL = 5000, SWING = 10000, LONGER_HORIZON = 30000 have no unit in the name. Confirm the unit and rename in ARCH.
    Q5 Approval-pending flags. MIN_VEGA has no _APPROVAL_PENDING companion, and the generated docstring calls the pending set "C12 dealer/greeks" although it includes SPX, WAL, budget and newsletter constants. Verify against ARCH V1 §AI.3, then fix scripts/gen_constants.py if needed.
    Q6 Enforcing approval-pending. Nothing stops a kernel from using a pending constant. Option: an accessor that raises unless approved, or a lint test.
    Q7 Structural constants location. INT64_MIN/MAX, MICROS_PER_MILL, DURATION_MS_MAX and the suffix tuples live in units.py/time.py, not constants.py (AGENTS rule 8). Confirm they are exempt, and check what scripts/check_constants.py covers.
    Q8 Plausible epoch range. epoch_ms accepts any int64, so seconds (~1.7e9) or microseconds pass silently. Operator must supply min/max bounds.
    Q9 DURATION_MS_MAX = 2**31-1 is about 24.86 days; an age_ms over that fails construction. Confirm intended.
    Q10 _epoch_ns. The naming rule accepts it but there is no nanosecond type. Add EpochNs or drop the suffix.
    Q11 Clock port. time.time_ns() is not monotonic. Decide whether the port needs a monotonic reading for durations.
    Q12 Randomness and uuid. Constitution allows only as_of-seeded randomness. Decide how to lint random, uuid, os.urandom in domain/** and kernels/**.
    Q13 Name matches both epoch and duration (for example epoch_latency_ms): currently returns "epoch". Should it be rejected as ambiguous?
    Q14 Dollars conversion for cents/mills. Confirm whether any formula converts them, and with what divisor.
    Q15 pocs/interface/ drift. It duplicates AGENTS.md, .opencode/, and openspec/ and already differs (it lacks 041b-evaluation-protocol.md). Freeze it as a POC snapshot, delete it, or sync it.
    Q16 Unreviewed items. The archived 005 design.md, proposal.md, tasks.md, the domain-enums and repo-bootstrap specs, errors.py, ports/clock.py, and the SPEC citations were not reviewed. Verify them.

Part 4: Housekeeping

    .github/workflows/repo-index.yml commits docs/REPO_INDEX.md to master after pushes. Run git pull --rebase before pushing local work.
    docs/reference/CURRENT appears as a single file in the index, which suggests a symlink. Confirm tests/unit/test_reference_bundle.py covers that.

Verification checklist

    Run the project's test, type-check and lint commands from pyproject.toml / docs/STACK.md.
    Run python3 scripts/check_constants.py.
    Confirm coverage is at least 95% on src/quantflow/domain/**.
    Confirm no changes under openspec/changes/archive/, docs/reference/, applied migrations, or src/quantflow/domain/constants.py.
    Confirm every Part 3 item is recorded in openspec/conflicts-and-gaps.md and none is implemented.
