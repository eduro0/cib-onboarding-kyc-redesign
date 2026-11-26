"""KPI charts for the deck: one small-multiples figure per case type, As-Is vs To-Be.

Implements: kpi-model/baseline-vs-to-be, kpi-model/numbers-from-model

One panel per KPI, each on its own axis (the KPIs have different units, so they never share a scale). Two bars
per panel, labelled with their values. Colours are the first two slots of the reference categorical palette
(validated colourblind-safe as an adjacent pair); text stays in text ink. Every value comes from the model's
numbers, and the footer says the data is simulated.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

AS_IS, TO_BE = "#eb6834", "#2a78d6"
SURFACE, INK, INK_2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
PANELS = [("cycle_days", "Cycle time", "days", "{:.0f}"), ("touch_hours", "Touch time", "staff hours / case", "{:.1f}"),
          ("first_pass", "First-pass rate", "share of cases", "{:.0%}"), ("rework", "Rework", "loops / case", "{:.2f}"),
          ("client_touches", "Client touches", "asks / case", "{:.1f}")]


def figure(numbers: dict, short: str, title: str, path: Path) -> None:
    panels = PANELS + ([("on_time", "Reviews on time", "share of reviews", "{:.0%}")] if short == "rev" else [])
    fig, axes = plt.subplots(1, len(panels), figsize=(16, 7), dpi=110, facecolor=SURFACE)
    for ax, (key, label, unit, fmt) in zip(axes, panels):
        name = "rev_on_time" if key == "on_time" else f"{short}_{key}"
        # percentages for shares are points apart; the bar labels show the two levels, never a relative change
        before, after = numbers[f"{name}_as_is"], numbers[f"{name}_to_be"]
        bars = ax.bar([0, 1], [before, after], width=0.62, color=[AS_IS, TO_BE], edgecolor=SURFACE, linewidth=2)
        top = max(before, after) * 1.25 or 1
        ax.set_ylim(0, top)
        for bar, v in zip(bars, (before, after)):
            ax.text(bar.get_x() + bar.get_width() / 2, v + top * 0.02, fmt.format(v), ha="center", va="bottom",
                    fontsize=15, fontweight="bold", color=INK)
        ax.set_xticks([0, 1], ["As-Is", "To-Be"], fontsize=12, color=INK_2)
        ax.set_title(label, fontsize=14, fontweight="bold", color=INK, loc="left", pad=22)
        ax.text(0, 1.015, unit, transform=ax.transAxes, fontsize=10.5, color=INK_2)
        ax.set_facecolor(SURFACE)
        ax.tick_params(axis="y", colors=INK_2, labelsize=10, length=0)
        ax.yaxis.grid(True, color=GRID, linewidth=0.8)
        ax.set_axisbelow(True)
        for side in ("top", "right", "left"):
            ax.spines[side].set_visible(False)
        ax.spines["bottom"].set_color(GRID)
        if fmt.endswith("%}"):
            ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0, decimals=0))
    fig.suptitle(title, x=0.012, y=0.985, ha="left", fontsize=18, fontweight="bold", color=INK)
    fig.text(0.012, 0.015, "Simulated data, not real bank data. Maps drawn from public rules; every model input is a "
             "labelled guess (Assumptions tab of kpi-model.xlsx).", fontsize=10.5, color=INK_2)
    fig.tight_layout(rect=(0, 0.04, 1, 0.93), w_pad=2.5)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, facecolor=SURFACE)
    plt.close(fig)
