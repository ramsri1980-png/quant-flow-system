"""010a group 4 — atomic runner (tasks 4.1-4.6).

Derived from `specs/migration-runner/spec.md` scenarios (Atomic apply and
rollback, Independent per-store results, Standalone connection PRAGMAs,
Embedded reuse and DuckDB temp_directory, Forward-only) and design D9/D13/D14.

Imports the runner module object (not names) so each sub-task's subset can go
green incrementally while later sub-tasks stay red.
"""

from __future__ import annotations

import ast
import hashlib
import inspect
import sqlite3
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from pathlib import Path

import pytest

from quantflow.domain.errors import MigrationLedgerError, MigrationValidationError
from quantflow.domain.time import epoch_ms
from quantflow.migrations import manifest as m
from quantflow.migrations import runner as r
from quantflow.ports.clock import Clock

FIXED_NOW = epoch_ms(1_760_000_000_000)
ALPHA = "010_alpha"
BASELINE = m.BASELINE_ID
POST = "070_post"


class FakeClock:
    def __init__(self, now: int = FIXED_NOW) -> None:
        self._now = now

    def now_ms(self) -> int:
        return self._now


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #


@contextmanager
def _connect(store: m.Store, tmp_path: Path) -> Iterator[object]:
    """Open a standalone connection through the runner's own factories."""
    conn: object
    if store is m.Store.SQLITE:
        conn = r.open_standalone_sqlite(_db_path(tmp_path, store))
    else:
        conn = r.open_standalone_duckdb(_db_path(tmp_path, store), tmp_path / "duckdb_tmp")
    try:
        yield conn
    finally:
        conn.close()  # type: ignore[attr-defined]


def _db_path(tmp_path: Path, store: m.Store) -> Path:
    return tmp_path / ("quant_state.db" if store is m.Store.SQLITE else "quant_flow.duckdb")


def _sql_file(root: Path, relpath: str, body: str) -> str:
    path = root / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(body.encode())
    return hashlib.sha256(body.encode()).hexdigest()


def _manifest(
    root: Path,
    specs: Sequence[tuple[str, m.Store, str, tuple[str, ...], bool]],
    baseline_covered: object = None,
) -> m.Manifest:
    entries: list[dict[str, object]] = []
    for migration_id, store, body, deps, enabled in specs:
        rel = f"{store.value}/{migration_id}.sql"
        entries.append(
            {
                "id": migration_id,
                "store": store.value,
                "path": rel,
                "sha256": _sql_file(root, rel, body),
                "applies_after": list(deps),
                "component": "core",
                "enabled": enabled,
            }
        )
    doc: dict[str, object] = {"version": 1, "migrations": entries}
    if baseline_covered is not None:
        doc["baseline_covered"] = baseline_covered
    return m.parse_manifest(doc)


def _ledger(conn: object, store: m.Store) -> tuple[r.LedgerRow, ...]:
    return r.ledger_rows(conn, store)  # type: ignore[arg-type]


def _tables(conn: object, store: m.Store) -> frozenset[str]:
    return r.application_tables(conn, store)  # type: ignore[arg-type]


@pytest.fixture(params=[m.Store.SQLITE, m.Store.DUCKDB], ids=["sqlite", "duckdb"])
def store(request: pytest.FixtureRequest) -> m.Store:
    return request.param


# --------------------------------------------------------------------------- #
# 1. statement splitting (boundary/units + trigger handling)
# --------------------------------------------------------------------------- #


class TestStatementSplitting:
    def test_splits_two_simple_statements(self) -> None:
        assert r.split_statements("CREATE TABLE a (x INT); CREATE TABLE b (y INT);") == (
            "CREATE TABLE a (x INT);",
            "CREATE TABLE b (y INT);",
        )

    def test_ignores_semicolon_inside_single_quoted_string(self) -> None:
        assert r.split_statements("INSERT INTO t VALUES ('a;b');") == (
            "INSERT INTO t VALUES ('a;b');",
        )

    def test_handles_escaped_quote_inside_string(self) -> None:
        assert r.split_statements("INSERT INTO t VALUES ('it''s; ok');") == (
            "INSERT INTO t VALUES ('it''s; ok');",
        )

    def test_keeps_semicolons_inside_a_trigger_body(self) -> None:
        sql = (
            "CREATE TRIGGER tr AFTER INSERT ON t BEGIN "
            "INSERT INTO t VALUES ('x;y'); UPDATE t SET a = 1; END;"
        )
        assert r.split_statements(sql) == (sql,)

    def test_ignores_semicolon_inside_line_comment(self) -> None:
        sql = "-- comment; here\nCREATE TABLE t (a INT);"
        assert r.split_statements(sql) == (sql,)

    def test_ignores_semicolon_inside_block_comment(self) -> None:
        sql = "/* a; b */ CREATE TABLE t (a INT);"
        assert r.split_statements(sql) == (sql,)

    def test_trailing_statement_without_semicolon_is_kept(self) -> None:
        assert r.split_statements("CREATE TABLE t (a INT)") == ("CREATE TABLE t (a INT)",)

    def test_whitespace_only_yields_no_statements(self) -> None:
        assert r.split_statements("\n  \n") == ()


