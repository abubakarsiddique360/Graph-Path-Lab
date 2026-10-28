import pytest

from graph_path_lab.grid import Grid, GridError

SIMPLE = """\
S..
.#.
..G
"""


def test_parses_free_walls_start_goal():
    grid = Grid.from_text(SIMPLE)
    assert (grid.width, grid.height) == (3, 3)
    assert grid.start == (0, 0)
    assert grid.goal == (2, 2)
    assert grid.is_wall((1, 1))
    assert grid.cost((0, 0)) == 1
    assert grid.walls == 1


def test_digits_are_terrain_cost():
    grid = Grid.from_text("S9.\n...\n..G")
    assert grid.cost((1, 0)) == 9
    assert grid.weighted_cells == 1


def test_neighbours_skip_walls_and_edges():
    grid = Grid.from_text(SIMPLE)
    assert sorted(grid.neighbors((0, 0))) == [(0, 1), (1, 0)]
    assert sorted(grid.neighbors((1, 1))) == [(0, 1), (1, 0), (1, 2), (2, 1)]
    assert (1, 1) not in grid.neighbors((0, 1))


def test_open_ratio_and_cells():
    grid = Grid.from_text(SIMPLE)
    assert grid.cells == 9
    assert grid.open_ratio == pytest.approx(0.889, abs=0.001)


def test_text_round_trip():
    grid = Grid.from_text(SIMPLE)
    assert grid.to_text() == SIMPLE.strip()
    assert Grid.from_text(grid.to_text()) == grid


@pytest.mark.parametrize(
    "text,message",
    [
        ("", "empty"),
        ("S..\n..G\n.\n", "same width"),
        ("...\n...\n...", "no start"),
        ("S..\n...\n...", "no goal"),
        ("SS.\n...\n..G", "more than one start"),
        ("S..\n...\nGG.", "more than one goal"),
        ("S?.\n...\n..G", "unknown map character"),
        ("SG.\n...\n...", "too close"),
    ],
)
def test_rejects_bad_maps(text, message):
    with pytest.raises(GridError, match=message):
        Grid.from_text(text)


def test_missing_file(tmp_path):
    with pytest.raises(GridError, match="not found"):
        Grid.load(tmp_path / "absent.txt")


def test_out_of_bounds_cost_is_an_error():
    grid = Grid.from_text(SIMPLE)
    with pytest.raises(GridError, match="outside"):
        grid.cost((9, 9))
    assert not grid.is_passable((9, 9))
