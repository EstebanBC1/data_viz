"""data_vizual: bare-bones pandas helpers and styled matplotlib plots.

Import the functions you need directly from the top-level package, e.g.::

    import data_vizual as dv

    dv.set_theme("dark")             # pick the visual language once
    df = dv.load_csv("data/sales.csv")
    dv.summary_statistics(df)
    ax = dv.histogram(df, "revenue", title="Revenue is right-skewed")

The building blocks live in ``data_vizual.core``; they are re-exported here so
the public API is flat and easy to discover.
"""

from .core import (
    available_themes,
    bar_plot,
    column_types,
    direct_label,
    histogram,
    line_plot,
    load_csv,
    missing_value_counts,
    scatter_plot,
    set_theme,
    summary_statistics,
    theme_tokens,
)

__version__ = "0.2.0"

# The names that make up the public API (what `from data_vizual import *` gets,
# and a clear inventory for readers).
__all__ = [
    # Theme / design system
    "set_theme",
    "available_themes",
    "theme_tokens",
    # Loading
    "load_csv",
    # Summaries
    "column_types",
    "missing_value_counts",
    "summary_statistics",
    # Plots
    "line_plot",
    "bar_plot",
    "histogram",
    "scatter_plot",
    "direct_label",
]
