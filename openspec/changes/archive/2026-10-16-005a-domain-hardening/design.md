# Design: 005a Domain hardening (review fixes for 005)

## Context

005 is archived; this change fixes review findings without touching the
archive. Verified in source (2026-10-16):

- `src/quantflow/domain/units.py:57-59` — `micros_to_mills` calls
  `int(value)` unvalidated (float truncates, bool/out-of-range pass), unlike
  the `checked_int()`-gated factories at lines 33-45.
- `Cents/Micros/Mills/EpochMs/DurationMs` are `typing.NewType`
  (runtime no-op); only factories validate. A grep of `src/quantflow/**`
  found exactly one direct wrapper call outside `domain/units.py`/
  `domain/time.py`: `src/quantflow/adapters/clock.py:17`
  (`return EpochMs(time.time_ns() // 1_000_000)`).
- `src/quantflow/domain/time.py:45-51` — `field_name_kind` uses bare
  `endswith` and a loose `"epoch_" in name` substring test
  (`message_ms`.endswith(`age_ms`) is True).
- `tests/unit/test_wall_clock_scan.py:14-15` — 5 banned call names,
  2 banned modules; no relative-import ban.
- `src/quantflow/domain/enums.py` — already correct per SPEC V2 §19.2
  (shared ACTIVE/RETRACTED/EXPIRED); the 005 brief's "same literal in two
  vocabularies → test fails" claim is false as written; wording fix goes in
  the spec delta, not in code.
- Pre-audits: no relative imports anywhere in `src/quantflow/**`; no
  `perf_counter`/`process_time`/`urandom`/`monotonic_ns`/`time_ns(` outside
  `adapters/clock.py:17`; existing `tests/unit/domain/test_time.py` naming
  tests use only token-clean names (`observed_ts`, `created_at`,
  `cursor_epoch_ms`, `fetch_staleness_ms`, `wait_duration_ms`,
  `elapsed_ms_wait`) — none relies on the loose matching being removed.

Open questions Q1-Q16 (brief Part 3) are recorded in
`openspec/conflicts-and-gaps.md` (operator instruction 2026-10-16: record
here; resolution deferred to 005b or the consuming feature).

## Goals / Non-Goals

**Goals:**
- Make every Part 1 item enforceable by tests (tests first) with
  `domain/**` coverage ≥ 95% held.
- Spec wording matches implemented behaviour (Part 2 deltas).

**Non-Goals:**
- Part 3 items (no thresholds, names, or formulas invented — record only).
- `domain/constants.py` changes (generated; fix `scripts/gen_constants.py`
  only when a constants change is approved — none here).
- `enums.py`, ports, migrations, DB code, `random`/`uuid` linting (Q12),
  monotonic-clock redesign (Q11).

## Reuse

- `quantflow.domain.units`: `checked_int`, `_round_half_even_div`,
  `MICROS_PER_MILL` (1.1 reuses them; no new conversion API).
- `quantflow.domain.time`: `epoch_ms()` factory (1.2 SystemClock fix),
  `EPOCH_NAME_SUFFIXES` / `DURATION_NAME_SUFFIXES` (1.4 token matching),
  `FieldNameError`.
- `quantflow.domain.enums` + `quantflow.domain.errors`
  (`UnitValueError`, `VocabularyError`): unchanged; 1.3 only pins behaviour.
- `tests/unit/test_wall_clock_scan.py`: extend the existing scan in place
  (`find_wall_clock_violations`), no new test module.
- New modules: none. New file only `tests/unit/test_direct_unit_construction.py`
  (005's test-layout convention: scan-style tests live under `tests/unit/`).

## Decisions

1. **Factory-only construction via AST test; NewType stays** (brief default;
   Q1's int-subclass alternative recorded, not implemented). Rationale:
   runtime enforcement without changing static types; `mypy --strict`
   behaviour unchanged; the AST test's `ALLOWED_FILES` is exactly
   `domain/units.py` and `domain/time.py`, with the documented limit that
   `typing.cast(Cents, x)` is not detected (stated in the test docstring).
2. **`micros_to_mills` validates with `checked_int(value, field="micros")`**
   then converts — identical shape to the factories, so TypeError
   (non-int/bool) and UnitValueError (range) match existing conventions.
3. **Token-boundary naming match** (`_has_token_suffix`, `_is_epoch_name`):
   epoch checked first (unchanged precedence — a dual-match name such as
   `epoch_latency_ms` still returns `epoch`; Q13 records whether that should
   become a rejection). `startswith("epoch_")`/`"_epoch_" in name` replaces
   the loose `"epoch_" in name` so a name only matches on token boundaries.
4. **Scan extension is fail-closed by design**: generic method names
   (`time()`, `today()`) flag any caller with that name — accepted
   trade-off, commented in the test. Relative-import branch precedes the
   existing `ImportFrom` branch so `from . import x` (module name `None`) and
   `from ..adapters import clock` are caught. `random`/`uuid` intentionally
   untouched (Q12 → 005b).
5. **Spec citation quotes stay verbatim**: the money-units Source line keeps
   constitution Sec 4's quoted "(÷1e6)" even though the normative body now
   forbids applying a single divisor to cents/mills — the quote is evidence
   of the constitution text, not a rule.
6. **Hand-built artifacts**: this session had no openspec CLI (hard rules 1/5
   waived by operator instruction 2026-10-16; duplicate check done
   manually). Structure mirrors the archived 005 artifacts; run
   `openspec validate` before apply.

## Risks / Trade-offs

- [Existing test relied on loose naming matching] → pre-audit found none;
  if apply-phase runs surface one, it goes to conflicts-and-gaps Open
  questions and the item stops (brief rule) — new tests are not weakened.
- [AST scan now flags legitimate `time()`-named methods in domain/kernels] →
  pre-audit found no such calls; fail-closed is intended (comment in test).
- [Coverage regression if tests land before fixes] → red-then-green order
  per item, full suite after each item; one commit per green item.
- [Hand-written spec deltas may drift from schema] → `openspec validate` in
  final verification.

## Open Questions

- BLOCKING for 005b / the consuming features (recorded, NOT implemented):
  Q2 (floats in constants.py), Q3 (_PCT semantics), Q4 (unitless
  constants), Q5 (approval-pending flags), Q6 (enforcing approval-pending),
  Q7 (structural constants location), Q8 (plausible epoch range), Q9
  (DURATION_MS_MAX ≈ 24.86 days), Q10 (`_epoch_ns` with no EpochNs type),
  Q12 (random/uuid lint), Q15 (pocs/interface drift), Q16 (unreviewed 005
  artifacts).
- NON-BLOCKING for 005a (proceed per brief default; confirm in 005b):
  Q1 (wrapper strategy — factory+AST proceeds), Q11 (monotonic clock —
  `SystemClock` keeps the non-monotonic `time.time_ns()` read), Q13
  (dual-match precedence — epoch wins, unchanged), Q14 (dollars divisor for
  cents/mills — no formula converts them yet).
- No BLOCKING question prevents applying Part 1/2 of this change.

## Migrations touched

None (no DB code; no store/id/component).
