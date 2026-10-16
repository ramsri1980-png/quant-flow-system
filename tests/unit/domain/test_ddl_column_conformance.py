"""005c 5.1: frozen SPEC V2 §19.2 time columns classify correctly.

Inverted design (operator ruling 2026-10-16; design D5). The conformance test
does **not** classify every §19.2 column. It filters column names to those that
declare a time semantic -- an epoch/duration token on an underscore token
boundary (SPEC V1 §19.8.3 Rules 1-2) -- and asserts each one classifies as
`epoch` or `duration`. A column whose name carries no time token is out of
scope by construction: it is not a time column by naming convention, which is
the point of the rule. There is **no** non-time allowlist to maintain.

`*_date` columns carry their own convention (SPEC V1 §19.8.1: SQLite date
columns are TEXT in ISO 8601), so they are asserted to be TEXT and to not
classify as an epoch/duration value.

The token filter is boundary-anchored, not substring: `max_attempts` merely
contains `_at`, and `spot_at_entry_micros` merely contains `_at`; neither
declares a time semantic.

Sources: SPEC V1 Sec 19.8.3 Rule 1/Rule 2; SPEC V2 Sec 19.2; 005c brief D4/2.4.
"""

import re
from pathlib import Path

import pytest

from quantflow.domain.errors import FieldNameError
from quantflow.domain.time import field_name_kind

SPEC_VOL2 = (
    Path(__file__).parents[3]
    / "docs"
    / "reference"
    / "CURRENT"
    / "SPEC_v2.0.5.1_Vol2_Data_Canonical.md"
)

SECTION_START = "19.2 Operational Entities (SQLite)"
SECTION_END = "19.3 Analytical Entities (DuckDB)"

# Column declaration: name + storage type, at line start or after a comma
# (the frozen DDL packs several columns onto one line).
COLUMN = re.compile(r"(?:^|,)\s*([a-z_]+)\s+(INTEGER|BIGINT|TEXT|REAL|BLOB)\b")

# Epoch/duration tokens per SPEC V1 §19.8.3 Rules 1-2. `*_epoch_ms` / `*_epoch_ns`
# are already covered by the `_ms` / `_ns` suffixes.
TIME_SUFFIX_TOKENS = ("_ts", "_at", "_until", "_ms", "_ns")

# SQLite date columns are TEXT ISO 8601 (SPEC V1 §19.8.1), not epoch values.
DATE_NAME_SUFFIX = "_date"

# A small positive list of known §19.2 time columns, pinned so a regression is
# caught even if the token filter ever stopped matching.
KNOWN_TIME_COLUMNS = {
    "abandoned_at": "epoch",
    "acknowledged_at": "epoch",
    "applied_at": "epoch",
    "blocked_until": "epoch",
    "cooldown_until": "epoch",
    "created_at": "epoch",
    "entered_at": "epoch",
    "entry_ts": "epoch",
    "last_event_ts": "epoch",
    "provider_ts": "epoch",
    "quote_ts": "epoch",
    "rearmed_at": "epoch",
    "resolved_at": "epoch",
    "staleness_ms": "duration",
    "updated_at": "epoch",
    "valid_until": "epoch",
}


def _section_columns() -> list[tuple[str, str]]:
    """(name, storage type) for every column declared in SPEC V2 §19.2."""
    lines = SPEC_VOL2.read_text().splitlines()
    start = next(i for i, line in enumerate(lines) if line.startswith(SECTION_START))
    end = next(i for i, line in enumerate(lines) if i > start and line.startswith(SECTION_END))
    columns: list[tuple[str, str]] = []
    for line in lines[start:end]:
        columns.extend((match.group(1), match.group(2)) for match in COLUMN.finditer(line))
    return columns


def _declares_time(name: str) -> bool:
    """True when name carries a time token on an underscore token boundary."""
    return name.endswith(TIME_SUFFIX_TOKENS) or name.startswith("epoch_") or "_epoch_" in name


def test_section_parse_finds_the_frozen_columns():
    columns = _section_columns()
    assert len(columns) > 500
    names = {name for name, _ in columns}
    assert {"cooldown_until", "rearmed_at", "created_at"} <= names


def test_every_time_token_column_classifies():
    offenders = []
    for name, _storage in _section_columns():
        if not _declares_time(name):
            continue
        try:
            field_name_kind(name)
        except FieldNameError as exc:
            offenders.append(f"{name}: {exc}")
    assert offenders == [], (
        "frozen DDL column names that declare a time semantic must classify as "
        "epoch or duration (SPEC V1 Sec 19.8.3):\n" + "\n".join(offenders)
    )


def test_time_token_filter_is_not_vacuous():
    filtered = {name for name, _ in _section_columns() if _declares_time(name)}
    assert len(filtered) >= 50


@pytest.mark.parametrize("name", ["max_attempts", "spot_at_entry_micros", "attempt_at_count"])
def test_substring_token_is_not_a_time_declaration(name):
    assert not _declares_time(name)


def test_date_columns_are_text_and_not_time_values():
    offenders = []
    for name, storage in _section_columns():
        if not name.endswith(DATE_NAME_SUFFIX):
            continue
        if storage != "TEXT":
            offenders.append(f"{name}: {storage} (expected TEXT; SPEC V1 Sec 19.8.1)")
            continue
        try:
            field_name_kind(name)
        except FieldNameError:
            continue
        offenders.append(f"{name}: classified as a time value, expected a date")
    assert offenders == [], offenders


@pytest.mark.parametrize(("name", "kind"), sorted(KNOWN_TIME_COLUMNS.items()))
def test_known_time_columns_classify(name, kind):
    assert field_name_kind(name) == kind


def test_cooldown_until_classifies_as_epoch():
    # Regression pin: raised FieldNameError before `_until` was an epoch suffix.
    assert field_name_kind("cooldown_until") == "epoch"


def test_rearmed_at_classifies_as_epoch():
    assert field_name_kind("rearmed_at") == "epoch"
