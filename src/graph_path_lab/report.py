"""Tables of results: one scenario per block, one algorithm per row."""

from __future__ import annotations

import json

from .bench import summary
from .search import SearchResult

ORDER = ("bfs", "dfs", "dijkstra", "greedy", "astar")


def _row(result: SearchResult) -> str:
    state = "ok" if result.found else "unreachable"
    return (
        f"  {result.algorithm:<14}{result.expanded:>8}{result.frontier_peak:>9}"
        f"{result.cost:>9.1f}{result.steps:>7}{result.elapsed_ms:>9.3f}  {state}"
    )


def render_text(results: dict[str, list[SearchResult]], *, title: str = "Path search") -> str:
    lines = [title, "=" * 66]
    lines.append(
        f"{'':<16}{'expanded':>8}{'peak':>9}{'cost':>9}{'steps':>7}{'ms':>9}"
    )
    for scenario, scenario_results in results.items():
        lines.append("")
        lines.append(f"{scenario}")
        for result in scenario_results:
            lines.append(_row(result))
    return "\n".join(lines)


def render_markdown(results: dict[str, list[SearchResult]]) -> str:
    lines = ["### Path search comparison", ""]
    lines.append("| Scenario | Algorithm | Expanded | Frontier peak | Cost | Steps | ms |")
    lines.append("| --- | --- | ---: | ---: | ---: | ---: | ---: |")
    for scenario, scenario_results in results.items():
        for result in scenario_results:
            cost = f"{result.cost:.0f}" if result.found else "unreachable"
            lines.append(
                f"| {scenario} | `{result.algorithm}` | {result.expanded} | "
                f"{result.frontier_peak} | {cost} | {result.steps} | "
                f"{result.elapsed_ms:.3f} |"
            )
    return "\n".join(lines)


def render_json(results: dict[str, list[SearchResult]]) -> str:
    return json.dumps(summary(results), indent=2)


def render_single(result: SearchResult, *, grid_text: str | None = None) -> str:
    lines = [f"algorithm   {result.algorithm}"]
    if not result.found:
        lines.append("result      no path exists")
    else:
        lines.append(f"path        {result.steps} steps, cost {result.cost:g}")
    lines.append(f"expanded    {result.expanded} nodes")
    lines.append(f"peak        {result.frontier_peak} nodes in the frontier")
    lines.append(f"time        {result.elapsed_ms:.3f} ms")
    if grid_text is not None:
        lines.append("")
        lines.append(grid_text)
    return "\n".join(lines)
