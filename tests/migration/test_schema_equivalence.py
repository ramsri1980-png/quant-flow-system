"""Task 6.1 — fresh vs upgrade schema equivalence (design testing class 6).

A closed synthetic manifest subset (baseline + one post-baseline migration) is
applied two ways:

- **fresh**: every migration applied to a brand-new store;
- **upgrade**: only the subset applied first, then the full manifest upgrades
  the store with the remaining migration(s).

The two stores must end with canonically identical application schemas —
compared via canonical ``sqlite_master`` rows (SQLite) and
``information_schema`` table/column introspection (DuckDB), never via
byte-identical DB files.
"""

from __future__ import annotations

from pathlib import Path

from quantflow.migrations import manifest as m
from quantflow.migrations import runner as r

from .conftest import FakeClock, build_manifest, connect, db_path

BASELINE = m.BASELINE_ID
ALPHA = "010_alpha"
BETA = "020_beta"

# --------------------------------------------------------------------------- #
# closed synthetic manifest subset (per-store SQL, varied DDL)
# --------------------------------------------------------------------------- #

_SQLITE_BODY = {
    BASELINE: (
        "CREATE TABLE instruments (id INTEGER PRIMARY KEY, symbol TEXT NOT NULL UNIQUE);"
        "\nCREATE TABLE audit_log (note TEXT);"
    ),
    ALPHA: (
        "CREATE TABLE quotes ("
        "id INTEGER PRIMARY KEY, instrument_id INTEGER NOT NULL REFERENCES instruments(id),"
        " cents INTEGER NOT NULL);"
        "\nCREATE INDEX idx_quotes_instrument ON quotes(instrument_id);"
        "\nCREATE VIEW quote_symbols AS"
        " SELECT q.id, i.symbol, q.cents FROM quotes q JOIN instruments i ON i.id = q.instrument_id;"
    ),
    BETA: (
        "ALTER TABLE quotes ADD COLUMN micros INTEGER NOT NULL DEFAULT 0;"
        "\nCREATE TRIGGER trg_quotes_audit AFTER INSERT ON quotes BEGIN"
        " INSERT INTO audit_log (note) VALUES ('quote;with;semicolons'); END;"
    ),
}

_DUCKDB_BODY = {
    BASELINE: (
        "CREATE TABLE instruments (id BIGINT, symbol VARCHAR NOT NULL, PRIMARY KEY (id));"
        "\nCREATE TABLE audit_log (note VARCHAR);"
    ),
    ALPHA: (
        "CREATE TABLE quotes (id BIGINT, instrument_id BIGINT NOT NULL, cents BIGINT NOT NULL,"
        " PRIMARY KEY (id));"
        "\nCREATE INDEX idx_quotes_instrument ON quotes(instrument_id);"
        "\nCREATE VIEW quote_symbols AS"
        " SELECT q.id, i.symbol, q.cents FROM quotes q JOIN instruments i ON i.id = q.instrument_id;"
    ),
    BETA: "ALTER TABLE quotes ADD COLUMN micros BIGINT DEFAULT 0;",
}


def _specs(store: m.Store, ids: tuple[str, ...]) -> list[tuple[str, m.Store, str, tuple[str, ...]]]:
    body = _SQLITE_BODY if store is m.Store.SQLITE else _DUCKDB_BODY
    deps = {BASELINE: (), ALPHA: (BASELINE,), BETA: (ALPHA,)}
    return [(mid, store, body[mid], deps[mid]) for mid in ids]


# --------------------------------------------------------------------------- #
# canonical schema introspection
# --------------------------------------------------------------------------- #


def _canonical_sqlite_schema(conn: object) -> tuple[tuple[str, str, str], ...]:
    assert conn is not None
    raw = conn.execute(  # type: ignore[attr-defined]
        "SELECT type, name, sql FROM sqlite_master"
        " WHERE name NOT LIKE 'sqlite_%' AND name != ?"
        " ORDER BY type, name",
        (r.ledger_table(m.Store.SQLITE),),
    ).fetchall()
    return tuple((row_type, name, " ".join((sql or "").split())) for row_type, name, sql in raw)


