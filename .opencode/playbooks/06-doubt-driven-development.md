# Playbook: doubt-driven development (load for non-trivial decisions only)
Before committing to a design, formula, schema, or fix:
1. State the claim and the evidence (cite doc §, test, or output). No evidence → mark UNVERIFIED.
2. Attack it: name 3 ways it could be wrong (wrong units, stale data, restart, ordering, doc conflict, future leakage).
3. Check each cheaply (read the source, run a one-line test) — do not argue from memory.
4. If a spec gap or conflict appears: stop, add to Open Questions / conflicts log, ask the operator. Do not invent.
5. Record outcome in one line: `Decision / Evidence / Residual risk`.
Skip for trivial edits. Max ~10 lines of reasoning output.
