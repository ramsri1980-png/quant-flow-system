# 005b — Domain fail-closed hardening

## Why
Four open questions from the 005a review (Q6, Q8, Q12, Q13) are
fail-closed gaps: silent reads of approval-pending constants, no
plausible-range gate on epoch ms, incomplete AST bans for randomness,
and ambiguous time field names accepted silently. Each is small and
independent. Closing them in one change keeps the domain layer's
"reject anything uncertain" discipline intact.

## What Changes
- Add `approved(name)` accessor for domain constants; direct reads of
  approval-pending names fail an AST test.
- Add `EPOCH_MS_MIN` / `EPOCH_MS_MAX` bounds (2010-01-01 to 2060-01-01
  UTC) to `epoch_ms()`.
- Extend the wall-clock AST scan to reject `random`, `uuid`, and their
  call shapes in `domain/**` and `kernels/**`.
- Reject time field names that match both epoch and duration patterns
  (e.g. `epoch_latency_ms`) as ambiguous.

## Impact
- Capabilities: epoch-clock, domain-constants
- Affected files: `src/quantflow/domain/{time,errors,constants}.py`,
  `scripts/gen_constants.py`, `tests/unit/{domain/test_time,
  domain/test_constants_access,test_wall_clock_scan}.py`
- No migrations. No ARCH edits. Coverage stays >= 95% on `domain/**`.
