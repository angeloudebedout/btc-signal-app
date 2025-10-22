from datetime import datetime
from typing import Optional

import pandas as pd

from data.fetch_fred import get_fred_macro_series


def _fallback_series(column_name: str, periods: int = 24) -> pd.DataFrame:
    """Create a simple fallback DataFrame when live data is unavailable."""
    dates = pd.date_range(end=datetime.utcnow(), periods=periods, freq="M")
    trend = pd.Series(range(periods), index=dates, dtype="float64")
    fallback = pd.DataFrame({column_name: trend})
    fallback.index.name = "Date"
    return fallback


def get_cpi(start: Optional[datetime] = None) -> pd.DataFrame:
    """
    Fetch US CPI (Consumer Price Index) from FRED.

    Returns a DataFrame indexed by date with a `US_CPI` column.
    Provides a generated fallback series if FRED cannot be reached.
    """
    start = start or datetime(2015, 1, 1)
    fred = get_fred_macro_series("CPIAUCSL", start.strftime("%Y-%m-%d"))
    if fred.empty:
        return _fallback_series("US_CPI")

    fred = fred.rename(columns={"CPIAUCSL": "US_CPI"})
    return fred
