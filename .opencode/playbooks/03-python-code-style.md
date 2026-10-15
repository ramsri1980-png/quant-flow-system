# Playbook: Python code style (load only when writing/editing Python)
- `ruff format` + `ruff check` clean; line length per pyproject. Imports sorted by ruff; absolute imports.
- Names: snake_case funcs/vars, PascalCase types, UPPER_SNAKE constants (defined once; QuantFlow constants live in ARCH V1 §AI.3 → one `constants` module).
- Functions small, one purpose, ≤ ~40 lines; early returns; no deep nesting (>3).
- Docstring on public API: one line + units/side effects. Comments explain why, cite spec as "SPEC V3 §8.4".
- No magic numbers; no mutable defaults; no wildcard imports; no print (use logging).
- Layout: domain/ (pure), kernels/ (pure), ports/, adapters/, app/. Dependencies point inward only.
- Prefer stdlib + existing deps; ask before adding a dependency.
- Done = `uv run ruff format --check . && uv run ruff check .`.
