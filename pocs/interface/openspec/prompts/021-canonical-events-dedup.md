# 021 Canonical events and dedup
Epic: E2 | Depends: 020 | Blockers: hashing rules
Use: /opsx-propose @openspec/prompts/021-canonical-events-dedup.md
Capabilities: canonicalization, dedup, idempotency-keys
Sources: SPEC V1 ingestion/canonical event sections; SPEC V2 §19 (event tables).
Requirements:
1. Provider payload → canonical event via adapter only; kernels see canonical form.
2. Dedup deterministic and idempotent across restart.
3. raw_color → normalized_meaning only via fixture-backed mapping table.
Seed scenarios: same alert twice; reordered fields; unknown color; missing field.
Open questions: BLOCKING content-hash composition, canonical JSON rules, CANONICAL_TRACE_NAMESPACE value; mapping tables need fixtures.
Out of scope: provider fetching.
