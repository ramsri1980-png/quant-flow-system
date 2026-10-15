---
description: Schema, migration and repository work (SQLite WAL + DuckDB epoch-ms rules)
agent: qf-build
---
@.opencode/playbooks/07-quantflow-db-migration.md
@.opencode/playbooks/04-test-driven-development.md
@openspec/conflicts-and-gaps.md

Change / task scope: $ARGUMENTS

Run the OpenSpec apply workflow (see .opencode/commands/opsx-apply.md) for migration/repository tasks only. Check conflicts C8/C9/C10 first and stop if the task depends on an unresolved one. Temp paths only; never touch /data.
