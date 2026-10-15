# 070 Control plane and Muse
Epic: E7 | Depends: 011 | Blockers: none known
Use: /opsx-propose @openspec/prompts/070-control-plane-muse.md
Capabilities: quantctl, muse-readonly-tools
Sources: ARCH V1; constitution §6
Requirements:
1. Operator mutations only via quantctl → quantd with operator_control_audit row.
2. MCP/Muse tools read-only fixed templates: no SQL, shell, URL, secret, order, migration tools.
Seed scenarios: unaudited mutation rejected; forbidden tool absent
Open questions (do not invent): tool list beyond docs
Out of scope: UI
