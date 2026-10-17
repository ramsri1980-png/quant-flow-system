"""Shared fixtures/helpers for the 010a migration integration suite.

All DB artifacts are created under pytest's ``tmp_path`` only; nothing here
resolves under ``/data`` (design testing strategy, class 10).
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from pathlib import Path

import pytest

from quantflow.domain.time import epoch_ms
from quantflow.migrations import manifest as m
from quantflow.migrations import runner as r

FIXED_NOW = epoch_ms(1_760_000_000_000)


class FakeClock:
    def __init__(self, now: int = FIXED_NOW) -> None:
        self._now = now

    def now_ms(self) -> int:
        return self._now


def db_path(tmp_path: Path, store: m.Store) -> Path:
    return tmp_path / ("quant_state.db" if store is m.Store.SQLITE else "quant_flow.duckdb")


@contextmanager
def connect(store: m.Store, tmp_path: Path) -> Iterator[object]:
    """Open a standalone connection through the runner's own factories."""
    conn: object
    if store is m.Store.SQLITE:
        conn = r.open_standalone_sqlite(db_path(tmp_path, store))
    else:
        conn = r.open_standalone_duckdb(db_path(tmp_path, store), tmp_path / "duckdb_tmp")
    try:
        yield conn
    finally:
        conn.close()  # type: ignore[attr-defined]


def sql_file(root: Path, relpath: str, body: str) -> str:
    path = root / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(body.encode())
    return hashlib.sha256(body.encode()).hexdigest()


def build_manifest(
    root: Path,
    specs: Sequence[tuple[str, m.Store, str, tuple[str, ...]]],
) -> m.Manifest:
    """Write each ``{id, store, body, deps}`` spec to disk and parse the doc."""
    entries: list[dict[str, object]] = []
    for migration_id, store, body, deps in specs:
        rel = f"{store.value}/{migration_id}.sql"
        entries.append(
            {
                "id": migration_id,
                "store": store.value,
                "path": rel,
                "sha256": sql_file(root, rel, body),
                "applies_after": list(deps),
                "component": "core",
                "enabled": True,
            }
        )
    return m.parse_manifest({"version": 1, "migrations": entries})


@pytest.fixture(params=[m.Store.SQLITE, m.Store.DUCKDB], ids=["sqlite", "duckdb"])
def store(request: pytest.FixtureRequest) -> m.Store:
    return request.param
