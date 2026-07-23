"""Core helpers for data_vizual.

This single module holds the library's building blocks, grouped into four
plain-function sections:

    0. Design tokens & theme -> the visual language (light / dark)
    1. Loading data          -> get a CSV into a pandas DataFrame
    2. Summarizing data      -> quick answers about shape, types, and gaps
    3. Plotting data         -> styled matplotlib charts you can build on

Everything is a small, single-purpose function (no god class) that returns a
standard pandas or matplotlib object. That keeps each piece easy to read, test,
and debug, and lets you compose them however you like.

Design language
---------------
The defaults aim for a quiet, precise, presentation-ready look: the data is the
loudest element, chrome (axes, ticks, gridlines) recedes to hairlines, type is a
clean system sans, and the color palette is a restrained, colorblind-safe set.
Both light and dark themes ship. Call :func:`set_theme` once to pick a mode; the
plot functions also style each Axes individually, so charts look right even if
you never touch the global theme.

Conventions (see CLAUDE.md):
    - pandas, not polars
    - matplotlib only for plotting
"""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from cycler import cycler
from matplotlib.ticker import FuncFormatter

# ---------------------------------------------------------------------------
# 0. Design tokens & theme
# ---------------------------------------------------------------------------
#
# Tokens are the single source of truth for the visual language. Everything the
# plots draw pulls its colors from here, so re-theming (or swapping in your own
# brand palette) is a one-place edit rather than a hunt through the code.
#
# The categorical order is deliberate, not cosmetic: it is a colorblind-safe
# sequence, so the first N colors of any chart stay distinguishable. Assign in
# order; never shuffle or cycle beyond the list.

# Font stack: a clean system sans everywhere. DejaVu Sans is matplotlib's
# always-available fallback, so text renders even where system fonts are absent.
_FONT_STACK = [
    "system-ui",
    "-apple-system",
    "Segoe UI",
    "Helvetica Neue",
    "Arial",
    "DejaVu Sans",
]

# The design language is NEUTRAL-FIRST: ~80–90% of every chart is neutral
# (surfaces, ink, gridlines, axes). Color is spent deliberately — on the
# primary series, a highlighted item, a category, or a status — never as
# decoration. Blue is the accent of emphasis, not a background or a default for
# everything.
#
# Series colors are STABLE across the library: series 1 is always blue, series 2
# always orange, and so on, in both light and dark, so a color means the same
# thing everywhere. Per the never-color-alone rule, series color is always
# paired with a marker, line style, or direct label by the caller.
_APPLE_PALETTE = [
    "#007AFF",  # 1 blue   (also the accent / primary-emphasis color)
    "#FF9500",  # 2 orange
    "#34C759",  # 3 green
    "#AF52DE",  # 4 purple
    "#FF3B30",  # 5 red
    "#5AC8FA",  # 6 teal
]

# Semantic colors are reserved for meaning and never reused as "series 7".
_SEMANTIC = {
    "good": "#34C759",     # positive / success
    "warning": "#FF9500",  # caution
    "bad": "#FF3B30",      # negative / failure / destructive
    "neutral": "#86868B",  # neutral / inactive
}

_THEMES: dict[str, dict] = {
    "light": {
        # Neutral surfaces and ink (Apple-like near-black on white).
        "surface": "#ffffff",   # chart background — pure neutral
        "page": "#f5f5f7",      # figure background — near-white
        "primary": "#1d1d1f",   # titles / strongest text (near-black)
        "secondary": "#6e6e73",  # axis labels / tick text (gray)
        "muted": "#86868b",     # ticks / de-emphasized (gray)
        "grid": "#e8e8ed",      # hairline gridlines (subtle gray)
        "baseline": "#d2d2d7",  # axis spines (subtle gray)
        # Deliberate color.
        "accent": "#007AFF",    # the one point of emphasis (primary series)
        "series": list(_APPLE_PALETTE),
        # Comparison roles.
        "context": "#86868B",   # de-emphasized "context" series (use with alpha)
        "reference": "#d2d2d7",  # baselines / reference lines
        **_SEMANTIC,
    },
    "dark": {
        # Neutral charcoal/black surfaces with light ink.
        "surface": "#1c1c1e",   # chart background — charcoal
        "page": "#000000",      # figure background — black
        "primary": "#f5f5f7",   # titles / strongest text (near-white)
        "secondary": "#aeaeb2",  # axis labels / tick text (gray)
        "muted": "#8e8e93",     # ticks / de-emphasized (gray)
        "grid": "#2c2c2e",      # hairline gridlines (subtle gray)
        "baseline": "#3a3a3c",  # axis spines (subtle gray)
        "accent": "#007AFF",    # same blue identity as light
        "series": list(_APPLE_PALETTE),  # identical hues -> stable identity
        "context": "#86868B",
        "reference": "#48484a",  # darker reference gray for the dark surface
        **_SEMANTIC,
    },
}

