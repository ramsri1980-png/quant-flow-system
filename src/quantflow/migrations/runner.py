"""Atomic per-store migration runner (010a).

Group 3.2 scope: the authoritative SPEC V2 §19.2 ledger — its exact DDL,
bootstrap in an isolated committed transaction, and the single-row-per-id
outcome state machine. Classification, baseline identity, and closure follow in
tasks 3.3-3.5.

The runner is I/O only (it never decides anything): it reads/writes the ledger
through an injected connection and takes all timestamps from the Clock port.
Every failure mode fails closed as a `MigrationLedgerError` — a bootstrap
failure is a hard error and is never recorded as a migration outcome row.
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from importlib import metadata
from pathlib import Path
from typing import Any

from quantflow.domain.errors import MigrationLedgerError, MigrationValidationError
from quantflow.domain.time import EpochMs, epoch_ms
from quantflow.migrations.manifest import (
    ADOPT_ONLY_SLOTS,
    BASELINE_ID,
    Manifest,
    ManifestEntry,
    Store,
)
from quantflow.ports.clock import Clock

#: A DBAPI-style connection: `sqlite3.Connection` or `duckdb.DuckDBPyConnection`.
#: Both expose ``execute``/``fetchall``; the runner only uses that surface.
Connection = Any

#: The store-specific authoritative ledger table name (SPEC V2 §19.2).
LEDGER_TABLES: Mapping[Store, str] = {
    Store.SQLITE: "schema_version_sqlite",
    Store.DUCKDB: "schema_version_duckdb",
}

#: Exact SPEC V2 §19.2 ledger DDL. SQLite uses INTEGER, DuckDB BIGINT for
#: `applied_at` (no DuckDB TIMESTAMP); `result` is a closed OK/FAILED vocabulary.
LEDGER_DDL: Mapping[Store, str] = {
    Store.SQLITE: (
        "CREATE TABLE schema_version_sqlite ("
        "migration_id TEXT PRIMARY KEY, "
        "checksum TEXT NOT NULL, "
        "applied_at INTEGER NOT NULL, "
        "app_version TEXT NOT NULL, "
        "result TEXT NOT NULL CHECK(result IN ('OK','FAILED')))"
    ),
    Store.DUCKDB: (
        "CREATE TABLE schema_version_duckdb ("
        "migration_id TEXT PRIMARY KEY, checksum TEXT NOT NULL, "
        "applied_at BIGINT NOT NULL, app_version TEXT NOT NULL, "
        "result TEXT NOT NULL CHECK(result IN ('OK','FAILED')))"
    ),
}

# Literal per-store SQL avoids dynamic query construction (no string-built SQL).
_LEDGER_SELECT_ALL: Mapping[Store, str] = {
    Store.SQLITE: (
        "SELECT migration_id, checksum, applied_at, app_version, result "
        "FROM schema_version_sqlite ORDER BY migration_id"
    ),
    Store.DUCKDB: (
        "SELECT migration_id, checksum, applied_at, app_version, result "
        "FROM schema_version_duckdb ORDER BY migration_id"
    ),
}

_LEDGER_SELECT_ONE: Mapping[Store, str] = {
    Store.SQLITE: (
        "SELECT migration_id, checksum, applied_at, app_version, result "
        "FROM schema_version_sqlite WHERE migration_id = ?"
    ),
    Store.DUCKDB: (
        "SELECT migration_id, checksum, applied_at, app_version, result "
        "FROM schema_version_duckdb WHERE migration_id = ?"
    ),
}

_LEDGER_UPSERT: Mapping[Store, str] = {
    Store.SQLITE: (
        "INSERT INTO schema_version_sqlite "
        "(migration_id, checksum, applied_at, app_version, result) "
        "VALUES (?, ?, ?, ?, ?) "
        "ON CONFLICT(migration_id) DO UPDATE SET "
        "checksum = excluded.checksum, applied_at = excluded.applied_at, "
        "app_version = excluded.app_version, result = excluded.result"
    ),
    Store.DUCKDB: (
        "INSERT INTO schema_version_duckdb "
        "(migration_id, checksum, applied_at, app_version, result) "
        "VALUES (?, ?, ?, ?, ?) "
        "ON CONFLICT(migration_id) DO UPDATE SET "
        "checksum = excluded.checksum, applied_at = excluded.applied_at, "
        "app_version = excluded.app_version, result = excluded.result"
    ),
}

_ALL_TABLES_SQLITE = "SELECT name FROM sqlite_master WHERE type = 'table'"
_ALL_TABLES_DUCKDB = "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'"


class LedgerResult(StrEnum):
    """Closed ledger outcome vocabulary (SPEC V2 §19.2; no IN_PROGRESS)."""

    OK = "OK"
    FAILED = "FAILED"


class StoreState(StrEnum):
    """How a store relates to the baseline (design D6)."""

    FRESH = "fresh"
    ALREADY_BASELINED = "already_baselined"
    LEGACY = "legacy"


@dataclass(frozen=True, slots=True)
class LedgerRow:
    """One authoritative ledger row (one per `migration_id`)."""

    migration_id: str
    checksum: str
    applied_at: EpochMs
    app_version: str
    result: LedgerResult


def ledger_table(store: Store) -> str:
    """The authoritative ledger table name for ``store``."""
    return LEDGER_TABLES[store]


def _all_table_names(conn: Connection, store: Store) -> frozenset[str]:
    sql = _ALL_TABLES_SQLITE if store is Store.SQLITE else _ALL_TABLES_DUCKDB
    rows = conn.execute(sql).fetchall()
    return frozenset(str(row[0]) for row in rows)


def ledger_exists(conn: Connection, store: Store) -> bool:
    """True when the store's ledger table is present."""
    return ledger_table(store) in _all_table_names(conn, store)


