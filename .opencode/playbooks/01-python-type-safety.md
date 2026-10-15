# Playbook: Python type safety (load only when writing/editing typed Python)
- Python 3.12, `mypy --strict` clean. No bare `Any`; no `# type: ignore` without an error code + reason.
- Annotate all public signatures and return types. Use `X | None`, `list[str]`, `type` aliases (`type Cents = int`).
- Money/time: `NewType` for Cents, Micros, Mills, EpochMs. Never mix; conversions only in one units module.
- Domain objects: `@dataclass(frozen=True, slots=True)` or pydantic at boundaries only. Kernels take/return plain frozen types.
- Ports: `typing.Protocol`; adapters implement them. No isinstance chains; use `match` on enums/tagged unions.
- Enums: `StrEnum`; separate enum per vocabulary (no shared members across grade/state/episode).
- Narrow, don't cast. `assert_never` in exhaustive matches. Generics: `TypeVar` with bounds, only if reused.
- External data (JSON/DB rows) is `object` until validated into a typed model.
- Done = `uv run mypy --strict` passes on touched files.
