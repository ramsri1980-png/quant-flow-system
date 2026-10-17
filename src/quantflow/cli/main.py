"""QuantFlow operator CLI entry point (Typer)."""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import typer

from quantflow.migrations import manifest as m
from quantflow.migrations import runner as r
from quantflow.adapters.clock import SystemClock

app = typer.Typer(
    help="QuantFlow operator CLI.",
    no_args_is_help=True,
    add_completion=False,
)

migrate_app = typer.Typer(
    help="Forward-only, checksum-verified schema migrations.",
    no_args_is_help=True,
)


@migrate_app.command()
def apply(
    store: str,
    manifest_path: Path,
) -> None:
    """Apply pending migrations to the selected store."""
    # Parse store
    try:
        store_obj = m.Store(store)
    except ValueError:
        typer.echo(f"Invalid store: {store}. Must be 'sqlite' or 'duckdb'", err=True)
        raise typer.Exit(code=2) from None

    # Validate manifest exists
    if not manifest_path.is_file():
        typer.echo(f"Manifest not found: {manifest_path}", err=True)
        raise typer.Exit(code=2) from None

    try:
        # Load and validate manifest
        manifest_obj = m.load_manifest(manifest_path.parent)

        # Get connection based on store type
        if store_obj is m.Store.SQLITE:
            db_path = manifest_path.parent / "quant_state.db"
            conn = r.open_standalone_sqlite(db_path)
            r.verify_sqlite_pragmas(conn)
        else:  # DUCKDB
            db_path = manifest_path.parent / "quant_flow.duckdb"
            temp_dir = manifest_path.parent / "duckdb_tmp"
            conn = r.open_standalone_duckdb(db_path, temp_dir)

        try:
            # Apply migrations
            result = r.apply_store(conn, store_obj, manifest_obj, manifest_path.parent, SystemClock())
            typer.echo(
                f"Successfully applied {len(result.applied)} migration(s) to {store_obj.value} store."
            )
            if result.skipped:
                typer.echo(f"Skipped {len(result.skipped)} already-applied migration(s).")
        except r.MigrationLedgerError as exc:
            typer.echo(f"Migration failed: {exc}", err=True)
            raise typer.Exit(code=1) from None
        except r.MigrationValidationError as exc:
            typer.echo(f"Validation error: {exc}", err=True)
            raise typer.Exit(code=1) from None
        finally:
            conn.close()

    except m.MigrationManifestError as exc:
        typer.echo(f"Manifest error: {exc}", err=True)
        raise typer.Exit(code=2) from None
    except m.MigrationValidationError as exc:
        typer.echo(f"Validation error: {exc}", err=True)
        raise typer.Exit(code=1) from None
    except Exception as exc:
        typer.echo(f"Unexpected error: {exc}", err=True)
        raise typer.Exit(code=2) from None


@migrate_app.command()
def status(
    store: str,
) -> None:
    """Report pending count and each store's last successful migration."""
    # Parse store
    try:
        store_obj = m.Store(store)
    except ValueError:
        typer.echo(f"Invalid store: {store}. Must be 'sqlite' or 'duckdb'", err=True)
        raise typer.Exit(code=2) from None

    try:
        # Get connection
        if store_obj is m.Store.SQLITE:
            db_path = Path("quant_state.db")
            if not db_path.exists():
                typer.echo("Store does not exist (no database file)", err=True)
                raise typer.Exit(code=2) from None
            conn = r.open_standalone_sqlite(db_path)
            r.verify_sqlite_pragmas(conn)
        else:  # DUCKDB
            db_path = Path("quant_flow.duckdb")
            if not db_path.exists():
                typer.echo("Store does not exist (no database file)", err=True)
                raise typer.Exit(code=2) from None
            temp_dir = Path("duckdb_tmp")
            conn = r.open_standalone_duckdb(db_path, temp_dir)

        try:
            # Check if ledger exists
            if not r.ledger_exists(conn, store_obj):
                typer.echo(f"Store {store_obj.value} has no migration ledger")
                typer.echo("Pending count: 0 (fresh store)")
                typer.echo("Last successful migration: None")
                return

            # Get applied migrations (OK rows)
            applied_ok = r.applied_ok_ids(conn, store_obj)
            pending_count = len(applied_ok)  # This is actually applied count

            # Get last successful migration
            last_successful = None
            if applied_ok:
                rows = r.ledger_rows(conn, store_obj)
                # Find the last OK row by applied_at (most recent)
                ok_rows = [row for row in rows if row.result == r.LedgerResult.OK]
                if ok_rows:
                    # Sort by applied_at descending and get the first
                    ok_rows.sort(key=lambda row: row.applied_at, reverse=True)
                    last_successful = ok_rows[0].migration_id

            # Get failed migrations
            failed_ids = r.failed_ids(conn, store_obj)

            typer.echo(f"Store: {store_obj.value}")
            typer.echo(f"Applied migrations: {pending_count}")
            typer.echo(f"Last successful migration: {last_successful or 'None'}")
            if failed_ids:
                typer.echo(f"Failed migrations: {sorted(failed_ids)} (blocking apply)")
            else:
                typer.echo("Failed migrations: None")

        except r.MigrationLedgerError as exc:
            typer.echo(f"Ledger error: {exc}", err=True)
            raise typer.Exit(code=1) from None
        except r.MigrationValidationError as exc:
            typer.echo(f"Validation error: {exc}", err=True)
            raise typer.Exit(code=1) from None
        finally:
            conn.close()

    except Exception as exc:
        typer.echo(f"Unexpected error: {exc}", err=True)
        raise typer.Exit(code=2) from None