# --------------------------------------------------------------------------- #
# 2. fresh + upgrade apply (golden order, atomic OK rows)
# --------------------------------------------------------------------------- #


class TestApplyFreshAndUpgrade:
    def test_fresh_apply_creates_schema_and_ok_rows_in_order(
        self, store: m.Store, tmp_path: Path
    ) -> None:
        body_base = "CREATE TABLE base_probe (id INTEGER);"
        body_post = "CREATE TABLE post_probe (id INTEGER);"
        manifest = _manifest(
            tmp_path,
            [
                (BASELINE, store, body_base, (), True),
                (POST, store, body_post, (BASELINE,), True),
            ],
        )
        with _connect(store, tmp_path) as conn:
            result = r.apply_store(conn, store, manifest, tmp_path, FakeClock())  # type: ignore[arg-type]
            assert result.applied == (BASELINE, POST)
            assert result.skipped == ()
            rows = _ledger(conn, store)
        assert [row.migration_id for row in rows] == [BASELINE, POST]
        assert all(row.result is r.LedgerResult.OK for row in rows)

    def test_upgrade_applies_only_the_new_migration(self, store: m.Store, tmp_path: Path) -> None:
        first = _manifest(
            tmp_path,
            [(BASELINE, store, "CREATE TABLE base_probe (id INTEGER);", (), True)],
        )
        with _connect(store, tmp_path) as conn:
            r.apply_store(conn, store, first, tmp_path, FakeClock())  # type: ignore[arg-type]
        second = _manifest(
            tmp_path,
            [
                (BASELINE, store, "CREATE TABLE base_probe (id INTEGER);", (), True),
                (POST, store, "CREATE TABLE post_probe (id INTEGER);", (BASELINE,), True),
            ],
        )
        with _connect(store, tmp_path) as conn:
            result = r.apply_store(conn, store, second, tmp_path, FakeClock())  # type: ignore[arg-type]
            assert result.applied == (POST,)
            assert result.skipped == (BASELINE,)
            assert "post_probe" in _tables(conn, store)


# --------------------------------------------------------------------------- #
# 3. replay / idempotency / restart
# --------------------------------------------------------------------------- #


class TestReplayAndRestart:
    def test_reapply_of_a_closed_manifest_is_a_noop(self, store: m.Store, tmp_path: Path) -> None:
        manifest = _manifest(
            tmp_path, [(BASELINE, store, "CREATE TABLE base_probe (id INTEGER);", (), True)]
        )
        with _connect(store, tmp_path) as conn:
            r.apply_store(conn, store, manifest, tmp_path, FakeClock())  # type: ignore[arg-type]
        with _connect(store, tmp_path) as conn:
            result = r.apply_store(conn, store, manifest, tmp_path, FakeClock())  # type: ignore[arg-type]
            assert result.applied == ()
            assert result.skipped == (BASELINE,)
            assert len(_ledger(conn, store)) == 1

    def test_replay_does_not_rewrite_ok_rows(self, store: m.Store, tmp_path: Path) -> None:
        manifest = _manifest(
            tmp_path, [(BASELINE, store, "CREATE TABLE base_probe (id INTEGER);", (), True)]
        )
        with _connect(store, tmp_path) as conn:
            r.apply_store(conn, store, manifest, tmp_path, FakeClock(FIXED_NOW))  # type: ignore[arg-type]
            first = _ledger(conn, store)[0]
        with _connect(store, tmp_path) as conn:
            r.apply_store(conn, store, manifest, tmp_path, FakeClock(FIXED_NOW + 60_000))  # type: ignore[arg-type]
            second = _ledger(conn, store)[0]
        assert first.applied_at == second.applied_at == FIXED_NOW

    def test_restart_mid_suite_resumes_remaining(self, store: m.Store, tmp_path: Path) -> None:
        partial = _manifest(
            tmp_path, [(BASELINE, store, "CREATE TABLE base_probe (id INTEGER);", (), True)]
        )
        full = _manifest(
            tmp_path,
            [
                (BASELINE, store, "CREATE TABLE base_probe (id INTEGER);", (), True),
                (POST, store, "CREATE TABLE post_probe (id INTEGER);", (BASELINE,), True),
            ],
        )
        with _connect(store, tmp_path) as conn:
            r.apply_store(conn, store, partial, tmp_path, FakeClock())  # type: ignore[arg-type]
        with _connect(store, tmp_path) as conn:  # restart: new connection, same file
            result = r.apply_store(conn, store, full, tmp_path, FakeClock(FIXED_NOW + 60_000))  # type: ignore[arg-type]
            assert result.applied == (POST,)


