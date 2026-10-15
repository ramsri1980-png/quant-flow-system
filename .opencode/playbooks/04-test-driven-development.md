# Playbook: TDD (load when implementing tasks)
Loop per task: RED (write failing test) → GREEN (smallest code) → REFACTOR (tests stay green). Never write production code without a failing test first.
- Derive tests from the spec's `#### Scenario:` blocks; one test per scenario, named after it.
- Ten classes per feature: golden, boundary/units/sign, missing/stale/malformed, duplicate/idempotency/restart, port contract, migration fresh+upgrade, replay, property invariants (hypothesis), no-future-leakage, temp-paths-only.
- Kernels: pure → golden vectors + property tests; coverage ≥95% on kernels/** and domain/**.
- Use fakes for ports and an injected Clock; never real time, network, providers, or `/data`.
- Test behavior, not implementation. No weakening a domain test to make a live provider pass.
- Run the narrowest test first (`uv run pytest path::test -x`), then the full suite before marking a task done.
- Bug found → add a regression test first.
