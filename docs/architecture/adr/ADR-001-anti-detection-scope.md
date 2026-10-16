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


## Amendment 2026-10-15 — Source scope only

ADR-001 resolves WHICH sources are authorized for automation. It does
not reduce ARCH Vol 3 §E or §F requirements for sources that ARE
authorized. Any source with `automation_allowed = 1` and an unexpired
review must satisfy every §E and §F rule in full:

- session rhythm §E.0–E.14 (truncated-sampling jitter, session length,
  start-hour draw, weekly multipliers, micro-breaks, pacing floor,
  opening sequence, idle disengagement, winding-down)
- reference browser setup §F.A
- fingerprint coherence §F.B
- traffic shape §F.C
- loopback echo §F.D
- renderer & interaction hygiene §F.H
- prohibited list §F.P (no headless, no Playwright, no Puppeteer, no
  fresh context per session, no automated CAPTCHA solving, no DoH in
  the capture namespace)

"Source scope" is not "capability scope." Reducing the set of
authorized sources never reduces what §E/§F require for the sources
that remain authorized.

## Frozen-layer audit pointer

Prove ARCH Vol 3 §E/§F is unmodified from the v5.1.5.1 freeze (commit 2ce33ea):

    git show 2ce33ea:docs/reference/release-v2.0.5.1-v5.1.5.1/ARCH_v5.1.5.1_Vol3_Capture_AntiDetection.md | sha256sum

Expected: 2d7a90e533196af61745bc4efd3259b7b64b519b8ec78662392b50a911285e23

Errata patches to SPEC Vol 1-4 and ARCH Vol 1-2 do not touch ARCH Vol 3 or SPEC Vol 4 §11.
