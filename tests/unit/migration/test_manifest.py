"""010a group 2 — manifest validator tests (tasks 2.1-2.6).

Derived from `specs/migration-runner/spec.md` scenarios and design D1-D5/D11.
Imports the module object (not names) so each sub-task's subset can go green
incrementally while later sub-tasks stay red.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from hypothesis import given
from hypothesis import strategies as st

from quantflow.domain.errors import MigrationError, MigrationManifestError, MigrationValidationError
from quantflow.migrations import manifest as m

# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #


def _entry(
    *,
    migration_id: str = "010_first",
    store: str = "sqlite",
    path: str | None = None,
    sha256: str = "0" * 64,
    applies_after: object = (),
    component: str = "core",
    enabled: object = True,
) -> dict[str, object]:
    return {
        "id": migration_id,
        "store": store,
        "path": path if path is not None else f"{store}/{migration_id}.sql",
        "sha256": sha256,
        "applies_after": list(applies_after)  # type: ignore[arg-type]
        if isinstance(applies_after, tuple)
        else applies_after,
        "component": component,
        "enabled": enabled,
    }


def _doc(*entries: dict[str, object], baseline_covered: object = None) -> dict[str, object]:
    doc: dict[str, object] = {"version": 1, "migrations": list(entries)}
    if baseline_covered is not None:
        doc["baseline_covered"] = baseline_covered
    return doc


def _write_sql(root: Path, relpath: str, body: str = "SELECT 1;\n") -> str:
    path = root / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(body.encode())
    import hashlib

    return hashlib.sha256(body.encode()).hexdigest()


def _materialize(root: Path, doc: dict[str, object]) -> Path:
    """Write MANIFEST.json + a real file per entry, hashing actual bytes."""
    entries = doc["migrations"]
    assert isinstance(entries, list)
    for entry in entries:
        assert isinstance(entry, dict)
        body = f"-- {entry['id']}\nSELECT 1;\n"
        entry["sha256"] = _write_sql(root, str(entry["path"]), body)
    (root / "MANIFEST.json").write_text(json.dumps(doc))
    return root / "MANIFEST.json"


# --------------------------------------------------------------------------- #
# 1. schema
# --------------------------------------------------------------------------- #


class TestManifestSchema:
    def test_valid_entry_is_accepted(self) -> None:
        man = m.parse_manifest(_doc(_entry()))
        assert [e.id for e in man.entries] == ["010_first"]
        assert man.entries[0].store == m.Store.SQLITE
        assert man.entries[0].applies_after == ()
        assert man.entries[0].enabled is True

    @pytest.mark.parametrize(
        "field",
        ["id", "store", "path", "sha256", "applies_after", "component", "enabled"],
    )
    def test_missing_required_field_fails_naming_field(self, field: str) -> None:
        entry = _entry()
        del entry[field]
        with pytest.raises(MigrationManifestError, match=field):
            m.parse_manifest(_doc(entry))

    def test_scalar_applies_after_is_rejected(self) -> None:
        with pytest.raises(MigrationManifestError):
            m.parse_manifest(_doc(_entry(applies_after="010_other")))

    def test_duplicate_id_fails(self) -> None:
        with pytest.raises(MigrationManifestError):
            m.parse_manifest(_doc(_entry(), _entry()))

    def test_same_id_in_other_store_is_allowed(self) -> None:
        man = m.parse_manifest(
            _doc(
                _entry(migration_id="010_x", store="sqlite"),
                _entry(migration_id="010_x", store="duckdb"),
            )
        )
        assert len(man.entries) == 2

    def test_empty_component_is_unclassified(self) -> None:
        with pytest.raises(MigrationManifestError):
            m.parse_manifest(_doc(_entry(component="")))

    def test_non_bool_enabled_is_rejected(self) -> None:
        with pytest.raises(MigrationManifestError):
            m.parse_manifest(_doc(_entry(enabled="yes")))

    def test_non_string_id_is_rejected(self) -> None:
        with pytest.raises(MigrationManifestError):
            m.parse_manifest(_doc(_entry(migration_id=10)))  # type: ignore[arg-type]

    def test_non_mapping_root_fails(self) -> None:
        with pytest.raises(MigrationManifestError):
            m.parse_manifest(["not", "a", "mapping"])


# --------------------------------------------------------------------------- #
# 2. path safety / id form
# --------------------------------------------------------------------------- #


class TestPathSafety:
    def test_traversal_path_is_rejected(self) -> None:
        with pytest.raises(MigrationManifestError):
            m.parse_manifest(_doc(_entry(path="../duckdb/010_first.sql")))

    def test_absolute_path_is_rejected(self) -> None:
        with pytest.raises(MigrationManifestError):
            m.parse_manifest(_doc(_entry(path="/etc/010_first.sql")))

    def test_path_in_other_store_is_rejected(self) -> None:
        with pytest.raises(MigrationManifestError):
            m.parse_manifest(_doc(_entry(store="sqlite", path="duckdb/010_first.sql")))

    def test_filename_form_is_enforced(self) -> None:
        with pytest.raises(MigrationManifestError):
            m.parse_manifest(_doc(_entry(path="sqlite/010-first.sql")))

    def test_backslash_path_is_rejected(self) -> None:
        with pytest.raises(MigrationManifestError):
            m.parse_manifest(_doc(_entry(path="sqlite\\010_first.sql")))

    def test_bad_sha256_is_rejected(self) -> None:
        with pytest.raises(MigrationManifestError):
            m.parse_manifest(_doc(_entry(sha256="DEADBEEF")))


# --------------------------------------------------------------------------- #
# 3. slot policy
# --------------------------------------------------------------------------- #


class TestSlotPolicy:
    @pytest.mark.parametrize(
        ("store", "migration_id"),
        [
            ("sqlite", "072_reserved"),
            ("sqlite", "075_reserved"),
            ("sqlite", "079_reserved"),
            ("duckdb", "046_reserved"),
            ("duckdb", "047_reserved"),
            ("duckdb", "049_reserved"),
        ],
    )
    def test_reserved_slot_is_an_error(self, store: str, migration_id: str) -> None:
        man = m.parse_manifest(_doc(_entry(migration_id=migration_id, store=store)))
        with pytest.raises(MigrationValidationError):
            m.validate_slots(man)

    @pytest.mark.parametrize(
        ("store", "migration_id"),
        [
            ("sqlite", "071_core_repair"),
            ("duckdb", "043_adoption"),
            ("duckdb", "044_adoption"),
            ("duckdb", "045_adoption"),
            ("duckdb", "050_core_repair"),
        ],
    )
    def test_adopt_only_slot_is_not_never(self, store: str, migration_id: str) -> None:
        man = m.parse_manifest(_doc(_entry(migration_id=migration_id, store=store)))
        m.validate_slots(man)  # MUST NOT raise

    def test_adopt_only_slot_boundaries(self) -> None:
        m.validate_slots(
            m.parse_manifest(_doc(_entry(migration_id="045_adoption", store="duckdb")))
        )
        with pytest.raises(MigrationValidationError):
            m.validate_slots(
                m.parse_manifest(_doc(_entry(migration_id="046_reserved", store="duckdb")))
            )

    def test_adopt_only_is_not_auto_applied(self) -> None:
        man = m.parse_manifest(
            _doc(_entry(migration_id="043_adoption", store="duckdb", enabled=True))
        )
        assert m.apply_order(man, m.Store.DUCKDB) == ()
        assert [e.id for e in m.adopt_only_entries(man, m.Store.DUCKDB)] == ["043_adoption"]

    def test_normal_enabled_entry_is_applied(self) -> None:
        man = m.parse_manifest(_doc(_entry(migration_id="042_core")))
        assert [e.id for e in m.apply_order(man, m.Store.SQLITE)] == ["042_core"]


# --------------------------------------------------------------------------- #
# 4. unmanifested / missing files
# --------------------------------------------------------------------------- #


class TestUnmanifestedFiles:
    def test_unmanifested_sql_file_fails(self, tmp_path: Path) -> None:
        root = tmp_path / "migrations"
        doc = _doc(_entry())
        _materialize(root, doc)
        _write_sql(root, "sqlite/011_extra.sql")
        manifest = m.parse_manifest(doc)
        with pytest.raises(MigrationValidationError, match="011_extra"):
            m.validate_file_inventory(manifest, root)

    def test_missing_manifest_file_fails(self, tmp_path: Path) -> None:
        root = tmp_path / "migrations"
        doc = _doc(_entry())
        manifest = m.parse_manifest(doc)  # no file written
        with pytest.raises(MigrationValidationError, match="010_first"):
            m.validate_file_inventory(manifest, root)

    def test_fully_manifested_store_is_ok(self, tmp_path: Path) -> None:
        root = tmp_path / "migrations"
        doc = _doc(_entry())
        _materialize(root, doc)
        m.validate_file_inventory(m.parse_manifest(doc), root)


# --------------------------------------------------------------------------- #
# 5. dependencies
# --------------------------------------------------------------------------- #


class TestDependencies:
    def test_unknown_dependency_fails(self) -> None:
        man = m.parse_manifest(_doc(_entry(applies_after=("099_missing",))))
        with pytest.raises(MigrationValidationError):
            m.validate_dependencies(man)

    def test_cross_store_dependency_is_rejected(self) -> None:
        man = m.parse_manifest(
            _doc(
                _entry(migration_id="010_a", store="sqlite", applies_after=("020_b",)),
                _entry(migration_id="020_b", store="duckdb"),
            )
        )
        with pytest.raises(MigrationValidationError):
            m.validate_dependencies(man)

    def test_cycle_is_rejected(self) -> None:
        man = m.parse_manifest(
            _doc(
                _entry(migration_id="010_a", applies_after=("020_b",)),
                _entry(migration_id="020_b", applies_after=("010_a",)),
            )
        )
        with pytest.raises(MigrationValidationError):
            m.validate_dependencies(man)

    def test_self_dependency_is_rejected(self) -> None:
        man = m.parse_manifest(_doc(_entry(migration_id="010_a", applies_after=("010_a",))))
        with pytest.raises(MigrationValidationError):
            m.validate_dependencies(man)

    def test_baseline_covered_dependency_is_allowed(self) -> None:
        man = m.parse_manifest(
            _doc(
                _entry(migration_id="070_post", applies_after=("050_hist",)),
                baseline_covered={"sqlite": ["050_hist"]},
            )
        )
        m.validate_dependencies(man)  # MUST NOT raise


# --------------------------------------------------------------------------- #
# 6. ordering
# --------------------------------------------------------------------------- #


class TestOrdering:
    def test_numeric_id_breaks_ties(self) -> None:
        man = m.parse_manifest(
            _doc(
                _entry(migration_id="030_c"),
                _entry(migration_id="010_a"),
                _entry(migration_id="020_b"),
            )
        )
        assert [e.id for e in m.apply_order(man, m.Store.SQLITE)] == [
            "010_a",
            "020_b",
            "030_c",
        ]

    def test_dependency_precedes_dependent(self) -> None:
        man = m.parse_manifest(
            _doc(
                _entry(migration_id="030_c", applies_after=("020_b",)),
                _entry(migration_id="020_b"),
            )
        )
        order = [e.id for e in m.apply_order(man, m.Store.SQLITE)]
        assert order.index("020_b") < order.index("030_c")

    def test_baseline_is_first(self) -> None:
        man = m.parse_manifest(
            _doc(
                _entry(migration_id="010_a"),
                _entry(migration_id="000_baseline"),
            )
        )
        assert [e.id for e in m.apply_order(man, m.Store.SQLITE)][0] == m.BASELINE_ID

    def test_disabled_entry_is_not_ordered(self) -> None:
        man = m.parse_manifest(
            _doc(
                _entry(migration_id="010_a"),
                _entry(migration_id="020_b", enabled=False),
            )
        )
        assert [e.id for e in m.apply_order(man, m.Store.SQLITE)] == ["010_a"]

    def test_order_is_stable_across_runs(self) -> None:
        man = m.parse_manifest(
            _doc(
                _entry(migration_id="030_c", applies_after=("010_a",)),
                _entry(migration_id="010_a"),
                _entry(migration_id="020_b", applies_after=("010_a",)),
            )
        )
        first = m.apply_order(man, m.Store.SQLITE)
        assert m.apply_order(man, m.Store.SQLITE) == first


# --------------------------------------------------------------------------- #
# 7. baseline_covered metadata
# --------------------------------------------------------------------------- #


class TestBaselineCoverage:
    def test_valid_coverage_is_parsed(self) -> None:
        man = m.parse_manifest(
            _doc(_entry(), baseline_covered={"sqlite": ["050_hist"], "duckdb": []})
        )
        assert man.baseline_covered[m.Store.SQLITE] == ("050_hist",)
        assert man.baseline_covered[m.Store.DUCKDB] == ()

    @pytest.mark.parametrize(
        "coverage",
        [
            ["050_hist"],  # not a mapping
            {"sqlite": "050_hist"},  # value not a list
            {"unknown": ["050_hist"]},  # unknown store
            {"sqlite": [50]},  # item not a string
        ],
    )
    def test_malformed_coverage_fails_closed(self, coverage: object) -> None:
        with pytest.raises(MigrationManifestError):
            m.parse_manifest(_doc(_entry(), baseline_covered=coverage))

    def test_empty_string_coverage_id_fails_closed(self) -> None:
        with pytest.raises(MigrationManifestError):
            m.parse_manifest(_doc(_entry(), baseline_covered={"sqlite": [""]}))

    def test_nested_coverage_item_fails_closed(self) -> None:
        with pytest.raises(MigrationManifestError):
            m.parse_manifest(_doc(_entry(), baseline_covered={"sqlite": [["050_hist"]]}))

    def test_absent_coverage_defaults_to_empty(self) -> None:
        man = m.parse_manifest(_doc(_entry()))
        assert man.covered_ids(m.Store.SQLITE) == ()
        assert man.covered_ids(m.Store.DUCKDB) == ()

    def test_coverage_is_informational_not_an_ok_row(self) -> None:
        man = m.parse_manifest(_doc(_entry(), baseline_covered={"sqlite": ["050_hist"]}))
        assert "050_hist" not in {e.id for e in man.entries}
        assert "050_hist" not in {e.id for e in m.apply_order(man, m.Store.SQLITE)}


# --------------------------------------------------------------------------- #
# 8. checksums / immutability
# --------------------------------------------------------------------------- #


class TestChecksums:
    def test_checksum_mismatch_fails_closed(self, tmp_path: Path) -> None:
        root = tmp_path / "migrations"
        doc = _doc(_entry())
        _write_sql(root, "sqlite/010_first.sql", "SELECT 1;\n")
        doc["migrations"][0]["sha256"] = "f" * 64  # type: ignore[index]
        with pytest.raises(MigrationValidationError):
            m.verify_checksums(m.parse_manifest(doc), root)

    def test_checksum_match_passes(self, tmp_path: Path) -> None:
        root = tmp_path / "migrations"
        doc = _doc(_entry())
        _materialize(root, doc)
        m.verify_checksums(m.parse_manifest(doc), root)

    def test_edited_applied_migration_is_detected(self, tmp_path: Path) -> None:
        root = tmp_path / "migrations"
        doc = _doc(_entry())
        _materialize(root, doc)
        manifest = m.parse_manifest(doc)
        # edit the file after its checksum was recorded (forward-only violation)
        _write_sql(root, "sqlite/010_first.sql", "SELECT 2;\n")
        with pytest.raises(MigrationValidationError):
            m.verify_checksums(manifest, root)


# --------------------------------------------------------------------------- #
# 9. loader (missing / malformed)
# --------------------------------------------------------------------------- #


class TestManifestLoader:
    def test_missing_manifest_fails(self, tmp_path: Path) -> None:
        with pytest.raises(MigrationManifestError):
            m.load_manifest(tmp_path / "migrations")

    def test_malformed_json_fails(self, tmp_path: Path) -> None:
        root = tmp_path / "migrations"
        root.mkdir()
        (root / "MANIFEST.json").write_text("{not json")
        with pytest.raises(MigrationManifestError):
            m.load_manifest(root)

    def test_load_valid_manifest_round_trips(self, tmp_path: Path) -> None:
        root = tmp_path / "migrations"
        doc = _doc(_entry())
        _materialize(root, doc)
        man = m.load_manifest(root)
        assert [e.id for e in man.entries] == ["010_first"]


# --------------------------------------------------------------------------- #
# 10. property invariants
# --------------------------------------------------------------------------- #


class TestManifestProperties:
    @given(st.lists(st.integers(min_value=10, max_value=42), unique=True, min_size=1, max_size=8))
    def test_order_is_numeric_and_deterministic(self, slots: list[int]) -> None:
        entries = [
            _entry(migration_id=f"{s:03d}_m{s}", path=f"sqlite/{s:03d}_m{s}.sql") for s in slots
        ]
        man = m.parse_manifest(_doc(*entries))
        expected = [f"{s:03d}_m{s}" for s in sorted(slots)]
        assert [e.id for e in m.apply_order(man, m.Store.SQLITE)] == expected
        assert m.apply_order(man, m.Store.SQLITE) == m.apply_order(man, m.Store.SQLITE)

    @given(
        slots=st.lists(st.integers(min_value=10, max_value=42), unique=True, min_size=2, max_size=6)
    )
    def test_dependencies_are_respected(self, slots: list[int]) -> None:
        ordered = sorted(slots)
        entries = []
        for index, slot in enumerate(ordered):
            deps = () if index == 0 else (f"{ordered[index - 1]:03d}_m{ordered[index - 1]}",)
            entries.append(
                _entry(
                    migration_id=f"{slot:03d}_m{slot}",
                    path=f"sqlite/{slot:03d}_m{slot}.sql",
                    applies_after=deps,
                )
            )
        man = m.parse_manifest(_doc(*entries))
        order = [e.id for e in m.apply_order(man, m.Store.SQLITE)]
        assert order == [f"{s:03d}_m{s}" for s in ordered]

    def test_every_error_is_a_migration_error(self) -> None:
        entry = _entry()
        del entry["id"]
        with pytest.raises(MigrationError):
            m.parse_manifest(_doc(entry))
