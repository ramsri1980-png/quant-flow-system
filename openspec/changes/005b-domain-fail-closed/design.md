# Design — 005b

## Capability mapping
- `epoch-clock` — Q8, Q12, Q13 touch time representation and scan rules.
- `domain-constants` — new capability home for the generated constants
  module and its access discipline (Q6).

## Decisions

### D1 — Constants accessor via generator, not runtime shim (Q6)
`scripts/gen_constants.py` emits the accessor alongside the values so
the generated module stays the single source of truth. The accessor
`approved(name)` returns the value only when the name is not in the
approval-pending set; otherwise raises `ConstantsError`.

### D2 — Epoch ms bounds are inclusive (Q8)
Range is `[EPOCH_MS_MIN, EPOCH_MS_MAX]`, both endpoints valid. Chosen
to reject seconds and micros silently passed as ms while remaining
generous against every SPEC lookback (3-year COT, 252-day IVR, 5-year
retention).

### D3 — Ambiguity is an error, not a precedence (Q13)
A name matching both epoch and duration patterns raises
`FieldNameError`. Silent precedence is what let `epoch_latency_ms`
through in 005a.

### D4 — Randomness ban mirrors 005a's scan shape (Q12)
Extend `BANNED_MODULES` and `BANNED_CALL_NAMES`; add a fixture. Same
pattern as `test_scan_detects_additional_clock_calls`.

## Reuse
- `src/quantflow/domain/time.py` — existing `field_name_kind`,
  `epoch_ms`, `DURATION_MS_MAX`.
- `src/quantflow/domain/errors.py` — existing error hierarchy.
- `tests/unit/test_wall_clock_scan.py` — extend, do not replace.
- `scripts/gen_constants.py` — extend emitter, do not fork.

## Open Questions
- None blocking. Q9 DURATION_MS_MAX vs cooldown seconds is resolved in
  `openspec/conflicts-and-gaps.md` (documentation note only).