def _canonical_duckdb_schema(conn: object) -> tuple[tuple[str, str, str, str, str, int], ...]:
    assert conn is not None
    raw = conn.execute(  # type: ignore[attr-defined]
        "SELECT t.table_name, t.table_type, c.column_name, c.data_type,"
        " c.is_nullable, c.ordinal_position"
        " FROM information_schema.tables t"
        " JOIN information_schema.columns c ON t.table_name = c.table_name"
        " WHERE t.table_schema = 'main' AND t.table_name != ?"
        " ORDER BY t.table_name, c.ordinal_position",
        (r.ledger_table(m.Store.DUCKDB),),
    ).fetchall()
    return tuple(tuple(row) for row in raw)  # type: ignore[misc]


def canonical_schema(conn: object, store: m.Store) -> tuple[object, ...]:
    return (
        _canonical_sqlite_schema(conn)
        if store is m.Store.SQLITE
        else _canonical_duckdb_schema(conn)
    )


# --------------------------------------------------------------------------- #
# fresh vs upgrade paths
# --------------------------------------------------------------------------- #


def apply_fresh(store: m.Store, tmp_path: Path) -> None:
    manifest = build_manifest(tmp_path, _specs(store, (BASELINE, ALPHA, BETA)))
    with connect(store, tmp_path) as conn:
        r.apply_store(conn, store, manifest, tmp_path, FakeClock())  # type: ignore[arg-type]


def apply_upgrade(store: m.Store, tmp_path: Path) -> None:
    subset = build_manifest(tmp_path, _specs(store, (BASELINE, ALPHA)))
    with connect(store, tmp_path) as conn:
        r.apply_store(conn, store, subset, tmp_path, FakeClock())  # type: ignore[arg-type]
    full = build_manifest(tmp_path, _specs(store, (BASELINE, ALPHA, BETA)))
    with connect(store, tmp_path) as conn:
        result = r.apply_store(conn, store, full, tmp_path, FakeClock())  # type: ignore[arg-type]
        assert result.applied == (BETA,)
        assert result.skipped == (BASELINE, ALPHA)


class TestFreshUpgradeSchemaEquivalence:
    def test_sqlite_fresh_and_upgrade_schemas_are_canonically_equal(self, tmp_path: Path) -> None:
        store = m.Store.SQLITE
        fresh = tmp_path / "fresh"
        upgrade = tmp_path / "upgrade"
        apply_fresh(store, fresh)
        apply_upgrade(store, upgrade)
        with connect(store, fresh) as conn:
            fresh_schema = canonical_schema(conn, store)
        with connect(store, upgrade) as conn:
            upgrade_schema = canonical_schema(conn, store)
        # The comparison is structural, not byte-identical files.
        assert fresh_schema != ()
        assert fresh_schema == upgrade_schema
        names = {name for _, name, _ in fresh_schema}
        assert {"instruments", "quotes", "audit_log", "quote_symbols", "trg_quotes_audit"} <= names
        assert db_path(fresh, store).read_bytes() != db_path(upgrade, store).read_bytes()

    def test_duckdb_fresh_and_upgrade_schemas_are_canonically_equal(self, tmp_path: Path) -> None:
        store = m.Store.DUCKDB
        fresh = tmp_path / "fresh"
        upgrade = tmp_path / "upgrade"
        apply_fresh(store, fresh)
        apply_upgrade(store, upgrade)
        with connect(store, fresh) as conn:
            fresh_schema = canonical_schema(conn, store)
        with connect(store, upgrade) as conn:
            upgrade_schema = canonical_schema(conn, store)
        assert fresh_schema != ()
        assert fresh_schema == upgrade_schema
        tables = {row[0] for row in fresh_schema}  # type: ignore[index]
        assert {"instruments", "quotes", "audit_log", "quote_symbols"} <= tables
        columns = {(row[0], row[2]) for row in fresh_schema}  # type: ignore[index]
        assert ("quotes", "micros") in columns
