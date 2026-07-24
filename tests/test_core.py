"""Tests for data_vizual (MVP surface).

Plotting tests use matplotlib's non-interactive "Agg" backend so they run
headless in CI.
"""

import matplotlib

matplotlib.use("Agg")  # must be set before pyplot is imported anywhere

import matplotlib.pyplot as plt
import pandas as pd
import pytest

import data_vizual as dv


@pytest.fixture(autouse=True)
def _reset_theme():
    dv.set_theme("light")
    yield
    plt.close("all")


@pytest.fixture
def df():
    return pd.DataFrame({
        "month": [1, 2, 3, 4],
        "revenue": [10.0, 20.0, 30.0, None],
        "region": ["N", "S", "N", "S"],
    })


# --- loading & summaries ---------------------------------------------------


def test_load_csv_reads_file(tmp_path, df):
    path = tmp_path / "d.csv"
    df.to_csv(path, index=False)
    loaded = dv.load_csv(path)
    assert list(loaded.columns) == ["month", "revenue", "region"]
    assert len(loaded) == 4


def test_load_csv_missing_file_raises():
    with pytest.raises(FileNotFoundError):
        dv.load_csv("does/not/exist.csv")


def test_summary_statistics(df):
    assert dv.summary_statistics(df).loc["count", "revenue"] == 3


def test_missing_value_counts(df):
    missing = dv.missing_value_counts(df)
    assert missing.iloc[0] == 1
    assert missing["revenue"] == 1


# --- theme -----------------------------------------------------------------


def test_available_themes():
    assert set(dv.available_themes()) == {"light", "dark"}


def test_theme_leads_with_blue():
    assert dv.theme_tokens("light")["accent"] == "#339CFF"
    assert dv.theme_tokens("light")["emphasis"] == "#B4652C"
    assert dv.theme_tokens("light")["series"][0] == "#339CFF"


def test_theme_tokens_are_copies():
    t = dv.theme_tokens("light")
    t["series"][0] = "#000000"
    assert dv.theme_tokens("light")["series"][0] != "#000000"


def test_theme_tokens_unknown_raises():
    with pytest.raises(KeyError):
        dv.theme_tokens("solarized")


def test_set_theme_updates_color_cycle():
    dv.set_theme("dark")
    colors = plt.rcParams["axes.prop_cycle"].by_key()["color"]
    assert colors[0] == dv.theme_tokens("dark")["accent"]


# --- charts ----------------------------------------------------------------


def test_line_plot_returns_axes(df):
    ax = dv.line_plot(df, x="month", y="revenue")
    assert ax.get_xlabel() == "month"
    assert len(ax.lines) >= 1


def test_bar_plot_returns_axes(df):
    ax = dv.bar_plot(df, x="region", y="month")
    assert len(ax.patches) == 4


def test_bar_by_sign_colors_and_zero_line():
    d = pd.DataFrame({"q": ["A", "B", "C"], "delta": [12, -5, 8]})
    ax = dv.bar_plot(d, x="q", y="delta", by_sign=True)
    accent = dv.theme_tokens()["accent"]
    negative = dv.theme_tokens()["negative"]
    faces = [plt.matplotlib.colors.to_hex(p.get_facecolor()).lower()
             for p in ax.patches]
    assert faces[0] == accent.lower()
    assert faces[1] == negative.lower()
    assert any(abs(ln.get_ydata()[0]) < 1e-9 for ln in ax.lines)


def test_bar_highlight_uses_muted_for_others():
    d = pd.DataFrame({"region": ["N", "S", "E"], "sales": [3, 5, 4]})
    ax = dv.bar_plot(d, x="region", y="sales", highlight="S")
    faces = [plt.matplotlib.colors.to_hex(p.get_facecolor()).lower()
             for p in ax.patches]
    assert faces[1] == dv.theme_tokens()["accent"].lower()
    assert faces[0] == dv.theme_tokens()["muted"].lower()


def test_scatter_plot_returns_axes(df):
    ax = dv.scatter_plot(df, x="month", y="revenue")
    assert len(ax.collections) == 1


def test_scatter_trendline_adds_line(df):
    ax = dv.scatter_plot(df, x="month", y="revenue", trendline=True)
    assert len(ax.lines) == 1


def test_hist_plot_has_bars_and_density_line():
    import numpy as np
    d = pd.DataFrame({"v": np.random.default_rng(0).normal(0, 1, 500)})
    ax = dv.hist_plot(d, column="v", bins=20)
    assert len(ax.patches) == 20        # histogram bars
    assert len(ax.lines) == 1           # overlaid density curve


def test_title_is_left_aligned(df):
    ax = dv.line_plot(df, x="month", y="revenue", title="Revenue climbs")
    assert ax.get_title(loc="left") == "Revenue climbs"


def test_missing_column_raises_clear_error(df):
    with pytest.raises(KeyError, match="nope"):
        dv.line_plot(df, x="month", y="nope")


def test_transparent_axes_background(df):
    ax = dv.bar_plot(df, x="region", y="month")
    assert ax.patch.get_alpha() == 0