def _rollback_quietly(conn: Connection) -> None:
    # Best-effort rollback; the original failure is what we surface.
    try:
        conn.execute("ROLLBACK")
    except Exception:  # noqa: BLE001 - rollback failure must not mask the cause
        return


def bootstrap_ledger(conn: Connection, store: Store) -> None:
    """Create the authoritative ledger in its own committed transaction.

    Idempotent: a present ledger is left untouched. Ledger creation is never
    part of a migration's payload, so a bootstrap failure is a hard error and
    writes no migration outcome row.
    """
    if ledger_exists(conn, store):
        return
    try:
        conn.execute("BEGIN")
        conn.execute(LEDGER_DDL[store])
        conn.execute("COMMIT")
    except Exception as exc:  # noqa: BLE001 - any bootstrap failure is fatal
        _rollback_quietly(conn)
        raise MigrationLedgerError(
            f"failed to bootstrap ledger {ledger_table(store)}: {exc}"
        ) from exc


def _to_row(raw: Sequence[object]) -> LedgerRow:
    migration_id, checksum, applied_at, app_version, result = raw
    if not isinstance(migration_id, str) or not migration_id:
        raise MigrationLedgerError(f"ledger row has an invalid migration_id {migration_id!r}")
    if not isinstance(checksum, str) or not checksum:
        raise MigrationLedgerError(f"ledger row {migration_id!r}: invalid checksum {checksum!r}")
    if not isinstance(app_version, str) or not app_version:
        raise MigrationLedgerError(
            f"ledger row {migration_id!r}: invalid app_version {app_version!r}"
        )
    try:
        parsed_at = epoch_ms(applied_at, field="applied_at")
    except Exception as exc:  # noqa: BLE001 - any unit failure fails closed
        raise MigrationLedgerError(
            f"ledger row {migration_id!r}: invalid applied_at {applied_at!r}"
        ) from exc
    try:
        parsed_result = LedgerResult(str(result))
    except ValueError as exc:
        raise MigrationLedgerError(
            f"ledger row {migration_id!r}: invalid result {result!r}"
        ) from exc
    return LedgerRow(
        migration_id=migration_id,
        checksum=checksum,
        applied_at=parsed_at,
        app_version=app_version,
        result=parsed_result,
    )


def ledger_rows(conn: Connection, store: Store) -> tuple[LedgerRow, ...]:
    """Read every ledger row, failing closed on any malformed value."""
    rows = conn.execute(_LEDGER_SELECT_ALL[store]).fetchall()
    return tuple(_to_row(row) for row in rows)


