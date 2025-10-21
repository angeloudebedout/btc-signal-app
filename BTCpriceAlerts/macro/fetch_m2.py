from datetime import datetime
from typing import Optional

import pandas as pd

try:
    from pandas_datareader import data as pdr_data
except ImportError:  # pandas-datareader is optional
    pdr_data = None


def _fallback_series(column_name: str, periods: int = 24) -> pd.DataFrame:
    """Create a simple fallback DataFrame when live data is unavailable."""
    dates = pd.date_range(end=datetime.utcnow(), periods=periods, freq="M")
    trend = pd.Series(range(periods), index=dates, dtype="float64")
    fallback = pd.DataFrame({column_name: trend})
    fallback.index.name = "Date"
    return fallback


def get_m2(start: Optional[datetime] = None) -> pd.DataFrame:
    """
    Fetch US M2 Money Supply from FRED.

    Returns a DataFrame indexed by date with a `US_M2` column.
    Provides a generated fallback series if FRED cannot be reached.
    """
    start = start or datetime(2015, 1, 1)

    if pdr_data is None:
        return _fallback_series("US_M2")

    try:
        m2 = pdr_data.DataReader("M2SL", "fred", start=start)
        m2 = m2.rename(columns={"M2SL": "US_M2"})
        m2.index = pd.to_datetime(m2.index)
        m2.index.name = "Date"
        return m2
    except Exception as exc:  # pragma: no cover - best-effort logging
        print(f"Error fetching M2: {exc}")
        return _fallback_series("US_M2")
