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

# 1. Load
df = dv.load_csv("data/sales.csv")

# 2. Summarize
dv.column_types(df)          # dtype of each column
dv.missing_value_counts(df)  # missing values per column (highest first)
dv.summary_statistics(df)    # count / mean / std / min / quartiles / max

# 3. Plot  (each returns a matplotlib Axes you can keep customizing)
ax = dv.histogram(df, "revenue", bins=20)
ax.set_title("Revenue distribution")

dv.line_plot(df, x="day", y="revenue")
dv.bar_plot(df, x="region", y="revenue")
dv.scatter_plot(df, x="ad_spend", y="revenue")
```

## API

| Function | Purpose |
| --- | --- |
| `load_csv(path, **kwargs)` | Read a CSV into a DataFrame (clear error if missing). |
| `column_types(df)` | Dtype of each column. |
| `missing_value_counts(df)` | Missing values per column, sorted descending. |
| `summary_statistics(df)` | Descriptive stats for numeric columns. |
| `line_plot(df, x, y, ax=None)` | Line chart of `y` over `x`. |
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
