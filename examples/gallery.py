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
    orders = pd.DataFrame({"order_value": rng.gamma(3.0, 9.0, 800)})
    return mrr, regions, qoq, signups, orders


def build(mode: str) -> plt.Figure:
    dv.set_theme(mode)
    t = dv.theme_tokens(mode)
    mrr, regions, qoq, signups, orders = make_data()

    fig, axes = plt.subplots(2, 2, figsize=(11, 8))
    fig.set_facecolor(t["page"])
    fig.suptitle(f"Brewed & Co. — FY2026   ·   {mode} theme",
                 x=0.06, ha="left", fontsize=17, fontweight="medium",
                 color=t["primary"])

    dv.line_plot(mrr, x="month", y="mrr", ax=axes[0, 0], fill=True,
                 title="Recurring revenue nearly doubled")
    axes[0, 0].set_ylabel("MRR ($)")

    h = dv.hist_plot(orders, column="order_value", bins=26, ax=axes[0, 1],
                     title="Order values cluster near $25")
    h.set_xlabel("order value ($)")

    dv.bar_plot(regions, x="region", y="subscribers", ax=axes[1, 0],
                pattern=True, title="West leads the subscriber base")
    axes[1, 0].set_ylabel("subscribers")

    dv.scatter_plot(signups, x="marketing_spend_k", y="new_subscribers",
                    ax=axes[1, 1], trendline=True,
                    title="Marketing spend lifts signups")

    fig.tight_layout(rect=(0, 0, 1, 0.95))
    return fig


def _ribbon(ax, t):
    """A subtle organic patterned ribbon behind the lower portion of the axes."""
    ax.set_xlim(-0.7, 4.7)
    x = np.linspace(-0.7, 4.7, 300)
    top = 9 + 2 * np.sin(x * 1.5) + 1.3 * np.sin(x * 3.1)
    band = ax.fill_between(x, 0, top, color=t["baseline"], alpha=0.28, zorder=0)
    for gy in np.arange(1.0, 10, 1.4):
        ln, = ax.plot(x, gy + 0.28 * np.sin(x * 2 + gy), color=t["muted"],
                      lw=0.9, alpha=0.4, zorder=1)
        ln.set_clip_path(band.get_paths()[0], ln.get_transform())


def hero(mode: str) -> plt.Figure:
    """Replicate the reference 'Espresso drives the catalog' look, built entirely
    from the library's patterned bar_plot on a soft ribbon backdrop."""
    dv.set_theme(mode)
    t = dv.theme_tokens(mode)
    catalog = pd.DataFrame({
        "product": ["Espresso", "Cold Brew", "Single-Origin", "Decaf", "Gear"],
        "revenue": [48, 32, 23, 12, 8],
    })
    fig, ax = plt.subplots(figsize=(11, 6.6))
    fig.set_facecolor(t["page"])
    _ribbon(ax, t)
    dv.bar_plot(catalog, x="product", y="revenue", ax=ax, pattern=True,
                title="Espresso drives the catalog")
    ax.set_ylim(0, 56)
    ax.annotate("Espresso contributes\n38% of product revenue",
                xy=(0, 48), xytext=(0.8, 54), ha="left", va="top",
                fontsize=11, color=t["secondary"],
                arrowprops=dict(arrowstyle="-", color=t["negative"], lw=2,
                                connectionstyle="angle3,angleA=0,angleB=90"))
    fig.text(0.09, 0.02, "Brewed & Co. · FY2026 revenue (USD millions)",
             color=t["muted"], fontsize=9, ha="left")
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    return fig


def main() -> None:
    for mode in ("light", "dark"):
        build(mode).savefig(f"gallery-{mode}.png", dpi=150)
        hero(mode).savefig(f"gallery-hero-{mode}.png", dpi=150)
        print(f"wrote gallery-{mode}.png + gallery-hero-{mode}.png")


if __name__ == "__main__":
    main()
