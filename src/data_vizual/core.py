"""data_vizual core (MVP): pandas + matplotlib helpers with a playful, softly
dimensional look — blue-led palette, soft shadows, quiet axes. Light/dark."""

from __future__ import annotations
from pathlib import Path

import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from cycler import cycler

# --- Theme tokens: the single source of truth for the visual system. Blue
# carries most of the weight; burnt orange is the emphasis color. Shadows give
# marks tactile depth without bulky cards.
THEMES = {
    "light": dict(
        page="#f4f1ea", primary="#1A1C1F", secondary="#4a4d52", muted="#8a8d92",
        grid="#1A1C1F", grid_alpha=0.10, baseline="#c9ccd1", outline="#ffffff",
        accent="#339CFF", emphasis="#B4652C", negative="#E25507",
        series=["#339CFF", "#B4652C", "#5DC977", "#3AB9B1", "#7E5A8C"],
        sd="#1A1C1F", sd_a=0.12, sl="#ffffff", sl_a=0.82,
    ),
    # Dark = Rosé Pine Moon: navy base, pine (blue) accent, gold emphasis, love
    # for negative, and a pine/gold/love/foam/iris series.
    "dark": dict(
        page="#232136", primary="#e0def4", secondary="#908caa", muted="#6e6a86",
        grid="#908caa", grid_alpha=0.14, baseline="#44415a", outline="#232136",
        accent="#3e8fb0", emphasis="#f6c177", negative="#eb6f92",
        series=["#3e8fb0", "#f6c177", "#eb6f92", "#9ccfd8", "#c4a7e7"],
        sd="#191724", sd_a=0.55, sl="#e0def4", sl_a=0.05,
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
        "font.weight": "regular", "axes.titleweight": "medium",
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

_MOTIFS = ("vertical", "waves", "dots", "grid", "scribble")

def _shadow(scale: float = 1.0) -> list:
    """A soft raised drop-shadow (down-right) giving each mark tactile depth."""
    t = theme_tokens()
    return [pe.SimplePatchShadow(offset=(3.5 * scale, -3.5 * scale),
                                 shadow_rgbFace=t["sd"], alpha=t["sd_a"] * 1.3),
            pe.Normal()]

def _pattern(ax, patch, kind, color, x0, x1, top, a=0.7):
    """Texture a bar by clipping an editorial motif inside it: parallel lines,
    hand-drawn waves/scribble, a dot field, or a grid — all pure matplotlib."""
    xs = np.linspace(x0, x1, 120)
    row = max(abs(top), 1) / 22
    clip = lambda art: art.set_clip_path(patch)
    if kind in ("vertical", "grid"):
        for gx in np.arange(x0, x1, (x1 - x0) / 7):
            clip(ax.plot([gx, gx], [0, top], color=color, lw=1, alpha=a, zorder=7)[0])
    if kind in ("horizontal", "grid"):
        for gy in np.arange(0, top, row):
            clip(ax.plot([x0, x1], [gy, gy], color=color, lw=1, alpha=a, zorder=7)[0])
    if kind in ("waves", "scribble"):
        f, amp = (18, .30) if kind == "waves" else (55, .12)
        for gy in np.arange(0, top, row):
            clip(ax.plot(xs, gy + row * amp * np.sin(xs * f),
                         color=color, lw=1, alpha=a, zorder=7)[0])
    if kind == "dots":
        gx, gy = np.meshgrid(np.arange(x0, x1, (x1 - x0) / 7), np.arange(row, top, row))
        clip(ax.scatter(gx.ravel(), gy.ravel(), s=6, color=color, alpha=a, zorder=7))

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
    if x:
        ax.set_xlabel(x)
    if y:
        ax.set_ylabel(y)
    if title:
        ax.set_title(title, loc="left")
    return ax

def line_plot(df, x, y, ax=None, title=None, color=None, label=None, marker="o",
              fill=False):
    """Line chart: a solid rounded line with a soft shadow and open markers;
    fill=True adds a soft editorial area tint beneath it."""
    ax = _axes(ax)
    t = theme_tokens()
    c = color or t["accent"]
    if fill:
        ax.fill_between(df[x], df[y], df[y].min(), color=c, alpha=0.15, zorder=2)
    (ln,) = ax.plot(df[x], df[y], color=c, label=label, linewidth=3.4,
                    solid_capstyle="round", solid_joinstyle="round", zorder=3)
    ln.set_path_effects([pe.SimpleLineShadow(offset=(0, -2.2), shadow_color=t["sd"],
                                             alpha=t["sd_a"] * 1.4), pe.Normal()])
    if marker:
        ax.plot(df[x], df[y], ls="none", marker=marker, ms=8,
                markerfacecolor=t["page"], markeredgecolor=c,
                markeredgewidth=2, zorder=4)
    return _style(ax, title, x, y)

def bar_plot(df, x, y, ax=None, title=None, color=None, by_sign=False,
             highlight=None, show_values=True, pattern=None):
    """Bars: softly raised with a shadow and direct value labels. Color by sign,
    highlight one, or (pattern=True) give each bar an editorial series color and
    a clipped motif; pattern="waves" applies one motif to every bar."""
    ax = _axes(ax)
    t = theme_tokens()
    if by_sign:
        colors = [t["accent"] if v >= 0 else t["negative"] for v in df[y]]
    elif highlight is not None:
        colors = [t["accent"] if c == highlight else t["muted"] for c in df[x]]
    elif pattern is True:
        colors = [t["series"][i % len(t["series"])] for i in range(len(df))]
    else:
        colors = color or t["accent"]
    bars = ax.bar(df[x], df[y], color=colors, edgecolor=t["outline"],
                  linewidth=1.5, width=0.72)
    for i, b in enumerate(bars):
        b.set_path_effects(_shadow())
        if pattern:
            kind = _MOTIFS[i % len(_MOTIFS)] if pattern is True else pattern
            _pattern(ax, b, kind, t["outline"], b.get_x(),
                     b.get_x() + b.get_width(), b.get_height())
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
    """Scatter: translucent blue points with a soft shadow; optional burnt-orange
    linear trend line."""
    ax = _axes(ax)
    t = theme_tokens()
    xs, ys = np.asarray(df[x], float), np.asarray(df[y], float)
    pts = ax.scatter(xs, ys, color=color or t["accent"], s=70, alpha=0.72,
                     edgecolors=t["outline"], linewidths=1.5, zorder=3)
    pts.set_path_effects(_shadow())
    if trendline and len(xs) >= 2:
        m, b = np.polyfit(xs, ys, 1)
        lx = np.array([xs.min(), xs.max()])
        ax.plot(lx, m * lx + b, color=t["emphasis"], linewidth=3,
                solid_capstyle="round", zorder=4)
    return _style(ax, title, x, y)

def hist_plot(df, column, bins=20, ax=None, title=None, color=None,
              pattern="vertical"):
    """Histogram with a smooth density curve (the distribution line) overlaid;
    bars carry the same editorial motif fill as bar_plot (pattern=None for solid)."""
    ax = _axes(ax)
    t = theme_tokens()
    v = np.asarray(df[column], float)
    v = v[~np.isnan(v)]
    counts, edges, patches = ax.hist(v, bins=bins, color=color or t["accent"],
                                     edgecolor=t["outline"], linewidth=1)
    for p, lo, hi in zip(patches, edges[:-1], edges[1:]):
        p.set_path_effects(_shadow(0.6))
        if pattern:
            _pattern(ax, p, pattern, t["outline"], lo, hi, p.get_height(), a=0.5)
    g = np.linspace(v.min(), v.max(), 200)
    h = 1.06 * v.std() * len(v) ** -0.2 or 1.0           # Silverman bandwidth
    d = np.exp(-((g[:, None] - v) / h) ** 2 / 2).sum(1) / (len(v) * h * 2.5066)
    ax.plot(g, d * (counts.max() / (d.max() or 1)), color=t["emphasis"],
            linewidth=3, solid_capstyle="round", zorder=4)
    return _style(ax, title, column, "count")