# --------------------------------------------------------------------------- #
# 4. atomic failure / rollback / FAILED handling
# --------------------------------------------------------------------------- #


class TestApplyFailure:
    def _failing_manifest(self, store: m.Store, tmp_path: Path) -> m.Manifest:
        body = (
            "CREATE TABLE partial_probe (id INTEGER);\nCREATE TABLE partial_probe (id INTEGER);\n"
        )
        return _manifest(tmp_path, [(BASELINE, store, body, (), True)])

    def test_failure_leaves_no_partial_ddl_and_exactly_one_failed_row(
        self, store: m.Store, tmp_path: Path
    ) -> None:
        manifest = self._failing_manifest(store, tmp_path)
        with _connect(store, tmp_path) as conn:
            with pytest.raises(MigrationLedgerError):
                r.apply_store(conn, store, manifest, tmp_path, FakeClock())  # type: ignore[arg-type]
            rows = _ledger(conn, store)
            assert [row.migration_id for row in rows] == [BASELINE]
            assert rows[0].result is r.LedgerResult.FAILED
            assert "partial_probe" not in _tables(conn, store)

    def test_failed_row_blocks_subsequent_apply(self, store: m.Store, tmp_path: Path) -> None:
        manifest = self._failing_manifest(store, tmp_path)
        with _connect(store, tmp_path) as conn:
            with pytest.raises(MigrationLedgerError):
                r.apply_store(conn, store, manifest, tmp_path, FakeClock())  # type: ignore[arg-type]
            with pytest.raises(MigrationLedgerError):
                r.apply_store(conn, store, manifest, tmp_path, FakeClock())  # type: ignore[arg-type]
            assert len(_ledger(conn, store)) == 1

    def test_repeated_failure_keeps_one_row(self, store: m.Store, tmp_path: Path) -> None:
        manifest = self._failing_manifest(store, tmp_path)
        entry = manifest.entries[0]
        with _connect(store, tmp_path) as conn:
            r.bootstrap_ledger(conn, store)  # type: ignore[arg-type]
            with pytest.raises(MigrationLedgerError):
                r.apply_entry(conn, store, entry, tmp_path, FakeClock())  # type: ignore[arg-type]
            with pytest.raises(MigrationLedgerError):
                r.apply_entry(conn, store, entry, tmp_path, FakeClock(FIXED_NOW + 60_000))  # type: ignore[arg-type]
            rows = _ledger(conn, store)
        assert len(rows) == 1
        assert rows[0].result is r.LedgerResult.FAILED
        assert rows[0].applied_at == FIXED_NOW + 60_000

    def test_success_writes_ok_and_no_failed(self, store: m.Store, tmp_path: Path) -> None:
        manifest = _manifest(
            tmp_path, [(BASELINE, store, "CREATE TABLE base_probe (id INTEGER);", (), True)]
        )
        entry = manifest.entries[0]
        with _connect(store, tmp_path) as conn:
            r.bootstrap_ledger(conn, store)  # type: ignore[arg-type]
            r.apply_entry(conn, store, entry, tmp_path, FakeClock())  # type: ignore[arg-type]
            rows = _ledger(conn, store)
        assert len(rows) == 1
        assert rows[0].result is r.LedgerResult.OK

    def test_semicolon_in_quoted_body_is_not_mis_split(
        self, store: m.Store, tmp_path: Path
    ) -> None:
        body = "CREATE TABLE quoted_probe (v TEXT);\nINSERT INTO quoted_probe VALUES ('a;b');\n"
        manifest = _manifest(tmp_path, [(BASELINE, store, body, (), True)])
        with _connect(store, tmp_path) as conn:
            r.apply_store(conn, store, manifest, tmp_path, FakeClock())  # type: ignore[arg-type]
            count = conn.execute("SELECT COUNT(*) FROM quoted_probe").fetchone()[0]  # type: ignore[attr-defined]
        assert count == 1

    def test_trigger_with_embedded_semicolons_is_executed(self, tmp_path: Path) -> None:
        store = m.Store.SQLITE
        body = (
            "CREATE TABLE ttrig (a INTEGER);\n"
            "CREATE TRIGGER tr_ins AFTER INSERT ON ttrig BEGIN "
            "UPDATE ttrig SET a = a + 1; UPDATE ttrig SET a = a + 1; END;\n"
            "INSERT INTO ttrig VALUES (1);\n"
        )
        manifest = _manifest(tmp_path, [(BASELINE, store, body, (), True)])
        with _connect(store, tmp_path) as conn:
            r.apply_store(conn, store, manifest, tmp_path, FakeClock())  # type: ignore[arg-type]
            triggers = conn.execute(  # type: ignore[attr-defined]
                "SELECT name FROM sqlite_master WHERE type = 'trigger'"
            ).fetchall()
            value = conn.execute("SELECT a FROM ttrig").fetchone()[0]  # type: ignore[attr-defined]
        assert [row[0] for row in triggers] == ["tr_ins"]
        assert value == 3


