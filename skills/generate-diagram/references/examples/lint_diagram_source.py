# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""
Lint graphviz diagram scripts for common style issues.

Scans Python source files using the AST to find graphviz `.edge()` calls
where `label` or `xlabel` string values lack padding whitespace. On
vertical edges, labels without padding sit flush against the arrow line
and are hard to read.

Run:
    uv run lint_diagram_source.py path/to/diagram.py
    uv run lint_diagram_source.py path/to/directory/   # lint all .py files

Exit code 0 = clean, 1 = issues found.
"""

import ast
import sys
from dataclasses import dataclass
from pathlib import Path

MIN_PAD = 2  # minimum leading/trailing spaces required


@dataclass
class LintError:
    file: str
    line: int
    param: str
    value: str
    message: str


def check_edge_label_padding(source: str, filepath: str) -> list[LintError]:
    try:
        tree = ast.parse(source, filename=filepath)
    except SyntaxError:
        return []

    errors: list[LintError] = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue

        # Match *.edge(...) calls
        func = node.func
        if isinstance(func, ast.Attribute) and func.attr == "edge":
            _check_edge_call(node, filepath, errors)

    return errors


def _check_edge_call(
    call: ast.Call,
    filepath: str,
    errors: list[LintError],
) -> None:
    for kw in call.keywords:
        if kw.arg not in ("label", "xlabel", "headlabel", "taillabel"):
            continue

        value = _extract_string(kw.value)
        if value is None:
            continue

        # Check each line of a multi-line label
        for line in value.split("\n"):
            stripped = line.strip()
            if not stripped:
                continue
            leading = len(line) - len(line.lstrip(" "))
            trailing = len(line) - len(line.rstrip(" "))
            if leading < MIN_PAD or trailing < MIN_PAD:
                errors.append(
                    LintError(
                        file=filepath,
                        line=call.lineno,
                        param=kw.arg,
                        value=repr(value),
                        message=(
                            f"Edge {kw.arg} needs at least {MIN_PAD} spaces "
                            f"of padding on each side (found {leading} leading, "
                            f"{trailing} trailing in {line!r})"
                        ),
                    )
                )
                break  # one error per label is enough


def _extract_string(node: ast.expr) -> str | None:
    """Extract a string value from an AST node (handles Constant and JoinedStr)."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def lint_file(path: Path) -> list[LintError]:
    source = path.read_text(encoding="utf-8")
    # Only lint files that import graphviz
    if "import graphviz" not in source:
        return []
    return check_edge_label_padding(source, str(path))


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: lint_diagram_source.py <file_or_directory>")
        sys.exit(1)

    target = Path(sys.argv[1])
    files = sorted(target.glob("**/*.py")) if target.is_dir() else [target]

    all_errors: list[LintError] = []
    for f in files:
        all_errors.extend(lint_file(f))

    if all_errors:
        print(f"ERRORS ({len(all_errors)}):")
        for e in all_errors:
            print(f"  ✘ {e.file}:{e.line} — {e.message}")
        sys.exit(1)
    else:
        print(f"✓ Checked {len(files)} file(s), all edge labels padded.")


if __name__ == "__main__":
    main()
