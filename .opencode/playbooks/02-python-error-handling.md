# Playbook: Python error handling (load only when writing code with failure paths)
- Fail closed: missing/stale/invalid input → explicit result (`Unavailable(reason)` / WATCH) or typed exception. Never silent default, 0, or `except: pass`.
- Domain errors: small hierarchy under `QuantFlowError`; one class per distinct reason code. Catch narrowly; re-raise with `raise X from e`.
- Validate at boundaries (adapters, IPC, CLI); trust types inside. Return `Result`-style unions in kernels instead of raising for expected cases.
- Never swallow in async tasks: await/gather with `return_exceptions` handled; cancellation (`CancelledError`) propagates.
- Retries only in adapters, bounded, with named-constant limits and backoff; idempotent operations only.
- Log once at the boundary with context (ids, payload_hash); never log secrets or raw payloads.
- Resource cleanup via `with`/`async with`/`try-finally`; no `time.sleep` in async code.
- Tests: each error path has a test asserting the exact reason code.
