# Tasks

## 1. Gates and preconditions

- [x] 1.1 Run the anti-detection hash gate and verify it prints
  `2d7a90e533196af61745bc4efd3259b7b64b519b8ec78662392b50a911285e23` for
  `docs/reference/CURRENT/ARCH_v5.1.5.1_Vol3_Capture_AntiDetection.md`; abort and
  report otherwise
- [x] 1.2 Confirm test entry points and tooling: `uv run pytest -q` runs the
  existing suite green and `python3 scripts/check_constants.py` exits 0 before any
  edit
- [x] 1.3 Confirm the §AI.3 rename scope: grep ARCH V1 §AI.4–§AI.6 for the four lane
  tokens; record the drift note (design.md "B7 drift note") and verify those sections
  are not edited

## 2. Q3 `_PCT` → `_RATIO` split (brief 2.1)

- [x] 2.1 RED: add/adjust a test asserting `SPX_FALSE_CROSS_TOLERANCE_RATIO` exists
  with value `0.0015` and no fraction-valued `_PCT` name is generated; verify it fails
  against the current module
- [x] 2.2 Rename the 11 fraction-valued `*_PCT` names to `*_RATIO` in ARCH V1 §AI.3
  (values unchanged); verify with `grep` that no `*_PCT` name in §AI.3 has a value in
  `(0, 1)`
- [x] 2.3 Regenerate with `python3 scripts/gen_constants.py` and update every
  consumer/test import of the renamed names; verify `uv run pytest -q` passes
- [x] 2.4 GREEN: verify the 2.1 test passes and `python3 scripts/check_constants.py`
  exits 0

## 3. Q4 lane rename + unit-suffix lint (brief 2.2)

- [x] 3.1 RED: write `tests/unit/domain/test_unit_suffix_lint.py` over the generated
  module (registered-suffix set plus a `{name: reason}` allowlist, and the
  fraction-`_PCT` guard) with a `tmp_path` bad-constant fixture; verify the fixture
  fails the lint before the rename
- [x] 3.2 Rename the four §AI.3 lane constants to `LANE_LATENCY_CUTOFF_MS_2DTE`,
  `_SHORT_TACTICAL`, `_SWING`, `_LONGER_HORIZON` (values 3000/5000/10000/30000) and
  regenerate; verify the four new names and values via a test
- [x] 3.3 Populate the allowlist with every remaining non-suffixed constant and a
  written reason (one entry per constant); verify the lint reports no violation on the
  regenerated module

## 4. Q5 generator label + approval invariant (brief 2.3)

- [x] 4.1 RED: add a `check_constants` test asserting an orphan constant (neither
  approved nor `_APPROVAL_PENDING`) fails with a clear error; verify it fails today
- [x] 4.2 Derive the pending-set label in `scripts/gen_constants.py` from the ARCH
  §AI.3 `[RECOMMENDED ...]` marker text (remove the hardcoded "C12 dealer/greeks") and
  regenerate; verify the module docstring/pending comment show the marker text
- [x] 4.3 Add `verify_approval_companions` to `scripts/check_constants.py` (every
  constant approved or has a `<NAME>_APPROVAL_PENDING` companion) and confirm
  `MIN_VEGA` is approved and a block member is pending; verify
  `python3 scripts/check_constants.py` exits 0 and the 4.1 test passes

## 5. `cooldown_until` + frozen-DDL conformance (brief 2.4)

- [x] 5.1 RED: write `tests/unit/domain/test_ddl_column_conformance.py` (parse
  SPEC V2 §19.2 columns, start-of-line **or** post-comma; classify only names that
  declare a time token per the boundary-anchored filter, invert the design — no
  non-time allowlist); verify it fails today on `cooldown_until`
- [x] 5.2 Add `"_until"` to `EPOCH_NAME_SUFFIXES` in `src/quantflow/domain/time.py`
  and add `*_until` to SPEC V1 §19.8.3 Rule 1; verify `cooldown_until` and `rearmed_at`
  classify as epoch via a test
