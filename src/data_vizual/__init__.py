"""data_vizual: bare-bones pandas helpers and styled matplotlib plots.

Import the functions you need directly from the top-level package, e.g.::

    import data_vizual as dv

    df = dv.load_csv("data/sales.csv")
    dv.summary_statistics(df)
    ax = dv.histogram(df, "revenue")

The building blocks live in ``data_vizual.core``; they are re-exported here so
the public API is flat and easy to discover.
"""

from .core import (
    bar_plot,
    column_types,
    histogram,
    line_plot,
    load_csv,
    missing_value_counts,
    scatter_plot,
    summary_statistics,
)

__version__ = "0.1.0"

# The names that make up the public API (what `from data_vizual import *` gets,
# and a clear inventory for readers).
__all__ = [
    "load_csv",
    "column_types",
    "missing_value_counts",
    "summary_statistics",
    "line_plot",
    "bar_plot",
    "histogram",
    "scatter_plot",
]
