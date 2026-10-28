"""Five search strategies, one loop, one result type.

The interesting comparisons in pathfinding are not "which is fastest" but "how much of the
map did it have to look at". Every function here returns the same ``SearchResult``, so a
benchmark can put BFS next to weighted A* without special cases.
"""

from __future__ import annotations

import heapq
import itertools
import time
from dataclasses import dataclass

from .grid import Coord, Grid

ALGORITHMS = ("bfs", "dfs", "dijkstra", "greedy", "astar")
DEFAULT_ALGORITHM = "astar"


@dataclass(frozen=True)
class SearchResult:
    algorithm: str
    found: bool
    path: tuple[Coord, ...]
    cost: float
    expanded: int
    frontier_peak: int
    elapsed_ms: float
    explored: tuple[Coord, ...] = ()

    @property
    def steps(self) -> int:
        return max(0, len(self.path) - 1)

    def as_dict(self) -> dict:
        return {
            "algorithm": self.algorithm,
            "found": self.found,
            "steps": self.steps,
            "cost": round(self.cost, 3),
            "expanded": self.expanded,
            "frontier_peak": self.frontier_peak,
            "elapsed_ms": round(self.elapsed_ms, 4),
            "path": [list(coord) for coord in self.path],
        }


def manhattan(a: Coord, b: Coord) -> float:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def euclidean(a: Coord, b: Coord) -> float:
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5


def zero(_a: Coord, _b: Coord) -> float:
    return 0.0


HEURISTICS = {"manhattan": manhattan, "euclidean": euclidean, "zero": zero}


def search(
    grid: Grid,
    algorithm: str = DEFAULT_ALGORITHM,
    *,
    weight: float = 1.0,
    heuristic: str = "manhattan",
) -> SearchResult:
    """Run one algorithm. ``weight > 1`` only affects A* (weighted A*, faster but suboptimal)."""
    if algorithm not in ALGORITHMS:
        raise ValueError(f"unknown algorithm {algorithm!r}; choose from {', '.join(ALGORITHMS)}")
    if heuristic not in HEURISTICS:
        raise ValueError(f"unknown heuristic {heuristic!r}; choose from {', '.join(HEURISTICS)}")
    if weight < 1.0:
        raise ValueError("weight must be >= 1.0")
    if algorithm == "greedy" and heuristic == "zero":
        # Greedy with a zero heuristic degenerates into a stack walk; refuse it rather than
        # produce a number that looks like a result.
        raise ValueError("greedy search needs a real heuristic")

    h = HEURISTICS[heuristic]
    label = algorithm if algorithm != "astar" or weight == 1.0 else f"astar w={weight:g}"
    tie = itertools.count()
    goal = grid.goal
    started = time.perf_counter()

    first_key = _key(algorithm, 0, weight, h, grid.start, goal, next(tie))
    frontier: list[tuple] = [(*first_key, grid.start)]
    best: dict[Coord, float] = {grid.start: 0.0}
    came_from: dict[Coord, Coord] = {}
    closed: set[Coord] = set()
    order: list[Coord] = []
    expanded = 0
    peak = 1
    found = False

    while frontier:
        current = heapq.heappop(frontier)[-1]
        if current in closed:
            continue
        closed.add(current)
        order.append(current)
        expanded += 1
        if current == goal:
            found = True
            break

        for neighbour in grid.neighbors(current):
            if neighbour in closed:
                continue
            if algorithm in ("bfs", "dfs"):
                step = best[current] + 1.0
            else:
                step = best[current] + grid.cost(neighbour)
            known = best.get(neighbour)
            if known is not None and known <= step:
                continue
            best[neighbour] = step
            came_from[neighbour] = current
            key = _key(algorithm, step, weight, h, neighbour, goal, next(tie))
            heapq.heappush(frontier, (*key, neighbour))
            peak = max(peak, len(frontier))

    elapsed = (time.perf_counter() - started) * 1000
    if not found:
        return SearchResult(label, False, (), float("inf"), expanded, peak, elapsed,
                            tuple(order))

    path = [goal]
    while path[-1] != grid.start:
        path.append(came_from[path[-1]])
    path.reverse()
    cost = float(sum(grid.cost(cell) for cell in path[1:]))
    return SearchResult(label, True, tuple(path), cost, expanded, peak, elapsed, tuple(order))


def _key(
    algorithm: str,
    step: float,
    weight: float,
    heuristic,
    node: Coord,
    goal: Coord,
    tie: int,
) -> tuple[float, ...]:
    """Ordering key. Ties are broken toward the goal so A* does not flood an open field."""
    estimate = float(heuristic(node, goal))
    if algorithm == "bfs":
        return (step, tie)
    if algorithm == "dfs":
        return (-float(tie),)
    if algorithm == "greedy":
        return (estimate, tie)
    if algorithm == "dijkstra":
        return (step, tie)
    return (step + weight * estimate, estimate, tie)
