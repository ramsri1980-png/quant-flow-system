# 013 Writer queue and outbox
Epic: E1 | Depends: 011, 012 | Blockers: none known
Use: /opsx-propose @openspec/prompts/013-writer-queue-outbox.md
Capabilities: writer-queue, outbox, idempotent-replay
Sources: ARCH V1 (quantd process model), ARCH V2 (storage); constitution §6.
Requirements:
1. Single serialized writer in quantd; bounded queue with explicit backpressure (named constants).
2. Outbox for SQLite→DuckDB propagation, at-least-once with idempotent apply.
3. Restart resumes from last committed outbox position; no loss, no duplicate effect.
4. Failures logged loudly, never silently dropped (fail closed).
Seed scenarios: crash between SQLite commit and outbox ack; queue full; poison message; duplicate delivery.
Open questions: outbox table schema/IDs if not in DDL; retry/backoff constants (name in ARCH V1 §AI.3 or ask).
Out of scope: provider ingestion.
