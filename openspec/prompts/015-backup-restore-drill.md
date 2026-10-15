# 015 Backup and restore drill
Epic: E1 | Depends: 011, 012 | Blockers: backup-target conflict
Use: /opsx-propose @openspec/prompts/015-backup-restore-drill.md
Capabilities: backup, restore-drill, offsite-copy
Sources: ARCH V1 (backup, rclone crypt B2/R2); runbook (LUKS header to MEGA).
Requirements:
1. Consistent SQLite+DuckDB snapshot backup to encrypted target.
2. Restore drill into temp path; verifies manifest hashes and schema parity.
3. No secrets in backup logs; credentials via systemd credentials only.
Seed scenarios: corrupt backup; partial upload; restore to empty dir; wrong key.
Open questions: BLOCKING offsite target (B2/R2 vs MEGA for LUKS header only); retention; schedule.
Out of scope: provider data re-fetch.
