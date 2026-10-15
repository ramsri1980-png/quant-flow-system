# Playbook: writing OpenSpec specs for QuantFlow (load for /qf-propose)
- Input is a brief `prompts/NNN-*.md`. Read its Sources in the docs; the docs win over the brief (log disagreement in conflicts-and-gaps.md).
- Split SPECIFIED (stated in docs) from UNSPECIFIED (heading-only, deferred, conflicting). Only SPECIFIED becomes requirements.
- Format: `### Requirement: <name>` with SHALL/MUST, then `#### Scenario:` WHEN/THEN. End each requirement with `Source: <DOC §x>`.
- Each requirement: ≥1 happy scenario + ≥1 failure/boundary (missing, stale, malformed, duplicate, restart).
- Never invent numbers/schemas/enums; reference named constants by name.
- Design.md must have "Open Questions" marked BLOCKING / NON-BLOCKING; list migrations touched (store, id, component).
- One feature = one change; slice by capability; don't mix epics.
- Tasks: tests first, final group ruff + mypy --strict + pytest; BLOCKING questions become "resolve with operator" tasks before apply.
- Keep artifacts terse; no prose padding.
