"""Core helpers for data_vizual.

This single module holds the library's building blocks, grouped into three
plain-function sections:

    1. Loading data      -> get a CSV into a pandas DataFrame
    2. Summarizing data  -> quick answers about shape, types, and gaps
    3. Plotting data     -> styled matplotlib charts you can build on

Everything is a small, single-purpose function (no god class) that returns a
standard pandas or matplotlib object. That keeps each piece easy to read, test,
and debug, and lets you compose them however you like.

Conventions (see CLAUDE.md):
    - pandas, not polars
    - matplotlib only for plotting
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

# ---------------------------------------------------------------------------
# 1. Loading data
# ---------------------------------------------------------------------------


def load_csv(path: str | Path, **read_csv_kwargs) -> pd.DataFrame:
    """Load a CSV file into a pandas DataFrame.

    A thin, friendly wrapper around ``pandas.read_csv``. It gives callers one
    obvious entry point for loading data and fails early with a clear message
    when the file is missing, instead of a lower-level error that is harder to
    trace.

    Parameters
    ----------
    path:
        Path to the CSV file, as a string or ``pathlib.Path``.
    **read_csv_kwargs:
        Extra keyword arguments passed straight through to ``pandas.read_csv``
        (e.g. ``sep=";"``, ``usecols=[...]``, ``parse_dates=[...]``).

    Returns
    -------
    pandas.DataFrame
        The parsed data.

    Raises
    ------
    FileNotFoundError
        If no file exists at ``path``.
    """
    path = Path(path)
    if not path.is_file():
        # Fail loudly and early: clearer than a stack trace from inside pandas.
        raise FileNotFoundError(f"No CSV file found at: {path}")

    return pd.read_csv(path, **read_csv_kwargs)


# ---------------------------------------------------------------------------
# 2. Summarizing data
# ---------------------------------------------------------------------------


def column_types(df: pd.DataFrame) -> pd.Series:
    """Return the dtype of each column.

    A one-line view of how pandas interpreted every column, which is often the
    first thing to check when a plot or calculation misbehaves (e.g. a numeric
    column accidentally loaded as text).

    Parameters
    ----------
    df:
        The DataFrame to inspect.

    Returns
    -------
    pandas.Series
        Column name -> dtype.
    """
    return df.dtypes


def missing_value_counts(df: pd.DataFrame) -> pd.Series:
    """Count missing (NaN) values per column, highest first.

    Missing data quietly breaks aggregations and plots, so surfacing it early
    is worth its own function. Columns are sorted descending so the biggest
    gaps are at the top.

    Parameters
    ----------
    df:
        The DataFrame to inspect.

    Returns
    -------
    pandas.Series
        Column name -> number of missing values, sorted descending.
    """
    return df.isna().sum().sort_values(ascending=False)


def summary_statistics(df: pd.DataFrame) -> pd.DataFrame:
    """Return descriptive statistics for the numeric columns.

    A thin wrapper around ``DataFrame.describe`` kept as its own named function
    so the intent reads clearly at the call site. Reports count, mean, std,
    min, quartiles, and max for each numeric column.

    Parameters
    ----------
    df:
        The DataFrame to summarize.

    Returns
    -------
    pandas.DataFrame
        Standard describe() table for numeric columns.
    """
    return df.describe()


# ---------------------------------------------------------------------------
# 3. Plotting data
# ---------------------------------------------------------------------------
#
# Every plot function follows the same simple contract so they are predictable
# and easy to extend into your own aesthetic:
#
#   - takes a DataFrame plus the column name(s) to plot
#   - accepts an optional ``ax`` so plots can be placed on your own figure
#   - creates a figure/axes when ``ax`` is not given
#   - returns the matplotlib ``Axes`` so you can keep customizing (titles,
#     colors, limits) after the fact
#
# Returning the Axes rather than calling ``plt.show()`` inside the function is
# the standard, debuggable pattern: nothing is hidden and you stay in control.


def _get_axes(ax: plt.Axes | None) -> plt.Axes:
    """Return the Axes to draw on, creating a new figure if none was given.

    Small internal helper (leading underscore = not part of the public API) so
    every plot function shares the exact same "use the caller's Axes or make a
    fresh one" behavior instead of repeating it.
    """
    if ax is None:
        _, ax = plt.subplots()
    return ax


def line_plot(
    df: pd.DataFrame,
    x: str,
    y: str,
    ax: plt.Axes | None = None,
) -> plt.Axes:
    """Draw a line chart of ``y`` against ``x``.

    Best for showing how a value changes over an ordered axis such as time.

    Parameters
    ----------
    df:
        The data to plot.
    x, y:
        Column names for the horizontal and vertical axes.
    ax:
        Optional existing Axes to draw on. If omitted, a new figure is created.

    Returns
    -------
    matplotlib.axes.Axes
        The Axes containing the plot.
    """
    ax = _get_axes(ax)
    ax.plot(df[x], df[y])
    ax.set_xlabel(x)
    ax.set_ylabel(y)
    return ax


def bar_plot(
    df: pd.DataFrame,
    x: str,
    y: str,
    ax: plt.Axes | None = None,
) -> plt.Axes:
    """Draw a bar chart of ``y`` for each category in ``x``.

    Best for comparing a numeric value across a set of discrete categories.

    Parameters
    ----------
    df:
        The data to plot.
    x:
        Column name for the categories (bars).
    y:
        Column name for the bar heights.
    ax:
        Optional existing Axes to draw on. If omitted, a new figure is created.

    Returns
    -------
    matplotlib.axes.Axes
        The Axes containing the plot.
    """
    ax = _get_axes(ax)
    ax.bar(df[x], df[y])
    ax.set_xlabel(x)
    ax.set_ylabel(y)
    return ax


def histogram(
    df: pd.DataFrame,
    column: str,
    bins: int = 10,
    ax: plt.Axes | None = None,
) -> plt.Axes:
    """Draw a histogram of a single numeric column.

    Best for seeing the distribution of one variable: where values cluster,
    how spread out they are, and whether the shape is skewed.

    Parameters
    ----------
    df:
        The data to plot.
    column:
        Numeric column to bin and count.
    bins:
        Number of bins to divide the range into. Defaults to 10.
    ax:
        Optional existing Axes to draw on. If omitted, a new figure is created.

    Returns
    -------
    matplotlib.axes.Axes
        The Axes containing the plot.
    """
    ax = _get_axes(ax)
    ax.hist(df[column], bins=bins)
    ax.set_xlabel(column)
    ax.set_ylabel("Frequency")
    return ax


def scatter_plot(
    df: pd.DataFrame,
    x: str,
    y: str,
    ax: plt.Axes | None = None,
) -> plt.Axes:
    """Draw a scatter plot of ``y`` against ``x``.

    Best for exploring the relationship between two numeric variables.

    Parameters
    ----------
    df:
        The data to plot.
    x, y:
        Column names for the horizontal and vertical axes.
    ax:
        Optional existing Axes to draw on. If omitted, a new figure is created.

    Returns
    -------
    matplotlib.axes.Axes
        The Axes containing the plot.
    """
    ax = _get_axes(ax)
    ax.scatter(df[x], df[y])
    ax.set_xlabel(x)
    ax.set_ylabel(y)
    return ax
