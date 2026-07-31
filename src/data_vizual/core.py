"""data_vizual core (MVP): pandas + matplotlib helpers with a clean, minimal
look — a two-color palette (burnt orange led, cream + plum in support), quiet
unframed axes, and faint gridlines. Light/dark.

Colour discipline: any single chart shows at most **two** of the three brand
hues, never all three at once, so nothing tips into colour overload. Orange
is the constant accent; cream and plum are the alternating second colour."""

from __future__ import annotations
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from cycler import cycler
from matplotlib.ticker import FuncFormatter

# --- Theme tokens: the single source of truth for the visual system. Burnt
# orange (#C44900) carries the data; cream (#EFD6AC) is the soft fill/second
# colour; plum (#432534) is the alternate used for emphasis, trend lines and
# negatives. Text always wears neutral ink, never a brand hue, so the two
# brand colours stay the only "colour" the eye has to track.
THEMES = {
    "light": dict(
        page="#FBF7F0", primary="#2B1A22", secondary="#6b5560", muted="#9c8a80",
        grid="#2B1A22", grid_alpha=0.08, baseline="#dccdb9", outline="#FBF7F0",
        accent="#C44900", support="#EFD6AC", emphasis="#432534", negative="#432534",
        series=["#C44900", "#432534", "#EFD6AC"],
    ),
    "dark": dict(
        page="#22171C", primary="#EFE3D5", secondary="#bcaea2", muted="#8a7c72",
        grid="#EFE3D5", grid_alpha=0.10, baseline="#4a3b42", outline="#22171C",
        accent="#C44900", support="#EFD6AC", emphasis="#EFD6AC", negative="#EFD6AC",
        series=["#C44900", "#EFD6AC", "#432534"],
    ),
}
_active = "light"

def available_themes() -> tuple:
    """Names of the built-in themes."""
    return tuple(THEMES)

def theme_tokens(mode: str | None = None) -> dict:
    """A copy of a theme's design tokens (defaults to the active theme)."""
    mode = mode or _active
    if mode not in THEMES:
        raise KeyError(f"Unknown theme {mode!r}. Choose from {available_themes()}.")
    t = dict(THEMES[mode])
    t["series"] = list(t["series"])
    return t

def set_theme(mode: str = "light") -> dict:
    """Apply a theme to matplotlib globally (call once); returns its tokens."""
    global _active
    t = theme_tokens(mode)
    _active = mode
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["system-ui", "-apple-system", "Helvetica Neue",
                            "Arial", "DejaVu Sans"],
        "font.weight": "normal", "axes.titleweight": "bold",
        "axes.titlesize": 15, "axes.titlelocation": "left", "axes.titlepad": 12,
        "axes.labelsize": 11, "figure.facecolor": t["page"],
        "savefig.facecolor": t["page"], "axes.facecolor": "none",
        "text.color": t["primary"], "axes.titlecolor": t["primary"],
        "axes.labelcolor": t["secondary"], "xtick.color": t["muted"],
        "ytick.color": t["muted"], "xtick.labelcolor": t["secondary"],
        "ytick.labelcolor": t["secondary"], "axes.edgecolor": t["baseline"],
        "axes.prop_cycle": cycler(color=t["series"]), "figure.figsize": (7, 4.5),
        "figure.dpi": 110, "savefig.dpi": 150, "savefig.bbox": "tight",
        "legend.frameon": False,
    })
    return t

def load_csv(path, **read_csv_kwargs) -> pd.DataFrame:
    """Read a CSV into a DataFrame (clear error if the file is missing)."""
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"No CSV file found at: {p}")
    return pd.read_csv(p, **read_csv_kwargs)

def summary_statistics(df: pd.DataFrame) -> pd.DataFrame:
    """describe() for the numeric columns."""
    return df.describe()

def missing_value_counts(df: pd.DataFrame) -> pd.Series:
    """Missing values per column, highest first."""
    return df.isna().sum().sort_values(ascending=False)

def _tick(v, _pos=None) -> str:
    """Readable y labels: thousands separators for big numbers, tidy otherwise."""
    if abs(v) >= 1000:
        return f"{v:,.0f}"
    return f"{v:g}"

def _axes(ax):
    """Return a themed Axes, creating a transparent-backed one if needed."""
    if ax is None:
        _, ax = plt.subplots()
        ax.set_prop_cycle(cycler(color=theme_tokens()["series"]))
    return ax

