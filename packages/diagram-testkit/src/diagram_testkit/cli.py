"""CLI entrypoint for diagram-testkit."""

import argparse
import sys
from pathlib import Path

from .checks import check_cluster_alignment, run_all_checks
from .parser import parse_svg


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="diagram-testkit",
        description="Lint SVG diagrams for quality issues",
    )
    sub = parser.add_subparsers(dest="command")

    lint_parser = sub.add_parser("lint", help="Check SVG files")
    lint_parser.add_argument("files", nargs="+", type=Path)
    lint_parser.add_argument(
        "--cluster-align",
        metavar="src=X,dst=Y",
        help="Check that cluster dst is centered below cluster src",
    )

    args = parser.parse_args()
    if args.command != "lint":
        parser.print_help()
        sys.exit(1)

    cluster_src = None
    cluster_dst = None
    if args.cluster_align:
        parts = dict(p.split("=") for p in args.cluster_align.split(","))
        cluster_src = parts.get("src")
        cluster_dst = parts.get("dst")
        if not cluster_src or not cluster_dst:
            print("Error: --cluster-align requires src=X,dst=Y")
            sys.exit(1)

    failed = False
    for svg_path in args.files:
        if not svg_path.exists():
            print(f"File not found: {svg_path}")
            failed = True
            continue

        svg = parse_svg(svg_path)
        errors = run_all_checks(svg)

        if cluster_src and cluster_dst:
            errors.extend(
                check_cluster_alignment(
                    svg, src=cluster_src, dst=cluster_dst
                )
            )

        if errors:
            print(f"FAIL: {svg_path}")
            for e in errors:
                print(f"  {e}")
            failed = True
        else:
            print(f"OK: {svg_path}")

    sys.exit(1 if failed else 0)
