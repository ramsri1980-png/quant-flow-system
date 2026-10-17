"""010a group 3 — ledger, classification, and baseline identity (tasks 3.1-3.5).

Derived from `specs/migration-runner/spec.md` scenarios (Authoritative ledger
bootstrap, Store classification, Ledger outcome states, Baseline ledger identity,
Baseline dependency closure, Application version source) and design D6-D11.

Imports the module object (not names) so each sub-task's subset can go green
incrementally while later sub-tasks stay red.
"""

from __future__ import annotations

import ast
import hashlib
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from importlib import metadata
from pathlib import Path

import duckdb
import pytest

from quantflow.domain.errors import MigrationLedgerError, MigrationValidationError
from quantflow.domain.time import EPOCH_MS_MIN, EpochMs, epoch_ms
from quantflow.migrations import manifest as m
from quantflow.migrations import runner as r
from quantflow.ports.clock import Clock

APP_TABLE = "options_master"
FIXED_NOW = epoch_ms(1_760_000_000_000)

# Fixed per-store SQL (no string building) for raw ledger inserts in tests.
_RAW_LEDGER_INSERT = {
    m.Store.SQLITE: "INSERT INTO schema_version_sqlite VALUES (?, ?, ?, ?, ?)",
    m.Store.DUCKDB: "INSERT INTO schema_version_duckdb VALUES (?, ?, ?, ?, ?)",
}


class FakeClock:
    """Injected test double; the ledger observes time only through the port."""

    def __init__(self, now: EpochMs = FIXED_NOW) -> None:
        self._now = now

    def now_ms(self) -> EpochMs:
        return self._now


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #


@contextmanager
def _connect(store: m.Store, path: Path) -> Iterator[object]:
    conn: object
    if store is m.Store.SQLITE:
        conn = sqlite3.connect(path, isolation_level=None)
    else:
        conn = duckdb.connect(str(path))
    try:
        yield conn
    finally:
        conn.close()  # type: ignore[attr-defined]


def _write_sql(root: Path, relpath: str, body: str) -> str:
    path = root / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(body.encode())
    return hashlib.sha256(body.encode()).hexdigest()


def _entry(
    *,
    migration_id: str = "000_baseline",
    store: str = "sqlite",
    path: str | None = None,
    sha256: str = "0" * 64,
    applies_after: tuple[str, ...] = (),
    enabled: bool = True,
) -> dict[str, object]:
    return {
        "id": migration_id,
        "store": store,
        "path": path if path is not None else f"{store}/{migration_id}.sql",
        "sha256": sha256,
        "applies_after": list(applies_after),
        "component": "core",
        "enabled": enabled,
    }


def _doc(*entries: dict[str, object], baseline_covered: object = None) -> dict[str, object]:
    doc: dict[str, object] = {"version": 1, "migrations": list(entries)}
    if baseline_covered is not None:
        doc["baseline_covered"] = baseline_covered
    return doc


def _insert_ok(conn: object, store: m.Store, migration_id: str, checksum: str = "a" * 64) -> None:
    r.write_row(
        conn,  # type: ignore[arg-type]
        store,
        r.LedgerRow(
            migration_id=migration_id,
            checksum=checksum,
            applied_at=FIXED_NOW,
            app_version="1.2.3",
            result=r.LedgerResult.OK,
        ),
    )


def _create_app_table(conn: object, store: m.Store) -> None:
    if store is m.Store.SQLITE:
        conn.execute("CREATE TABLE options_master (id TEXT PRIMARY KEY)")  # type: ignore[attr-defined]
    else:
        conn.execute("CREATE TABLE options_master (id VARCHAR PRIMARY KEY)")  # type: ignore[attr-defined]


@pytest.fixture(params=[m.Store.SQLITE, m.Store.DUCKDB], ids=["sqlite", "duckdb"])
def store(request: pytest.FixtureRequest) -> m.Store:
    return request.param


def _db_path(tmp_path: Path, store: m.Store) -> Path:
    return tmp_path / ("quant_state.db" if store is m.Store.SQLITE else "quant_flow.duckdb")


# --------------------------------------------------------------------------- #
# 1. bootstrap (missing/stale/malformed + migration fresh class)
# --------------------------------------------------------------------------- #


