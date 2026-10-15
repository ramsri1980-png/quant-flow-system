# 005 Domain types, units, clock
Epic: E0 setup | Depends: none | Blockers: C1 (bundle version), C8 (column type rule)
Use: /opsx-propose @openspec/prompts/005-domain-types-units-clock.md
Capabilities: money-units, epoch-clock, domain-enums, repo-bootstrap
Sources: SPEC V1 §1.4, §19.4.4 (V1+V2); SPEC V2 §19.8.3; ARCH V1 §AI.3 (constants); runbook Task 5 (freeze).

## Process
- Classify every item as RESOLVED_FROM_SOURCE / PROPOSED / BLOCKED.
- Ask one material question at a time. Do not re-ask settled design choices.
- Do NOT silently adopt optional thresholds, notifications, or schema amendments.
- State exact inputs/units/time/availability/IDs, store ownership, versioning, missing-data behavior, tests, and explicit exclusions.
- Map each requirement to a specific source section.
- Check actual implemented evidence (repo state), not only plans.
Requirements:
1. Typed integer wrappers for _cents/_micros/_mills; conversion to dollars only at formula boundary (÷1e6); no float in decision path.
2. Epoch-ms UTC type; ET display only; duration fields bounded integers; naming rule *_ts/*_at/*_epoch_* vs *_ms durations.
3. Injectable Clock port (as_of); no wall-clock reads in domain.
4. Enums with disjoint vocabularies: cluster_grade, cluster_state, episode_state (BASIC is grade only).
5. Named-constants module generated/checked from ARCH V1 §AI.3; constants referenced by name, defined once.
6. Reference bundle frozen under docs/reference/CURRENT with a hash manifest.
Seed scenarios: overflow/negative/rounding of unit conversion; float passed where int required → rejected; same enum literal in two vocabularies → test fails; constant duplicated → lint fails.
Open questions (do not invent): C1 which bundle version; C8 BIGINT vs INTEGER rule per column; rounding mode for ÷1e6 if unspecified.
Out of scope: DB code, providers, kernels.
