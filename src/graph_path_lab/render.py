"""Draw a search on the map: text for terminals, PNG panels for the README.

The picture is the point of this project. Two algorithms can return the same path and still
differ by an order of magnitude in how much of the map they had to look at, and that is
invisible in a table of timings but obvious in a heat map.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .grid import GOAL, START, WALL, Grid
from .search import SearchResult

COLORS = {
    "background": (13, 17, 23),
    "free": (246, 248, 250),
    "wall": (31, 36, 48),
    "explored": (175, 208, 255),
    "path": (47, 158, 68),
    "start": (28, 126, 214),
    "goal": (232, 89, 12),
    "text": (230, 237, 243),
    "muted": (139, 148, 158),
}


def render_ascii(grid: Grid, result: SearchResult | None = None) -> str:
    explored = set(result.explored) if result else set()
    path = set(result.path) if result else set()
    lines: list[str] = []
    for y in range(grid.height):
        row: list[str] = []
        for x in range(grid.width):
            coord = (x, y)
            if grid.is_wall(coord):
                row.append(WALL)
            elif coord == grid.start:
                row.append(START)
            elif coord == grid.goal:
                row.append(GOAL)
            elif coord in path:
                row.append("*")
            elif coord in explored:
                row.append("o")
            else:
                row.append(".")
        lines.append("".join(row))
    return "\n".join(lines)


def _font(size: int) -> ImageFont.FreeTypeFont:
    for name in ("consola.ttf", "cour.ttf", "DejaVuSansMono.ttf"):
        candidate = Path("C:/Windows/Fonts") / name
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size)
    return ImageFont.load_default()


def render_png(
    grid: Grid,
    result: SearchResult | None = None,
    *,
    cell: int = 16,
    label: str | None = None,
) -> Image.Image:
    explored = set(result.explored) if result else set()
    path = set(result.path) if result else set()
    header = 26 if label else 4
    margin = 4
    width = grid.width * cell + margin * 2
    height = grid.height * cell + header + margin
    image = Image.new("RGB", (width, height), COLORS["background"])
    draw = ImageDraw.Draw(image)
    if label:
        draw.text((margin + 2, 5), label, font=_font(max(11, cell - 4)),
                  fill=COLORS["text"])

    for y in range(grid.height):
        for x in range(grid.width):
            coord = (x, y)
            if grid.is_wall(coord):
                color = COLORS["wall"]
            elif coord == grid.start:
                color = COLORS["start"]
            elif coord == grid.goal:
                color = COLORS["goal"]
            elif coord in path:
                color = COLORS["path"]
            elif coord in explored:
                color = COLORS["explored"]
            else:
                color = COLORS["free"]
            box = [margin + x * cell, header + y * cell,
                   margin + (x + 1) * cell - 1, header + (y + 1) * cell - 1]
            draw.rectangle(box, fill=color)
    return image


def render_comparison_png(
    grid: Grid,
    results: list[SearchResult],
    path: str | Path,
    *,
    columns: int = 3,
    cell: int = 14,
    title: str = "",
) -> Path:
    panels = [
        render_png(
            grid,
            result,
            cell=cell,
            label=f"{result.algorithm}  {result.expanded} expanded  "
            f"{result.cost:g} cost",
        )
        for result in results
    ]
    if not panels:
        raise ValueError("need at least one result to render")
    columns = max(1, min(columns, len(panels)))
    rows = (len(panels) + columns - 1) // columns
    panel_width = max(panel.width for panel in panels)
    panel_height = max(panel.height for panel in panels)
    gap = 10
    top = 34 if title else 0
    width = columns * panel_width + (columns + 1) * gap
    height = top + rows * panel_height + (rows + 1) * gap
    canvas = Image.new("RGB", (width, height), COLORS["background"])
    draw = ImageDraw.Draw(canvas)
    if title:
        draw.text((gap, 10), title, font=_font(16), fill=COLORS["text"])
    for index, panel in enumerate(panels):
        column = index % columns
        row = index // columns
        x = gap + column * (panel_width + gap)
        y = top + gap + row * (panel_height + gap)
        canvas.paste(panel, (x, y))

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(target)
    return target


def legend_png(path: str | Path, cell: int = 18) -> Path:
    """A small colour key, so the maps do not need a paragraph of explanation."""
    entries = [
        ("free", COLORS["free"]),
        ("wall", COLORS["wall"]),
        ("explored", COLORS["explored"]),
        ("path", COLORS["path"]),
        ("start", COLORS["start"]),
        ("goal", COLORS["goal"]),
    ]
    width = sum(len(name) for name, _ in entries) * 9 + 40 + len(entries) * cell
    image = Image.new("RGB", (width, 34), COLORS["background"])
    draw = ImageDraw.Draw(image)
    x = 8
    font = _font(13)
    for name, color in entries:
        draw.rectangle([x, 9, x + cell, 9 + cell], fill=color)
        x += cell + 6
        draw.text((x, 11), name, font=font, fill=COLORS["text"])
        x += int(draw.textlength(name, font=font)) + 14
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    image.save(target)
    return target


__all__ = [
    "COLORS",
    "GOAL",
    "START",
    "WALL",
    "legend_png",
    "render_ascii",
    "render_comparison_png",
    "render_png",
]
