"""The grid: a text map where a digit is the cost of entering that cell.

    ....#....
    ..S..2...
    ....#..G.

``.`` free (cost 1), ``#`` wall, ``S`` start, ``G`` goal, ``2``-``9`` terrain cost.
Keeping the format textual means a test case is a string literal and a bug report is a
map you can paste into a file.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

Coord = tuple[int, int]

WALL = "#"
FREE = "."
START = "S"
GOAL = "G"
DIRECTIONS = ((1, 0), (-1, 0), (0, 1), (0, -1))


class GridError(ValueError):
    """Raised when a map cannot be read or is not a valid grid."""


@dataclass(frozen=True)
class Grid:
    width: int
    height: int
    costs: tuple[tuple[int, ...], ...]
    start: Coord
    goal: Coord

    @classmethod
    def from_text(cls, text: str) -> Grid:
        rows = [line.rstrip("\n") for line in text.splitlines() if line.strip()]
        if not rows:
            raise GridError("map is empty")
        width = len(rows[0])
        if any(len(row) != width for row in rows):
            raise GridError("all rows must have the same width")
        costs: list[tuple[int, ...]] = []
        start: Coord | None = None
        goal: Coord | None = None
        for y, row in enumerate(rows):
            line: list[int] = []
            for x, char in enumerate(row):
                if char == WALL:
                    line.append(0)
                elif char == START:
                    if start is not None:
                        raise GridError("map has more than one start")
                    start = (x, y)
                    line.append(1)
                elif char == GOAL:
                    if goal is not None:
                        raise GridError("map has more than one goal")
                    goal = (x, y)
                    line.append(1)
                elif char == FREE:
                    line.append(1)
                elif char.isdigit():
                    value = int(char)
                    if value < 1:
                        raise GridError(f"cost {char} at {x},{y} is not enterable")
                    line.append(value)
                else:
                    raise GridError(f"unknown map character {char!r} at {x},{y}")
            costs.append(tuple(line))
        if start is None:
            raise GridError("map has no start")
        if goal is None:
            raise GridError("map has no goal")
        gap = max(abs(start[0] - goal[0]), abs(start[1] - goal[1]))
        if gap < 2:
            raise GridError("start and goal are too close to be a useful map")
        return cls(width=width, height=len(rows), costs=tuple(costs), start=start, goal=goal)

    @classmethod
    def load(cls, path: str | Path) -> Grid:
        source = Path(path)
        try:
            text = source.read_text(encoding="utf-8")
        except FileNotFoundError as exc:
            raise GridError(f"map not found: {source}") from exc
        return cls.from_text(text)

    def in_bounds(self, coord: Coord) -> bool:
        x, y = coord
        return 0 <= x < self.width and 0 <= y < self.height

    def cost(self, coord: Coord) -> int:
        x, y = coord
        if not self.in_bounds(coord):
            raise GridError(f"coordinate outside the grid: {coord}")
        return self.costs[y][x]

    def is_wall(self, coord: Coord) -> bool:
        return self.cost(coord) == 0

    def is_passable(self, coord: Coord) -> bool:
        return self.in_bounds(coord) and self.cost(coord) > 0

    def neighbors(self, coord: Coord) -> list[Coord]:
        x, y = coord
        return [
            (x + dx, y + dy)
            for dx, dy in DIRECTIONS
            if self.is_passable((x + dx, y + dy))
        ]

    @property
    def cells(self) -> int:
        return self.width * self.height

    @property
    def walls(self) -> int:
        return sum(1 for row in self.costs for value in row if value == 0)

    @property
    def weighted_cells(self) -> int:
        return sum(1 for row in self.costs for value in row if value > 1)

    @property
    def open_ratio(self) -> float:
        return round((self.cells - self.walls) / self.cells, 3)

    def to_text(self) -> str:
        lines: list[str] = []
        for y, row in enumerate(self.costs):
            chars: list[str] = []
            for x, value in enumerate(row):
                coord = (x, y)
                if value == 0:
                    chars.append(WALL)
                elif coord == self.start:
                    chars.append(START)
                elif coord == self.goal:
                    chars.append(GOAL)
                elif value > 1:
                    chars.append(str(value))
                else:
                    chars.append(FREE)
            lines.append("".join(chars))
        return "\n".join(lines)
