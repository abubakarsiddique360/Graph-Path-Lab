"""Regenerate README assets from real runs.

Usage:  python scripts/render_assets.py
Writes: docs/benchmark.json, docs/images/bench-table.png,
        docs/images/explored-weighted.png, docs/images/nodes-expanded.svg
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from graph_path_lab.bench import SCENARIOS, run_all, run_scenario  # noqa: E402
from graph_path_lab.render import render_comparison_png  # noqa: E402
from graph_path_lab.report import render_text  # noqa: E402

BG = "#0d1117"
CHROME = "#161b22"
FG = "#e6edf3"
MUTED = "#8b949e"
ALGORITHM_COLORS = {
    "bfs": "#2f81f7",
    "dfs": "#a371f7",
    "dijkstra": "#3fb950",
    "greedy": "#d29922",
    "astar": "#f85149",
}
SHOWN = ("open field", "bottleneck", "weighted terrain")


def load_font(size: int) -> ImageFont.FreeTypeFont:
    for name in ("consola.ttf", "cour.ttf", "DejaVuSansMono.ttf"):
        candidate = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts" / name
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size)
    return ImageFont.load_default()


def render_terminal(text: str, out_path: Path, title: str) -> None:
    font = load_font(16)
    lines = text.expandtabs(4).splitlines() or [""]
    probe = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    char_width = probe.textlength("M", font=font)
    line_height = 23
    pad = 24
    width = int(max(len(line) for line in lines) * char_width) + pad * 2
    height = pad * 2 + len(lines) * line_height + 44
    image = Image.new("RGB", (max(width, 700), height), BG)
    draw = ImageDraw.Draw(image)
    draw.rectangle([0, 0, image.width, 34], fill=CHROME)
    for index, color in enumerate(("#ff5f56", "#ffbd2e", "#27c93f")):
        draw.ellipse([16 + index * 22, 10, 28 + index * 22, 22], fill=color)
    draw.text((92, 9), title, font=load_font(13), fill=MUTED)

    for row, line in enumerate(lines):
        color = FG
        stripped = line.strip()
        if row == 0:
            color = "#79c0ff"
        elif stripped.startswith(("bfs", "dfs", "dijkstra", "greedy", "astar")):
            name = stripped.split()[0]
            color = ALGORITHM_COLORS.get(name, FG)
        elif stripped and not stripped[0].isdigit() and "expanded" not in stripped:
            color = "#79c0ff"
        elif "expanded" in stripped:
            color = MUTED
        draw.text((pad, 50 + row * line_height), line, font=font, fill=color)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(out_path)


def render_bars(results: dict, out_path: Path) -> None:
    scenarios = list(results)
    algorithms = [item.algorithm for item in next(iter(results.values()))]
    height = 0.8 / len(algorithms)
    positions = range(len(scenarios))

    fig, ax = plt.subplots(figsize=(10.6, 4.2))
    fig.patch.set_facecolor("#ffffff")
    for index, algorithm in enumerate(algorithms):
        values = [next(r for r in results[s] if r.algorithm == algorithm).expanded
                  for s in scenarios]
        offsets = [p + index * height - 0.4 + height / 2 for p in positions]
        bars = ax.barh(offsets, values, height=height,
                       color=ALGORITHM_COLORS.get(algorithm, "#57606a"), label=algorithm)
        for bar, value in zip(bars, values, strict=True):
            ax.text(value * 1.06, bar.get_y() + bar.get_height() / 2, f"{value}",
                    va="center", fontsize=7, color="#24292f")
    ax.set_yticks(list(positions))
    ax.set_yticklabels(scenarios, fontsize=9)
    ax.set_xscale("log")
    ax.set_xlabel("nodes expanded before the goal was reached (log scale)")
    ax.set_title("Same answers, very different amounts of work", fontsize=11, loc="left")
    ax.legend(fontsize=8, frameon=False, ncol=5, loc="lower right")
    ax.grid(axis="x", which="both", linestyle=":", alpha=0.45)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, format=out_path.suffix.lstrip(".") or "svg", transparent=False)
    plt.close(fig)


def main() -> int:
    images = ROOT / "docs" / "images"
    images.mkdir(parents=True, exist_ok=True)

    results = run_all(scenarios=SHOWN)
    payload = {
        "scenarios": {
            name: [item.as_dict() for item in items] for name, items in results.items()
        }
    }
    (ROOT / "docs" / "benchmark.json").write_text(json.dumps(payload, indent=2),
                                                  encoding="utf-8")

    header = (
        "graph-path bench --scenarios \"open field,bottleneck,weighted terrain\"\n\n"
    )
    render_terminal(header + render_text(results), images / "bench-table.png",
                    "graph-path bench  -  five strategies on three maps")

    weighted = SCENARIOS["weighted terrain"]()
    render_comparison_png(
        weighted,
        run_scenario(weighted),
        images / "explored-weighted.png",
        columns=3,
        cell=26,
        title="weighted terrain: chevrons are explored cells, green is the path",
    )
    render_bars(results, images / "nodes-expanded.svg")

    maze = SCENARIOS["maze"]()
    print(
        "open field astar/bfs = "
        f"{next(r for r in results['open field'] if r.algorithm == 'astar').expanded}/"
        f"{next(r for r in results['open field'] if r.algorithm == 'bfs').expanded}; "
        "weighted best cost = "
        f"{min(r.cost for r in results['weighted terrain'])}; "
        f"maze open ratio {maze.open_ratio}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
