# Design: 005 Domain types, units, clock

## Context

`src/quantflow/` exists as package scaffolding only (empty `__init__.py`
files; runbook Task 7 done). No domain, kernel, or spec code yet;
`openspec/specs/` is empty. The reference bundle is frozen at
`docs/reference/release-v2.0.5.1-v5.1.5.1/` with `SHA256SUMS` and a
`docs/reference/CURRENT` symlink (runbook Task 5 done; conflicts C1 closed
2026-10-15). C8 closed: SPEC V2 Sec 19.4.4 is canonical -- SQLite INTEGER
(64-bit), DuckDB `_micros` BIGINT, DuckDB `_cents/_mills` INTEGER-or-BIGINT
as declared, all decision-path `_mills/_micros` BIGINT. Python 3.14, uv,
ruff/mypy(strict)/pytest already configured (runbook Task 9). Nothing to
reuse in code (`openspec/modules.md`: none yet).

## Goals / Non-Goals

**Goals:**
- Unit-typed integers (`_cents`, `_micros`, `_mills`), epoch-ms time type,
  Clock port, three disjoint enums, constants module checked against AI.3,
  bundle hash check -- all pure, typed, test-first.
- AST lint parity with SPEC V1 Sec 2.9.4.8 patterns (no fetch_/get_current_/
  read_pointer_ is out of scope here; only wall-clock reads are guarded now).

**Non-Goals:**
- DB code, migrations, providers, kernels (per brief: out of scope).
- Fractional (float) dollars in the decision path. Rounding is settled:
  integer-only, round-half-even at the display boundary (operator ruling
  2026-10-15) -- per-formula display formats are presentation concerns.
- Full enum coverage of every SPEC V2 CHECK list (only the three vocabularies
  in the brief).

## Decisions

1. **Unit wrappers as `NewType` over `int`**, not dataclasses or IntEnum.
   - Rationale: decision path is BIGINT end-to-end; NewType gives static
     float/int separation under `mypy --strict` with zero runtime cost and
     trivial SQLite/DuckDB binding (plain int). Dataclasses would add
     arithmetic-permission questions the docs do not answer (are
     `_cents + _cents` and `_cents * float` legal? unspecified).
   - Alternatives rejected: `int` subclass with validation (`__new__`
     overhead, pickle/copy edge cases); float-free dataclass (invented
     arithmetic API); IntEnum (implies closed value set -- wrong for prices).
   - Runtime rejection of float at boundaries uses an explicit
     `checked_int()` constructor (raises `TypeError` on `float`, `bool`
     passes as int subclass -- documented, tests pin it).

2. **Epoch time as `EpochMs = NewType("EpochMs", int)`** plus a
   `DurationMs` newtype with 64-bit (BIGINT / SQLite INTEGER) parity.
   RESOLVED (operator ruling 2026-10-15): no int32 bound. Durations are
   non-negative and validated against a named maximum `DURATION_MS_MAX`
   enforced in code at construction (fail closed on negative or larger
   values). The bound is structural, not a market constant from AI.3, and
   lives in the constants module for single-place revision.

3. **Clock port is a `Protocol`** with `now_ms() -> EpochMs`. Domain/kernels
   never import a concrete clock; application layer wires `SystemClock`
   (adapter, outside domain). AST test scans `domain/**` and `kernels/**`
   for `datetime.now`, `time.time`, `time.monotonic`, `datetime.utcnow`,
   `*.now(`, `*.today(` -- mirroring the Sec 2.9.4.8 lint pattern. Fail-closed:
   pattern miss = test failure, not warning.

4. **Enums as three Python `enum.Enum` classes** with distinct member sets
   even where literals overlap (`RETRACTED`, `EXPIRED`, `ACTIVE` in both
   cluster_state and episode_state). Python enums of different classes are
   not comparable by identity, and `StrEnum` coercion is avoided because
   `cluster_state_cls("RETRACTED")` must not accept an episode_state's value
   semantically -- we use plain `Enum` with `str` values and a strict
   `_missing_` that rejects unknown/case-mangled input (fail closed).
   Literal sets copied exactly from SPEC V2 Sec 19.2 CHECK constraints
   (golden test reads the frozen DDL text to prevent drift).

