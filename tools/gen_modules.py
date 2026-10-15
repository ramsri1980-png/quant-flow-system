#!/usr/bin/env python3
"""Generate openspec/modules.md: an index of existing modules for reuse-first work.
Usage: python3 tools/gen_modules.py [src_dir=src] [out=openspec/modules.md]"""
import ast, pathlib, sys
src = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "src")
out = pathlib.Path(sys.argv[2] if len(sys.argv) > 2 else "openspec/modules.md")
rows = ["# Module index (generated; do not edit). Reuse before creating.", ""]
for p in sorted(src.rglob("*.py")):
    if p.name.startswith("_") and p.name != "__init__.py": continue
    try: tree = ast.parse(p.read_text(encoding="utf-8"))
    except SyntaxError: continue
    items = []
    for n in tree.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and not n.name.startswith("_"):
            doc = (ast.get_docstring(n) or "").split("\n")[0][:80]
            kind = "class" if isinstance(n, ast.ClassDef) else "def"
            args = "" if kind == "class" else "(" + ", ".join(a.arg for a in n.args.args) + ")"
            items.append(f"  - {kind} {n.name}{args} — {doc}")
    if items:
        mdoc = (ast.get_docstring(tree) or "").split("\n")[0][:80]
        rows.append(f"- `{p.as_posix()}` — {mdoc}"); rows += items
out.parent.mkdir(parents=True, exist_ok=True); out.write_text("\n".join(rows) + "\n")
print(f"wrote {out} ({len(rows)} lines)")
