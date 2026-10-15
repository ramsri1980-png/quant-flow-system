# 020 Raw event archive and IPC
Epic: E2 | Depends: 011, 013 | Blockers: IPC gaps
Use: /opsx-propose @openspec/prompts/020-raw-event-archive-ipc.md
Capabilities: raw-archive, ipc-localhost, ack-protocol
Sources: ARCH V1 §M.1 (IPC), ARCH V3 §F.S (isolation); SPEC V1 ingestion sections.
Requirements:
1. Capture worker talks to quantd only over localhost/Unix socket; no DB, no vault token in worker.
2. Raw events archived immutably with payload_hash before parsing.
3. Credentials only via one-time quantd-mediated token (TTL 60 s).
4. Malformed/oversize message rejected and counted.
Seed scenarios: token reuse/expired; duplicate raw event; malformed frame; quantd restart mid-stream.
Open questions: BLOCKING no "pause capture intake" event and no ACK message type in the event list — define? canonical JSON hashing rules unspecified.
Out of scope: canonicalization, DQ.
