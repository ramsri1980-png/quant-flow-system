"""Typed domain error hierarchy (fail-closed; one class per distinct reason)."""


class QuantFlowError(Exception):
    """Base class for all QuantFlow domain errors."""


class UnitValueError(QuantFlowError, ValueError):
    """A unit-typed integer was invalid: outside the signed 64-bit range."""


class ConstantsError(QuantFlowError):
    """A constant read is not permitted: name is approval-pending or unknown."""


class FieldNameError(QuantFlowError, ValueError):
    """A field name violated the epoch-vs-duration naming rule."""


class VocabularyError(QuantFlowError, ValueError):
    """A literal was rejected by a closed domain vocabulary."""


class MigrationError(QuantFlowError):
    """Base class for migration-subsystem failures."""


class MigrationManifestError(MigrationError):
    """The migration manifest is missing, malformed, or schema-invalid."""


class MigrationLedgerError(MigrationError):
    """The migration ledger could not be bootstrapped or read consistently."""


class MigrationValidationError(MigrationError):
    """A migration failed dependency, closure, checksum, or ordering validation."""