def read_row(conn: Connection, store: Store, migration_id: str) -> LedgerRow | None:
    """Read one ledger row; a missing ledger or row reads as ``None``."""
    if not ledger_exists(conn, store):
        return None
    row = conn.execute(_LEDGER_SELECT_ONE[store], (migration_id,)).fetchone()
    if row is None:
        return None
    return _to_row(row)


def write_row(conn: Connection, store: Store, row: LedgerRow) -> None:
    """Upsert exactly one ledger row for ``row.migration_id``."""
    conn.execute(
        _LEDGER_UPSERT[store],
        (row.migration_id, row.checksum, int(row.applied_at), row.app_version, row.result.value),
    )


def applied_ok_ids(conn: Connection, store: Store) -> frozenset[str]:
    """IDs whose ledger row records a successful application."""
    return frozenset(
        row.migration_id for row in ledger_rows(conn, store) if row.result is LedgerResult.OK
    )


def failed_ids(conn: Connection, store: Store) -> frozenset[str]:
    """IDs whose ledger row records a failure."""
    return frozenset(
        row.migration_id for row in ledger_rows(conn, store) if row.result is LedgerResult.FAILED
    )


def application_tables(conn: Connection, store: Store) -> frozenset[str]:
    """Application tables present, excluding the ledger itself.

    The ledger is infrastructure, not application schema, so it never counts
    toward the emptiness check that gates baselining.
    """
    return _all_table_names(conn, store) - {ledger_table(store)}


def has_ok_baseline(conn: Connection, store: Store) -> bool:
    """True when an OK ``000_baseline`` ledger row exists for ``store``."""
    if not ledger_exists(conn, store):
        return False
    return BASELINE_ID in applied_ok_ids(conn, store)


def classify_store(conn: Connection, store: Store) -> StoreState:
    """Classify ``store`` as fresh, already-baselined, or legacy.

    An OK baseline row wins; otherwise application schema without a baseline is
    legacy (abort pending an explicit adoption plan); otherwise the store is
    fresh and baseline-eligible.
    """
    if has_ok_baseline(conn, store):
        return StoreState.ALREADY_BASELINED
    if application_tables(conn, store):
        return StoreState.LEGACY
    return StoreState.FRESH


def _app_version() -> str:
    try:
        return metadata.version("quantflow")
    except metadata.PackageNotFoundError as exc:
        raise MigrationLedgerError(
            "cannot resolve the quantflow package version via importlib.metadata; "
            "install the package before running migrations"
        ) from exc


def ok_row_for(entry: ManifestEntry, migrations_root: Path, clock: Clock) -> LedgerRow:
    """Build the OK ledger row for a successfully applied ``entry``.

    The checksum is the lowercase SHA-256 of the file's exact bytes (no
    sentinel); `applied_at` comes from the injected Clock; `app_version` comes
    solely from installed package metadata.
    """
    path = migrations_root / entry.path
    try:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as exc:
        raise MigrationLedgerError(f"cannot read migration file {entry.path}: {exc}") from exc
    return LedgerRow(
        migration_id=entry.id,
        checksum=digest,
        applied_at=clock.now_ms(),
        app_version=_app_version(),
        result=LedgerResult.OK,
    )


def check_baseline_closure(manifest: Manifest, store: Store, applied_ok: frozenset[str]) -> None:
    """Fail closed unless every applied dependency is satisfied.

    A dependency is satisfied by a recorded OK ledger row. IDs listed in the
    informational `baseline_covered` metadata are satisfied only by the real OK
    baseline row — coverage is never fabricated into a ledger row (design D11).
    Disabled and ADOPT-ONLY entries are not applied, so they are not checked.
    """
    covered = set(manifest.covered_ids(store))
    baseline_applied = BASELINE_ID in applied_ok
    adopt_only = ADOPT_ONLY_SLOTS[store]
    for entry in manifest.entries:
        if entry.store is not store or not entry.enabled or entry.slot in adopt_only:
            continue
        for dep in entry.applies_after:
            if dep in applied_ok:
                continue
            if dep in covered and baseline_applied:
                continue
            raise MigrationValidationError(
                f"migration {entry.id!r}: unsatisfied dependency {dep!r}"
            )
