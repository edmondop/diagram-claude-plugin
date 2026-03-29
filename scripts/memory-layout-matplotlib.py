# /// script
# requires-python = ">=3.10"
# dependencies = ["matplotlib"]
# ///
"""Memory layout diagram using matplotlib.

Demonstrates byte-level memory diagrams with pointer arrows — the kind
of diagram where you need exact coordinate control over every rectangle
and arrow. Key techniques:
- FancyBboxPatch for rounded memory cells
- FancyArrowPatch with arc3 connectionstyle for pointer arrows
- Explicit zorder to prevent patches covering text
- Negative arc radius to route arrows below content
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.patches as patches  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch  # noqa: E402

CELL_W = 2.2
CELL_H = 0.8


def draw_block(
    ax: plt.Axes,
    x: float,
    y: float,
    fields: list[tuple[str, str, str, str]],
    *,
    title: str = "",
    title_color: str = "#2d5f8a",
) -> None:
    ax.text(
        x + CELL_W / 2,
        y + len(fields) * CELL_H + 0.25,
        title,
        ha="center",
        va="bottom",
        fontsize=9,
        fontweight="bold",
        color=title_color,
    )
    for i, (addr, label, value, color) in enumerate(fields):
        yy = y + (len(fields) - 1 - i) * CELL_H
        rect = patches.FancyBboxPatch(
            (x, yy),
            CELL_W,
            CELL_H,
            boxstyle="round,pad=0.04",
            facecolor=color,
            edgecolor="#333",
            linewidth=1.2,
        )
        ax.add_patch(rect)
        ax.text(
            x - 0.1,
            yy + CELL_H / 2,
            addr,
            ha="right",
            va="center",
            fontsize=7,
            fontfamily="monospace",
            color="#888",
        )
        ax.text(
            x + CELL_W / 2,
            yy + CELL_H * 0.65,
            label,
            ha="center",
            va="center",
            fontsize=8,
            fontweight="bold",
            color="#333",
        )
        ax.text(
            x + CELL_W / 2,
            yy + CELL_H * 0.3,
            value,
            ha="center",
            va="center",
            fontsize=7,
            fontfamily="monospace",
            color="#555",
        )


def draw_arrow(
    ax: plt.Axes,
    start: tuple[float, float],
    end: tuple[float, float],
    *,
    color: str = "#2d5f8a",
    style: str = "arc3,rad=0.3",
    dashed: bool = False,
) -> None:
    arrow = FancyArrowPatch(
        start,
        end,
        arrowstyle="-|>",
        mutation_scale=12,
        color=color,
        linewidth=1.5,
        connectionstyle=style,
        linestyle="--" if dashed else "-",
    )
    ax.add_patch(arrow)


def main() -> None:
    Path("output").mkdir(exist_ok=True)

    fig, ax = plt.subplots(figsize=(5.5, 4.2))
    ax.set_xlim(-1.5, 10.5)
    ax.set_ylim(-0.5, 6)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.patch.set_facecolor("white")

    # Stack block: s1 (moved from, dead)
    draw_block(
        ax,
        0,
        1,
        [
            ("0x1000", "ptr", "0x5000", "#dbeafe"),
            ("0x1008", "len", "5", "#e2e8f0"),
            ("0x1010", "cap", "5", "#e2e8f0"),
        ],
        title="s1 @ 0x1000 (dead)",
    )

    # Stack block: s2 (move target)
    draw_block(
        ax,
        4.5,
        1,
        [
            ("0x2000", "ptr", "0x5000", "#dbeafe"),
            ("0x2008", "len", "5", "#e2e8f0"),
            ("0x2010", "cap", "5", "#e2e8f0"),
        ],
        title="s2 @ 0x2000",
    )

    # Heap buffer
    hx, hy = 7.2, 4.5
    ax.add_patch(
        plt.Rectangle((hx, hy), 2.2, 0.7, facecolor="#d4edda", edgecolor="#333", linewidth=1.2)
    )
    ax.text(hx + 1.1, hy + 0.35, '"hello"', ha="center", va="center", fontsize=8, fontfamily="monospace", color="#333")
    ax.text(hx + 1.1, hy + 0.9, "heap @ 0x5000", ha="center", fontsize=7, color="#888")

    # Arrow from s1.ptr — midpoint of ptr cell, route BELOW title text
    draw_arrow(ax, (2.2, 3.0), (7.2, 4.85), color="#16a34a", style="arc3,rad=-0.3")
    # Arrow from s2.ptr
    draw_arrow(ax, (6.7, 3.45), (7.2, 4.85), color="#16a34a", style="arc3,rad=0.1")

    ax.text(
        4.5,
        5.2,
        "both point to same\nheap buffer — safe",
        fontsize=8,
        color="#16a34a",
        ha="center",
        bbox=dict(facecolor="#f0fdf4", edgecolor="#16a34a", boxstyle="round,pad=0.2"),
    )

    ax.set_title("String move: pointers target external heap", fontsize=9, fontweight="bold", color="#333", pad=8)
    plt.tight_layout()

    fig.savefig("output/memory-layout-matplotlib.svg", format="svg", bbox_inches="tight")
    print("Saved: output/memory-layout-matplotlib.svg")
    plt.close()


if __name__ == "__main__":
    main()
