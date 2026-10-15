# 051 Quote and price adapters
Epic: E5 | Depends: 050, 021 | Blockers: provider schemas need fixtures
Use: /opsx-propose @openspec/prompts/051-quote-price-adapters.md
Capabilities: quote-adapter, price-adapter
Sources: SPEC V1 quote sections; ARCH V1 ports
Requirements:
1. Adapters behind ports; provider logic only here.
2. Freshness stamped; stale → unavailable.
3. Perp/proxy price flagged and never satisfies ACTIONABLE_NOW.
Seed scenarios: stale; schema drift; partial chain
Open questions (do not invent): payload schemas (fixtures required)
Out of scope: capture worker
