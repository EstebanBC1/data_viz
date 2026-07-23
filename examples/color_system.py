"""Demonstrate the neutral-first color system.

Renders the four canonical scenarios in both themes, so you can see where color
earns its place and where the design stays neutral::

    python examples/color_system.py     # writes color-system-light.png + -dark.png

Panels:
    1. Single series        -> one accent-blue series (the one emphasis)
    2. Multiple series      -> stable palette + markers + direct labels
    3. Highlighted compare  -> one blue series, the rest neutral context
    4. Positive / negative  -> semantic green / red by sign

Data is synthetic (generated in-code), so nothing is committed to disk.
"""

from __future__ import annotations

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import data_vizual as dv


def make_data():
    """Deterministic synthetic series for the four panels."""
    rng = np.random.default_rng(11)
    months = pd.date_range("2026-01-01", periods=12, freq="MS")

    # One growing revenue series (panel 1).
    single = pd.DataFrame(
        {"month": months, "revenue": np.linspace(120, 300, 12) + rng.normal(0, 6, 12)}
    )

    # Three comparable product lines (panels 2 and 3).
    multi = pd.DataFrame({
        "month": months,
        "Product A": np.linspace(80, 210, 12) + rng.normal(0, 5, 12),
        "Product B": np.linspace(60, 250, 12) + rng.normal(0, 5, 12),
        "Product C": np.linspace(140, 170, 12) + rng.normal(0, 5, 12),
    })

    # Quarterly change, positive and negative (panel 4).
    change = pd.DataFrame(
        {"quarter": ["Q1", "Q2", "Q3", "Q4", "Q5", "Q6"],
         "growth": [8.2, 3.1, -4.6, 6.0, -2.3, 9.4]}
    )
    return single, multi, change


def _tidy_dates(ax):
    """Two-month date ticks so labels never collide in a narrow panel."""
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b"))


def build(mode: str) -> plt.Figure:
    dv.set_theme(mode)
    t = dv.theme_tokens(mode)
    single, multi, change = make_data()

    fig, axes = plt.subplots(2, 2, figsize=(12, 8.5))
    fig.set_facecolor(t["page"])
    fig.suptitle(
        f"Color & style system — {mode} theme",
        x=0.06, ha="left", fontsize=17, fontweight="semibold", color=t["primary"],
    )

    # --- 1. Single series: blue is the one point of emphasis ---------------
    ax1 = axes[0, 0]
    dv.area_plot(single, x="month", y="revenue", ax=ax1,
                 title="1 · Single series — accent = the subject")
    _tidy_dates(ax1)

    # --- 2. Multiple series: stable palette + markers + direct labels -------
    ax2 = axes[0, 1]
    series_style = [("Product A", t["series"][0], "o", "-"),
                    ("Product B", t["series"][1], "s", "--"),
                    ("Product C", t["series"][2], "^", ":")]
    for name, color, marker, ls in series_style:
        dv.line_plot(multi, x="month", y=name, ax=ax2, color=color,
                     marker=marker, linestyle=ls)
        dv.direct_label(ax2, multi["month"].iloc[-1], multi[name].iloc[-1],
                        name, color=color)
    ax2.set_ylabel("revenue")
    ax2.set_title("2 · Multiple series — color = identity", loc="left")
    ax2.margins(x=0.18)  # room for the end labels
    _tidy_dates(ax2)

    # --- 3. Highlighted comparison: one blue, the rest neutral context ------
    ax3 = axes[1, 0]
    for name in ("Product A", "Product C"):            # context, pushed back
        dv.line_plot(multi, x="month", y=name, ax=ax3,
                     color=t["context"], alpha=0.45)
    dv.line_plot(multi, x="month", y="Product B", ax=ax3,   # the focus
                 color=t["accent"])
    dv.direct_label(ax3, multi["month"].iloc[-1], multi["Product B"].iloc[-1],
                    "Product B", color=t["accent"])
    ax3.set_ylabel("revenue")
    ax3.set_title("3 · Highlight — color = focus", loc="left")
    ax3.margins(x=0.18)
    _tidy_dates(ax3)

    # --- 4. Positive / negative: semantic green / red -----------------------
    ax4 = axes[1, 1]
    dv.bar_plot(change, x="quarter", y="growth", ax=ax4, by_sign=True,
                title="4 · Positive / negative — color = status")
    ax4.set_ylabel("growth (%)")

    fig.tight_layout(rect=(0, 0, 1, 0.95))
    return fig


def main() -> None:
    for mode in ("light", "dark"):
        fig = build(mode)
        out = f"color-system-{mode}.png"
        fig.savefig(out, dpi=150)
        print(f"wrote {out}")


if __name__ == "__main__":
    main()
