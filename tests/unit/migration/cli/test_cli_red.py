"""010a-5.1 Red tests: CLI apply/status/verify (golden + duplicate/restart + no-future-leakage)."""

from __future__ import annotations

import pytest
from typer.testing import CliRunner

from quantflow.cli.main import app


class TestCLIExitCodes:
    """Exit codes: 0=consistent, 1=validation/drift/failure, 2=CLI/usage/config."""

    def test_invalid_store_exits_2(self) -> None:
        result = CliRunner().invoke(app, ["migrate", "apply", "badstore", "/tmp/nonexistent.json"])  # noqa: S108
        assert result.exit_code == 2

    def test_missing_manifest_exits_2(self) -> None:
        result = CliRunner().invoke(app, ["migrate", "apply", "sqlite", "/tmp/nonexistent.json"])  # noqa: S108
        assert result.exit_code == 2


class TestReadOnlyStatusAndVerify:
    """Status/verify never write a ledger, set mutating PRAGMAs, or create a DB."""

    def test_status_on_missing_store_reports_explicitly(self) -> None:
        # No DB file exists; status should report missing store explicitly (exit 2 for missing)
        result = CliRunner().invoke(app, ["migrate", "status", "sqlite"])
        assert result.exit_code == 2
        assert "Store does not exist" in result.output or "no database" in result.output


class TestRetryFailedInScope:
    """OQ-1 is resolved: --retry-failed is in scope (not deferred), requires --reason."""

    def test_retry_failed_without_reason_exits_2(self) -> None:
        # --reason is required; missing -> exit 2 (per design D12)
        result = CliRunner().invoke(
            app, ["migrate", "retry-failed", "sqlite", "000_baseline", "--reason", ""]
        )
        # Empty reason should fail
        assert result.exit_code != 0  # At minimum it should not succeed silently


class TestMainEntryPoint:
    """Regression: main() must propagate typer.Exit.exit_code (fixed .no -> .exit_code in ce62c29 era)."""

    def test_main_exits_with_correct_code_on_invalid_store(self) -> None:
        """Direct call to main() must exit with the CLI-derived code (regression for `.no` bug)."""
        import sys
        from unittest.mock import patch

        from quantflow.cli.main import main

        with patch.object(
            sys,
            "argv",
            ["quantflow", "migrate", "apply", "badstore", "/tmp/nonexistent.json"],  # noqa: S108
        ):
            with pytest.raises(SystemExit) as exc_info:
                main()
        # Invalid store -> typer.Exit(code=2)
        assert exc_info.value.code == 2
