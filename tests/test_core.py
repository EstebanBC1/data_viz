"""Tests for data_vizual.core.

These cover the happy path for each public function plus the one error case we
raise ourselves. Plotting tests use matplotlib's non-interactive "Agg" backend
so they run headless (no display needed) in CI.
"""

import matplotlib

matplotlib.use("Agg")  # must be set before pyplot is imported anywhere

import pandas as pd
import pytest

import data_vizual as dv


@pytest.fixture
def df():
    """A tiny DataFrame with a missing value to exercise the summaries."""
    return pd.DataFrame(
        {
            "day": [1, 2, 3, 4],
            "revenue": [10.0, 20.0, 30.0, None],
            "region": ["N", "S", "N", "S"],
        }
    )


# --- Loading ---------------------------------------------------------------


def test_load_csv_reads_file(tmp_path, df):
    csv_path = tmp_path / "data.csv"
    df.to_csv(csv_path, index=False)

    loaded = dv.load_csv(csv_path)

    assert list(loaded.columns) == ["day", "revenue", "region"]
    assert len(loaded) == 4


def test_load_csv_missing_file_raises():
    with pytest.raises(FileNotFoundError):
        dv.load_csv("does/not/exist.csv")


# --- Summaries -------------------------------------------------------------


def test_column_types(df):
    types = dv.column_types(df)
    # Check the kind of type, not an exact dtype string: pandas versions differ
    # (e.g. text may be "object" or a dedicated string dtype).
    assert pd.api.types.is_integer_dtype(types["day"])
    assert not pd.api.types.is_numeric_dtype(types["region"])


def test_missing_value_counts(df):
    missing = dv.missing_value_counts(df)
    # revenue has the only gap and should sort to the top.
    assert missing.iloc[0] == 1
    assert missing["revenue"] == 1
    assert missing["day"] == 0


def test_summary_statistics(df):
    stats = dv.summary_statistics(df)
    # describe() reports numeric columns; "count" excludes the missing value.
    assert stats.loc["count", "revenue"] == 3


# --- Plots -----------------------------------------------------------------
# Each plot returns an Axes; we assert the return type and that data landed on
# it, which is enough to catch wiring bugs without checking pixels.


def test_line_plot_returns_axes(df):
    ax = dv.line_plot(df, x="day", y="revenue")
    assert ax.get_xlabel() == "day"
    assert len(ax.lines) == 1


def test_bar_plot_returns_axes(df):
    ax = dv.bar_plot(df, x="region", y="day")
    assert len(ax.patches) == 4  # one bar per row


def test_histogram_returns_axes(df):
    ax = dv.histogram(df, column="day", bins=4)
    assert ax.get_ylabel() == "Frequency"
    assert len(ax.patches) == 4  # one patch per bin


def test_scatter_plot_returns_axes(df):
    ax = dv.scatter_plot(df, x="day", y="revenue")
    assert ax.get_xlabel() == "day"
    assert len(ax.collections) == 1
