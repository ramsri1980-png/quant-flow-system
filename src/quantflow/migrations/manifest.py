"""Manifest loading and validation for the migration runner (010a).

The canonical manifest is a single `migrations/MANIFEST.json`:

```json
{
  "version": 1,
  "baseline_covered": {"sqlite": ["050_hist"], "duckdb": []},
  "migrations": [
    {"id": "...", "store": "sqlite", "path": "sqlite/NNN_<slug>.sql",
     "sha256": "<64 lowercase hex>", "applies_after": [],
     "component": "core", "enabled": true}
  ]
}
```

`applies_after` is always an array of store-local migration IDs. `store` and
`path` are validated together: the path is relative to the migrations root and
MUST resolve inside `migrations/<store>/` with the form `NNN_<slug>.sql`.
"""

from __future__ import annotations

import hashlib
import heapq
import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path, PurePosixPath

from quantflow.domain.errors import MigrationManifestError, MigrationValidationError

MANIFEST_FILENAME = "MANIFEST.json"
BASELINE_ID = "000_baseline"

_ID_RE = re.compile(r"^(?P<slot>\d{3})_[A-Za-z0-9][A-Za-z0-9._-]*$")
_SQL_FILENAME_RE = re.compile(r"^(?P<slot>\d{3})_[^/\\]+\.sql$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

_REQUIRED_FIELDS = ("id", "store", "path", "sha256", "applies_after", "component", "enabled")


class Store(StrEnum):
    """The two stores that own a migration ledger."""

    SQLITE = "sqlite"
    DUCKDB = "duckdb"


#: Slots that MUST never carry a manifest entry (reserved for a future phase).
NEVER_SLOTS: Mapping[Store, frozenset[int]] = {
    Store.SQLITE: frozenset(range(72, 80)),
    Store.DUCKDB: frozenset(range(46, 50)),
}

#: Slots that MUST NOT be auto-applied until an operator-approved enablement
#: (mechanism owned by 010b; 010a never auto-applies these).
ADOPT_ONLY_SLOTS: Mapping[Store, frozenset[int]] = {
    Store.SQLITE: frozenset({71}),
    Store.DUCKDB: frozenset({43, 44, 45, 50}),
}


@dataclass(frozen=True, slots=True)
class ManifestEntry:
    """One authorized migration."""

    id: str
    store: Store
    path: str
    sha256: str
    applies_after: tuple[str, ...]
    component: str
    enabled: bool

    @property
    def slot(self) -> int:
        """The three-digit numeric slot encoded in the migration ID."""
        return int(self.id[:3])


@dataclass(frozen=True, slots=True)
class Manifest:
    """A parsed, schema-validated migration manifest."""

    entries: tuple[ManifestEntry, ...]
    baseline_covered: Mapping[Store, tuple[str, ...]]

    def entry_ids(self, store: Store) -> frozenset[str]:
        """IDs declared as manifest entries for ``store``."""
        return frozenset(e.id for e in self.entries if e.store is store)

    def covered_ids(self, store: Store) -> tuple[str, ...]:
        """Historically covered IDs recorded for ``store`` (informational)."""
        return self.baseline_covered.get(store, ())


def _require_field(entry: Mapping[str, object], field: str, index: int) -> object:
    if field not in entry:
        raise MigrationManifestError(f"manifest entry {index}: missing required field '{field}'")
    return entry[field]


def _parse_id(value: object, index: int) -> str:
    if not isinstance(value, str) or _ID_RE.match(value) is None:
        raise MigrationManifestError(f"manifest entry {index}: invalid migration id {value!r}")
    return value


def _parse_store(value: object, index: int) -> Store:
    try:
        return Store(value)  # type: ignore[arg-type]
    except ValueError as exc:
        raise MigrationManifestError(f"manifest entry {index}: invalid store {value!r}") from exc


def _parse_path(value: object, store: Store, index: int) -> str:
    if not isinstance(value, str) or "\\" in value:
        raise MigrationManifestError(f"manifest entry {index}: invalid path {value!r}")
    parts = PurePosixPath(value).parts
    if ".." in parts or len(parts) != 2 or parts[0] != store.value:
        raise MigrationManifestError(
            f"manifest entry {index}: path {value!r} must resolve inside migrations/{store.value}/"
        )
    if _SQL_FILENAME_RE.match(parts[1]) is None:
        raise MigrationManifestError(
            f"manifest entry {index}: path {value!r} must use the form NNN_<slug>.sql"
        )
    return value


def _parse_sha256(value: object, index: int) -> str:
    if not isinstance(value, str) or _SHA256_RE.match(value) is None:
        raise MigrationManifestError(
            f"manifest entry {index}: 'sha256' must be 64 lowercase hex digits"
        )
    return value


def _parse_applies_after(value: object, index: int) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise MigrationManifestError(
            f"manifest entry {index}: 'applies_after' must be an array of IDs"
        )
    deps: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item:
            raise MigrationManifestError(
                f"manifest entry {index}: 'applies_after' entries must be non-empty strings"
            )
        deps.append(item)
    return tuple(deps)


def _parse_component(value: object, index: int) -> str:
    if not isinstance(value, str) or not value:
        raise MigrationManifestError(
            f"manifest entry {index}: 'component' must be a non-empty classification"
        )
    return value


def _parse_enabled(value: object, index: int) -> bool:
    if not isinstance(value, bool):
        raise MigrationManifestError(f"manifest entry {index}: 'enabled' must be a boolean")
    return value


def _parse_baseline_covered(raw: Mapping[str, object]) -> Mapping[Store, tuple[str, ...]]:
    covered: dict[Store, tuple[str, ...]] = {store: () for store in Store}
    value = raw.get("baseline_covered")
    if value is None:
        return covered
    if not isinstance(value, Mapping):
        raise MigrationManifestError("'baseline_covered' must be an object keyed by store")
    for key, ids in value.items():
        try:
            store = Store(key)
        except ValueError as exc:
            raise MigrationManifestError(
                f"'baseline_covered' names an unknown store {key!r}"
            ) from exc
        if not isinstance(ids, list):
            raise MigrationManifestError(f"'baseline_covered[{key}]' must be an array")
        parsed: list[str] = []
        for item in ids:
            if not isinstance(item, str) or not item:
                raise MigrationManifestError(
                    f"'baseline_covered[{key}]' entries must be non-empty strings"
                )
            parsed.append(item)
        covered[store] = tuple(parsed)
    return covered


def parse_manifest(raw: object) -> Manifest:
    """Parse and schema-validate a manifest document (pure; no disk access)."""
    if not isinstance(raw, Mapping):
        raise MigrationManifestError("manifest must be a JSON object")
    entries_raw = raw.get("migrations")
    if not isinstance(entries_raw, list):
        raise MigrationManifestError("manifest must contain a 'migrations' array")

    entries: list[ManifestEntry] = []
    seen: set[tuple[Store, str]] = set()
    for index, item in enumerate(entries_raw):
        if not isinstance(item, Mapping):
            raise MigrationManifestError(f"manifest entry {index} must be an object")
        for field in _REQUIRED_FIELDS:
            _require_field(item, field, index)
        entry_id = _parse_id(item["id"], index)
        store = _parse_store(item["store"], index)
        path = _parse_path(item["path"], store, index)
        sha256 = _parse_sha256(item["sha256"], index)
        applies_after = _parse_applies_after(item["applies_after"], index)
        component = _parse_component(item["component"], index)
        enabled = _parse_enabled(item["enabled"], index)
        key = (store, entry_id)
        if key in seen:
            raise MigrationManifestError(
                f"duplicate migration id {entry_id!r} in store {store.value!r}"
            )
        seen.add(key)
        entries.append(
            ManifestEntry(
                id=entry_id,
                store=store,
                path=path,
                sha256=sha256,
                applies_after=applies_after,
                component=component,
                enabled=enabled,
            )
        )
    return Manifest(entries=tuple(entries), baseline_covered=_parse_baseline_covered(raw))


def validate_slots(manifest: Manifest) -> None:
    """Reject entries that occupy a reserved (NEVER) slot for their store."""
    for entry in manifest.entries:
        if entry.slot in NEVER_SLOTS[entry.store]:
            raise MigrationValidationError(
                f"migration id {entry.id!r} uses a reserved {entry.store.value} slot "
                f"({entry.slot:03d})"
            )


def adopt_only_entries(manifest: Manifest, store: Store) -> tuple[ManifestEntry, ...]:
    """ADOPT-ONLY entries for ``store`` (reported; never auto-applied in 010a)."""
    return tuple(
        entry
        for entry in manifest.entries
        if entry.store is store and entry.slot in ADOPT_ONLY_SLOTS[store]
    )


def validate_file_inventory(manifest: Manifest, migrations_root: Path) -> None:
    """Fail closed on unmanifested ``.sql`` files or manifest entries with no file."""
    for store in Store:
        store_dir = migrations_root / store.value
        on_disk: set[str] = set()
        if store_dir.is_dir():
            on_disk = {
                path.relative_to(migrations_root).as_posix() for path in store_dir.rglob("*.sql")
            }
        for extra in sorted(on_disk - {e.path for e in manifest.entries}):
            raise MigrationValidationError(f"unmanifested migration file: {extra}")
        for entry in manifest.entries:
            if entry.store is store and entry.path not in on_disk:
                raise MigrationValidationError(
                    f"manifest entry {entry.id!r} has no file at {entry.path}"
                )


def validate_dependencies(manifest: Manifest) -> None:
    """Validate store-local dependency existence, cross-store rejection, acyclicity."""
    ids_by_store = {store: manifest.entry_ids(store) for store in Store}
    for entry in manifest.entries:
        same_store = ids_by_store[entry.store]
        covered = set(manifest.covered_ids(entry.store))
        for dep in entry.applies_after:
            if dep in same_store or dep in covered:
                continue
            other = next(
                (s for s in Store if s is not entry.store and dep in ids_by_store[s]), None
            )
            if other is not None:
                raise MigrationValidationError(
                    f"migration {entry.id!r} declares a cross-store dependency on {dep!r} "
                    f"({other.value} entry from a {entry.store.value} migration)"
                )
            raise MigrationValidationError(f"migration {entry.id!r} depends on unknown id {dep!r}")
    _detect_cycles(manifest)


def _detect_cycles(manifest: Manifest) -> None:
    for store in Store:
        entries = [e for e in manifest.entries if e.store is store]
        if not entries:
            continue
        ids = {e.id for e in entries}
        indegree = dict.fromkeys(ids, 0)
        adjacency: dict[str, list[str]] = {entry_id: [] for entry_id in ids}
        for entry in entries:
            for dep in entry.applies_after:
                if dep == entry.id:
                    raise MigrationValidationError(f"migration {entry.id!r} depends on itself")
                if dep in ids:
                    adjacency[dep].append(entry.id)
                    indegree[entry.id] += 1
        ready = [entry_id for entry_id, degree in indegree.items() if degree == 0]
        processed = 0
        while ready:
            node = ready.pop()
            processed += 1
            for dependent in adjacency[node]:
                indegree[dependent] -= 1
                if indegree[dependent] == 0:
                    ready.append(dependent)
        if processed != len(entries):
            raise MigrationValidationError(f"dependency cycle among {store.value} migrations")


def apply_order(manifest: Manifest, store: Store) -> tuple[ManifestEntry, ...]:
    """Enabled, non-ADOPT-ONLY entries in stable topological order.

    Ties are broken by numeric slot then ID, with ``000_baseline`` first. The
    ordering is derived from the dependency graph, never from ``MAX(migration_id)``.
    """
    adopt_only = ADOPT_ONLY_SLOTS[store]
    nodes = {
        entry.id: entry
        for entry in manifest.entries
        if entry.store is store and entry.enabled and entry.slot not in adopt_only
    }
    indegree = dict.fromkeys(nodes, 0)
    adjacency: dict[str, list[str]] = {entry_id: [] for entry_id in nodes}
    for entry in nodes.values():
        for dep in entry.applies_after:
            if dep in nodes:
                adjacency[dep].append(entry.id)
                indegree[entry.id] += 1
    heap = [(entry.slot, entry.id) for entry in nodes.values() if indegree[entry.id] == 0]
    heapq.heapify(heap)
    ordered: list[ManifestEntry] = []
    while heap:
        _, entry_id = heapq.heappop(heap)
        ordered.append(nodes[entry_id])
        for dependent in adjacency[entry_id]:
            indegree[dependent] -= 1
            if indegree[dependent] == 0:
                heapq.heappush(heap, (nodes[dependent].slot, dependent))
    if len(ordered) != len(nodes):
        raise MigrationValidationError(f"dependency cycle among enabled {store.value} migrations")
    return tuple(ordered)


def verify_checksums(manifest: Manifest, migrations_root: Path) -> None:
    """Fail closed unless every file's exact bytes hash to its manifest SHA-256.

    Forward-only: an applied migration is never edited, so any on-disk/manifest
    mismatch is a hard error raised before anything is applied.
    """
    for entry in manifest.entries:
        path = migrations_root / entry.path
        try:
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
        except FileNotFoundError as exc:
            raise MigrationValidationError(f"migration file missing: {entry.path}") from exc
        except OSError as exc:
            raise MigrationValidationError(
                f"cannot read migration file {entry.path}: {exc}"
            ) from exc
        if digest != entry.sha256:
            raise MigrationValidationError(
                f"checksum mismatch for {entry.id!r} ({entry.path}): "
                f"manifest {entry.sha256} != on-disk {digest}"
            )


def load_manifest(migrations_root: Path) -> Manifest:
    """Read and validate `<migrations_root>/MANIFEST.json`."""
    path = migrations_root / MANIFEST_FILENAME
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise MigrationManifestError(f"migration manifest not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise MigrationManifestError(
            f"migration manifest is not valid JSON: {path}: {exc}"
        ) from exc
    except OSError as exc:
        raise MigrationManifestError(f"cannot read migration manifest: {path}: {exc}") from exc
    manifest = parse_manifest(raw)
    validate_slots(manifest)
    validate_file_inventory(manifest, migrations_root)
    validate_dependencies(manifest)
    return manifest
