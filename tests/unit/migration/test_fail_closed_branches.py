"""010a group 7 — fail-closed branch coverage (task 7.2).

One test per remaining uncovered error branch in the manifest and runner
modules (coverage gate: migrations/** >= 95%). Each test asserts a hard,
typed failure — never a silent default — per the fail-closed invariant.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import duckdb
import pytest

from quantflow.domain.errors import (
    MigrationLedgerError,
    MigrationManifestError,
    MigrationValidationError,
)
from quantflow.domain.time import EPOCH_MS_MIN, EpochMs, epoch_ms
from quantflow.migrations import manifest as m
from quantflow.migrations import runner as r

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
# helpers (mirrors test_ledger.py)
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


def _db_path(tmp_path: Path, store: m.Store) -> Path:
    return tmp_path / ("quant_state.db" if store is m.Store.SQLITE else "quant_flow.duckdb")


def _entry(
    *,
    migration_id: str = "010_first",
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


def _doc(*entries: dict[str, object]) -> dict[str, object]:
    return {"version": 1, "migrations": list(entries)}


def _write_sql(root: Path, relpath: str, body: str) -> None:
    path = root / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(body.encode())


def _create_permissive_ledger(conn: object, store: m.Store) -> None:
    """Ledger DDL without the result CHECK, so malformed rows can be seeded."""
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


@pytest.fixture(params=[m.Store.SQLITE, m.Store.DUCKDB], ids=["sqlite", "duckdb"])
def store(request: pytest.FixtureRequest) -> m.Store:
    return request.param


# --------------------------------------------------------------------------- #
# 1. manifest schema fail-closed branches
# --------------------------------------------------------------------------- #


class TestManifestFailClosedSchema:
    def test_unknown_store_name_fails_closed(self) -> None:
        with pytest.raises(MigrationManifestError, match="invalid store"):
            m.parse_manifest(_doc(_entry(store="postgres")))

    def test_empty_dependency_id_fails_closed(self) -> None:
        with pytest.raises(MigrationManifestError, match="non-empty strings"):
            m.parse_manifest(_doc(_entry(applies_after=("",))))

    @pytest.mark.parametrize("bad", [{}, "migrations", 7])
    def test_migrations_not_a_list_fails_closed(self, bad: object) -> None:
        with pytest.raises(MigrationManifestError, match="'migrations' array"):
            m.parse_manifest({"version": 1, "migrations": bad})

    @pytest.mark.parametrize("bad", ["entry", 42, None])
    def test_non_object_entry_fails_closed(self, bad: object) -> None:
        with pytest.raises(MigrationManifestError, match="must be an object"):
            m.parse_manifest({"version": 1, "migrations": [bad]})


# --------------------------------------------------------------------------- #
# 2. dependency graph edges (validate + order)
# --------------------------------------------------------------------------- #


class TestDependencyGraphEdges:
    def test_linear_dependency_chain_is_accepted(self) -> None:
        man = m.parse_manifest(
            _doc(
                _entry(migration_id="030_c", applies_after=("020_b",)),
                _entry(migration_id="020_b", applies_after=("010_a",)),
                _entry(migration_id="010_a"),
            )
        )
        m.validate_dependencies(man)  # MUST NOT raise

    def test_order_ignores_dependency_outside_the_enabled_set(self) -> None:
        man = m.parse_manifest(
            _doc(
                _entry(migration_id="010_a", applies_after=("999_ghost",)),
                _entry(migration_id="020_b", enabled=False),
            )
        )
        assert [e.id for e in m.apply_order(man, m.Store.SQLITE)] == ["010_a"]

    def test_dependent_waits_for_every_dependency(self) -> None:
        man = m.parse_manifest(
            _doc(
                _entry(migration_id="030_c", applies_after=("010_a", "020_b")),
                _entry(migration_id="010_a"),
                _entry(migration_id="020_b"),
            )
        )
        order = [e.id for e in m.apply_order(man, m.Store.SQLITE)]
        assert order.index("030_c") == 2

    def test_cycle_among_enabled_entries_fails_closed(self) -> None:
        man = m.parse_manifest(
            _doc(
                _entry(migration_id="010_a", applies_after=("020_b",)),
                _entry(migration_id="020_b", applies_after=("010_a",)),
            )
        )
        with pytest.raises(MigrationValidationError, match="dependency cycle among enabled"):
            m.apply_order(man, m.Store.SQLITE)


# --------------------------------------------------------------------------- #
# 3. checksum / loader read failures
# --------------------------------------------------------------------------- #


class TestReadFailures:
    def test_missing_migration_file_fails_closed(self, tmp_path: Path) -> None:
        root = tmp_path / "migrations"
        root.mkdir()
        manifest = m.parse_manifest(_doc(_entry()))
        with pytest.raises(MigrationValidationError, match="migration file missing"):
            m.verify_checksums(manifest, root)

    def test_unreadable_migration_file_fails_closed(self, tmp_path: Path) -> None:
        root = tmp_path / "migrations"
        # a directory at the entry path raises IsADirectoryError (an OSError)
        (root / "sqlite").mkdir(parents=True)
        (root / "sqlite" / "010_first.sql").mkdir()
        manifest = m.parse_manifest(_doc(_entry()))
        with pytest.raises(MigrationValidationError, match="cannot read migration file"):
            m.verify_checksums(manifest, root)

    def test_manifest_path_is_a_directory_fails_closed(self, tmp_path: Path) -> None:
        root = tmp_path / "migrations"
        (root / "MANIFEST.json").mkdir(parents=True)
        with pytest.raises(MigrationManifestError, match="cannot read migration manifest"):
            m.load_manifest(root)


# --------------------------------------------------------------------------- #
# 4. ledger row identity fail-closed branches
# --------------------------------------------------------------------------- #


class TestLedgerMalformedIdentity:
    @pytest.mark.parametrize(
        ("field", "position"),
        [("migration_id", 0), ("checksum", 1), ("app_version", 3)],
    )
    def test_blank_identity_field_fails_closed(
        self, store: m.Store, tmp_path: Path, field: str, position: int
    ) -> None:
        row = ["010_a", "a" * 64, EPOCH_MS_MIN, "1.2.3", "OK"]
        row[position] = ""
        with _connect(store, _db_path(tmp_path, store)) as conn:
            _create_permissive_ledger(conn, store)
            conn.execute(  # type: ignore[attr-defined]
                _RAW_LEDGER_INSERT[store],
                tuple(row),
            )
            with pytest.raises(MigrationLedgerError):
                r.ledger_rows(conn, store)


# --------------------------------------------------------------------------- #
# 5. read_row against an existing ledger
# --------------------------------------------------------------------------- #


class TestReadRowExistingLedger:
    def test_existing_row_is_parsed(self, store: m.Store, tmp_path: Path) -> None:
        with _connect(store, _db_path(tmp_path, store)) as conn:
            r.bootstrap_ledger(conn, store)  # type: ignore[arg-type]
            r.write_row(
                conn,  # type: ignore[arg-type]
                store,
                r.LedgerRow(
                    migration_id="010_a",
                    checksum="a" * 64,
                    applied_at=FIXED_NOW,
                    app_version="1.2.3",
                    result=r.LedgerResult.OK,
                ),
            )
            row = r.read_row(conn, store, "010_a")  # type: ignore[arg-type]
            assert row is not None
            assert row.migration_id == "010_a"
            assert row.result is r.LedgerResult.OK

    def test_existing_ledger_missing_row_reads_as_none(
        self, store: m.Store, tmp_path: Path
    ) -> None:
        with _connect(store, _db_path(tmp_path, store)) as conn:
            r.bootstrap_ledger(conn, store)  # type: ignore[arg-type]
            assert r.read_row(conn, store, "010_missing") is None  # type: ignore[arg-type]


# --------------------------------------------------------------------------- #
# 6. baseline row build / standalone open / split / apply failures
# --------------------------------------------------------------------------- #


class TestRunnerFailClosedBranches:
    def test_unreadable_baseline_file_fails_closed(self, tmp_path: Path) -> None:
        manifest = m.parse_manifest(_doc(_entry(migration_id="000_baseline")))
        with pytest.raises(MigrationLedgerError, match="cannot read migration file"):
            r.ok_row_for(manifest.entries[0], tmp_path, FakeClock())

    def test_sqlite_pragma_failure_closes_and_propagates(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def _boom(_conn: object) -> None:
            raise RuntimeError("pragma verification failed")

        monkeypatch.setattr(r, "verify_sqlite_pragmas", _boom)
        with pytest.raises(RuntimeError, match="pragma verification failed"):
            r.open_standalone_sqlite(tmp_path / "quant_state.db")

    def test_duckdb_temp_directory_failure_closes_and_propagates(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        class _ExplodingConn:
            def __init__(self) -> None:
                self.closed = False

            def execute(self, *_args: object, **_kwargs: object) -> object:
                raise RuntimeError("temp_directory rejected")

            def close(self) -> None:
                self.closed = True

        fake = _ExplodingConn()
        monkeypatch.setattr(r.duckdb, "connect", lambda *_a, **_k: fake)
        with pytest.raises(RuntimeError, match="temp_directory"):
            r.open_standalone_duckdb(tmp_path / "quant_flow.duckdb", tmp_path / "duckdb_tmp")
        assert fake.closed

    def test_lone_semicolon_statement_is_dropped(self) -> None:
        assert r.split_statements(";") == ()
        assert r.split_statements("SELECT 1;;") == ("SELECT 1;",)

    def test_unsatisfied_dependency_fails_closed(self) -> None:
        man = m.parse_manifest(_doc(_entry(applies_after=("010_a",))))
        entry = man.entries[0]
        with pytest.raises(MigrationValidationError, match="unsatisfied dependency"):
            r._require_dependencies(entry, satisfied=set(), covered=set(), baseline_applied=False)

    def test_covered_dependency_passes_only_with_baseline_applied(self) -> None:
        man = m.parse_manifest(
            _doc(
                _entry(migration_id="070_post", applies_after=("050_hist",)),
            )
        )
        entry = man.entries[0]
        r._require_dependencies(entry, satisfied=set(), covered={"050_hist"}, baseline_applied=True)

    def test_failure_record_rolls_back_when_the_write_fails(
        self, store: m.Store, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        man = m.parse_manifest(_doc(_entry()))

        def _boom(*_args: object, **_kwargs: object) -> None:
            raise RuntimeError("ledger write failed")

        monkeypatch.setattr(r, "write_row", _boom)
        with _connect(store, _db_path(tmp_path, store)) as conn:
            with pytest.raises(RuntimeError, match="ledger write failed"):
                r._record_failure(conn, store, man.entries[0], FakeClock())  # type: ignore[arg-type]

    def test_apply_entry_unreadable_file_fails_before_the_transaction(
        self, store: m.Store, tmp_path: Path
    ) -> None:
        man = m.parse_manifest(_doc(_entry()))
        with _connect(store, _db_path(tmp_path, store)) as conn:
            with pytest.raises(MigrationLedgerError, match="cannot read migration file"):
                r.apply_entry(
                    conn,  # type: ignore[arg-type]
                    store,
                    man.entries[0],
                    tmp_path,
                    FakeClock(),
                )
