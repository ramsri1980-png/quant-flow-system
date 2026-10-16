# Tasks — 005b

## 1. Q6 — approved() accessor
- [x] 1.1 Add `ConstantsError` to `src/quantflow/domain/errors.py` if absent
- [x] 1.2 Extend `scripts/gen_constants.py` to emit `approved(name)` accessor
- [x] 1.3 Regenerate `src/quantflow/domain/constants.py`
- [x] 1.4 New `tests/unit/domain/test_constants_access.py` (approved/denied)
- [x] 1.5 AST test rejecting direct reads of `*_APPROVAL_PENDING` in domain/kernels

## 2. Q8 — Epoch ms plausible range
- [x] 2.1 Add `EPOCH_MS_MIN`, `EPOCH_MS_MAX` constants in `time.py`
- [x] 2.2 Reject out-of-range values in `epoch_ms()`
- [x] 2.3 Red tests: seconds rejected, micros rejected, min/max edges

## 3. Q12 — Ban random / uuid / secrets
- [x] 3.1 Extend `BANNED_MODULES` and `BANNED_CALL_NAMES` in `test_wall_clock_scan.py`
- [x] 3.2 Add fixture exercising all three imports plus call shapes
- [x] 3.3 Confirm scan passes on current domain/ and kernels/

## 4. Q13 — Reject ambiguous time names
- [x] 4.1 `field_name_kind` raises `FieldNameError` on dual-match names
- [x] 4.2 Red tests: `epoch_latency_ms` raises; existing names still classify

## 5. Verification
- [x] 5.1 `uv run pytest -q`
- [x] 5.2 `uv run ruff check src tests`
- [x] 5.3 `uv run ruff format --check src tests`
- [x] 5.4 `uv run mypy --strict src/quantflow`
- [x] 5.5 `uv run pytest --cov=src/quantflow --cov-report=term-missing` (domain/** >= 95%)
- [x] 5.6 `python3 scripts/check_constants.py` exit 0
