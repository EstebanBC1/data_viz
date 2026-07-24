"""data_vizual: playful, softly dimensional pandas + matplotlib charts."""

from .core import (available_themes, bar_plot, hist_plot, line_plot, load_csv,
                   scatter_plot, set_theme, theme_tokens)

__version__ = "0.5.0"
__all__ = ["set_theme", "available_themes", "theme_tokens", "load_csv",
           "line_plot", "bar_plot", "hist_plot", "scatter_plot"]
