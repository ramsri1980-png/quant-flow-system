"""Check: AI.3 constants defined once, generated module un-drifted.

SPEC V1 §1.4.33-1.4.34: a duplicate definition of an AI.3 constant name
outside domain/constants.py fails; an UPPER_SNAKE_CASE module-level constant
not sourced from AI.3 fails unless it is a documented structural constant
(STRUCTURAL_ALLOWLIST -- explicit, fail-closed for anything new).

005c Q7: structural constants are exempt from the "named constants live once in
ARCH V1 §AI.3" rule (AGENTS rule 8) because they are type invariants, not
tunable config, and live in units.py/time.py by design. They are enumerated in
STRUCTURAL_ALLOWLIST above; nothing else is exempt.

Usage: python3 scripts/check_constants.py
"""

import ast
import importlib.util
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CURRENT_BUNDLE = REPO_ROOT / "docs" / "reference" / "CURRENT"
ARCH_VOL1 = CURRENT_BUNDLE / "ARCH_v5.1.5.1_Vol1_Foundation.md"
CONSTANTS_MODULE = REPO_ROOT / "src" / "quantflow" / "domain" / "constants.py"
SRC_TREE = REPO_ROOT / "src" / "quantflow"

UPPER_SNAKE = re.compile(r"^[A-Z][A-Z0-9_]+$")

# Structural (non-AI.3) constants, each with a reason. Anything new must be
# added here deliberately -- fail closed, never silently allow.
STRUCTURAL_ALLOWLIST = {
    "INT64_MIN": "signed 64-bit storage bound (SPEC V2 Sec 19.4.4)",
    "INT64_MAX": "signed 64-bit storage bound (SPEC V2 Sec 19.4.4)",
    "MICROS_PER_MILL": "unit-scale divisor (ARCH V4 Sec D.3 unit contract)",
    "DURATION_MS_MAX": "validated duration maximum (RQ-007 operator ruling)",
    "EPOCH_MS_MIN": "epoch-ms plausible-range floor (SPEC V1 Sec 19.8.3, 005b Q8)",
    "EPOCH_MS_MAX": "epoch-ms plausible-range ceiling (SPEC V1 Sec 19.8.3, 005b Q8)",
    "EPOCH_NAME_SUFFIXES": "SPEC V1 Sec 19.8.3 Rule 1 naming table",
    "DURATION_NAME_SUFFIXES": "SPEC V1 Sec 19.8.3 Rule 2 naming table",
    "HOST": "POC adapter endpoint config (env-derived; not decision path)",
    "PORT": "POC adapter endpoint config (env-derived; not decision path)",
    "MANIFEST_FILENAME": "010a brief D1 manifest filename (SPEC/ARCH structural)",
    "BASELINE_ID": "000_baseline logical ID (SPEC V2 19.2; ARCH V2 C.3; 010a D10)",
    "NEVER_SLOTS": "NEVER-slot policy (ARCH V2 C.3; 010a D5)",
    "ADOPT_ONLY_SLOTS": "ADOPT-ONLY slot policy (ARCH V2 C.3; 010a D5)",
}