5. **Constants module generated + checked, not hand-written.**
   `scripts/gen_constants.py` parses ARCH V1 Sec AI.3 in
   `docs/reference/CURRENT/` into `src/quantflow/domain/constants.py`
   (UPPER_SNAKE_CASE names, values verbatim). A pytest regenerates to a temp
   path and byte-compares (drift = red). Constants marked
   `[RECOMMENDED ... approval]` in AI.3 (the C12 dealer/greeks set) are
   emitted with `APPROVAL_PENDING = True` companions; features 031-036 must
   flip this via recorded operator approval, not silently. Code references
   constants by name; a token-scan check fails on UPPER_SNAKE_CASE literals
   outside the constants module (mirrors SPEC V1 Sec 1.4.34/1.4.33 CI lint).
   - Alternative rejected: runtime parse of AI.3 on import (kernel purity,
     import-time I/O, slower tests); hand-written constants (drift risk,
     the docs already mandate the lint).

6. **Bundle hash check as a plain pytest** reading
   `docs/reference/CURRENT/SHA256SUMS` and hashing each file -- no DB, no
   network, temp-paths only for its own outputs.

## Risks / Trade-offs

- [NewType gives static-only float rejection; floats can still sneak in via
  `int(x)` casts] → AST scan for `int(` casts on unit values is too noisy;
  rely on strict types + boundary `checked_int()` + tests, and later features
  add domain-specific guards.
- [AI.3 parse brittleness if the frozen doc format were edited] → bundle is
  hash-frozen; any format change requires re-freezing and updating the parser
  deliberately (check fails closed on unparsable lines).
- [Approval-pending constants could be imported and used] → marker + lint in
  031-036; this change ships no consumer.
- [DurationMs `DURATION_MS_MAX` is structural, not doc-normative] → operator
  ruling 2026-10-15 keeps BIGINT/64-bit parity with a code-validated maximum;
  the named constant lives in one place for easy revision if a doc adds a
  bound later.

## Migrations touched

None. No SQLite or DuckDB migration is created, edited, or applied by this
change (DB code out of scope). No applied migration is modified.

## Reuse

- `openspec/modules.md`: no existing Python modules (`src/quantflow/` is
  package scaffolding only) -- nothing reusable.
- New modules and why each is needed:
  - `domain/units.py` -- canonical home of the three unit newtypes (docs
    mandate exactly one representation; none exists).
  - `domain/time.py` -- epoch/duration types (same).
  - `domain/enums.py` -- three disjoint vocabularies (same).
  - `domain/constants.py` -- generated from AI.3 (SPEC V1 Sec 1.4.33).
  - `ports/clock.py` -- Clock Protocol (adapters are the only place a
    concrete clock may live; no port exists yet).
  - `scripts/gen_constants.py`, `scripts/check_constants.py` -- generation
    and CI check.
- Test classes per constitution Sec 11 / brief seed scenarios are mapped in
  tasks.md.

## Open Questions

- **RESOLVED (operator ruling 2026-10-15) -- Rounding for unit
  conversions.** Integer-only with round-half-even at the display boundary.
  The decision path carries integers end-to-end; no fractional dollars value
  enters or persists there. Where an integer unit conversion or a
  display-boundary dollars conversion requires rounding, it uses
  round-half-even -- consistent with ARCH V4 precedents (`round()` in
  S_mills = round(S_micros/1000); explicit `round_half_even` for
  delta_microcents). No per-formula rounding mode is left to invent for the
  conversion itself (feature 030+ formula boundaries adopt the same rule).
- **RESOLVED (operator ruling 2026-10-15) -- DurationMs bound.** DurationMs
  stays BIGINT with a validated maximum in code: 64-bit (BIGINT / SQLite
  INTEGER) parity, non-negative, and rejected above the named structural
  constant `DURATION_MS_MAX`. No int32 bound; SPEC V1 Sec 19.8.3 Rule 2's
  INTEGER mapping is satisfied at 64-bit in Python.
- **NON-BLOCKING -- bool acceptance.** Python `bool` is an `int` subclass;
  `checked_int()` will reject `bool` explicitly. Assumed strict; flag if the
  operator wants bools to pass.
- **RESOLVED -- C1 bundle version:** v2.0.5.1/v5.1.5.1, 11 files, CURRENT
  symlink present, SHA256SUMS verified (runbook Task 5 done; conflicts log
  closed 2026-10-15).
- **RESOLVED -- C8 column-type rule:** SPEC V2 Sec 19.4.4 canonical;
  SQLite INTEGER (64-bit); DuckDB decision-path unit columns BIGINT
  (conflicts log closed 2026-10-15). Python wrappers are unbounded `int`
  statically constrained to signed 64-bit at construction.
