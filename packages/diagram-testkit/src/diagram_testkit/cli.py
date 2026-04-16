"""CLI entrypoint for diagram-testkit."""

import argparse
import sys
from pathlib import Path

from diagram_testkit.checks import check_container_alignment
from diagram_testkit.checks import run_all_checks_with_file
from diagram_testkit.extractors import extract
from diagram_testkit.model import Format


def _parse_cluster_align(raw: str) -> tuple[str, str]:
    parts = dict(p.split("=") for p in raw.split(","))
    src, dst = parts.get("src"), parts.get("dst")
    if not src or not dst:
        print("Error: --cluster-align requires src=X,dst=Y")  # noqa: T201
        sys.exit(1)
    return src, dst


def _lint_file(
    svg_path: Path,
    *,
    fmt: Format | None,
    cluster_align: tuple[str, str] | None,
) -> bool:
    if not svg_path.exists():
        print(f"File not found: {svg_path}")  # noqa: T201
        return True

    elems = extract(svg_path, format=fmt)
    errors = run_all_checks_with_file(elems, svg_path)

    if cluster_align:
        errors.extend(
            check_container_alignment(elems, src=cluster_align[0], dst=cluster_align[1])
        )

    if errors:
        print(f"FAIL: {svg_path}")  # noqa: T201
        for e in errors:
            print(f"  {e}")  # noqa: T201
        return True

    print(f"OK: {svg_path}")  # noqa: T201
    return False


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="diagram-testkit",
        description="Lint SVG diagrams for quality issues",
    )
    sub = parser.add_subparsers(dest="command")

    lint_parser = sub.add_parser("lint", help="Check SVG files")
    lint_parser.add_argument("files", nargs="+", type=Path)
    lint_parser.add_argument(
        "--format",
        choices=[f.value for f in Format],
        help="Override format auto-detection",
    )
    lint_parser.add_argument(
        "--cluster-align",
        metavar="src=X,dst=Y",
        help="Check that container dst is centered below container src",
    )

    args = parser.parse_args()
    if args.command != "lint":
        parser.print_help()  # noqa: T201
        sys.exit(1)

    fmt = Format(args.format) if args.format else None
    cluster_align = _parse_cluster_align(args.cluster_align) if args.cluster_align else None

    results = [_lint_file(p, fmt=fmt, cluster_align=cluster_align) for p in args.files]
    failed = any(results)
    sys.exit(1 if failed else 0)
