005c Domain cleanup — PCT/PPM split, unit-suffix lint, 005b regression, test gaps

Epic: E0 setup | Depends: 005b (merged) | Blockers: none
Use: /qf-propose @openspec/prompts/005c-domain-cleanup.md
Expected change directory: openspec/changes/005c-domain-cleanup/
Capabilities (modified): domain-constants, epoch-clock, money-units
Sources: 005a open questions Q3, Q4, Q5, Q7 (openspec/conflicts-and-gaps.md);
  005b review follow-ups (random regression, test gaps, cooldown_until)

## Process
- This is a PROPOSE-phase prompt. Produce ONLY proposal.md, design.md,
  tasks.md, and spec deltas under openspec/changes/005c-domain-cleanup/.
  Do NOT modify source files during propose. Code changes come later via
  /qf-apply.
- Do NOT edit the archived 005, 005a, or 005b changes.
- Spec edits are deltas under this change, not edits to openspec/specs/**.
- Classify each item RESOLVED_FROM_SOURCE / PROPOSED / BLOCKED.
- Tests first. One item per commit. domain/** coverage stays >= 95%.
- Do not invent thresholds, names, or formulas (AGENTS rule 11).
- Do not hand-edit src/quantflow/domain/constants.py (generated).
- Anti-detection gate: BEFORE committing anything, run
    sha256sum docs/reference/CURRENT/ARCH_v5.1.5.1_Vol3_Capture_AntiDetection.md
  Expected: 2d7a90e533196af61745bc4efd3259b7b64b519b8ec78662392b50a911285e23
  If the hash differs, ABORT and report. No item in this change touches
  ARCH Vol 3, SPEC Vol 4 Sec 11, or the anti-detection surface.
- Frozen-bundle scope: only ARCH Vol 1 Sec AI.3 and SPEC Vol 1 Sec 19.8.3 may
  change. Anything else under docs/reference/CURRENT/ is out of scope; revert
  and report.

## Part 1 — Decisions (already made, apply as-is)

### D1 — Suffix policy (Q3)
Three suffixes, each encoding a distinct shape:
- `_PCT` (int): whole percent points only. 60 means 60%.
- `_PPM` (int): parts-per-million for decision-path thresholds.
- `_RATIO` (float): dimensionless [0,1] analysis-only ratios.

Rename the fraction-valued _PCT constants to `_RATIO`:
- `SPX_FALSE_CROSS_TOLERANCE_PCT = 0.0015` -> `SPX_FALSE_CROSS_TOLERANCE_RATIO`
- `GAMMA_FLIP_AGREEMENT_PCT` -> `GAMMA_FLIP_AGREEMENT_RATIO` (if fraction-valued)
- `WALL_PROXIMITY_PCT` -> `WALL_PROXIMITY_RATIO` (if fraction-valued)
Verify each against ARCH Vol 1 Sec AI.3 before renaming; if a name is already
percent-points-valued, leave it as `_PCT`.

### D2 — Structural constants location (Q7)
`EPOCH_MS_MIN`, `EPOCH_MS_MAX`, `DURATION_MS_MAX`, `INT64_MIN/MAX`,
`MICROS_PER_MILL`, and the suffix tuples STAY in `units.py`/`time.py`. They
are type invariants, not tunable config. Document the exemption from AGENTS
rule 8 in AGENTS.md and in the `scripts/check_constants.py` docstring.

### D3 — `_epoch_ns` (Q10)
Deferred. No change in 005c.

### D4 — `cooldown_until` (Claude finding, confirmed real)
`cooldown_until` appears in the frozen DDL (SPEC Vol 2 Sec 19.2 lines ~1504
and ~2174) as an epoch column. Add `_until` to `EPOCH_NAME_SUFFIXES` in
`src/quantflow/domain/time.py`. Add a conformance test that runs
`field_name_kind` over every `*_until` / `*_ts` / `*_at` column name parsed
from the frozen DDL under docs/reference/CURRENT/SPEC_v2.0.5.1_Vol2_Data_Canonical.md,
asserting none raise FieldNameError.

### D5 — 005b regression: `random` in BANNED_CALL_NAMES (Claude finding, must fix)
005b added `"random"` to `BANNED_CALL_NAMES` in
`tests/unit/test_wall_clock_scan.py`. This blocks `rng.random()` where `rng`
is an injected numpy Generator — the exact pattern Q12 permits. Remove
`"random"` from `BANNED_CALL_NAMES`. Keep `"random"` in `BANNED_MODULES`
(module import ban stays). Also drop `"randint"` and `"randrange"` from call
names if they can appear on an injected Generator — evaluate case by case and
document the reasoning in the test docstring.

## Part 2 — Implement (each item independent, tests first)

### 2.1 Q3 suffix split (HIGH)
Files: src/quantflow/domain/constants.py (regenerate),
       scripts/gen_constants.py (if needed for new suffixes),
       every consumer of the renamed constants.
Steps:
- Verify each `*_PCT` name against ARCH Vol 1 Sec AI.3 to classify it as
  whole-percent vs fraction.
- Rename fraction-valued ones to `_RATIO`.
- If any decision-path threshold must become integer `_PPM`, note it in
  design.md as a follow-up; do NOT convert in this change unless the spec
  explicitly requires it.
- Regenerate constants.py via scripts/gen_constants.py.
- Update imports and tests. Grep for old names across src/ and tests/.
Done when: no float-valued `_PCT` remains; pytest, ruff, mypy clean.

### 2.2 Q4 lane latency rename + unit-suffix lint (HIGH)
Files: src/quantflow/domain/constants.py (regenerate),
       scripts/gen_constants.py,
       new tests/unit/domain/test_unit_suffix_lint.py.
Steps:
- Confirm ARCH Vol 1 Sec AI.3 unit for TACTICAL_2DTE etc. (spec says ms).
- Rename to LANE_LATENCY_CUTOFF_MS_2DTE / _SHORT_TACTICAL / _SWING /
  _LONGER_HORIZON. Preserve the value (3000/5000/10000/30000).
- Add AST lint in tests/unit/domain/test_unit_suffix_lint.py: every
  UPPER_SNAKE constant in src/quantflow/domain/constants.py must end in a
  registered unit suffix (_MS, _PCT, _PPM, _RATIO, _MICROCENTS, _BPS,
  _SECONDS, _DAYS, _USD, _CENTS, _MICROS, _MILLS) OR be listed in an
  explicit allowlist with a reason. Fixture: a deliberately-bad constant
  fails the lint.
Done when: lint passes on current constants.py; fixture fails on bad input.

### 2.3 Q5 generator docstring + approval invariant (HIGH)
Files: scripts/gen_constants.py, scripts/check_constants.py.
Steps:
- Change gen_constants.py to derive the pending-set docstring label from
  the actual approval-pending markers in ARCH Vol 1 Sec AI.3, not the
  hardcoded "C12 dealer/greeks" string.
- Change check_constants.py to assert every constant is either approved or
  has an `_APPROVAL_PENDING` companion. If a constant is neither, fail with
  a clear error. This closes the MIN_VEGA gap.
- Regenerate constants.py.
Done when: check_constants.py exit 0 on current tree; a fixture with an
orphan constant fails.

### 2.4 cooldown_until + DDL conformance (HIGH)
Files: src/quantflow/domain/time.py,
       new tests/unit/domain/test_ddl_column_conformance.py.
Steps:
- Add "_until" to the suffix tuple checked by _has_token_suffix inside the
  epoch branch of field_name_kind.
- Write test_ddl_column_conformance.py: parse column names from
  docs/reference/CURRENT/SPEC_v2.0.5.1_Vol2_Data_Canonical.md (regex for
  `^\s*([a-z_]+)\s+(INTEGER|BIGINT|TEXT|REAL|BLOB)`) and assert every name
  either classifies as epoch/duration OR is in an explicit non-time allowlist
  (state, id, notes, etc.). Red first: cooldown_until currently raises.
Done when: the DDL test passes; rearmed_at already passes as _at.

### 2.5 005b random regression (HIGH)
File: tests/unit/test_wall_clock_scan.py.
Steps:
- RED: add test_scan_does_not_flag_injected_generator_rng_method that writes
  a fixture `def f(rng): return rng.random() + rng.normal()` and asserts the
  scan reports zero violations. This fails today because "random" is in
  BANNED_CALL_NAMES.
- GREEN: remove "random" (and randint/randrange if applicable) from
  BANNED_CALL_NAMES. Keep "random" in BANNED_MODULES.
- Keep existing tests for `import random` and `random.randint(...)` passing
  via the module ban.
Done when: injected-generator fixture passes; existing banned-module tests
still pass.

### 2.6 Test gaps (MEDIUM)
Files: tests/unit/domain/test_units.py, tests/unit/domain/test_time.py.
Steps:
- Add to test_units.py:
    @given(st.integers(min_value=INT64_MIN, max_value=INT64_MAX))
    def test_micros_to_mills_matches_decimal_oracle(v):
        from decimal import Decimal, ROUND_HALF_EVEN
        expected = int((Decimal(v) / 1000).quantize(Decimal(1),
                       rounding=ROUND_HALF_EVEN))
        assert micros_to_mills(v) == expected
- Add to test_time.py:
    @pytest.mark.parametrize("bad", [True, False])
    def test_epoch_ms_rejects_bool(bad): ...
    @pytest.mark.parametrize("bad", [True, False])
    def test_duration_ms_rejects_bool(bad): ...
- Split epoch range error messages in src/quantflow/domain/time.py so
  below-MIN and above-MAX are distinguishable. Update the two match=
  assertions accordingly.
Done when: hypothesis test passes with default 100 examples; bool tests
raise UnitValueError (or TypeError, whichever the checked_int helper
already raises -- be consistent).

### 2.7 Q14 dollars-conversion AST guard (MEDIUM)
File: new tests/unit/domain/test_dollars_conversion_scan.py.
Steps:
- AST scan over src/quantflow/domain/** and src/quantflow/kernels/**.
- Flag any BinOp(Div) whose divisor is the literal 100, 1000, or 1_000_000
  or MICROS_PER_DOLLAR/MILLS_PER_DOLLAR/CENTS_PER_DOLLAR constant, UNLESS
  the enclosing function name is in an explicit allowlist.
- Start with an EMPTY allowlist so nothing passes today (fail-closed). Each
  kernel that legitimately converts registers itself in a follow-up.
- Fixture: bad expression flagged.
Done when: scan passes on current tree (no domain code divides by these
values); fixture fails on bad input.

### 2.8 AGENTS.md corrections (LOW, doc-only)
File: AGENTS.md.
Steps:
- Reword the "cluster_grade / cluster_state / episode_state are disjoint
  vocabularies" line to: "Distinct non-bridging types. cluster_state and
  episode_state share ACTIVE / RETRACTED / EXPIRED by SPEC V2 Sec 19.2.
  BASIC is a grade only."
- Add the Q2 narrow-float rule: "Rule 2 interpretation: no floats for
  money, time, quantity, or price. Dimensionless [0,1] ratios may be float
  (e.g. opposing_share, confluence_score, coverage caps). Decision-path
  thresholds that gate a state use integer _PPM. Whole percent points use
  integer _PCT."
- Add the Q7 exemption: "Structural constants (INT64_MIN/MAX, MICROS_PER_MILL,
  DURATION_MS_MAX, EPOCH_MS_MIN/MAX, suffix tuples) live in units.py/time.py
  by design; they are type invariants, not tunable config, and are exempt
  from rule 8."

## Part 3 — Deferred (record only, do not implement)
Append to openspec/conflicts-and-gaps.md under "Resolved (2026-10-16)":
- Q3: suffix split per D1, implemented in 005c.
- Q4: renamed to _LANE_LATENCY_CUTOFF_MS per ARCH Sec AI.3, implemented in 005c.
- Q5: generator + check_constants invariant, implemented in 005c.
- Q7: structural constants stay in time.py/units.py, exemption documented.
  Resolved by documentation, no code move.
- Q10: DEFERRED until feature 020 handles nanosecond timestamps.
- cooldown_until: RESOLVED (005c) -- _until added to epoch suffixes.
- random call-name regression: RESOLVED (005c) -- call-name ban removed,
  module ban kept.

## Verification checklist (run before commit)
- uv run pytest -q
- uv run ruff check src tests
- uv run ruff format --check src tests
- uv run mypy --strict src/quantflow
- uv run pytest --cov=src/quantflow --cov-report=term-missing  (domain/** >= 95%)
- python3 scripts/check_constants.py  (exit 0)
- sha256sum docs/reference/CURRENT/ARCH_v5.1.5.1_Vol3_Capture_AntiDetection.md
    Must equal 2d7a90e533196af61745bc4efd3259b7b64b519b8ec78662392b50a911285e23
- git diff --stat docs/reference/CURRENT/  -- only ARCH Vol 1 Sec AI.3
    and SPEC Vol 1 Sec 19.8.3 sections may appear; everything else reverts.
- git status --short  -- no .bak- files staged.

## Out of scope (do not attempt in 005c)
- No change to ARCH Vol 3, SPEC Vol 4 Sec 11, or anti-detection.
- No new EpochNs type (Q10 deferred).
- No conversion of decision-path floats to _PPM unless the ARCH spec
  explicitly requires it (D1 says note as follow-up).
- No move of EPOCH_MS_MIN/MAX to constants.py (D2 says stay in time.py).
- Layout rule (constitution Sec 12) is optional and NOT part of this change.
