from __future__ import annotations

import io
import logging
from typing import Dict, Optional

import numpy as np
import pandas as pd
import requests

FRED_CSV_ENDPOINT = "https://fred.stlouisfed.org/graph/fredgraph.csv"
_logger = logging.getLogger(__name__)


def _fallback_series(series_id: str, start_date: str) -> pd.DataFrame:
    """Generate a synthetic monthly series when live FRED data is unavailable."""
    start = pd.to_datetime(start_date)
    periods = 60
    dates = pd.date_range(start=start, periods=periods, freq="M")
    trend = np.linspace(0, periods - 1, periods, dtype="float64")
    oscillation = 0.6 * np.sin(np.linspace(0, 4 * np.pi, periods))
    values = trend + oscillation
    df = pd.DataFrame({series_id: values}, index=dates)
    df.index.name = "Date"
    return df


def _fetch_fred_csv(series_id: str, start_date: str) -> Optional[pd.DataFrame]:
    """
    Retrieve a series from the lightweight fredgraph CSV endpoint.

    Returns None when the request fails.
    """
    params: Dict[str, str] = {
        "id": series_id,
        "cosd": start_date,
    }

    try:
        response = requests.get(FRED_CSV_ENDPOINT, params=params, timeout=10)
        response.raise_for_status()
    except requests.RequestException as exc:
        _logger.warning("FRED request failed for %s: %s", series_id, exc)
        return None

    try:
        df = pd.read_csv(io.StringIO(response.text))
    except Exception as exc:  # pragma: no cover - parsing issue
        _logger.warning("FRED CSV parse failed for %s: %s", series_id, exc)
        return None

    if "DATE" not in df.columns or series_id not in df.columns:
        _logger.warning("FRED CSV missing expected columns for %s", series_id)
        return None

    df["DATE"] = pd.to_datetime(df["DATE"])
    df.set_index("DATE", inplace=True)
    df.index.name = "Date"
    return df[[series_id]]


def get_fred_macro_series(series_id: str, start_date: str = "2017-01-01") -> pd.DataFrame:
    """
    Fetch macroeconomic data from FRED, falling back to a synthetic series when needed.
    """
    df = _fetch_fred_csv(series_id, start_date)
    if df is not None and not df.empty:
        return df

    return _fallback_series(series_id, start_date)


if __name__ == "__main__":  # pragma: no cover - manual check helper
    cpi = get_fred_macro_series("CPIAUCSL")
    print(cpi.tail())