class TestLedgerBootstrap:
    def test_bootstrap_creates_empty_ledger_before_first_migration(
        self, store: m.Store, tmp_path: Path
    ) -> None:
        with _connect(store, _db_path(tmp_path, store)) as conn:
            assert not r.ledger_exists(conn, store)
            r.bootstrap_ledger(conn, store)
            assert r.ledger_exists(conn, store)
            assert r.ledger_rows(conn, store) == ()

    def test_bootstrap_is_idempotent_on_restart(self, store: m.Store, tmp_path: Path) -> None:
        path = _db_path(tmp_path, store)
        with _connect(store, path) as conn:
            r.bootstrap_ledger(conn, store)
            _insert_ok(conn, store, "000_baseline")
        with _connect(store, path) as conn:  # restart: reopen the same file
            r.bootstrap_ledger(conn, store)
            assert [row.migration_id for row in r.ledger_rows(conn, store)] == ["000_baseline"]

    def test_bootstrap_failure_is_a_hard_error_and_writes_no_row(
        self, store: m.Store, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        class _FailingConnection:
            def execute(self, sql: str, parameters: object = ()) -> object:
                raise sqlite3.OperationalError("simulated bootstrap failure")

        monkeypatch.setattr(r, "ledger_exists", lambda *args, **kwargs: False)
        with pytest.raises(MigrationLedgerError):
            r.bootstrap_ledger(_FailingConnection(), store)  # type: ignore[arg-type]


# --------------------------------------------------------------------------- #
# 2. exact SPEC V2 §19.2 schema
# --------------------------------------------------------------------------- #


class TestLedgerSchema:
    DDL_SQLITE = (
        "CREATE TABLE schema_version_sqlite ("
        "migration_id TEXT PRIMARY KEY, "
        "checksum TEXT NOT NULL, "
        "applied_at INTEGER NOT NULL, "
        "app_version TEXT NOT NULL, "
        "result TEXT NOT NULL CHECK(result IN ('OK','FAILED')))"
    )
    DDL_DUCKDB = (
        "CREATE TABLE schema_version_duckdb ("
        "migration_id TEXT PRIMARY KEY, checksum TEXT NOT NULL, "
        "applied_at BIGINT NOT NULL, app_version TEXT NOT NULL, "
        "result TEXT NOT NULL CHECK(result IN ('OK','FAILED')))"
    )

    def test_ddl_matches_spec_vol2_exactly(self, store: m.Store) -> None:
        expected = self.DDL_SQLITE if store is m.Store.SQLITE else self.DDL_DUCKDB
        assert " ".join(r.LEDGER_DDL[store].split()) == " ".join(expected.split())

    def test_ledger_table_name_is_store_specific(self, store: m.Store) -> None:
        assert r.ledger_table(store) == r.LEDGER_TABLES[store]
        assert r.ledger_table(store) != r.ledger_table(
            m.Store.DUCKDB if store is m.Store.SQLITE else m.Store.SQLITE
        )

    def test_exact_columns_after_bootstrap(self, store: m.Store, tmp_path: Path) -> None:
        with _connect(store, _db_path(tmp_path, store)) as conn:
            r.bootstrap_ledger(conn, store)
            names = _column_names(conn, store)
        assert names == ["migration_id", "checksum", "applied_at", "app_version", "result"]

    def test_result_check_constraint_rejects_other_values(
        self, store: m.Store, tmp_path: Path
    ) -> None:
        with _connect(store, _db_path(tmp_path, store)) as conn:
            r.bootstrap_ledger(conn, store)
            with pytest.raises((sqlite3.IntegrityError, duckdb.ConstraintException)):
                conn.execute(  # type: ignore[attr-defined]
                    _RAW_LEDGER_INSERT[store],
                    ("x", "abc", EPOCH_MS_MIN, "0", "IN_PROGRESS"),
                )

    def test_result_vocabulary_is_closed(self) -> None:
        assert {member.value for member in r.LedgerResult} == {"OK", "FAILED"}


def _column_names(conn: object, store: m.Store) -> list[str]:
    if store is m.Store.SQLITE:
        rows = conn.execute(  # type: ignore[attr-defined]
            "PRAGMA table_info(" + r.ledger_table(store) + ")"
        ).fetchall()
        return [str(row[1]) for row in sorted(rows, key=lambda row: row[0])]
    rows = conn.execute(  # type: ignore[attr-defined]
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_name = ? ORDER BY ordinal_position",
        (r.ledger_table(store),),
    ).fetchall()
    return [str(row[0]) for row in rows]


# --------------------------------------------------------------------------- #
# 3. store classification (fresh / already-baselined / legacy)
# --------------------------------------------------------------------------- #


class TestStoreClassification:
    def test_missing_ledger_and_no_tables_is_fresh(self, store: m.Store, tmp_path: Path) -> None:
        with _connect(store, _db_path(tmp_path, store)) as conn:
            assert r.classify_store(conn, store) is r.StoreState.FRESH

    def test_bootstrapped_empty_ledger_without_app_tables_is_fresh(
        self, store: m.Store, tmp_path: Path
    ) -> None:
        with _connect(store, _db_path(tmp_path, store)) as conn:
            r.bootstrap_ledger(conn, store)
            assert r.application_tables(conn, store) == frozenset()
            assert r.classify_store(conn, store) is r.StoreState.FRESH

    def test_ok_baseline_row_is_already_baselined(self, store: m.Store, tmp_path: Path) -> None:
        with _connect(store, _db_path(tmp_path, store)) as conn:
            r.bootstrap_ledger(conn, store)
            _insert_ok(conn, store, m.BASELINE_ID)
            assert r.classify_store(conn, store) is r.StoreState.ALREADY_BASELINED

    def test_application_table_without_baseline_is_legacy(
        self, store: m.Store, tmp_path: Path
    ) -> None:
        with _connect(store, _db_path(tmp_path, store)) as conn:
            _create_app_table(conn, store)
            assert r.classify_store(conn, store) is r.StoreState.LEGACY

    def test_failed_baseline_with_application_table_is_legacy(
        self, store: m.Store, tmp_path: Path
    ) -> None:
        with _connect(store, _db_path(tmp_path, store)) as conn:
            r.bootstrap_ledger(conn, store)
            r.write_row(
                conn,
                store,
                r.LedgerRow(
                    migration_id=m.BASELINE_ID,
                    checksum="b" * 64,
                    applied_at=FIXED_NOW,
                    app_version="1.2.3",
                    result=r.LedgerResult.FAILED,
                ),
            )
            _create_app_table(conn, store)
            assert r.classify_store(conn, store) is r.StoreState.LEGACY

    def test_non_empty_ledger_with_application_tables_is_not_baseline_eligible(
        self, store: m.Store, tmp_path: Path
    ) -> None:
        with _connect(store, _db_path(tmp_path, store)) as conn:
            r.bootstrap_ledger(conn, store)
            _insert_ok(conn, store, "069_hist")
            _create_app_table(conn, store)
            assert r.classify_store(conn, store) is r.StoreState.LEGACY

    def test_ledger_is_excluded_from_the_emptiness_check(
        self, store: m.Store, tmp_path: Path
    ) -> None:
        with _connect(store, _db_path(tmp_path, store)) as conn:
            r.bootstrap_ledger(conn, store)
            # the only table is the ledger itself; the store is still empty
            assert r.application_tables(conn, store) == frozenset()
            assert r.ledger_table(store) in _all_table_names(conn, store)


def _all_table_names(conn: object, store: m.Store) -> frozenset[str]:
    if store is m.Store.SQLITE:
        rows = conn.execute(  # type: ignore[attr-defined]
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
    else:
        rows = conn.execute(  # type: ignore[attr-defined]
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'"
        ).fetchall()
    return frozenset(str(row[0]) for row in rows)


# --------------------------------------------------------------------------- #
# 4. ledger rows (duplicate/idempotency/restart + malformed)
# --------------------------------------------------------------------------- #


class TestLedgerRows:
    def test_missing_row_reads_as_none(self, store: m.Store, tmp_path: Path) -> None:
        with _connect(store, _db_path(tmp_path, store)) as conn:
            assert r.read_row(conn, store, "010_missing") is None

    def test_write_row_upserts_a_single_row_per_id(self, store: m.Store, tmp_path: Path) -> None:
        with _connect(store, _db_path(tmp_path, store)) as conn:
            r.bootstrap_ledger(conn, store)
            _insert_ok(conn, store, "010_a", checksum="a" * 64)
            _insert_ok(conn, store, "010_a", checksum="c" * 64)
            rows = r.ledger_rows(conn, store)
            assert [row.migration_id for row in rows] == ["010_a"]
            assert rows[0].checksum == "c" * 64

    def test_ok_and_failed_ids_are_separated(self, store: m.Store, tmp_path: Path) -> None:
        with _connect(store, _db_path(tmp_path, store)) as conn:
            r.bootstrap_ledger(conn, store)
            _insert_ok(conn, store, m.BASELINE_ID)
            r.write_row(
                conn,
                store,
                r.LedgerRow(
                    migration_id="020_b",
                    checksum="d" * 64,
                    applied_at=FIXED_NOW,
                    app_version="1.2.3",
                    result=r.LedgerResult.FAILED,
                ),
            )
            assert r.applied_ok_ids(conn, store) == frozenset({m.BASELINE_ID})
            assert r.failed_ids(conn, store) == frozenset({"020_b"})

    def test_malformed_result_fails_closed(self, store: m.Store, tmp_path: Path) -> None:
        with _connect(store, _db_path(tmp_path, store)) as conn:
            _create_permissive_ledger(conn, store)
            conn.execute(  # type: ignore[attr-defined]
                _RAW_LEDGER_INSERT[store],
                ("010_a", "a" * 64, EPOCH_MS_MIN, "1.2.3", "IN_PROGRESS"),
            )
            with pytest.raises(MigrationLedgerError):
                r.ledger_rows(conn, store)

    def test_malformed_applied_at_fails_closed(self, store: m.Store, tmp_path: Path) -> None:
        with _connect(store, _db_path(tmp_path, store)) as conn:
            _create_permissive_ledger(conn, store)
            conn.execute(  # type: ignore[attr-defined]
                _RAW_LEDGER_INSERT[store],
                ("010_a", "a" * 64, 0, "1.2.3", "OK"),
            )
            with pytest.raises(MigrationLedgerError):
                r.ledger_rows(conn, store)


def _create_permissive_ledger(conn: object, store: m.Store) -> None:
    if store is m.Store.SQLITE:
        conn.execute(  # type: ignore[attr-defined]
            "CREATE TABLE schema_version_sqlite (migration_id TEXT PRIMARY KEY, "
            "checksum TEXT NOT NULL, applied_at INTEGER NOT NULL, "
            "app_version TEXT NOT NULL, result TEXT NOT NULL)"
        )
    else:
        conn.execute(  # type: ignore[attr-defined]
            "CREATE TABLE schema_version_duckdb (migration_id TEXT PRIMARY KEY, "
            "checksum TEXT NOT NULL, applied_at BIGINT NOT NULL, "
            "app_version TEXT NOT NULL, result TEXT NOT NULL)"
        )


# --------------------------------------------------------------------------- #
# 5. baseline identity (D8/D10)
# --------------------------------------------------------------------------- #


class TestBaselineIdentity:
    def test_ok_row_uses_real_lowercase_sha256_not_a_sentinel(self, tmp_path: Path) -> None:
        body = "-- 000_baseline\nCREATE TABLE baseline_probe (id INTEGER);\n"
        digest = _write_sql(tmp_path, "sqlite/000_baseline.sql", body)
        manifest = m.parse_manifest(_doc(_entry()))
        entry = manifest.entries[0]
        row = r.ok_row_for(entry, tmp_path, FakeClock())
        assert row.migration_id == m.BASELINE_ID
        assert row.checksum == digest
        assert row.checksum == hashlib.sha256(body.encode()).hexdigest()
        assert row.checksum != "0" * 64
        assert row.checksum == row.checksum.lower() and len(row.checksum) == 64

    def test_applied_at_comes_from_the_injected_clock(self, tmp_path: Path) -> None:
        _write_sql(tmp_path, "sqlite/000_baseline.sql", "SELECT 1;\n")
        manifest = m.parse_manifest(_doc(_entry()))
        entry = manifest.entries[0]
        first = r.ok_row_for(entry, tmp_path, FakeClock(epoch_ms(1_700_000_000_000)))
        second = r.ok_row_for(entry, tmp_path, FakeClock(epoch_ms(1_750_000_000_000)))
        assert first.applied_at == 1_700_000_000_000
        assert second.applied_at == 1_750_000_000_000
        assert first.applied_at != second.applied_at

    def test_app_version_comes_from_package_metadata(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _write_sql(tmp_path, "sqlite/000_baseline.sql", "SELECT 1;\n")
        manifest = m.parse_manifest(_doc(_entry()))
        monkeypatch.setattr(metadata, "version", lambda _name: "9.9.9-test")
        row = r.ok_row_for(manifest.entries[0], tmp_path, FakeClock())
        assert row.app_version == "9.9.9-test"

    def test_missing_package_version_fails_with_a_packaging_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _write_sql(tmp_path, "sqlite/000_baseline.sql", "SELECT 1;\n")
        manifest = m.parse_manifest(_doc(_entry()))

        def _raise(_name: str) -> str:
            raise metadata.PackageNotFoundError("quantflow")

        monkeypatch.setattr(metadata, "version", _raise)
        with pytest.raises(MigrationLedgerError):
            r.ok_row_for(manifest.entries[0], tmp_path, FakeClock())

    def test_ok_row_result_is_ok_only_for_a_successful_write(
        self, store: m.Store, tmp_path: Path
    ) -> None:
        _write_sql(tmp_path, "sqlite/000_baseline.sql", "SELECT 1;\n")
        manifest = m.parse_manifest(_doc(_entry()))
        row = r.ok_row_for(manifest.entries[0], tmp_path, FakeClock())
        assert row.result is r.LedgerResult.OK
        with _connect(store, _db_path(tmp_path, store)) as conn:
            r.bootstrap_ledger(conn, store)
            r.write_row(conn, store, row)
            assert r.applied_ok_ids(conn, store) == frozenset({m.BASELINE_ID})


# --------------------------------------------------------------------------- #
# 6. baseline dependency closure (D11)
# --------------------------------------------------------------------------- #


class TestBaselineClosure:
    def _manifest_with_baseline_dependent(self) -> m.Manifest:
        return m.parse_manifest(
            _doc(
                _entry(migration_id="000_baseline"),
                _entry(migration_id="070_post", applies_after=(m.BASELINE_ID,)),
            )
        )

    def test_baseline_dependency_without_ok_row_fails(self) -> None:
        manifest = self._manifest_with_baseline_dependent()
        with pytest.raises(MigrationValidationError):
            r.check_baseline_closure(manifest, m.Store.SQLITE, frozenset())

    def test_baseline_dependency_with_ok_row_passes(self) -> None:
        manifest = self._manifest_with_baseline_dependent()
        r.check_baseline_closure(manifest, m.Store.SQLITE, frozenset({m.BASELINE_ID}))

    def test_unapplied_non_baseline_dependency_fails(self) -> None:
        manifest = m.parse_manifest(
            _doc(
                _entry(migration_id="010_a"),
                _entry(migration_id="070_post", applies_after=("010_a",)),
            )
        )
        with pytest.raises(MigrationValidationError):
            r.check_baseline_closure(manifest, m.Store.SQLITE, frozenset())

    def test_baseline_covered_is_never_an_ok_row(self) -> None:
        manifest = m.parse_manifest(
            _doc(
                _entry(migration_id="000_baseline"),
                _entry(migration_id="070_post", applies_after=("050_hist",)),
                baseline_covered={"sqlite": ["050_hist"]},
            )
        )
        # coverage satisfies closure only when the real baseline row exists
        with pytest.raises(MigrationValidationError):
            r.check_baseline_closure(manifest, m.Store.SQLITE, frozenset())
        r.check_baseline_closure(manifest, m.Store.SQLITE, frozenset({m.BASELINE_ID}))

    def test_disabled_entries_are_not_closure_checked(self) -> None:
        manifest = m.parse_manifest(
            _doc(_entry(migration_id="070_post", applies_after=(m.BASELINE_ID,), enabled=False))
        )
        r.check_baseline_closure(manifest, m.Store.SQLITE, frozenset())


# --------------------------------------------------------------------------- #
# 7. port contract / no wall-clock leakage
# --------------------------------------------------------------------------- #


class TestLedgerPortContract:
    def test_fake_clock_satisfies_the_clock_protocol(self) -> None:
        assert isinstance(FakeClock(), Clock)

    def test_runner_source_imports_no_wall_clock_module(self) -> None:
        source = Path(r.__file__).read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(r.__file__))
        banned = {"time", "datetime"}
        imported: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.append(node.module)
        assert not [name for name in imported if name.split(".")[0] in banned]
