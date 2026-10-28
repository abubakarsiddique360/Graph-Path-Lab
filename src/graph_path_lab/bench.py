"""Scenario maps used by the benchmark, defined in code so they cannot go stale."""

from __future__ import annotations

from collections.abc import Callable

from .grid import Grid
from .search import SearchResult, search

DEFAULT_ALGORITHMS = ("bfs", "dfs", "dijkstra", "greedy", "astar")

MAZE = """\
####################
#S...#.............#
#.##.#.###########.#
#.#..#.#.........#.#
#.#.##.#.#######.#.#
#.#....#.#.....#.#.#
#.######.#.###.#.#.#
#........#.#.#.#.#.#
########.#.#.#.#.#.#
#........#.#.#...#.#
#.########.#.#####.#
#..........#......G#
####################
"""

BOTTLENECK = """\
....................
....................
....................
.........#..........
.........#..........
.........#..........
........S#G.........
.........#..........
.........#..........
....................
....................
"""

WEIGHTED = """\
S..2....9....2......
.22....999...2......
..2.....9....2..3...
..222..99...22..3...
.....2.9....2...3...
......29....2...3...
.......9....2.......
.......999992.......
....................
.................G..
"""


def open_field(width: int = 31, height: int = 21) -> Grid:
    rows = ["." * width for _ in range(height)]
    rows[0] = "S" + rows[0][1:]
    rows[-1] = rows[-1][:-1] + "G"
    return Grid.from_text("\n".join(rows))


def maze() -> Grid:
    return Grid.from_text(MAZE)


def bottleneck() -> Grid:
    return Grid.from_text(BOTTLENECK)


def weighted() -> Grid:
    return Grid.from_text(WEIGHTED)


SCENARIOS: dict[str, Callable[[], Grid]] = {
    "open field": open_field,
    "maze": maze,
    "bottleneck": bottleneck,
    "weighted terrain": weighted,
}


def run_scenario(
    grid: Grid, algorithms: tuple[str, ...] = DEFAULT_ALGORITHMS
) -> list[SearchResult]:
    return [search(grid, algorithm) for algorithm in algorithms]


def run_all(
    algorithms: tuple[str, ...] = DEFAULT_ALGORITHMS,
    scenarios: tuple[str, ...] | None = None,
) -> dict[str, list[SearchResult]]:
    names = scenarios or tuple(SCENARIOS)
    return {name: run_scenario(SCENARIOS[name](), algorithms) for name in names}


def summary(results: dict[str, list[SearchResult]]) -> dict:
    rows: list[dict] = []
    for scenario, scenario_results in results.items():
        for result in scenario_results:
            rows.append({"scenario": scenario, **result.as_dict()})
    return {"scenarios": len(results), "runs": len(rows), "results": rows}
