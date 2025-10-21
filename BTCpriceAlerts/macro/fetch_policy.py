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


def get_policy_rate(start: Optional[datetime] = None) -> pd.DataFrame:
    """
    Fetch US effective federal funds rate (policy rate) from FRED.

    Returns a DataFrame indexed by date with a `US_Policy_Rate` column.
    Provides a generated fallback series if FRED cannot be reached.
    """
    start = start or datetime(2015, 1, 1)

    if pdr_data is None:
        return _fallback_series("US_Policy_Rate")

    try:
        rate = pdr_data.DataReader("FEDFUNDS", "fred", start=start)
        rate = rate.rename(columns={"FEDFUNDS": "US_Policy_Rate"})
        rate.index = pd.to_datetime(rate.index)
        rate.index.name = "Date"
        return rate
    except Exception as exc:  # pragma: no cover - best-effort logging
        print(f"Error fetching Policy Rate: {exc}")
        return _fallback_series("US_Policy_Rate")
