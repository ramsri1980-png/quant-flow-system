"""010a group 1 scaffolding (tasks 1.3/1.4).

Confirms the migrations package and `migrate` CLI exist and that the migration
error types are importable and caught by QuantFlowError (fail closed).
"""

from __future__ import annotations

import importlib

import pytest
from typer.testing import CliRunner

from quantflow.cli.main import app
from quantflow.domain import errors

MIGRATION_ERRORS = (
    "MigrationError",
    "MigrationManifestError",
    "MigrationLedgerError",
    "MigrationValidationError",
)


def test_migrations_package_importable() -> None:
    importlib.import_module("quantflow.migrations")
    importlib.import_module("quantflow.migrations.manifest")
    importlib.import_module("quantflow.migrations.runner")


def test_migrate_help_prints_usage() -> None:
    result = CliRunner().invoke(app, ["migrate", "--help"])
    assert result.exit_code == 0, result.output
    for subcommand in ("apply", "status", "verify"):
        assert subcommand in result.output


@pytest.mark.parametrize("name", MIGRATION_ERRORS)
def test_migration_error_types_are_quantflow_errors(name: str) -> None:
    error_type = getattr(errors, name)
    assert issubclass(error_type, errors.QuantFlowError)


def test_specific_migration_errors_share_the_migration_base() -> None:
    assert issubclass(errors.MigrationManifestError, errors.MigrationError)
    assert issubclass(errors.MigrationLedgerError, errors.MigrationError)
    assert issubclass(errors.MigrationValidationError, errors.MigrationError)
