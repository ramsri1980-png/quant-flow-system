# Tasks: 005 Domain types, units, clock

Test classes (constitution Sec 11 / brief seed scenarios) mapped per group:
golden, boundary/units/sign, missing/stale/malformed, duplicate/idempotency,
port contract, migration (N/A -- no DB code in this change), replay (N/A),
property invariants, no-future-leakage (N/A -- no time-dependent kernels
yet; covered by wall-clock AST scan), temp-paths-only.

## 0. Resolve BLOCKING open questions with operator (before implementation)

- [x] 0.1 Confirm rounding mode for unit-to-dollars (÷1e6) conversions, or
  confirm "defer to first formula feature (030+) with explicit per-formula
  mode" (design Open Questions, item 1). Record ruling in
  `openspec/conflicts-and-gaps.md`.
  RESOLVED 2026-10-15 (operator): integer-only, round-half-even at the
  display boundary; recorded as RQ-006 in the conflicts log.
- [x] 0.2 Confirm or reject the PROPOSED int32 bound on DurationMs (design
  Open Questions, item 2). Record ruling.
  RESOLVED 2026-10-15 (operator): no int32 bound; DurationMs stays BIGINT
  (64-bit) with a validated maximum `DURATION_MS_MAX` in code; recorded as
  RQ-007 in the conflicts log.

## 1. money-units (red tests first)

- [x] 1.1 Golden: `_cents`/`_micros`/`_mills` construct from int, round-trip
  exactly (tests/unit/domain/test_units.py)
- [x] 1.2 Boundary/units/sign: overflow beyond signed 64-bit rejected; negative
  round-trips unchanged; float raises TypeError; bool rejected (pin
  `checked_int` behavior)
- [x] 1.3 Property invariants (hypothesis): any int64-range value round-trips;
  construction never wraps or clamps
- [x] 1.4 Missing/malformed: None, str, Decimal inputs all rejected explicitly
- [x] 1.5 Implement `src/quantflow/domain/units.py` (NewType + checked_int)
  until 1.1-1.4 are green
- [x] 1.6 Golden: no `to_dollars`/float accessor exists in `domain/units.py`
  (AST/source scan)
- [x] 1.7 Golden/boundary: integer unit conversions round half-even (0.5
  cases both directions); no fractional dollars value produced on the
  decision path (money-units spec, rounding scenarios; RQ-006)
  Done 2026-10-15: `micros_to_mills` (exact integer `_round_half_even_div`,
  no float intermediate); 58 tests green; ruff + mypy --strict clean.

## 2. epoch-clock (red tests first)

- [x] 2.1 Golden/boundary: EpochMs constructs from int, rejects float and
  out-of-int64; DurationMs rejects negative and > DURATION_MS_MAX (RQ-007;
  64-bit BIGINT parity, no int32 bound)
- [x] 2.2 Duplicate/idempotency: naming-rule test fails on an ambiguous
  `*_ms` field name and passes on `*_ts`/`*_at`/`*_epoch_ms`/
  `*staleness_ms`/`*duration_ms` (exercise the rule with synthetic classes)
- [x] 2.3 Port contract: Clock Protocol -- fake clock injected, `now_ms()`
  returns EpochMs; SystemClock adapter lives outside domain/
- [x] 2.4 No-future-leakage: AST scan of `domain/**` and `kernels/**` fails
  on `datetime.now(`/`time.time(`/`time.monotonic(`/`datetime.utcnow(`
  (include a deliberately-bad fixture proving the scan detects)
- [x] 2.5 Golden: epoch/duration types carry no timezone attribute; ET
  rendering helper (if any) is outside domain/ and kernels/
- [x] 2.6 Implement `src/quantflow/domain/time.py` +
  `src/quantflow/ports/clock.py` until 2.1-2.5 green
  Done 2026-10-15: plus `src/quantflow/adapters/clock.py` (SystemClock, per
  design decision 3) and `FieldNameError` in `domain/errors.py`;
  DURATION_MS_MAX = 2**31-1 in `domain/time.py` (SPEC V1 §19.8.3 Rule 2
  column-safe bound). 21 tests green; ruff + mypy --strict clean.

