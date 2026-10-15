# Playbook: code review (load for /qf-review)
Review in this order; report only real findings with file:line and a fix.
1. Spec match: every Requirement/Scenario has code + test; nothing extra built (list deviations).
2. Correctness: units (_cents/_micros/_mills), signs, off-by-one, epoch ms, integer overflow, rounding, idempotency, restart.
3. Fail-closed: no silent defaults, no swallowed errors, no unauthorized provider call.
4. Purity/boundaries: kernels pure (no I/O, clock, randomness); only quantd writes DBs; no fetch_*/get_current_*/read_pointer_* in builders.
5. Tests: scenario coverage, meaningful asserts, no /data, no time.sleep.
6. Types/style: mypy --strict, ruff clean, no new `Any`.
7. Security: no secrets/payloads in code or logs; read-only tool surfaces stay read-only.
8. Simplicity: delete dead code, avoid speculative abstraction.
Output: `BLOCKER / MAJOR / MINOR` list, then a one-line verdict. Do not edit code unless asked.
