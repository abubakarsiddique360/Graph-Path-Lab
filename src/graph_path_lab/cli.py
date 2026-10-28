"""Command line entry point for ``graph-path``."""

from __future__ import annotations

import argparse
import sys

from . import __version__
from .bench import DEFAULT_ALGORITHMS, SCENARIOS, run_all, run_scenario
from .grid import Grid, GridError
from .render import render_ascii, render_comparison_png, render_png
from .report import render_json, render_markdown, render_single, render_text
from .search import ALGORITHMS, search


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="graph-path",
        description="Compare pathfinding algorithms on a character grid.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    solve = sub.add_parser("solve", help="run one algorithm on one map")
    solve.add_argument("--map", required=True)
    solve.add_argument("--algorithm", choices=ALGORITHMS, default="astar")
    solve.add_argument("--heuristic", default="manhattan")
    solve.add_argument("--weight", type=float, default=1.0)
    solve.add_argument("--ascii", action="store_true", help="draw the explored set as text")
    solve.add_argument("--png", help="write the explored set as a PNG")

    compare = sub.add_parser("compare", help="run every algorithm on one map")
    compare.add_argument("--map", required=True)
    compare.add_argument("--algorithms", default=",".join(DEFAULT_ALGORITHMS))
    compare.add_argument("--format", choices=("text", "markdown", "json"), default="text")
    compare.add_argument("--png", help="write a panel image, one algorithm per panel")

    bench = sub.add_parser("bench", help="run every algorithm on the built-in scenarios")
    bench.add_argument("--scenarios", default=",".join(SCENARIOS))
    bench.add_argument("--algorithms", default=",".join(DEFAULT_ALGORITHMS))
    bench.add_argument("--format", choices=("text", "markdown", "json"), default="text")
    bench.add_argument("--png", help="write a panel image for the maze scenario")

    maps = sub.add_parser("maps", help="list the built-in scenarios")
    maps.add_argument("--show", help="print one scenario as a map")
    return parser


def _load_map(path: str) -> Grid | None:
    try:
        return Grid.load(path)
    except GridError as exc:
        print(f"map error: {exc}", file=sys.stderr)
        return None


def _parse_list(raw: str, allowed: tuple[str, ...], label: str) -> tuple[str, ...] | None:
    items = tuple(part.strip() for part in raw.split(",") if part.strip())
    if not items:
        print(f"error: {label} list is empty", file=sys.stderr)
        return None
    unknown = [item for item in items if item not in allowed]
    if unknown:
        print(f"error: unknown {label}: {', '.join(unknown)}", file=sys.stderr)
        return None
    return items


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    if args.command == "maps":
        if args.show:
            if args.show not in SCENARIOS:
                print(f"unknown scenario: {args.show}", file=sys.stderr)
                print("known: " + ", ".join(SCENARIOS), file=sys.stderr)
                return 2
            print(SCENARIOS[args.show]().to_text())
            return 0
        for name, factory in SCENARIOS.items():
            grid = factory()
            print(
                f"{name:<18} {grid.width:>3}x{grid.height:<3} "
                f"{grid.walls:>4} walls   {grid.weighted_cells:>3} weighted   "
                f"open {grid.open_ratio:.0%}"
            )
        return 0

    if args.command == "bench":
        names = _parse_list(args.scenarios, tuple(SCENARIOS), "scenario")
        algorithms = _parse_list(args.algorithms, ALGORITHMS, "algorithm")
        if names is None or algorithms is None:
            return 2
        results = run_all(algorithms, names)
        _emit(results, args.format)
        if args.png:
            render_comparison_png(
                SCENARIOS["maze"](),
                results["maze"],
                args.png,
                title="maze: explored cells per algorithm",
            )
            print(f"wrote {args.png}", file=sys.stderr)
        return 0

    grid = _load_map(args.map)
    if grid is None:
        return 2

    if args.command == "solve":
        try:
            result = search(grid, args.algorithm, weight=args.weight,
                            heuristic=args.heuristic)
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        text = render_ascii(grid, result) if args.ascii else None
        print(render_single(result, grid_text=text))
        if args.png:
            render_png(grid, result, label=f"{result.algorithm} on {args.map}").save(args.png)
            print(f"wrote {args.png}", file=sys.stderr)
        return 0 if result.found else 1

    if args.command == "compare":
        algorithms = _parse_list(args.algorithms, ALGORITHMS, "algorithm")
        if algorithms is None:
            return 2
        results = run_scenario(grid, algorithms)
        _emit({args.map: results}, args.format)
        if args.png:
            render_comparison_png(grid, results, args.png,
                                  title=f"{args.map}: explored cells per algorithm")
            print(f"wrote {args.png}", file=sys.stderr)
        return 0 if all(result.found for result in results) else 1

    return 2


def _emit(results, fmt: str) -> None:
    if fmt == "json":
        print(render_json(results))
    elif fmt == "markdown":
        print(render_markdown(results))
    else:
        print(render_text(results))
