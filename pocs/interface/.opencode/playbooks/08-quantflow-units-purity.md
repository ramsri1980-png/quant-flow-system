# Playbook: QuantFlow units, time and kernel purity (load for kernels/domain/builder work)
- Units: option prices `_cents`, underlying/index `_micros`, strikes/levels `_mills`. Integer in decision path; DOUBLE only analysis-only; ÷1e6 only at formula boundary; convert in one module.
- Time: UTC epoch ms; ET for display only; as_of is a parameter, never `datetime.now()`.
- Kernels: pure functions; no I/O, no wall clock, no randomness except as_of-seeded; same inputs+versions → byte-identical output; no provider calls.
- AnalysisSnapshotBuilder: forbidden calls `fetch_*`, `get_current_*`, `read_pointer_*` (enforce with AST test). Evidence = immutable observation IDs, never package_quote_current.package_quote_id.
- Constants: named once (ARCH V1 §AI.3); import by name; never restate a number.
- Decision order: SPEC V3 §8.4 with signal_valid (§8.1a). Thresholds apply to calibrated lower bounds. 0DTE/1DTE research-only. Enums disjoint (cluster_grade / cluster_state / episode_state).
- Unspecified formula or threshold → Open Question; never invent.
- Tests: golden vectors, boundary/sign, property invariants, no-future-leakage.
