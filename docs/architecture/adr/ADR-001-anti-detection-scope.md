# ADR-001 — Anti-detection scope

Status: Accepted
Date: 2026-10-13

## Context
The capture layer must operate within authorized access only.
ARCH v5.1.5.1 Vol 3 §F is the frozen baseline; it may only be
strengthened, never weakened.

## Decision
Option A. Anti-detection covers authorized session management
of the operator's own paid accounts under
`source_authorization.automation_allowed = 1` with an unexpired
review. It does not cover bypass of provider access controls,
CAPTCHA solving, or continuing past a persistent challenge or
403. On any such signal, the system stops and routes to manual
review.

## Consequences
- Any capture code path must consult source_authorization first.
- The frozen suite (ARCH Vol 3 §F.Q) may grow; it may not shrink.
- Amendments require a diffed change proposal and a re-run of
  the suite.