def _style(ax, title, x=None, y=None):
    """Quiet chrome: transparent bg, one baseline, faint y-grid, direct title."""
    t = theme_tokens()
    ax.patch.set_alpha(0)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(t["baseline"])
    ax.spines["bottom"].set_linewidth(0.8)
    ax.set_axisbelow(True)
    ax.grid(True, axis="y", color=t["grid"], alpha=t["grid_alpha"], linewidth=0.8)
    ax.grid(False, axis="x")
    ax.tick_params(length=0)
    ax.yaxis.set_major_formatter(FuncFormatter(_tick))
    if x:
        ax.set_xlabel(x)
    if y:
        ax.set_ylabel(y)
    if title:
        ax.set_title(title, loc="left")
    return ax

def line_plot(df, x, y, ax=None, title=None, color=None, label=None, marker="o",
              fill=False):
    """Line chart: a clean 2px line with open markers; fill=True adds a soft
    cream area tint beneath it (line + fill = two colours, never a third)."""
    ax = _axes(ax)
    t = theme_tokens()
    c = color or t["accent"]
    if fill:
        ax.fill_between(df[x], df[y], df[y].min(), color=t["support"],
                        alpha=0.55, linewidth=0, zorder=1)
    ax.plot(df[x], df[y], color=c, label=label, linewidth=2.4,
            solid_capstyle="round", solid_joinstyle="round", zorder=3)
    if marker:
        ax.plot(df[x], df[y], ls="none", marker=marker, ms=6,
                markerfacecolor=t["page"], markeredgecolor=c,
                markeredgewidth=1.8, zorder=4)
    return _style(ax, title, x, y)

def bar_plot(df, x, y, ax=None, title=None, color=None, by_sign=False,
             highlight=None, show_values=True):
    """Bars: flat, single-colour by default with direct value labels. `by_sign`
    colours by polarity (orange up / plum down), `highlight` accents one bar and
    greys the rest — at most two colours, so the comparison stays legible."""
    ax = _axes(ax)
    t = theme_tokens()
    if by_sign:
        colors = [t["accent"] if v >= 0 else t["negative"] for v in df[y]]
    elif highlight is not None:
        colors = [t["accent"] if c == highlight else t["muted"] for c in df[x]]
    else:
        colors = color or t["accent"]
    ax.bar(df[x], df[y], color=colors, edgecolor=t["page"], linewidth=1.2,
           width=0.7)
    if by_sign:
        ax.axhline(0, color=t["baseline"], linewidth=1, zorder=1)
    if show_values:
        for c, v in zip(df[x], df[y]):
            up = v >= 0
            ax.annotate(f"{v:,.0f}", (c, v), (0, 4 if up else -4),
                        textcoords="offset points", ha="center",
                        va="bottom" if up else "top", fontsize=9,
                        color=t["secondary"])
    return _style(ax, title, x, y)

def scatter_plot(df, x, y, ax=None, title=None, color=None, trendline=False):
    """Scatter: translucent orange points; optional plum linear trend line
    (points + trend = two colours)."""
    ax = _axes(ax)
    t = theme_tokens()
    xs, ys = np.asarray(df[x], float), np.asarray(df[y], float)
    ax.scatter(xs, ys, color=color or t["accent"], s=55, alpha=0.8,
               edgecolors=t["page"], linewidths=1, zorder=3)
    if trendline and len(xs) >= 2:
        m, b = np.polyfit(xs, ys, 1)
        lx = np.array([xs.min(), xs.max()])
        ax.plot(lx, m * lx + b, color=t["emphasis"], linewidth=2.4,
                solid_capstyle="round", zorder=4)
    return _style(ax, title, x, y)

def hist_plot(df, column, bins=20, ax=None, title=None, color=None):
    """Histogram with a smooth density curve (the distribution line) overlaid:
    solid orange bars, a plum density line — two colours, no third."""
    ax = _axes(ax)
    t = theme_tokens()
    v = np.asarray(df[column], float)
    v = v[~np.isnan(v)]
    counts, edges, patches = ax.hist(v, bins=bins, color=color or t["accent"],
                                     edgecolor=t["page"], linewidth=0.8)
    g = np.linspace(v.min(), v.max(), 200)
    h = 1.06 * v.std() * len(v) ** -0.2 or 1.0           # Silverman bandwidth
    d = np.exp(-((g[:, None] - v) / h) ** 2 / 2).sum(1) / (len(v) * h * 2.5066)
    ax.plot(g, d * (counts.max() / (d.max() or 1)), color=t["emphasis"],
            linewidth=2.4, solid_capstyle="round", zorder=4)
    return _style(ax, title, column, "count")