def _load_gen_constants():
    spec = importlib.util.spec_from_file_location(
        "gen_constants", Path(__file__).with_name("gen_constants.py")
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load gen_constants.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_ENUM_BASE_NAMES = frozenset({"Enum", "IntEnum", "StrEnum", "IntFlag", "Flag"})


def _target_names(target: ast.expr) -> list[str]:
    """Defined names of an assignment target (chained/tuple/starred aware)."""
    if isinstance(target, ast.Name):
        return [target.id]
    if isinstance(target, (ast.Tuple, ast.List)):
        names: list[str] = []
        for element in target.elts:
            names.extend(
                _target_names(element.value if isinstance(element, ast.Starred) else element)
            )
        return names
    return []  # attribute/subscript targets are not named constants


def _enum_class_nodes(tree: ast.Module) -> set[ast.ClassDef]:
    """ClassDef nodes subclassing enum.Enum directly or via an in-file base."""
    bases_by_name: dict[str, list[str]] = {}
    nodes: dict[str, ast.ClassDef] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            nodes.setdefault(node.name, node)
            bases_by_name[node.name] = [
                base.attr if isinstance(base, ast.Attribute) else base.id
                for base in node.bases
                if isinstance(base, (ast.Name, ast.Attribute))
            ]
    enum_names = {
        name for name, bases in bases_by_name.items() if any(b in _ENUM_BASE_NAMES for b in bases)
    }
    changed = True
    while changed:  # propagate enum-ness through in-file subclass chains
        changed = False
        for name, bases in bases_by_name.items():
            if name not in enum_names and any(b in enum_names for b in bases):
                enum_names.add(name)
                changed = True
    return {nodes[name] for name in enum_names}


def _enclosing_class(node: ast.AST, parents: dict[ast.AST, ast.AST]) -> ast.ClassDef | None:
    """Nearest ClassDef ancestor of node, or None at module/function level."""
    current = parents.get(node)
    while current is not None:
        if isinstance(current, ast.ClassDef):
            return current
        current = parents.get(current)
    return None


def scan_source_tree(root: Path, generated_names: set[str]) -> list[str]:
    """Flag duplicate AI.3 names and unsourced UPPER_SNAKE constants, any scope.

    Scans every assignment form in every scope (module, function, class);
    enum-class bodies are skipped because members are vocabulary literals, not
    constants. Only the canonical domain/constants.py is exempt (by path, not
    basename). Fail closed: anything new must be allowlisted or added to AI.3.
    """
    violations: list[str] = []
    for path in sorted(root.rglob("*.py")):
        if "__pycache__" in path.parts or path.resolve() == CONSTANTS_MODULE.resolve():
            continue
        tree = ast.parse(path.read_text(), filename=str(path))
        parents = {
            child: parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)
        }
        enum_classes = _enum_class_nodes(tree)
        for node in ast.walk(tree):
            targets: list[ast.expr]
            if isinstance(node, ast.Assign):
                targets = node.targets
            elif isinstance(node, ast.AnnAssign) and node.value is not None:
                targets = [node.target]
            else:
                continue  # bare annotations declare no value; not definitions
            enclosing = _enclosing_class(node, parents)
            if enclosing is not None and enclosing in enum_classes:
                continue  # enum members are vocabulary literals, not constants
            for name in (defined for target in targets for defined in _target_names(target)):
                if not UPPER_SNAKE.match(name):
                    continue
                if name in generated_names:
                    violations.append(
                        f"{path}:{node.lineno} duplicate of AI.3 constant {name} "
                        "(define once in domain/constants.py, reference by name)"
                    )
                elif name not in STRUCTURAL_ALLOWLIST:
                    violations.append(
                        f"{path}:{node.lineno} UPPER_SNAKE constant {name} not sourced "
                        "from ARCH V1 AI.3 (add to AI.3 or STRUCTURAL_ALLOWLIST)"
                    )
    return violations


def verify_no_drift(arch_path: Path, module_path: Path) -> list[str]:
    """Byte-compare committed constants.py against a fresh regeneration."""
    gen = _load_gen_constants()
    expected = gen.generate(arch_path).encode()
    actual = module_path.read_bytes()
    if expected == actual:
        return []
    parsed = {c.name: c.value for c in gen.parse_ai3_constants(arch_path.read_text())}
    committed: dict[str, object] = {}
    for node in ast.parse(module_path.read_text()).body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name):
                committed[target.id] = ast.literal_eval(node.value)
    drifted = sorted(n for n, v in parsed.items() if committed.get(n) != float(v))
    return [f"{module_path} drifted from AI.3; constants: {drifted}"]


def _module_assigned_names(module_path: Path) -> set[str]:
    """Module-level assignment target names in the generated constants module."""
    names: set[str] = set()
    for node in ast.parse(module_path.read_text()).body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name):
                names.add(target.id)
    return names


def verify_approval_companions(arch_path: Path, module_path: Path) -> list[str]:
    """Fail closed unless every AI.3 constant is approved or marked pending.

    005c Q5: a constant that is neither a value assignment (approved) nor
    carries a <NAME>_APPROVAL_PENDING companion is an orphan and fails.
    """
    gen = _load_gen_constants()
    entries = gen.parse_ai3_constants(arch_path.read_text())
    assigned = _module_assigned_names(module_path)
    violations: list[str] = []
    for entry in entries:
        companion = f"{entry.name}_APPROVAL_PENDING"
        if entry.approval_pending:
            if companion not in assigned:
                violations.append(
                    f"{module_path}: approval-pending constant {entry.name} "
                    f"is missing its {companion} companion"
                )
        elif entry.name not in assigned:
            violations.append(
                f"{module_path}: AI.3 constant {entry.name} is neither approved "
                f"(no value assignment) nor marked approval-pending ({companion}); "
                "add it to AI.3 or mark it pending"
            )
        elif companion in assigned:
            violations.append(
                f"{module_path}: approved constant {entry.name} unexpectedly "
                f"carries an {companion} companion"
            )
    return violations


def main() -> int:
    """Run drift + duplicate/unsourced checks over the repo; exit 1 on fail."""
    gen = _load_gen_constants()
    generated = {c.name for c in gen.parse_ai3_constants(ARCH_VOL1.read_text())}
    violations = verify_no_drift(ARCH_VOL1, CONSTANTS_MODULE)
    violations += verify_approval_companions(ARCH_VOL1, CONSTANTS_MODULE)
    violations += scan_source_tree(SRC_TREE, generated)
    for violation in violations:
        print(violation, file=sys.stderr)
    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