# --------------------------------------------------------------------------- #
# 5. legacy store aborts before applying anything
# --------------------------------------------------------------------------- #


class TestLegacyStoreAbort:
    def test_legacy_store_is_not_overwritten(self, store: m.Store, tmp_path: Path) -> None:
        manifest = _manifest(
            tmp_path, [(BASELINE, store, "CREATE TABLE base_probe (id INTEGER);", (), True)]
        )
        with _connect(store, tmp_path) as conn:
            if store is m.Store.SQLITE:
                conn.execute("CREATE TABLE legacy_probe (id TEXT PRIMARY KEY)")  # type: ignore[attr-defined]
            else:
                conn.execute("CREATE TABLE legacy_probe (id VARCHAR PRIMARY KEY)")  # type: ignore[attr-defined]
            with pytest.raises(MigrationValidationError):
                r.apply_store(conn, store, manifest, tmp_path, FakeClock())  # type: ignore[arg-type]
            # the legacy table is intact; nothing was baselined, written, or applied
            assert "legacy_probe" in _tables(conn, store)
            assert not r.ledger_exists(conn, store)  # type: ignore[arg-type]


# --------------------------------------------------------------------------- #
# 6. per-store independence (dual-run partial failure)
# --------------------------------------------------------------------------- #


class TestPerStoreIndependence:
    def test_duckdb_failure_keeps_committed_sqlite(self, tmp_path: Path) -> None:
        good = _manifest(
            tmp_path,
            [(BASELINE, m.Store.SQLITE, "CREATE TABLE base_probe (id INTEGER);", (), True)],
        )
        bad = _manifest(
            tmp_path,
            [
                (
                    BASELINE,
                    m.Store.DUCKDB,
                    "CREATE TABLE dprobe (id INTEGER);\nCREATE TABLE dprobe (id INTEGER);\n",
                    (),
                    True,
                )
            ],
        )
        with _connect(m.Store.SQLITE, tmp_path) as sconn:
            r.apply_store(sconn, m.Store.SQLITE, good, tmp_path, FakeClock())  # type: ignore[arg-type]
        with _connect(m.Store.DUCKDB, tmp_path) as dconn:
            with pytest.raises(MigrationLedgerError):
                r.apply_store(dconn, m.Store.DUCKDB, bad, tmp_path, FakeClock())  # type: ignore[arg-type]
        with _connect(m.Store.SQLITE, tmp_path) as sconn:
            assert r.applied_ok_ids(sconn, m.Store.SQLITE) == frozenset({BASELINE})  # type: ignore[arg-type]
        with _connect(m.Store.DUCKDB, tmp_path) as dconn:
            assert r.applied_ok_ids(dconn, m.Store.DUCKDB) == frozenset()  # type: ignore[arg-type]