- [x] 5.3 GREEN: assert every time-token column classifies, `*_date` columns are TEXT,
  and a pinned positive list of known time columns matches; verify the conformance test
  passes and no time-shaped column is exempt

## 6. 005b `random` call-name regression (brief 2.5)

- [x] 6.1 RED: add
  `test_scan_does_not_flag_injected_generator_rng_method` (fixture
  `def f(rng): return rng.random() + rng.normal()`) asserting zero violations; verify
  it fails today
- [x] 6.2 Remove `"random"`, `"randint"`, `"randrange"` from `BANNED_CALL_NAMES`
  (keep `"random"` in `BANNED_MODULES`), document the reasoning in the test docstring,
  and update the `test_scan_detects_random_and_uuid_shapes` count to the module-ban
  violations only; verify 6.1 passes and the `import random` /
  `from random import randint` tests still fail as expected
- [x] 6.3 Update `openspec/changes/005c-domain-cleanup/specs/epoch-clock/spec.md`
  only if the implemented call-name set differs from the delta; verify
  `uv run pytest -q tests/unit/test_wall_clock_scan.py` passes

## 7. Test gaps and epoch message split (brief 2.6)

- [x] 7.1 Add the Hypothesis `micros_to_mills` oracle test to
  `tests/unit/domain/test_units.py`; verify it passes over the default 100 examples
- [x] 7.2 Add `test_epoch_ms_rejects_bool` / `test_duration_ms_rejects_bool` asserting
  `TypeError` (from `units.checked_int`); verify both pass
- [x] 7.3 Split the `epoch_ms()` range check into below-`EPOCH_MS_MIN` and
  above-`EPOCH_MS_MAX` branches with distinct messages; update the two `match=`
  assertions in `tests/unit/domain/test_time.py` and verify they pass

## 8. Q14 dollars-conversion AST guard (brief 2.7)

- [x] 8.1 RED: write `tests/unit/domain/test_dollars_conversion_scan.py` (AST scan
  over `domain/**` and `kernels/**`, empty allowlist, divisor literals
  `100`/`1000`/`1_000_000` or named dollars divisors) with a bad-expression fixture;
  verify the fixture is flagged and the real tree passes
- [x] 8.2 Confirm `micros_to_mills` (divisor `MICROS_PER_MILL`) is not flagged and the
  scan passes with the empty allowlist; verify no allowlist entries are needed yet

## 9. Documentation, conflicts log, and final verification

- [x] 9.1 Apply the AGENTS.md corrections (Q2 narrow-float rule, Q7 structural
  exemption, disjoint-vocabulary rewording) and the `check_constants.py` docstring
  exemption note; verify AGENTS.md stays ≤ 40 lines and reads correctly
- [x] 9.2 Append the brief Part 3 entries under "Resolved (2026-10-16)" in
  `openspec/conflicts-and-gaps.md` (Q3, Q4, Q5, Q7, Q10 deferred, `cooldown_until`,
  random call-name regression); verify the seven entries are present and correctly
  marked
- [x] 9.3 Run the full gate: `uv run pytest -q`, `uv run ruff check src tests`,
  `uv run ruff format --check src tests`, `uv run mypy --strict src/quantflow`,
  `uv run pytest --cov=src/quantflow --cov-report=term-missing` (domain/** ≥ 95%),
  `python3 scripts/check_constants.py`; verify all exit 0
- [x] 9.4 Re-run the anti-detection hash gate (task 1.1) and verify
  `git diff --stat docs/reference/release-v2.0.5.1-v5.1.5.1/` shows only ARCH Vol 1
  (the `*_RATIO` references and the §AI.3 lane constants), SPEC V1 §19.8.3, and the
  `SHA256SUMS` entry for those two files (use the resolved path; `docs/reference/CURRENT/`
  is a symlink and prints nothing), and `git status --short` has no `.bak-` files

## Workflow follow-up

- Archive the change after review: `/opsx-verify 005c-domain-cleanup`, then
  `/opsx-archive`, so the three spec deltas land in `openspec/specs/` and the
  conflicts log stays current.
