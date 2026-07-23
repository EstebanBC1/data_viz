"""Render a small gallery of data_vizual's default charts.

Run it to see the refined defaults in both light and dark themes::

    python examples/gallery.py            # writes gallery-light.png + gallery-dark.png
    python examples/gallery.py --show     # open an interactive window instead

The data here is synthetic (generated in-code), so the example is fully
self-contained and commits no CSVs (see CLAUDE.md).
"""

from __future__ import annotations

import argparse

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import data_vizual as dv


def make_data() -> dict[str, pd.DataFrame]:
    """Build a few tiny, deterministic datasets to plot."""
    rng = np.random.default_rng(7)  # fixed seed -> stable, comparable output

    months = pd.date_range("2026-01-01", periods=12, freq="MS")
    trend = pd.DataFrame(
        {"month": months, "revenue": np.linspace(120, 320, 12) + rng.normal(0, 8, 12)}
    )

    regions = pd.DataFrame(
        {"region": ["North", "South", "East", "West", "Central"],
         "sales": [820, 660, 940, 510, 730]}
    )

    distribution = pd.DataFrame({"order_value": rng.gamma(2.0, 40.0, 400)})

    relationship = pd.DataFrame({"ad_spend": rng.uniform(5, 60, 120)})
    relationship["revenue"] = (
        relationship["ad_spend"] * 4.5 + rng.normal(0, 25, 120)
    )

    return {
        "trend": trend,
        "regions": regions,
        "distribution": distribution,
        "relationship": relationship,
    }


def build_gallery(mode: str, data: dict[str, pd.DataFrame]) -> plt.Figure:
    """Draw all four chart types on one figure using the given theme."""
    dv.set_theme(mode)
    tokens = dv.theme_tokens(mode)

    # A 2x2 layout of small multiples; generous spacing lets each breathe.
    fig, axes = plt.subplots(2, 2, figsize=(11, 8))
    fig.set_facecolor(tokens["page"])
    fig.suptitle(
        f"data_vizual default charts — {mode} theme",
        x=0.06, ha="left", fontsize=17, fontweight="semibold",
        color=tokens["primary"],
    )

    dv.line_plot(
        data["trend"], x="month", y="revenue", ax=axes[0, 0],
        title="Revenue grew steadily through 2026",
    )
    dv.bar_plot(
        data["regions"], x="region", y="sales", ax=axes[0, 1],
        title="East leads regional sales",
    )
    dv.histogram(
        data["distribution"], column="order_value", bins=24, ax=axes[1, 0],
        title="Order values are right-skewed",
    )
    dv.scatter_plot(
        data["relationship"], x="ad_spend", y="revenue", ax=axes[1, 1],
        title="Ad spend tracks revenue",
    )

    fig.tight_layout(rect=(0, 0, 1, 0.95))
    return fig


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--show", action="store_true",
                        help="Open interactive windows instead of saving PNGs.")
    args = parser.parse_args()

    data = make_data()
    for mode in ("light", "dark"):
        fig = build_gallery(mode, data)
        if args.show:
            continue
        out = f"gallery-{mode}.png"
        fig.savefig(out, dpi=150)
        print(f"wrote {out}")

    if args.show:
        plt.show()


if __name__ == "__main__":
    main()