# --------------------------------------------------------------------------- #
# 7. connection policy (PRAGMAs, embedded reuse, temp_directory)
# --------------------------------------------------------------------------- #


class TestConnectionPolicy:
    def test_configure_sets_required_sqlite_pragmas(self, tmp_path: Path) -> None:
        conn = sqlite3.connect(tmp_path / "p.db", isolation_level=None)
        try:
            r.configure_sqlite_pragmas(conn)
            r.verify_sqlite_pragmas(conn)
        finally:
            conn.close()

    def test_verify_refuses_incompatible_pragmas(self, tmp_path: Path) -> None:
        conn = sqlite3.connect(tmp_path / "p.db", isolation_level=None)
        try:
            r.configure_sqlite_pragmas(conn)
            conn.execute("PRAGMA foreign_keys=OFF")
            with pytest.raises(MigrationValidationError):
                r.verify_sqlite_pragmas(conn)
        finally:
            conn.close()

    def test_open_standalone_sqlite_sets_pragmas_and_manual_transactions(
        self, tmp_path: Path
    ) -> None:
        conn = r.open_standalone_sqlite(tmp_path / "s.db")
        try:
            assert conn.isolation_level is None
            r.verify_sqlite_pragmas(conn)
        finally:
            conn.close()

    def test_required_pragma_values_match_arch_v2_c1(self) -> None:
        assert dict(r.SQLITE_PRAGMAS) == {
            "journal_mode": "wal",
            "synchronous": 1,
            "foreign_keys": 1,
            "busy_timeout": 5000,
        }

    def test_duckdb_temp_directory_is_set_and_under_tmp(self, tmp_path: Path) -> None:
        temp_dir = tmp_path / "duckdb_tmp"
        conn = r.open_standalone_duckdb(tmp_path / "d.duckdb", temp_dir)
        try:
            current = conn.execute("SELECT current_setting('temp_directory')").fetchone()[0]
            assert str(temp_dir) in str(current)
            assert str(current).startswith(str(tmp_path))
            assert "/data" not in str(current)
        finally:
            conn.close()

    def test_duckdb_refuses_a_data_path(self, tmp_path: Path) -> None:
        with pytest.raises(MigrationValidationError):
            r.open_standalone_duckdb(tmp_path / "d.duckdb", Path("/data/duckdb_tmp"))

    def test_embedded_reuse_is_verified_without_reconfiguring(self, tmp_path: Path) -> None:
        # A raw connection lacking the required PRAGMAs must be refused, proving
        # the embedded path checks rather than mutates.
        conn = sqlite3.connect(tmp_path / "e.db", isolation_level=None)
        try:
            conn.execute("PRAGMA foreign_keys=OFF")
            with pytest.raises(MigrationValidationError):
                r.verify_sqlite_pragmas(conn)
        finally:
            conn.close()


# --------------------------------------------------------------------------- #
# 8. temp-paths-only
# --------------------------------------------------------------------------- #


class TestTempPathsOnly:
    def test_all_db_artifacts_live_under_tmp_path(self, store: m.Store, tmp_path: Path) -> None:
        manifest = _manifest(
            tmp_path, [(BASELINE, store, "CREATE TABLE base_probe (id INTEGER);", (), True)]
        )
        with _connect(store, tmp_path) as conn:
            r.apply_store(conn, store, manifest, tmp_path, FakeClock())  # type: ignore[arg-type]
        for path in tmp_path.rglob("*"):
            assert str(path).startswith(str(tmp_path))

    def test_duckdb_temp_directory_has_no_implicit_default(self) -> None:
        # An explicit scratch path is mandatory, so there is no /data default.
        parameter = inspect.signature(r.open_standalone_duckdb).parameters["temp_directory"]
        assert parameter.default is inspect.Parameter.empty


# --------------------------------------------------------------------------- #
# 9. port contract
# --------------------------------------------------------------------------- #


class TestRunnerPortContract:
    def test_fake_clock_satisfies_the_clock_protocol(self) -> None:
        assert isinstance(FakeClock(), Clock)

    def test_runner_imports_no_wall_clock_module(self) -> None:
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