# The theme new charts use by default. Kept as module state so a single
# set_theme() call changes every subsequent plot, matching the familiar
# matplotlib/seaborn "set it once" workflow.
_active_mode = "light"


def available_themes() -> tuple[str, ...]:
    """Return the names of the built-in themes.

    Returns
    -------
    tuple of str
        Currently ``("light", "dark")``.
    """
    return tuple(_THEMES)


def theme_tokens(mode: str | None = None) -> dict:
    """Return a copy of the design tokens for a theme.

    Useful when you want to match the library's colors in your own custom
    drawing (e.g. pick ``theme_tokens()["series"][0]`` for a highlight).

    Parameters
    ----------
    mode:
        Theme name (``"light"`` or ``"dark"``). Defaults to the active theme.

    Returns
    -------
    dict
        A copy of the token dictionary (safe to mutate without side effects).

    Raises
    ------
    KeyError
        If ``mode`` is not a known theme.
    """
    mode = mode or _active_mode
    if mode not in _THEMES:
        raise KeyError(f"Unknown theme {mode!r}. Choose from {available_themes()}.")
    # Return a copy so callers can't accidentally mutate the shared tokens.
    tokens = dict(_THEMES[mode])
    tokens["series"] = list(tokens["series"])
    return tokens


def set_theme(mode: str = "light") -> dict:
    """Apply a theme's tokens to matplotlib's global defaults.

    Call this once at the top of a script or notebook. It sets typography, the
    color cycle, background surfaces, and subtle chrome so that *every*
    subsequent chart — including plain ``matplotlib`` calls — inherits the
    look. The individual plot functions apply the same styling per-Axes, so you
    only strictly need this to pick light vs. dark and to affect your own
    matplotlib code.

    Parameters
    ----------
    mode:
        ``"light"`` (default) or ``"dark"``.

    Returns
    -------
    dict
        The tokens that were applied (handy for reuse).

    Raises
    ------
    KeyError
        If ``mode`` is not a known theme.
    """
    global _active_mode
    tokens = theme_tokens(mode)
    _active_mode = mode

    plt.rcParams.update(
        {
            # Typography: one clean sans, a clear size hierarchy, left-aligned
            # titles so the headline reads like a sentence, not a caption.
            "font.family": "sans-serif",
            "font.sans-serif": _FONT_STACK,
            "axes.titlesize": 15,
            "axes.titleweight": "semibold",
            "axes.titlelocation": "left",
            "axes.titlepad": 12,
            "axes.labelsize": 11,
            "xtick.labelsize": 10,
            "ytick.labelsize": 10,
            "legend.fontsize": 10,
            # Restrained, cohesive color: surfaces, ink, and the categorical
            # cycle all come from the tokens.
            "figure.facecolor": tokens["page"],
            "axes.facecolor": tokens["surface"],
            "savefig.facecolor": tokens["page"],
            "text.color": tokens["primary"],
            "axes.titlecolor": tokens["primary"],
            "axes.labelcolor": tokens["secondary"],
            "xtick.color": tokens["muted"],
            "ytick.color": tokens["muted"],
            "xtick.labelcolor": tokens["secondary"],
            "ytick.labelcolor": tokens["secondary"],
            "axes.edgecolor": tokens["baseline"],
            "grid.color": tokens["grid"],
            "axes.prop_cycle": cycler(color=tokens["series"]),
            # Subtle chrome: hairlines everywhere, data drawn above the grid.
            "axes.linewidth": 0.8,
            "axes.axisbelow": True,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "grid.linewidth": 0.8,
            "xtick.major.width": 0.8,
            "ytick.major.width": 0.8,
            "xtick.major.size": 3,
            "ytick.major.size": 3,
            # Marks: 2px lines with round ends, comfortably sized markers.
            "lines.linewidth": 2.0,
            "lines.solid_capstyle": "round",
            "lines.solid_joinstyle": "round",
            "lines.markersize": 6,
            # Frameless legends — the box is chart clutter; the swatch is enough.
            "legend.frameon": False,
            # A sensible, presentation-friendly default canvas.
            "figure.figsize": (7.0, 4.5),
            "figure.dpi": 110,
            "savefig.dpi": 150,
            "savefig.bbox": "tight",
        }
    )
    return tokens


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
#   - accepts an optional ``title`` (the one takeaway) and ``color`` override
#   - accepts an optional ``ax`` so plots can be placed on your own figure
#   - creates a themed figure/axes when ``ax`` is not given
#   - returns the matplotlib ``Axes`` so you can keep customizing
#
# Returning the Axes rather than calling ``plt.show()`` inside the function is
# the standard, debuggable pattern: nothing is hidden and you stay in control.


