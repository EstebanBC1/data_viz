"""A worked example on realistic (but fictional) data.

Tells one coherent story — the 2026 year of *Brewed & Co.*, a made-up coffee
subscription company — using every chart type on data shaped like the real
thing (seasonality, skew, correlation, positive/negative swings). Run it to
render an eight-panel "dashboard" in both themes::

    python examples/showcase.py     # writes showcase-light.png + showcase-dark.png

All data is generated in-code (deterministic), so nothing is committed.
"""

from __future__ import annotations

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import data_vizual as dv


def make_data():
    """Fictional but plausible datasets for Brewed & Co., FY2026."""
    rng = np.random.default_rng(2026)
    months = pd.date_range("2026-01-01", periods=12, freq="MS")

    # Monthly recurring revenue: steady growth with a summer dip.
    season = np.array([0, 1, 3, 5, 6, 4, 2, 3, 6, 9, 12, 15]) * 1000
    mrr = pd.DataFrame({"month": months,
                        "mrr": 42000 + np.linspace(0, 52000, 12) + season
                        + rng.normal(0, 1500, 12)})

    # Revenue by product line.
    products = pd.DataFrame({
        "product": ["Espresso", "Cold Brew", "Single-Origin", "Decaf", "Gear"],
        "revenue": [48200, 31400, 22600, 11800, 7300],
    })

    # Active subscribers by region.
    regions = pd.DataFrame({
        "region": ["West", "Northeast", "South", "Midwest", "Intl"],
        "subscribers": [3180, 2760, 2410, 1880, 1230],
    })

    # Subscriber growth for three plans (a multi-series line).
    plans = pd.DataFrame({
        "month": months,
        "Basic": (1800 + np.linspace(0, 900, 12) + rng.normal(0, 40, 12)).round(),
        "Plus": (1200 + np.linspace(0, 2100, 12) + rng.normal(0, 50, 12)).round(),
        "Pro": (600 + np.linspace(0, 1500, 12) + rng.normal(0, 45, 12)).round(),
    })

    # Distribution of order values ($) — right-skewed, as spend usually is.
    orders = pd.DataFrame({"order_value": rng.gamma(3.0, 9.0, 600)})

    # Marketing spend vs. new subscribers — a clear positive relationship.
    spend = rng.uniform(3, 42, 90)
    signups = pd.DataFrame({
        "marketing_spend_k": spend,
        "new_subscribers": (spend * 21 + rng.normal(0, 55, 90) + 40).round(),
    })

    # Quarter-over-quarter change in net adds (%), some up, some down.
    qoq = pd.DataFrame({
        "quarter": ["Q1", "Q2", "Q3", "Q4"],
        "net_add_change": [18.4, 7.2, -5.6, 12.1],
    })

    return mrr, products, regions, plans, orders, signups, qoq


def _tidy_dates(ax):
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b"))


def build(mode: str) -> plt.Figure:
    dv.set_theme(mode)
    t = dv.theme_tokens(mode)
    mrr, products, regions, plans, orders, signups, qoq = make_data()

    fig, axes = plt.subplots(4, 2, figsize=(12, 16))
    fig.set_facecolor(t["page"])
    fig.suptitle(
        f"Brewed & Co. — FY2026 in review   ·   {mode} theme",
        x=0.06, ha="left", fontsize=18, fontweight="semibold", color=t["primary"],
    )

    # 1. MRR trend (area).
    a = dv.area_plot(mrr, x="month", y="mrr", ax=axes[0, 0],
                     title="Recurring revenue nearly doubled")
    a.set_ylabel("MRR ($)")
    _tidy_dates(a)

    # 2. Revenue by product (rounded bars).
    dv.bar_plot(products, x="product", y="revenue", ax=axes[0, 1],
                title="Espresso drives the catalog")
    axes[0, 1].set_ylabel("revenue ($)")

    # 3. Plan growth (multi-series line, direct-labeled).
    ax_plans = axes[1, 0]
    styles = [("Basic", t["series"][0], "o", "-"),
              ("Plus", t["series"][1], "s", "--"),
              ("Pro", t["series"][2], "^", ":")]
    for name, color, marker, ls in styles:
        dv.line_plot(plans, x="month", y=name, ax=ax_plans, color=color,
                     marker=marker, linestyle=ls)
        dv.direct_label(ax_plans, plans["month"].iloc[-1], plans[name].iloc[-1],
                        name, color=color)
    ax_plans.set_ylabel("subscribers")
    ax_plans.set_title("Plus is outgrowing every plan", loc="left")
    ax_plans.margins(x=0.2)
    _tidy_dates(ax_plans)

    # 4. Subscribers by region (lollipop).
    dv.lollipop_plot(regions, x="region", y="subscribers", ax=axes[1, 1],
                     title="The West leads subscriptions")

    # 5. Highlight the top region (bar highlight).
    dv.bar_plot(regions, x="region", y="subscribers", ax=axes[2, 0],
                highlight="West", title="One region in focus: the West")
    axes[2, 0].set_ylabel("subscribers")

    # 6. Order-value distribution (histogram).
    h = dv.histogram(orders, column="order_value", bins=28, ax=axes[2, 1],
                     title="Most orders cluster near $25")
    h.set_xlabel("order value ($)")

    # 7. Marketing vs. signups (scatter).
    s = dv.scatter_plot(signups, x="marketing_spend_k", y="new_subscribers",
                        ax=axes[3, 0], title="Marketing spend lifts signups")
    s.set_xlabel("marketing spend ($k)")
    s.set_ylabel("new subscribers")

    # 8. Quarterly change (positive / negative bars).
    q = dv.bar_plot(qoq, x="quarter", y="net_add_change", ax=axes[3, 1],
                    by_sign=True, title="Net adds dipped in Q3, rebounded in Q4")
    q.set_ylabel("net-add change (%)")

    fig.tight_layout(rect=(0, 0, 1, 0.97))
    return fig


def main() -> None:
    for mode in ("light", "dark"):
        fig = build(mode)
        out = f"showcase-{mode}.png"
        fig.savefig(out, dpi=150)
        print(f"wrote {out}")


if __name__ == "__main__":
    main()
