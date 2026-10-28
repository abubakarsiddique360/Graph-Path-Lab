"""Graph-Path-Lab: compare pathfinding algorithms on the same grid."""

from .bench import DEFAULT_ALGORITHMS, SCENARIOS, run_all, run_scenario
from .grid import Coord, Grid, GridError
from .render import render_ascii, render_comparison_png
from .search import HEURISTICS, SearchResult, search

__all__ = [
    "DEFAULT_ALGORITHMS",
    "HEURISTICS",
    "SCENARIOS",
    "Coord",
    "Grid",
    "GridError",
    "SearchResult",
    "render_ascii",
    "render_comparison_png",
    "run_all",
    "run_scenario",
    "search",
]

__version__ = "1.0.0"
