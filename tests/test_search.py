import pytest

from graph_path_lab.bench import SCENARIOS, open_field, run_all, run_scenario, summary
from graph_path_lab.grid import Grid
from graph_path_lab.search import ALGORITHMS, HEURISTICS, search

CORRIDOR = """\
S.......
######.#
#......#
#.######
#......G
"""

WEIGHTED = """\
S4......
......G.
"""

UNREACHABLE = """\
S.#
.#.
.#G
"""


def test_bfs_returns_the_shortest_path_in_steps():
    result = search(Grid.from_text(CORRIDOR), "bfs")
    assert result.found
    assert result.steps == 21
    assert result.cost == 21.0
    assert result.path[0] == (0, 0)
    assert result.path[-1] == (7, 4)
    assert len(result.path) == result.steps + 1


def test_all_algorithms_agree_on_an_unweighted_map():
    grid = Grid.from_text(CORRIDOR)
    costs = {algorithm: search(grid, algorithm).cost for algorithm in ALGORITHMS}
    assert len(set(costs.values())) == 1


def test_dijkstra_and_astar_are_optimal_on_weighted_terrain():
    grid = Grid.from_text(WEIGHTED)
    dijkstra = search(grid, "dijkstra")
    astar = search(grid, "astar")
    assert dijkstra.cost == astar.cost == 7.0
    # Same number of steps, three units more expensive: step count is not cost.
    assert search(grid, "bfs").steps == dijkstra.steps == 7
    assert search(grid, "bfs").cost == 10.0


def test_greedy_is_fast_but_not_always_optimal():
    grid = Grid.from_text(WEIGHTED)
    greedy = search(grid, "greedy")
    dijkstra = search(grid, "dijkstra")
    assert greedy.expanded <= dijkstra.expanded
    assert greedy.cost > dijkstra.cost


def test_astar_expands_far_less_than_bfs_on_open_ground():
    grid = open_field(31, 21)
    bfs = search(grid, "bfs")
    astar = search(grid, "astar")
    assert astar.cost == bfs.cost
    assert astar.expanded * 5 < bfs.expanded


def test_weighted_astar_trades_cost_for_speed():
    grid = Grid.from_text(CORRIDOR)
    exact = search(grid, "astar")
    fast = search(grid, "astar", weight=3.0)
    assert fast.expanded <= exact.expanded
    assert fast.cost >= exact.cost
    assert fast.algorithm == "astar w=3"


def test_unreachable_goal_is_reported():
    result = search(Grid.from_text(UNREACHABLE), "astar")
    assert not result.found
    assert result.path == ()
    assert result.cost == float("inf")
    assert result.expanded > 0


def test_euphoria_and_zero_heuristics_are_available():
    grid = Grid.from_text(CORRIDOR)
    assert set(HEURISTICS) == {"manhattan", "euclidean", "zero"}
    assert search(grid, "astar", heuristic="euclidean").cost == search(grid, "astar").cost
    assert search(grid, "astar", heuristic="zero").cost == search(grid, "astar").cost


def test_unknown_inputs_are_rejected():
    grid = Grid.from_text(CORRIDOR)
    with pytest.raises(ValueError, match="unknown algorithm"):
        search(grid, "best")
    with pytest.raises(ValueError, match="unknown heuristic"):
        search(grid, "astar", heuristic="chebyshev")
    with pytest.raises(ValueError, match="weight"):
        search(grid, "astar", weight=0.5)
    with pytest.raises(ValueError, match="greedy"):
        search(grid, "greedy", heuristic="zero")


def test_results_are_deterministic():
    grid = SCENARIOS["maze"]()
    first = search(grid, "astar")
    second = search(grid, "astar")
    assert first.path == second.path
    assert first.expanded == second.expanded


def test_result_serialises_without_the_explored_set():
    result = search(SCENARIOS["bottleneck"](), "dijkstra")
    payload = result.as_dict()
    assert "explored" not in payload
    assert payload["steps"] == len(payload["path"]) - 1
    assert payload["cost"] == result.cost


def test_every_builtin_scenario_is_solvable():
    for name, factory in SCENARIOS.items():
        grid = factory()
        result = search(grid, "dijkstra")
        assert result.found, name


def test_run_scenario_and_summary():
    results = run_scenario(SCENARIOS["bottleneck"](), ("bfs", "astar"))
    assert [item.algorithm for item in results] == ["bfs", "astar"]
    totals = summary({"bottleneck": results})
    assert totals["scenarios"] == 1
    assert totals["runs"] == 2
    assert totals["results"][0]["scenario"] == "bottleneck"


def test_run_all_covers_requested_scenarios():
    results = run_all(("bfs",), ("open field", "maze"))
    assert set(results) == {"open field", "maze"}
    assert all(len(items) == 1 for items in results.values())