def _format_number(value: float) -> str:
    """Format a tick value: thousands-grouped, no noisy trailing ``.0``.

    ``1000`` -> ``"1,000"``, ``325.0`` -> ``"325"``, ``0.5`` -> ``"0.5"``.
    Consistent number formatting is a small thing that makes charts look
    finished.
    """
    if float(value).is_integer():
        return format(int(value), ",")   # whole numbers: drop the decimal
    return format(value, ",")            # keep real decimals as-is


def _comma_formatter() -> FuncFormatter:
    """Tick formatter applying :func:`_format_number` to the value axis."""
    return FuncFormatter(lambda value, _pos: _format_number(value))


def _require_columns(df: pd.DataFrame, columns: Sequence[str]) -> None:
    """Raise a clear error if any requested column is missing.

    matplotlib/pandas would eventually raise a ``KeyError``, but naming the
    missing column *and* listing what's available turns a debugging session
    into a one-line fix.
    """
    missing = [c for c in columns if c not in df.columns]
    if missing:
        raise KeyError(
            f"Column(s) {missing} not found. "
            f"Available columns: {list(df.columns)}"
        )


def _new_axes() -> plt.Axes:
    """Create a fresh themed figure and Axes.

    Applies the active theme's surfaces and categorical color cycle up front so
    that even without a global :func:`set_theme` call, a brand-new chart is
    already on-palette.
    """
    tokens = theme_tokens()
    fig, ax = plt.subplots()
    fig.set_facecolor(tokens["page"])
    ax.set_facecolor(tokens["surface"])
    ax.set_prop_cycle(cycler(color=tokens["series"]))
    return ax


def _style_axes(ax: plt.Axes) -> None:
    """Apply the quiet, presentation-ready chrome to an Axes.

    Idempotent and safe to call on any Axes (including one the caller passed
    in): it only touches chrome — spines, ticks, gridlines, colors — never the
    data. This is what keeps the look consistent across every chart type.
    """
    tokens = theme_tokens()

    # Let the data dominate: hide the top/right frame, keep the remaining
    # spines as hairlines in the recessive baseline color.
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_visible(True)
        ax.spines[side].set_color(tokens["baseline"])
        ax.spines[side].set_linewidth(0.8)

    # A single, horizontal hairline grid sitting *behind* the data. Consistent
    # across chart types so the family reads as one system.
    ax.set_axisbelow(True)
    ax.grid(True, axis="y", color=tokens["grid"], linewidth=0.8)
    ax.grid(False, axis="x")

    # Muted ticks, readable tick labels.
    ax.tick_params(colors=tokens["muted"], length=3, width=0.8,
                   labelcolor=tokens["secondary"])

    # Consistent thousands grouping on the value axis.
    ax.yaxis.set_major_formatter(_comma_formatter())


def _render_empty(ax: plt.Axes, message: str = "No data to display") -> plt.Axes:
    """Draw a clean, centered placeholder for an empty dataset.

    A useful empty state beats a blank or broken-looking chart: strip the
    chrome and show a quiet message so the reader knows the chart worked but
    had nothing to plot.
    """
    tokens = theme_tokens()
    ax.set_facecolor(tokens["surface"])
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.text(
        0.5, 0.5, message,
        transform=ax.transAxes, ha="center", va="center",
        color=tokens["muted"], fontsize=12,
    )
    return ax


