# data_vizual

A small, pip-installable Python library of **bare-bones pandas helpers and
styled matplotlib plots** — the foundation for building your own personal data
visualization aesthetic.

This is the MVP of the `data_viz` project: it reduces the boilerplate of going
from a raw dataset to useful summaries and charts. Every function does exactly
one thing, has a conventional name, and returns a standard pandas or matplotlib
object, so the library stays easy to read, test, and debug.

## Installation

From a local clone (editable install for development):

```bash
pip install -e .
```

Once published, it will install the usual way:

```bash
pip install data_vizual
```

## Usage

```python
import data_vizual as dv

dv.set_theme("light")        # pick the visual language once ("light" or "dark")

# 1. Load
df = dv.load_csv("data/sales.csv")

# 2. Summarize
dv.column_types(df)          # dtype of each column
dv.missing_value_counts(df)  # missing values per column (highest first)
dv.summary_statistics(df)    # count / mean / std / min / quartiles / max

# 3. Plot  (each returns a matplotlib Axes you can keep customizing)
ax = dv.histogram(df, "revenue", bins=20, title="Revenue is right-skewed")

dv.line_plot(df, x="day", y="revenue", title="Revenue climbed all year")
dv.area_plot(df, x="day", y="revenue")   # gradient fill adds depth
dv.bar_plot(df, x="region", y="revenue")
dv.scatter_plot(df, x="ad_spend", y="revenue")
```

See it for yourself — the examples gallery renders every chart type in both
themes:

```bash
python examples/gallery.py          # writes gallery-light.png and gallery-dark.png
python examples/gallery.py --show   # or open interactive windows
```

## Design system

The design language is **neutral-first**: roughly 80–90% of every chart is
neutral (backgrounds, ink, gridlines, axes are white/near-white/charcoal and
gray). **Color is spent deliberately** — on the primary series, a highlighted
item, a category, or a status — never as decoration. Blue is the accent of
emphasis, not a theme. Two themes ship: **`light`** and **`dark`**.

**Color tokens** (read any with `dv.theme_tokens()`):

| Token | Role |
| --- | --- |
| `surface` / `page` | chart & figure backgrounds — neutral |
| `primary` / `secondary` / `muted` | text ink — near-black/white and gray |
| `grid` / `baseline` | hairline gridlines and axis spines — subtle gray |
| `accent` | the one point of emphasis — **blue `#007AFF`** |
| `series` | the 6-color categorical palette (stable identity) |
| `good` / `warning` / `bad` / `neutral` | reserved semantic colors |
| `context` / `reference` | de-emphasized comparison series & baselines |

**Series palette** — stable identity across the library (series 1 is always
blue, 2 orange, …), identical in light and dark so a color means one thing:

| 1 blue | 2 orange | 3 green | 4 purple | 5 red | 6 teal |
| --- | --- | --- | --- | --- | --- |
| `#007AFF` | `#FF9500` | `#34C759` | `#AF52DE` | `#FF3B30` | `#5AC8FA` |

**Where color is (and isn't) used**

- **Single series** → the accent blue (the subject is the emphasis).
- **Multiple series** → the palette in order, always paired with a marker,
  line style, or direct label (never color alone). `line_plot(..., marker="o",
  linestyle="--")`.
- **Highlight a comparison** → the focus series in `accent`, the rest in
  `context` gray at low `alpha`; or `bar_plot(..., highlight="East")`.
- **Positive / negative** → `bar_plot(..., by_sign=True)` colors bars
  green/red by sign and adds a zero reference line.
- **Semantic** → `good`/`warning`/`bad`/`neutral` are reserved for meaning and
  never reused as another series color.

Run `python examples/color_system.py` to render all of these in both themes.

`area_plot` uses a theme-aware depth gradient by default (`gradient=True`): the
accent color under the line eases to a light tint at the baseline. Pass
`gradient=False` for a flat wash.

**What the defaults do**

- Left-aligned title as the single takeaway (`title=` on any plot).
- Top/right spines removed; remaining axes and a horizontal-only grid are
  hairlines sitting *behind* the data.
- Clean system-sans typography with a clear size hierarchy.
- Thousands-grouped numbers with no noisy trailing `.0`.
- Frameless legends; a `direct_label(ax, x, y, text)` helper for labeling the
  point that tells the story instead of a legend.
- A tidy empty state ("No data to display") instead of a blank chart, and clear
  errors that name a missing column and list what's available.

**Customization.** Attractive defaults are easy; overrides are always available:

```python
dv.set_theme("dark")                              # switch themes
dv.bar_plot(df, "region", "sales", color="#eb6834")  # override a single color
ax = dv.line_plot(df, "day", "revenue")
ax.set_ylim(0, 500)                               # it's a normal Axes — tweak freely
```

Every plot also accepts an existing `ax=`, so you can compose charts onto your
own figures (e.g. small multiples, like the gallery).

> Note: charts are static matplotlib figures, so there is no animation by
> design (which keeps motion out of the way). Web concepts like
> `prefers-reduced-motion` and loading states don't apply to static output.

## API

| Function | Purpose |
| --- | --- |
| `load_csv(path, **kwargs)` | Read a CSV into a DataFrame (clear error if missing). |
| `column_types(df)` | Dtype of each column. |
| `missing_value_counts(df)` | Missing values per column, sorted descending. |
| `summary_statistics(df)` | Descriptive stats for numeric columns. |
| `line_plot(df, x, y, ax=None)` | Line chart of `y` over `x`. |
| `area_plot(df, x, y, gradient=True)` | Filled area with a subtle depth gradient (`gradient=False` for a flat wash). |
| `bar_plot(df, x, y, ax=None)` | Bar chart of `y` per category `x`. |
| `histogram(df, column, bins=10, ax=None)` | Distribution of one numeric column. |
| `scatter_plot(df, x, y, ax=None)` | Relationship between two numeric columns. |

Every plot function accepts an optional `ax`, so you can compose charts onto
your own figures, and returns the `Axes` rather than showing it — keeping you
in control of styling and making plots easy to test.

## Project layout

```
data_viz/
├── src/
│   └── data_vizual/
│       ├── __init__.py   # public API
│       └── core.py       # all functions (load / summarize / plot)
├── tests/
│   └── test_core.py
├── README.md
├── pyproject.toml
└── LICENSE
```

## Development

```bash
pip install -e ".[dev]"   # install with test dependencies
pytest -q                 # run the tests
```

## Conventions

- Use **pandas**, not polars.
- Plots use **matplotlib** only.
- Raw data lives in `data/`; CSVs are never committed.

## License

Licensed under the terms of the [MIT License](LICENSE).
