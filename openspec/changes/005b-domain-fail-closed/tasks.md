# Tasks — 005b

## 1. Q6 — approved() accessor
- [ ] 1.1 Add `ConstantsError` to `src/quantflow/domain/errors.py` if absent
- [ ] 1.2 Extend `scripts/gen_constants.py` to emit `approved(name)` accessor
- [ ] 1.3 Regenerate `src/quantflow/domain/constants.py`
- [ ] 1.4 New `tests/unit/domain/test_constants_access.py` (approved/denied)
- [ ] 1.5 AST test rejecting direct reads of `*_APPROVAL_PENDING` in domain/kernels

## 2. Q8 — Epoch ms plausible range
- [ ] 2.1 Add `EPOCH_MS_MIN`, `EPOCH_MS_MAX` constants in `time.py`
- [ ] 2.2 Reject out-of-range values in `epoch_ms()`
- [ ] 2.3 Red tests: seconds rejected, micros rejected, min/max edges

## 3. Q12 — Ban random / uuid / secrets
- [ ] 3.1 Extend `BANNED_MODULES` and `BANNED_CALL_NAMES` in `test_wall_clock_scan.py`
- [ ] 3.2 Add fixture exercising all three imports plus call shapes
- [ ] 3.3 Confirm scan passes on current domain/ and kernels/

## 4. Q13 — Reject ambiguous time names
- [ ] 4.1 `field_name_kind` raises `FieldNameError` on dual-match names
- [ ] 4.2 Red tests: `epoch_latency_ms` raises; existing names still classify

## 5. Verification
- [ ] 5.1 `uv run pytest -q`
- [ ] 5.2 `uv run ruff check src tests`
- [ ] 5.3 `uv run ruff format --check src tests`
- [ ] 5.4 `uv run mypy --strict src/quantflow`
- [ ] 5.5 `uv run pytest --cov=src/quantflow --cov-report=term-missing` (domain/** >= 95%)
- [ ] 5.6 `python3 scripts/check_constants.py` exit 0
