"""Render the MVP chart gallery on realistic (fictional) data.

A small dashboard for *Brewed & Co.*, a made-up coffee-subscription company —
one figure per theme, showing the three chart types on data shaped like the
real thing::

    python examples/gallery.py     # writes gallery-light.png + gallery-dark.png

Data is generated in-code (deterministic), so nothing is committed.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import data_vizual as dv


def make_data():
    rng = np.random.default_rng(2026)
    months = np.arange(1, 13)
    mrr = pd.DataFrame({
        "month": months,
        "mrr": np.array([42, 45, 48, 52, 55, 58, 61, 64, 74, 88, 103, 120]) * 1000
        + rng.normal(0, 700, 12),
    })
    regions = pd.DataFrame({
        "region": ["West", "Northeast", "South", "Midwest", "Intl"],
        "subscribers": [3180, 2760, 2410, 1880, 1230],
    })
    qoq = pd.DataFrame({
        "quarter": ["Q1", "Q2", "Q3", "Q4"],
        "net_add_change": [18, 7, -6, 12],
    })
    spend = rng.uniform(3, 42, 90)
    signups = pd.DataFrame({
        "marketing_spend_k": spend,
        "new_subscribers": (spend * 21 + rng.normal(0, 55, 90) + 40).round(),
    })
    return mrr, regions, qoq, signups


def build(mode: str) -> plt.Figure:
    dv.set_theme(mode)
    t = dv.theme_tokens(mode)
    mrr, regions, qoq, signups = make_data()

    fig, axes = plt.subplots(2, 2, figsize=(11, 8))
    fig.set_facecolor(t["page"])
    fig.suptitle(f"Brewed & Co. — FY2026   ·   {mode} theme",
                 x=0.06, ha="left", fontsize=17, fontweight="medium",
                 color=t["primary"])

    dv.line_plot(mrr, x="month", y="mrr", ax=axes[0, 0],
                 title="Recurring revenue nearly doubled")
    axes[0, 0].set_ylabel("MRR ($)")

    dv.bar_plot(regions, x="region", y="subscribers", ax=axes[0, 1],
                highlight="West", title="One region in focus: the West")

    dv.bar_plot(qoq, x="quarter", y="net_add_change", ax=axes[1, 0],
                by_sign=True, title="Net adds dipped in Q3, rebounded in Q4")
    axes[1, 0].set_ylabel("net-add change (%)")

    dv.scatter_plot(signups, x="marketing_spend_k", y="new_subscribers",
                    ax=axes[1, 1], trendline=True,
                    title="Marketing spend lifts signups")

    fig.tight_layout(rect=(0, 0, 1, 0.95))
    return fig


def main() -> None:
    for mode in ("light", "dark"):
        fig = build(mode)
        out = f"gallery-{mode}.png"
        fig.savefig(out, dpi=150)
        print(f"wrote {out}")


if __name__ == "__main__":
    main()
