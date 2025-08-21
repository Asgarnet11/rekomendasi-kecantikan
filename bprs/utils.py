from __future__ import annotations
import numpy as np
import pandas as pd

def read_csv_flex(path_or_buffer):
    """Reader fleksibel: coba ; lalu , lalu latin-1."""
    for args in (
        {},
        {"delimiter": ";"},
        {"encoding": "latin-1"},
        {"engine": "python", "on_bad_lines": "skip"},
        {"delimiter": ";", "engine": "python", "on_bad_lines": "skip"},
    ):
        try:
            return pd.read_csv(path_or_buffer, **args)
        except Exception:
            pass
    return pd.read_csv(path_or_buffer)  # fallback

def safe_price_bounds(series: pd.Series) -> tuple[int, int]:
    s = pd.to_numeric(series, errors="coerce")
    s = s[np.isfinite(s)]
    if s.empty:
        return 0, 1
    vmin = int(np.nanmin(s))
    vmax = int(np.nanmax(s))
    if vmin >= vmax:
        return max(0, vmin - 1), vmin + 1
    return vmin, vmax