def _finish(ax: plt.Axes, title: str | None) -> plt.Axes:
    """Apply chrome and the optional title, then return the Axes.

    Small shared tail so every plot ends the same way — one place to adjust the
    common finishing touches.
    """
    _style_axes(ax)
    if title:
        # The single takeaway, left-aligned like a headline.
        ax.set_title(title, loc="left")
    return ax


def direct_label(
    ax: plt.Axes,
    x,
    y,
    text: str,
    color: str | None = None,
) -> plt.Axes:
    """Place a direct label next to a point on an existing chart.

    Direct labels are often clearer than a legend: put the name right where the
    data is. Use sparingly — label the endpoint or the one series that tells
    the story, not every point.

    Parameters
    ----------
    ax:
        The Axes to annotate.
    x, y:
        Data coordinates the label points at.
    text:
        The label text.
    color:
        Optional text color. Defaults to the theme's secondary ink (text should
        wear text colors, not the data color).

    Returns
    -------
    matplotlib.axes.Axes
        The same Axes, for chaining.
    """
    tokens = theme_tokens()
    ax.annotate(
        text,
        xy=(x, y),
        xytext=(6, 0),
        textcoords="offset points",
        va="center",
        fontsize=10,
        color=color or tokens["secondary"],
    )
    return ax


def line_plot(
    df: pd.DataFrame,
    x: str,
    y: str,
    ax: plt.Axes | None = None,
    title: str | None = None,
    color: str | None = None,
    label: str | None = None,
    alpha: float = 1.0,
    marker: str | None = None,
    linestyle: str = "-",
) -> plt.Axes:
    """Draw a line chart of ``y`` against ``x``.

    Best for showing how a value changes over an ordered axis such as time. On a
    fresh Axes the first line takes the accent blue (a single series is the one
    point of emphasis); call it repeatedly on the same ``ax`` to add more series,
    each taking the next stable palette color.

    Parameters
    ----------
    df:
        The data to plot.
    x, y:
        Column names for the horizontal and vertical axes.
    ax:
        Optional existing Axes to draw on. If omitted, a new themed figure is
        created.
    title:
        Optional headline stating the chart's single takeaway.
    color:
        Optional line color. Defaults to the next color in the theme cycle.
        Pass ``theme_tokens()["context"]`` (with a lower ``alpha``) to render a
        de-emphasized context series in a comparison.
    label:
        Optional series name (used by a legend or direct label).
    alpha:
        Line opacity. Lower it (e.g. 0.5) to push a context series back.
    marker:
        Optional point marker (e.g. ``"o"``, ``"s"``, ``"^"``). Pairing each
        series with a distinct marker keeps them distinguishable without relying
        on color alone.
    linestyle:
        Line style (e.g. ``"-"``, ``"--"``, ``":"``) — another color-free way to
        tell series apart.

    Returns
    -------
    matplotlib.axes.Axes
        The Axes containing the plot.
    """
    ax = ax if ax is not None else _new_axes()
    if len(df) == 0:
        return _render_empty(ax)
    _require_columns(df, [x, y])

    ax.plot(df[x], df[y], color=color, label=label, alpha=alpha,
            marker=marker, linestyle=linestyle)
    ax.set_xlabel(x)
    ax.set_ylabel(y)
    return _finish(ax, title)


def _x_to_numbers(values: pd.Series) -> np.ndarray:
    """Convert an x column to floats matplotlib can place on an axis.

    Dates become matplotlib date numbers (the same units the axis uses), so a
    gradient image lines up with the plotted line. Everything else is coerced
    to float.
    """
    if np.issubdtype(np.asarray(values).dtype, np.datetime64):
        return mdates.date2num(values)
    return np.asarray(values, dtype=float)


def _blend(color_a: str, color_b: str, weight: float) -> tuple[float, float, float]:
    """Mix two colors: ``weight`` of ``color_b`` into ``color_a`` (0..1)."""
    a = np.array(plt.matplotlib.colors.to_rgb(color_a))
    b = np.array(plt.matplotlib.colors.to_rgb(color_b))
    return tuple(a * (1 - weight) + b * weight)