## 3. domain-enums (red tests first)

- [x] 3.1 Golden: member sets exactly match SPEC V2 Sec 19.2 CHECK lists
  (grade: BASIC/MEDIUM_CONFLUENCE/HIGH_CONFLUENCE; cluster_state:
  ACTIVE/MIXED/BULLISH_REVERSAL/BEARISH_REVERSAL/RETRACTED/EXPIRED;
  episode_state: FORMING/ACTIVE/UPGRADED/REVERSED/RETRACTED/EXPIRED)
- [x] 3.2 Boundary: shared literals do not bridge types (RETRACTED/EXPIRED/
  ACTIVE cross-usage rejected at type-check and at runtime); BASIC rejected
  as state; 'basic'/'High_Confluence'/whitespace-mangled literals rejected
- [x] 3.3 Property invariants: no enum member converts implicitly to float
  (grade-as-probability guard)
- [x] 3.4 Implement `src/quantflow/domain/enums.py` until 3.1-3.3 green
  Done 2026-10-15: `_ClosedVocabulary` base with strict `_missing_` raising
  `VocabularyError` (fail closed, no coercion); golden test parses the
  frozen SPEC V2 §19.2 DDL (design decision 4) + hardcoded pin; 26 tests
  green; ruff + mypy --strict clean.

## 4. repo-bootstrap (red tests first)

- [x] 4.1 Golden: `gen_constants.py` parses AI.3 from
  `docs/reference/CURRENT/` and regenerates `constants.py` byte-identical
  (temp-path output only; drift = red)
- [x] 4.2 Duplicate check: UPPER_SNAKE_CASE token defined outside
  `domain/constants.py` fails the check (deliberately-bad fixture)
- [x] 4.3 Malformed/missing: tampered bundle file or broken CURRENT symlink
  fails the hash check (exercise on temp copies, never the real bundle)
- [x] 4.4 Approval gating: AI.3 `[RECOMMENDED ... approval]` constants carry
  APPROVAL_PENDING marker; test asserts marker present
- [x] 4.5 Implement `scripts/gen_constants.py`,
  `scripts/check_constants.py`, generated `domain/constants.py`, and
  `tests/unit/test_reference_bundle.py` until 4.1-4.4 green
  Done 2026-10-15: parser scoped to AI.3 (604-727, ends at AI.4), fails
  closed on duplicate names; drift test byte-compares regeneration (named
  constants on failure); hash check = plain pytest with real bundle
  (read-only) + tampered/missing/broken-symlink temp fixtures;
  `STRUCTURAL_ALLOWLIST` in check_constants.py documents the 8 non-AI.3
  structural/POC names (fail-closed for anything new). 14 tests green;
  `python3 scripts/check_constants.py` exit 0; ruff + mypy --strict clean.

## 5. Final verification

- [x] 5.1 `ruff check` and `ruff format --check` green
  (scoped to change files: src/, tests/, scripts/gen_constants.py,
  scripts/check_constants.py, scripts/gen_modules_index.py; pre-existing
  S603 in the user-modified scripts/update_runbook.py left untouched)
- [x] 5.2 `mypy --strict` green on `src/quantflow/**` (27 files)
- [x] 5.3 `pytest` green; coverage >=95% on `src/quantflow/domain/**`
  (125 passed; 100% coverage)
- [x] 5.4 Confirm no test or module touches `/data` (temp paths only; grep
  for `/data` in new files) -- no matches in src/quantflow, tests/unit, or
  the new scripts
- [x] 5.5 Regenerate `openspec/modules.md`
  (`python3 scripts/gen_modules_index.py`) -- script was missing; created
  it (declared in modules.md header), regenerated: 10 modules listed
- [x] 5.6 Update `openspec/conflicts-and-gaps.md` with any resolutions made
  in task group 0; confirm no new conflicts introduced
  RQ-006/RQ-007 recorded at propose time; new deferral RQ-008 (AI.1/AI.2
  constants out of the AI.3 generation scope); no doc conflicts introduced

## 6. Review remediation (qf-review MAJORs, 2026-10-16)

