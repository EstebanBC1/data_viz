"""Tests for data_vizual.core.

These cover the happy path for each public function, the theme/design-system
behavior, and the error and empty states. Plotting tests use matplotlib's
non-interactive "Agg" backend so they run headless (no display needed) in CI.
"""

import matplotlib

matplotlib.use("Agg")  # must be set before pyplot is imported anywhere

import matplotlib.pyplot as plt
import pandas as pd
import pytest

import data_vizual as dv


@pytest.fixture(autouse=True)
def _reset_theme():
    """Keep tests isolated: start each on the light theme."""
    dv.set_theme("light")
    yield


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


# --- Theme / design system -------------------------------------------------


def test_available_themes():
    assert set(dv.available_themes()) == {"light", "dark"}


def test_series_palette_is_stable_across_themes():
    # A series color means the same thing in light and dark (stable identity).
    assert dv.theme_tokens("light")["series"] == dv.theme_tokens("dark")["series"]
    assert dv.theme_tokens("light")["series"][0] == "#007AFF"


def test_semantic_tokens_present():
    tokens = dv.theme_tokens("light")
    for role in ("good", "warning", "bad", "neutral", "accent", "context",
                 "reference"):
        assert role in tokens


def test_bar_by_sign_colors_and_zero_line():
    d = pd.DataFrame({"q": ["A", "B", "C"], "delta": [12, -5, 8]})
    ax = dv.bar_plot(d, x="q", y="delta", by_sign=True)
    good, bad = dv.theme_tokens()["good"], dv.theme_tokens()["bad"]
    facecolors = [p.get_facecolor() for p in ax.patches]
    assert plt.matplotlib.colors.to_hex(facecolors[0]).lower() == good.lower()
    assert plt.matplotlib.colors.to_hex(facecolors[1]).lower() == bad.lower()
    # A zero reference line was added.
    assert any(abs(ln.get_ydata()[0]) < 1e-9 for ln in ax.lines)


def test_bar_highlight_uses_neutral_for_others():
    d = pd.DataFrame({"region": ["N", "S", "E"], "sales": [3, 5, 4]})
    ax = dv.bar_plot(d, x="region", y="sales", highlight="S")
    accent = dv.theme_tokens()["accent"]
    neutral = dv.theme_tokens()["neutral"]
    hexes = [plt.matplotlib.colors.to_hex(p.get_facecolor()).lower()
             for p in ax.patches]
    assert hexes[1] == accent.lower()      # highlighted
    assert hexes[0] == neutral.lower()     # context


def test_theme_tokens_are_copies():
    # Mutating a returned token dict must not corrupt the shared palette.
    tokens = dv.theme_tokens("light")
    tokens["series"][0] = "#000000"
    assert dv.theme_tokens("light")["series"][0] != "#000000"


def test_theme_tokens_unknown_raises():
    with pytest.raises(KeyError):
        dv.theme_tokens("solarized")


def test_set_theme_updates_color_cycle():
    dv.set_theme("dark")
    cycle_colors = plt.rcParams["axes.prop_cycle"].by_key()["color"]
    assert cycle_colors[0] == dv.theme_tokens("dark")["series"][0]


def test_set_theme_returns_tokens():
    tokens = dv.set_theme("light")
    assert tokens["surface"] == "#ffffff"


# --- Plots -----------------------------------------------------------------
# Each plot returns an Axes; we assert the return type and that data landed on
# it, which is enough to catch wiring bugs without checking pixels.


def test_line_plot_returns_axes(df):
    ax = dv.line_plot(df, x="day", y="revenue")
    assert ax.get_xlabel() == "day"
    assert len(ax.lines) == 1


def test_area_plot_gradient_returns_axes(df):
    ax = dv.area_plot(df, x="day", y="revenue")
    # Crisp top edge is a line; the gradient fill is an image below it.
    assert len(ax.lines) == 1
    assert len(ax.images) == 1


def test_area_plot_flat_fill(df):
    ax = dv.area_plot(df, x="day", y="revenue", gradient=False)
    # Flat wash uses fill_between (a PolyCollection), no gradient image.
    assert len(ax.images) == 0
    assert len(ax.collections) >= 1


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


def test_title_is_set_and_left_aligned(df):
    ax = dv.line_plot(df, x="day", y="revenue", title="Revenue climbs")
    assert ax.get_title(loc="left") == "Revenue climbs"


# --- Consistent styling across chart types ---------------------------------


@pytest.mark.parametrize(
    "make_plot",
    [
        lambda d: dv.line_plot(d, x="day", y="revenue"),
        lambda d: dv.bar_plot(d, x="region", y="day"),
        lambda d: dv.histogram(d, column="day"),
        lambda d: dv.scatter_plot(d, x="day", y="revenue"),
    ],
)
def test_chrome_is_consistent(df, make_plot):
    ax = make_plot(df)
    # Top and right spines are always hidden so the data dominates.
    assert not ax.spines["top"].get_visible()
    assert not ax.spines["right"].get_visible()


# --- Error and empty states ------------------------------------------------


def test_missing_column_raises_clear_error(df):
    with pytest.raises(KeyError, match="nope"):
        dv.line_plot(df, x="day", y="nope")


def test_empty_dataframe_renders_placeholder():
    empty = pd.DataFrame({"day": [], "revenue": []})
    ax = dv.line_plot(empty, x="day", y="revenue")
    # No line drawn, and a single centered message is shown instead.
    assert len(ax.lines) == 0
    texts = [t.get_text() for t in ax.texts]
    assert any("No data" in t for t in texts)


def test_direct_label_adds_annotation(df):
    ax = dv.line_plot(df, x="day", y="revenue")
    before = len(ax.texts)
    dv.direct_label(ax, 3, 30, "peak")
    assert len(ax.texts) == before + 1