def _gradient_fill(ax: plt.Axes, x: np.ndarray, y: np.ndarray, color: str) -> None:
    """Fill under a curve with a rich vertical *color* gradient for depth.

    Rather than fading to transparent, the fill shifts hue top-to-bottom: the
    full series color sits just under the line, easing to a lighter tint of the
    same color toward the baseline. The tint blends toward the theme surface, so
    the effect reads as depth in both light and dark modes. Opacity stays high
    (a solid fill), giving the "shaded" look of an editorial area chart while
    the crisp top edge keeps the value legible.
    """
    tokens = theme_tokens()
    baseline = min(0.0, float(np.nanmin(y)))

    # Row 0 is the baseline (origin="lower"): a light tint of the color; the top
    # row under the line is the full color. 60% toward the surface at the base
    # gives a clear gradient without washing the color out entirely.
    bottom_rgb = _blend(color, tokens["surface"], 0.60)
    top_rgb = plt.matplotlib.colors.to_rgb(color)

    ramp = np.linspace(0.0, 1.0, 256)[:, None]           # 0 at baseline, 1 at top
    gradient = np.empty((256, 1, 4))
    gradient[:, 0, :3] = np.array(bottom_rgb) + ramp * (np.array(top_rgb) - bottom_rgb)
    gradient[:, 0, 3] = 0.35 + ramp[:, 0] * 0.55         # 0.35 -> 0.90 opacity

    image = ax.imshow(
        gradient, aspect="auto", origin="lower",
        extent=[x.min(), x.max(), baseline, float(np.nanmax(y))],
        zorder=1,
    )
    # Clip the image to the polygon under the curve so only that region shows.
    vertices = np.column_stack([np.concatenate([x, x[::-1]]),
                                np.concatenate([y, np.full_like(y, baseline)])])
    clip = plt.Polygon(vertices, closed=True, transform=ax.transData)
    image.set_clip_path(clip)


def area_plot(
    df: pd.DataFrame,
    x: str,
    y: str,
    ax: plt.Axes | None = None,
    title: str | None = None,
    color: str | None = None,
    gradient: bool = True,
) -> plt.Axes:
    """Draw a filled area chart of ``y`` against ``x``, with optional depth.

    Like :func:`line_plot`, but the region under the line is filled. By default
    the fill uses a subtle vertical gradient (richer under the line, fading to
    the baseline) that adds depth without shouting. Set ``gradient=False`` for a
    flat, low-opacity wash instead.

    Best for emphasizing magnitude over time — the area reads as "how much",
    while the crisp top edge keeps the exact value legible.

    Parameters
    ----------
    df:
        The data to plot.
    x, y:
        Column names for the horizontal and vertical axes.
    ax:
        Optional existing Axes to draw on. If omitted, a new themed figure is
        created.
    title:
        Optional headline stating the chart's single takeaway.
    color:
        Optional fill/line color. Defaults to the theme's first categorical
        color.
    gradient:
        If ``True`` (default), fill with a vertical depth gradient; if
        ``False``, use a flat ~12%-opacity wash.

    Returns
    -------
    matplotlib.axes.Axes
        The Axes containing the plot.
    """
    ax = ax if ax is not None else _new_axes()
    if len(df) == 0:
        return _render_empty(ax)
    _require_columns(df, [x, y])

    tokens = theme_tokens()
    fill_color = color or tokens["accent"]

    # A crisp 2px top edge defines the value; the fill below carries the depth.
    ax.plot(df[x], df[y], color=fill_color, zorder=3)
    if gradient:
        _gradient_fill(ax, _x_to_numbers(df[x]), np.asarray(df[y], dtype=float),
                       fill_color)
    else:
        ax.fill_between(df[x], df[y], color=fill_color, alpha=0.12, zorder=1)

    ax.set_xlabel(x)
    ax.set_ylabel(y)
    ax.margins(x=0)  # let the fill meet the left/right edges, like the reference
    return _finish(ax, title)


