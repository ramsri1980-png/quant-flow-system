# 037 Decision state selection
Epic: E3 | Depends: 033, 036 | Blockers: RQ-002 open design conflict
Use: /opsx-propose @openspec/prompts/037-decision-state-selection.md
Capabilities: decision-order, signal-valid, state-selector
Sources: SPEC V3 §8.4, §8.1a; ARCH V4 §AH
Requirements:
1. Order: RETRACTED > INVALIDATED > STAND_DOWN → DQ gate → signal_valid → portfolio/market/entry outcomes.
2. ACTIONABLE_NOW needs calibrator, p_lower ≥ max(route threshold, p_BE+SAFETY_MARGIN), EV_lower>0, exit handler, fresh quotes.
3. ACTIONABLE_NOW is unreachable until AH exists (exit_handler_exists false).
4. Renderers never upgrade a decision; perp/proxy price never satisfies ACTIONABLE_NOW.
Seed scenarios: each precedence pair; exit handler missing; stale quote; proxy price
Open questions (do not invent): BLOCKING RQ-002; C7 label collisions — cite doc-qualified
Out of scope: exit handlers (080)
