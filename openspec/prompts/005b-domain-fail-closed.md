005b Domain fail-closed hardening

Epic: E0 setup | Depends: 005a (archived, merged) | Blockers: none
Use: /qf-propose @openspec/prompts/005b-domain-fail-closed.md
Expected change directory: openspec/changes/005b-domain-fail-closed/
Capabilities (modified): money-units, epoch-clock, domain-enums
Sources: 005a review open questions Q6, Q8, Q12, Q13 (openspec/conflicts-and-gaps.md)

## Process
## Process
- This is a PROPOSE-phase prompt. Produce ONLY proposal.md, design.md,
  tasks.md, and spec deltas under openspec/changes/005b-domain-fail-closed/.
  Do NOT modify source files. Code changes happen later via /qf-apply.
- Do NOT edit the archived 005 or 005a changes.
...
- Do NOT edit the archived 005 or 005a changes.
- Spec edits are deltas under this change, not edits to openspec/specs/**.
- Classify each item RESOLVED_FROM_SOURCE / PROPOSED / BLOCKED.
- Tests first (AGENTS rule 12). One item per commit. Keep domain/** coverage >= 95%.
- Do not invent thresholds, names, or formulas (AGENTS rule 11).
- Do not hand-edit src/quantflow/domain/constants.py (generated).
- Part 3 (below) records blockers in conflicts-and-gaps.md and stops.

## Part 1: Implement now

### 1.1 Q6 — Enforce approval-pending constants (HIGH)
Files:
- scripts/gen_constants.py (emit accessor)
- src/quantflow/domain/constants.py (regenerated)
- src/quantflow/domain/errors.py (new error class if needed)
- new tests/unit/domain/test_constants_access.py
Requirements:
- Add approved(name: str) -> int|float accessor that returns the value only
  if the name is NOT in the approval-pending set; raises ConstantsError otherwise.
- Extend the AST scan (or add a sibling) to reject direct reads of any
  *_APPROVAL_PENDING constant name in src/quantflow/domain/** and src/quantflow/kernels/**.
- Fixture: a deliberately-bad file reads a pending name directly -> 1 violation.
Done when: accessor tests pass, fixture fails on bad input, no domain file reads
a pending constant directly.

### 1.2 Q8 — Plausible epoch range (HIGH)
File: src/quantflow/domain/time.py
- Add EPOCH_MS_MIN = 1_262_304_000_000 (2010-01-01T00:00:00Z)
- Add EPOCH_MS_MAX = 2_840_140_800_000 (2060-01-01T00:00:00Z)
- epoch_ms() rejects values outside [EPOCH_MS_MIN, EPOCH_MS_MAX] with the
  existing error type.
Tests in tests/unit/domain/test_time.py:
- 1_700_000_000 (seconds) rejected
- 1_700_000_000_000 (ms) accepted
- 1_700_000_000_000_000 (micros) rejected
- EPOCH_MS_MIN - 1 rejected
- EPOCH_MS_MAX + 1 rejected
Done when: tests pass, no consumer breaks.

### 1.3 Q12 — Ban random, uuid, secrets in domain and kernels (HIGH)
File: tests/unit/test_wall_clock_scan.py
- BANNED_MODULES gains "random", "uuid" (secrets already added in 005a).
- BANNED_CALL_NAMES gains "getrandbits", "randint", "random", "randrange",
  "uuid1", "uuid4".
- New fixture with:
    import random
    import uuid
    import secrets
    x = random.randint(0, 1)
    y = uuid.uuid4()
    z = secrets.token_hex()
  Asserts the expected violation count.
Done when: scan passes on current domain/ and kernels/; fixture fails on
the deliberately-bad input.

### 1.4 Q13 — Reject ambiguous time field names (HIGH)
File: src/quantflow/domain/time.py
- field_name_kind(): if a name matches both epoch and duration patterns
  (e.g. epoch_latency_ms), raise FieldNameError instead of returning "epoch".
Tests in tests/unit/domain/test_time.py:
- field_name_kind("epoch_latency_ms") raises FieldNameError
- field_name_kind("epoch_ms") still returns "epoch"
- field_name_kind("quote_age_ms") still returns "duration"
Done when: existing tests still pass; new tests pass.

## Part 2: Spec deltas for this change
Write as delta specs under openspec/changes/005b-.../specs/<capability>/spec.md.

- epoch-clock MODIFIED — name classification rejects ambiguity; epoch_ms has
  a plausible-range gate.
- epoch-clock MODIFIED (documentation) — clarify that DURATION_MS_MAX bounds
  the DurationMs type used in *_duration_ms columns; cooldown config values
  (Vol 4 §18.14) are stored in SECONDS and are a separate concept. No overflow
  because the two never share a column. Closes Q9.
- money-units MODIFIED — constants accessor contract: only approved constants
  are readable from domain/kernels; pending constants require approved().

## Part 3: Record only, do not implement
Append to openspec/conflicts-and-gaps.md:
- Q9 status: RESOLVED (see epoch-clock delta above).
- Note that Q1, Q2, Q3, Q4, Q5, Q7, Q10, Q11, Q14, Q15, Q16 remain open
  and are being tracked for 005c / 005d.

## Verification checklist
- uv run pytest -q
- uv run ruff check src tests
- uv run ruff format --check src tests
- uv run mypy --strict src/quantflow
- uv run pytest --cov=src/quantflow --cov-report=term-missing  (domain/** >= 95%)
- python3 scripts/check_constants.py -> exit 0
