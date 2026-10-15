# 023 Filters and corporate actions
Epic: E2 | Depends: 021 | Blockers: none known
Use: /opsx-propose @openspec/prompts/023-filters-corp-actions.md
Capabilities: universe-filters, corporate-action-adjustment
Sources: SPEC V1 filter/universe sections; SPEC V2 §19 (corp action tables).
Requirements:
1. Filters pure and versioned; reject reason recorded.
2. Corporate actions adjust strikes/multipliers deterministically, in integer units.
3. Unknown adjustment → exclude and flag, never guess.
Seed scenarios: split; special dividend; ambiguous deliverable; filter version change.
Open questions: any filter parameter not in docs; adjustment source/provider.
Out of scope: backfill.
