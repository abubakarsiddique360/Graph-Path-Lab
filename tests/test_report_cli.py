import json

import pytest

from graph_path_lab.bench import SCENARIOS, run_scenario
from graph_path_lab.cli import main
from graph_path_lab.grid import Grid
from graph_path_lab.render import legend_png, render_ascii, render_comparison_png, render_png
from graph_path_lab.report import render_json, render_markdown, render_single, render_text
from graph_path_lab.search import search

MAZE = """\
S......
######.
.......
.######
......G
"""


@pytest.fixture()
def map_file(tmp_path):
    path = tmp_path / "maze.txt"
    path.write_text(MAZE, encoding="utf-8")
    return path


@pytest.fixture()
def grid():
    return Grid.from_text(MAZE)


def test_ascii_shows_path_and_explored(grid):
    text = render_ascii(grid, search(grid, "astar"))
    assert "*" in text
    assert "S" in text and "G" in text and "#" in text
    assert text.count("\n") == grid.height - 1


def test_png_is_written(grid, tmp_path):
    from PIL import Image

    out = tmp_path / "map.png"
    render_png(grid, search(grid, "bfs")).save(out)
    assert out.exists()
    with Image.open(out) as image:
        assert image.width > grid.width
        assert image.height > grid.height


def test_comparison_png_layout(grid, tmp_path):
    from PIL import Image

    results = run_scenario(grid, ("bfs", "astar", "bfs"))
    out = render_comparison_png(grid, results, tmp_path / "cmp.png", columns=3,
                               title="comparison")
    with Image.open(out) as image:
        assert image.width > 3 * grid.width
        assert image.height > grid.height


def test_legend_and_empty_guard(grid, tmp_path):
    out = legend_png(tmp_path / "legend.png")
    assert out.exists()
    with pytest.raises(ValueError, match="at least one"):
        render_comparison_png(grid, [], tmp_path / "none.png")


def test_text_report_lists_every_algorithm(grid):
    results = {"maze": run_scenario(grid, ("bfs", "astar"))}
    text = render_text(results)
    assert "maze" in text
    assert "bfs" in text and "astar" in text
    assert "expanded" in text


def test_markdown_and_json_reports(grid):
    results = {"maze": run_scenario(grid, ("bfs", "astar"))}
    markdown = render_markdown(results)
    assert "| Scenario | Algorithm |" in markdown
    payload = json.loads(render_json(results))
    assert payload["runs"] == 2


def test_single_report_can_embed_the_map(grid):
    result = search(grid, "astar")
    text = render_single(result, grid_text=render_ascii(grid, result))
    assert "algorithm   astar" in text
    assert "*" in text


def test_cli_solve(map_file, tmp_path, capsys):
    png = tmp_path / "solved.png"
    code = main(["solve", "--map", str(map_file), "--algorithm", "astar", "--ascii",
                 "--png", str(png)])
    output = capsys.readouterr().out
    assert code == 0
    assert "path        22 steps" in output
    assert "*" in output
    assert png.exists()


def test_cli_compare_json_and_png(map_file, tmp_path, capsys):
    png = tmp_path / "compare.png"
    code = main(["compare", "--map", str(map_file), "--algorithms", "bfs,astar",
                 "--format", "json", "--png", str(png)])
    payload = json.loads(capsys.readouterr().out)
    assert code == 0
    assert len(payload["results"]) == 2
    assert png.exists()


def test_cli_bench_markdown(capsys):
    assert main(["bench", "--scenarios", "maze", "--algorithms", "bfs,astar",
                 "--format", "markdown"]) == 0
    assert "| Scenario | Algorithm |" in capsys.readouterr().out


def test_cli_maps_listing_and_show(capsys):
    assert main(["maps"]) == 0
    listing = capsys.readouterr().out
    assert "open field" in listing
    assert main(["maps", "--show", "maze"]) == 0
    assert "S" in capsys.readouterr().out
    assert main(["maps", "--show", "nope"]) == 2


def test_cli_rejects_unknown_algorithm_name(map_file, capsys):
    assert main(["compare", "--map", str(map_file), "--algorithms", "bfs,best"]) == 2
    assert "unknown algorithm" in capsys.readouterr().err


def test_cli_rejects_bad_map(tmp_path, capsys):
    bad = tmp_path / "bad.txt"
    bad.write_text("no start or goal", encoding="utf-8")
    assert main(["solve", "--map", str(bad)]) == 2
    assert "map error" in capsys.readouterr().err


def test_cli_solve_unreachable_exits_one(tmp_path, capsys):
    blocked = tmp_path / "blocked.txt"
    blocked.write_text("S.#\n.#.\n.#G", encoding="utf-8")
    assert main(["solve", "--map", str(blocked)]) == 1
    assert "no path exists" in capsys.readouterr().out


def test_builtin_scenarios_are_drawable():
    for factory in SCENARIOS.values():
        grid = factory()
        assert render_ascii(grid).count("\n") == grid.height - 1