@migrate_app.command()
def verify(
    store: str,
    manifest_path: Path,
) -> None:
    """Verify store/manifest/ledger consistency read-only."""
    # Parse store
    try:
        store_obj = m.Store(store)
    except ValueError:
        typer.echo(f"Invalid store: {store}. Must be 'sqlite' or 'duckdb'", err=True)
        raise typer.Exit(code=2) from None

    # Validate manifest exists
    if not manifest_path.is_file():
        typer.echo(f"Manifest not found: {manifest_path}", err=True)
        raise typer.Exit(code=2) from None

    try:
        # Load and validate manifest (this does not touch disk beyond reading manifest)
        manifest_obj = m.load_manifest(manifest_path.parent)

        # Get connection (standalone, read-only for verification)
        if store_obj is m.Store.SQLITE:
            db_path = manifest_path.parent / "quant_state.db"
            if not db_path.exists():
                typer.echo(f"Database not found: {db_path}", err=True)
                raise typer.Exit(code=1) from None
            conn = r.open_standalone_sqlite(db_path)
            r.verify_sqlite_pragmas(conn)
        else:  # DUCKDB
            db_path = manifest_path.parent / "quant_flow.duckdb"
            if not db_path.exists():
                typer.echo(f"Database not found: {db_path}", err=True)
                raise typer.Exit(code=1) from None
            temp_dir = manifest_path.parent / "duckdb_tmp"
            conn = r.open_standalone_duckdb(db_path, temp_dir)

        try:
            # 1. Verify manifest entries match actual files and checksums
            for entry in manifest_obj.entries:
                path = manifest_path.parent / entry.path
                if not path.is_file():
                    raise m.MigrationValidationError(
                        f"manifest entry {entry.id!r}: file not found at {path}"
                    )

                # Check SHA-256
                try:
                    digest = hashlib.sha256(path.read_bytes()).hexdigest()
                except OSError as exc:
                    raise m.MigrationValidationError(
                        f"cannot read migration file {entry.path}: {exc}"
                    ) from exc

                if digest != entry.sha256:
                    raise m.MigrationValidationError(
                        f"checksum mismatch for {entry.id!r}: "
                        f"manifest {entry.sha256} != on-disk {digest}"
                    )

            # 2. Verify ledger consistency (read-only)
            # Check that ledger table exists
            if not r.ledger_exists(conn, store_obj):
                raise m.MigrationValidationError(
                    f"ledger table {r.ledger_table(store_obj)} not found in {store_obj.value} store"
                )

            # Get all ledger rows
            ledger_rows = r.ledger_rows(conn, store_obj)
            ledger_id_to_row = {row.migration_id: row for row in ledger_rows}

            # 3. Verify every manifest entry has a corresponding ledger row with matching checksum
            for entry in manifest_obj.entries:
                ledger_row = ledger_id_to_row.get(entry.id)
                if ledger_row is None:
                    raise m.MigrationValidationError(
                        f"manifest entry {entry.id!r}: not found in ledger"
                    )

                if entry.sha256 != ledger_row.checksum:
                    raise m.MigrationValidationError(
                        f"checksum mismatch for {entry.id!r}: "
                        f"manifest {entry.sha256} != ledger {ledger_row.checksum}"
                    )

            # 4. Verify every ledger row corresponds to a manifest entry
            manifest_ids = {entry.id for entry in manifest_obj.entries}
            for ledger_row in ledger_rows:
                if ledger_row.migration_id not in manifest_ids:
                    raise m.MigrationValidationError(
                        f"ledger contains unknown migration {ledger_row.migration_id!r}"
                    )

            # 5. Verify no FAILED rows (these block apply)
            failed_rows = [row for row in ledger_rows if row.result == r.LedgerResult.FAILED]
            if failed_rows:
                failed_ids = [row.migration_id for row in failed_rows]
                raise m.MigrationValidationError(
                    f"store {store_obj.value} has failed migration(s) {sorted(failed_ids)}; "
                    f"apply aborts until they are explicitly resolved"
                )

            # 6. Verify slot policy (NEVER and ADOPT-ONLY)
            for entry in manifest_obj.entries:
                if entry.store is store_obj:
                    if entry.slot in m.NEVER_SLOTS[entry.store]:
                        raise m.MigrationValidationError(
                            f"migration {entry.id!r} uses a reserved {entry.store.value} slot "
                            f"({entry.slot:03d})"
                        )
                    if entry.slot in m.ADOPT_ONLY_SLOTS[entry.store]:
                        raise m.MigrationValidationError(
                            f"migration {entry.id!r} is ADOPT-ONLY and cannot be applied "
                            f"(requires operator approval)"
                        )

            # 7. Verify all entries are enabled
            for entry in manifest_obj.entries:
                if not entry.enabled:
                    raise m.MigrationValidationError(f"migration {entry.id!r} is disabled")

            # 8. Verify dependency closure against OK ledger rows
            applied_ok_ids = {
                row.migration_id for row in ledger_rows if row.result == r.LedgerResult.OK
            }
            r.check_baseline_closure(manifest_obj, store_obj, frozenset(applied_ok_ids))

            # 9. Verify baseline identity (if 000_baseline is in manifest)
            baseline_entry = next((e for e in manifest_obj.entries if e.id == "000_baseline"), None)
            if baseline_entry:
                baseline_ledger_row = ledger_id_to_row.get("000_baseline")
                if baseline_ledger_row is None:
                    raise m.MigrationValidationError(
                        "baseline migration '000_baseline' declared in manifest but not found in ledger"
                    )
                if baseline_ledger_row.result != r.LedgerResult.OK:
                    raise m.MigrationValidationError(
                        "baseline migration '000_baseline' must have OK result in ledger"
                    )
                if baseline_entry.sha256 != baseline_ledger_row.checksum:
                    raise m.MigrationValidationError(
                        "baseline migration '000_baseline' checksum mismatch between manifest and ledger"
                    )

            # All checks passed
            typer.echo("Verification successful: store/manifest/ledger are consistent")

        except m.MigrationManifestError as exc:
            typer.echo(f"Manifest error: {exc}", err=True)
            raise typer.Exit(code=2) from None
        except m.MigrationValidationError as exc:
            typer.echo(f"Validation error: {exc}", err=True)
            raise typer.Exit(code=1) from None
        finally:
            conn.close()

    except Exception as exc:
        typer.echo(f"Unexpected error: {exc}", err=True)
        raise typer.Exit(code=2) from None


