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

- [ ] 1.1 Golden: `_cents`/`_micros`/`_mills` construct from int, round-trip
  exactly (tests/unit/domain/test_units.py)
- [ ] 1.2 Boundary/units/sign: overflow beyond signed 64-bit rejected; negative
  round-trips unchanged; float raises TypeError; bool rejected (pin
  `checked_int` behavior)
- [ ] 1.3 Property invariants (hypothesis): any int64-range value round-trips;
  construction never wraps or clamps
- [ ] 1.4 Missing/malformed: None, str, Decimal inputs all rejected explicitly
- [ ] 1.5 Implement `src/quantflow/domain/units.py` (NewType + checked_int)
  until 1.1-1.4 are green
- [ ] 1.6 Golden: no `to_dollars`/float accessor exists in `domain/units.py`
  (AST/source scan)
- [ ] 1.7 Golden/boundary: integer unit conversions round half-even (0.5
  cases both directions); no fractional dollars value produced on the
  decision path (money-units spec, rounding scenarios; RQ-006)

## 2. epoch-clock (red tests first)

- [ ] 2.1 Golden/boundary: EpochMs constructs from int, rejects float and
  out-of-int64; DurationMs rejects negative and > DURATION_MS_MAX (RQ-007;
  64-bit BIGINT parity, no int32 bound)
- [ ] 2.2 Duplicate/idempotency: naming-rule test fails on an ambiguous
  `*_ms` field name and passes on `*_ts`/`*_at`/`*_epoch_ms`/
  `*staleness_ms`/`*duration_ms` (exercise the rule with synthetic classes)
- [ ] 2.3 Port contract: Clock Protocol -- fake clock injected, `now_ms()`
  returns EpochMs; SystemClock adapter lives outside domain/
- [ ] 2.4 No-future-leakage: AST scan of `domain/**` and `kernels/**` fails
  on `datetime.now(`/`time.time(`/`time.monotonic(`/`datetime.utcnow(`
  (include a deliberately-bad fixture proving the scan detects)
- [ ] 2.5 Golden: epoch/duration types carry no timezone attribute; ET
  rendering helper (if any) is outside domain/ and kernels/
- [ ] 2.6 Implement `src/quantflow/domain/time.py` +
  `src/quantflow/ports/clock.py` until 2.1-2.5 green

## 3. domain-enums (red tests first)

- [ ] 3.1 Golden: member sets exactly match SPEC V2 Sec 19.2 CHECK lists
  (grade: BASIC/MEDIUM_CONFLUENCE/HIGH_CONFLUENCE; cluster_state:
  ACTIVE/MIXED/BULLISH_REVERSAL/BEARISH_REVERSAL/RETRACTED/EXPIRED;
  episode_state: FORMING/ACTIVE/UPGRADED/REVERSED/RETRACTED/EXPIRED)
- [ ] 3.2 Boundary: shared literals do not bridge types (RETRACTED/EXPIRED/
  ACTIVE cross-usage rejected at type-check and at runtime); BASIC rejected
  as state; 'basic'/'High_Confluence'/whitespace-mangled literals rejected
- [ ] 3.3 Property invariants: no enum member converts implicitly to float
  (grade-as-probability guard)
- [ ] 3.4 Implement `src/quantflow/domain/enums.py` until 3.1-3.3 green

## 4. repo-bootstrap (red tests first)

- [ ] 4.1 Golden: `gen_constants.py` parses AI.3 from
  `docs/reference/CURRENT/` and regenerates `constants.py` byte-identical
  (temp-path output only; drift = red)
- [ ] 4.2 Duplicate check: UPPER_SNAKE_CASE token defined outside
  `domain/constants.py` fails the check (deliberately-bad fixture)
- [ ] 4.3 Malformed/missing: tampered bundle file or broken CURRENT symlink
  fails the hash check (exercise on temp copies, never the real bundle)
- [ ] 4.4 Approval gating: AI.3 `[RECOMMENDED ... approval]` constants carry
  APPROVAL_PENDING marker; test asserts marker present
- [ ] 4.5 Implement `scripts/gen_constants.py`,
  `scripts/check_constants.py`, generated `domain/constants.py`, and
  `tests/unit/test_reference_bundle.py` until 4.1-4.4 green

## 5. Final verification

- [ ] 5.1 `ruff check` and `ruff format --check` green
- [ ] 5.2 `mypy --strict` green on `src/quantflow/**`
- [ ] 5.3 `pytest` green; coverage >=95% on `src/quantflow/domain/**`
- [ ] 5.4 Confirm no test or module touches `/data` (temp paths only; grep
  for `/data` in new files)
- [ ] 5.5 Regenerate `openspec/modules.md`
  (`python3 scripts/gen_modules_index.py`)
- [ ] 5.6 Update `openspec/conflicts-and-gaps.md` with any resolutions made
  in task group 0; confirm no new conflicts introduced