def bar_plot(
    df: pd.DataFrame,
    x: str,
    y: str,
    ax: plt.Axes | None = None,
    title: str | None = None,
    color: str | None = None,
    by_sign: bool = False,
    highlight: object | None = None,
) -> plt.Axes:
    """Draw a bar chart of ``y`` for each category in ``x``.

    Best for comparing a numeric value across a set of discrete categories.

    By default all bars share the accent color (a single measure). Two options
    add *meaning* to the color instead of decoration:

    - ``by_sign=True`` colors each bar by the sign of ``y`` — green for
      positive, red for negative — and draws a zero reference line. Use for
      change / delta charts.
    - ``highlight=<category>`` paints every bar neutral gray except the named
      category, which takes the accent color. Use to point at one bar.

    Parameters
    ----------
    df:
        The data to plot.
    x:
        Column name for the categories (bars).
    y:
        Column name for the bar heights.
    ax:
        Optional existing Axes to draw on. If omitted, a new themed figure is
        created.
    title:
        Optional headline stating the chart's single takeaway.
    color:
        Optional single bar color (ignored when ``by_sign`` or ``highlight`` is
        set). Defaults to the accent color.
    by_sign:
        Color bars green/red by the sign of ``y`` and add a zero line.
    highlight:
        A value in ``x``; that bar is accent-colored and the rest neutral gray.

    Returns
    -------
    matplotlib.axes.Axes
        The Axes containing the plot.
    """
    ax = ax if ax is not None else _new_axes()
    if len(df) == 0:
        return _render_empty(ax)
    _require_columns(df, [x, y])

    tokens = theme_tokens()
    if by_sign:
        # Semantic color: the sign IS the message (positive vs negative).
        colors = [tokens["good"] if v >= 0 else tokens["bad"] for v in df[y]]
    elif highlight is not None:
        # Neutral-first: gray context, accent only on the bar being pointed at.
        colors = [tokens["accent"] if cat == highlight else tokens["neutral"]
                  for cat in df[x]]
    else:
        colors = color or tokens["accent"]

    # A 2px surface-colored edge reads as a clean gap between neighbors rather
    # than a heavy stroke; bars capped in width so the slot keeps some air.
    ax.bar(
        df[x], df[y],
        color=colors,
        edgecolor=tokens["surface"],
        linewidth=1.0,
        width=0.7,
    )
    if by_sign:
        # A quiet zero reference so positive/negative read against a baseline.
        ax.axhline(0, color=tokens["reference"], linewidth=1.0, zorder=1)

    ax.set_xlabel(x)
    ax.set_ylabel(y)
    return _finish(ax, title)


def histogram(
    df: pd.DataFrame,
    column: str,
    bins: int = 10,
    ax: plt.Axes | None = None,
    title: str | None = None,
    color: str | None = None,
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
        Optional existing Axes to draw on. If omitted, a new themed figure is
        created.
    title:
        Optional headline stating the chart's single takeaway.
    color:
        Optional bar color. Defaults to the theme's first categorical color.

    Returns
    -------
    matplotlib.axes.Axes
        The Axes containing the plot.
    """
    ax = ax if ax is not None else _new_axes()
    if len(df) == 0:
        return _render_empty(ax)
    _require_columns(df, [column])

    tokens = theme_tokens()
    ax.hist(
        df[column], bins=bins,
        color=color or tokens["accent"],
        edgecolor=tokens["surface"],
        linewidth=1.0,
    )
    ax.set_xlabel(column)
    ax.set_ylabel("Frequency")
    return _finish(ax, title)


def scatter_plot(
    df: pd.DataFrame,
    x: str,
    y: str,
    ax: plt.Axes | None = None,
    title: str | None = None,
    color: str | None = None,
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
        Optional existing Axes to draw on. If omitted, a new themed figure is
        created.
    title:
        Optional headline stating the chart's single takeaway.
    color:
        Optional marker color. Defaults to the theme's first categorical color.

    Returns
    -------
    matplotlib.axes.Axes
        The Axes containing the plot.
    """
    ax = ax if ax is not None else _new_axes()
    if len(df) == 0:
        return _render_empty(ax)
    _require_columns(df, [x, y])

    tokens = theme_tokens()
    # A thin surface-colored ring keeps overlapping points legible without
    # adding a heavy border.
    ax.scatter(
        df[x], df[y],
        color=color or tokens["accent"],
        s=42,
        edgecolors=tokens["surface"],
        linewidths=0.8,
        alpha=0.9,
    )
    ax.set_xlabel(x)
    ax.set_ylabel(y)
    return _finish(ax, title)