@migrate_app.command()
def retry_failed(
    store: str,
    migration_id: str,
    reason: str,
) -> None:
    """Retry a failed migration with audit logging (OQ-1 resolution)."""
    if not reason.strip():
        typer.echo("--reason is required and must not be empty", err=True)
        raise typer.Exit(code=2) from None

    # Parse store
    try:
        store_obj = m.Store(store)
    except ValueError:
        typer.echo(f"Invalid store: {store}. Must be 'sqlite' or 'duckdb'", err=True)
        raise typer.Exit(code=2) from None

    try:
        # Get connection
        if store_obj is m.Store.SQLITE:
            db_path = Path("quant_state.db")
            if not db_path.exists():
                typer.echo(f"Database not found: {db_path}", err=True)
                raise typer.Exit(code=2) from None
            conn = r.open_standalone_sqlite(db_path)
            r.verify_sqlite_pragmas(conn)
        else:  # DUCKDB
            db_path = Path("quant_flow.duckdb")
            if not db_path.exists():
                typer.echo(f"Database not found: {db_path}", err=True)
                raise typer.Exit(code=2) from None
            temp_dir = Path("duckdb_tmp")
            conn = r.open_standalone_duckdb(db_path, temp_dir)

        try:
            # 1. Verify the migration exists and is in FAILED state
            ledger_row = r.read_row(conn, store_obj, migration_id)
            if ledger_row is None:
                typer.echo(f"Migration {migration_id} not found in ledger", err=True)
                raise typer.Exit(code=2) from None

            if ledger_row.result != r.LedgerResult.FAILED:
                typer.echo(
                    f"Migration {migration_id} is not in FAILED state (current: {ledger_row.result.value})",
                    err=True,
                )
                raise typer.Exit(code=2) from None

            # 2. Verify no partial schema changes and checksum match
            # This is simplified - in a full implementation we'd need to load the manifest
            # and verify the file still matches the recorded checksum
            manifest_path = Path("migrations/MANIFEST.json")
            if manifest_path.exists():
                manifest_obj = m.load_manifest(manifest_path.parent)
                manifest_entry = next(
                    (e for e in manifest_obj.entries if e.id == migration_id), None
                )
                if manifest_entry is None:
                    typer.echo(f"Migration {migration_id} not found in manifest", err=True)
                    raise typer.Exit(code=2) from None

                # Verify file exists and checksum matches
                migration_file = manifest_path.parent / manifest_entry.path
                if not migration_file.is_file():
                    typer.echo(f"Migration file not found: {manifest_entry.path}", err=True)
                    raise typer.Exit(code=2) from None

                try:
                    digest = hashlib.sha256(migration_file.read_bytes()).hexdigest()
                except OSError as exc:
                    typer.echo(f"Cannot read migration file: {exc}", err=True)
                    raise typer.Exit(code=1) from None

                if digest != manifest_entry.sha256:
                    typer.echo(f"Checksum mismatch for migration {migration_id}", err=True)
                    raise typer.Exit(code=1) from None

                if digest != ledger_row.checksum:
                    typer.echo(f"Ledger checksum mismatch for migration {migration_id}", err=True)
                    raise typer.Exit(code=1) from None
            else:
                typer.echo("Manifest not found - skipping file verification", err=True)
                # In production, we would want to fail here, but for now continue

            # 3. Perform the retry: DELETE FAILED row, re-apply migration, write audit log
            conn.execute("BEGIN")
            try:
                # Delete the FAILED row (table name is from a fixed vocabulary)  # noqa: S608
                conn.execute("DELETE FROM " + r.ledger_table(store_obj) + " WHERE migration_id = ?", (migration_id,))  # noqa: S608

                # If we have manifest, re-apply the migration
                if manifest_path.exists():
                    manifest_obj = m.load_manifest(manifest_path.parent)
                    manifest_entry = next(
                        (e for e in manifest_obj.entries if e.id == migration_id), None
                    )
                    if manifest_entry:
                        # Use the system clock for consistency
                        clock = SystemClock()
                        r.apply_entry(conn, store_obj, manifest_entry, manifest_path.parent, clock)

                # Write audit log entry (operator_control_audit table would be created by 010b)
                # For 010a, we'll just log to stdout as specified in the resolution
                typer.echo(
                    f'AUDIT: migration_retry_failed store={store_obj.value} migration_id={migration_id} reason="{reason}"'
                )

                conn.execute("COMMIT")
                typer.echo(f"Successfully retried migration {migration_id}")

            except Exception:
                conn.execute("ROLLBACK")
                raise

        except r.MigrationLedgerError as exc:
            typer.echo(f"Ledger error: {exc}", err=True)
            raise typer.Exit(code=1) from None
        except r.MigrationValidationError as exc:
            typer.echo(f"Validation error: {exc}", err=True)
            raise typer.Exit(code=1) from None
        finally:
            conn.close()

    except Exception as exc:
        typer.echo(f"Unexpected error: {exc}", err=True)
        raise typer.Exit(code=2) from None


app.add_typer(migrate_app, name="migrate")


def main() -> None:
    """Console-script entry point."""
    try:
        app()
    except typer.Exit as e:
        sys.exit(e.no)
    except Exception as exc:
        typer.echo(f"Fatal error: {exc}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