- [x] 6.1 `check_constants.py` scans every scope under `src/quantflow/**`
  (chained/tuple assignments, function bodies, non-enum class bodies), keeps
  enum members skipped, and skips `domain/constants.py` by canonical path --
  not by basename (red fixtures first in tests/unit/test_constants_check.py)
  Done 2026-10-16: 5 red fixtures (chained, function-local, class-body,
  non-canonical constants.py, tuple targets) RED then green; enum-class
  detection (direct `Enum` base + in-file subclass chain) keeps members
  skipped; `scan_source_tree` signature unchanged (5 test callers).
- [x] 6.2 `gen_constants.py` fails closed on any non-comment AI.3 line that
  parses as neither prose/group label nor a constant (format drift raises;
  real-bundle prose still parses; red tests first)
  Done 2026-10-16: `CONSTANT_HEAD` + `_looks_like_constant`; drift raises
  `ValueError("unparsable AI.3 constant line (format drift): ...")`; prose and
  group-label regression test (incl. `ZERO_DTE ticker scope ...` shape);
  real-bundle byte-identical regeneration still green.
- [x] 6.3 Bundle hash check asserts set equality between the bundle's file
  set and the SHA256SUMS entries: an extra file in the bundle fails the check
  (red fixture first in tests/unit/test_reference_bundle.py)
  Done 2026-10-16: extra-file detection = `files_in_dir - manifest` (SHA256SUMS
  excluded: the manifest cannot list its own hash); red fixture green;
  existing tamper/missing exact-message assertions unchanged.
- [x] 6.4 Determinism scenario covered for the zero-kernel case: pin the
  empty kernel-module set explicitly so "same as_of -> identical output"
  (spec epoch-clock) cannot pass vacuously (red test first,
  tests/unit/test_clock.py)
  Done 2026-10-16: `EXPECTED_KERNEL_MODULES: list[str] = []` pin +
  deliberately-bad fixture proving the pin fires when a kernel module appears.

Verification 2026-10-16 (group 6): 8 red tests confirmed failing first, then
green; `uv run pytest -q` 136 passed; `uv run ruff check` and
`uv run ruff format --check` green on all change-owned files; `uv run mypy
--strict src/quantflow` 27 files clean; `python3 scripts/check_constants.py`
exit 0. Pre-existing debt left untouched per task 5.1 precedent: unformatted
`src/quantflow/adapters/mcp/{api_key,server}.py` + `src/quantflow/cli/mcp_probe.py`
(committed, unmodified) and `ruff check` errors in `tools/`. design.md
decisions 5-6 updated to match the broader scan and the set-equality check.

## 7. Review remediation (qf-review round 2 MAJORs, 2026-10-16)

- [x] 7.1 Wall-clock scan also bans `quantflow.adapters.*` imports under
  `domain/**` and `kernels/**` (design decision 3; spec epoch-clock scenario
  "No clock is reachable without injection"), with a deliberately-bad
  fixture proving the check fires (red first in tests/unit/test_wall_clock_scan.py)
  Done 2026-10-16: red fixture (`0 == 2`) then green; `_is_adapters_module`
  exact-prefix helper flags both `import quantflow.adapters...` and
  `from quantflow.adapters... import ...` in `find_wall_clock_violations`,
  which already runs over domain/** and kernels/** (real tree: no violations);
  module/function docstrings updated to record the 7.1 ban.
- [x] 7.2 Duration bound wording (doc-only, time.py unchanged): spec delta
  epoch-clock requalifies "no int32 bound" as "no int32 type bound;
  structural value bound 2**31-1 enforced at construction"; RQ-007 in
  `openspec/conflicts-and-gaps.md` records `DURATION_MS_MAX = 2**31 - 1`
  Done 2026-10-16: both edits applied; `src/quantflow/domain/time.py`
  untouched (still `DURATION_MS_MAX = 2**31 - 1`, enforced at construction).

Verification 2026-10-16 (group 7): red fixture confirmed failing first, then
green; `uv run pytest -q` 137 passed; `uv run ruff check` green on 005 scope;
`uv run ruff format --check` green on touched files; `uv run mypy --strict
src/quantflow` 27 files clean.
