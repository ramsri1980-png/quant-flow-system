"""Task 6.2 — integration-suite wiring guards for ``tests/migration/``.

Two suite-level invariants (design testing strategy):

- the fresh-vs-upgrade apply matrix completes in well under 10 s;
- no artifact the suite produces ever resolves under ``/data``.
"""

from __future__ import annotations

import time
from pathlib import Path

from quantflow.migrations import manifest as m

from .test_schema_equivalence import apply_fresh, apply_upgrade

_SUITE_BUDGET_MS = 10_000


class TestIntegrationTiming:
    def test_equivalence_matrix_completes_within_budget(self, tmp_path: Path) -> None:
        started = time.monotonic()
        for index, store in enumerate((m.Store.SQLITE, m.Store.DUCKDB)):
            apply_fresh(store, tmp_path / f"fresh{index}")
            apply_upgrade(store, tmp_path / f"upgrade{index}")
        elapsed_ms = (time.monotonic() - started) * 1000
        assert elapsed_ms < _SUITE_BUDGET_MS, f"migration matrix took {elapsed_ms:.0f} ms (> 10 s)"


class TestSuitePathGuards:
    def test_no_suite_artifact_resolves_under_data(self, tmp_path: Path) -> None:
        for index, store in enumerate((m.Store.SQLITE, m.Store.DUCKDB)):
            apply_fresh(store, tmp_path / f"fresh{index}")
        artifacts = [path for path in tmp_path.rglob("*") if path.is_file()]
        assert artifacts  # the suite really created DB files
        for path in artifacts:
            resolved = str(path.resolve())
            assert resolved.startswith(str(tmp_path.resolve()))
            assert not resolved.startswith("/data")

    def test_duckdb_temp_directory_is_the_suite_scratch_dir(self, tmp_path: Path) -> None:
        apply_fresh(m.Store.DUCKDB, tmp_path)
        temp_dir = tmp_path / "duckdb_tmp"
        assert temp_dir.is_dir()
        assert not str(temp_dir.resolve()).startswith("/data")
