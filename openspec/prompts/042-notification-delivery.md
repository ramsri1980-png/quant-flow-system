# 042 Notification delivery
Epic: E4 | Depends: 011 | Blockers: C4 ladder if escalation included
Use: /opsx-propose @openspec/prompts/042-notification-delivery.md
Capabilities: notifier, delivery-ledger
Sources: SPEC V1 delivery sections; SPEC V5 O.7.4
Requirements:
1. Delivery via port; failures retried with bounded policy and logged.
2. Renderers never change a decision.
3. No secrets in payload logs.
Seed scenarios: channel down; duplicate send; ack missing
Open questions (do not invent): BLOCKING C4 ladder vs one-shot re-emit
Out of scope: workflow content
Added (priority 3): consider a soft daily cap or digest for 0DTE cluster pushes (SPEC V1 §2.20.7.6 sets no global cap) — NON-BLOCKING open question for the operator.
