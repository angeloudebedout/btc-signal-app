# fetch_fred.py

import pandas_datareader.data as web
import pandas as pd
from datetime import datetime, timedelta

def get_fred_macro_series(series_id: str, start_date: str = "2017-01-01") -> pd.DataFrame:
    """
    Fetches macroeconomic data from FRED using its series ID.
    
    Args:
        series_id (str): FRED series ID (e.g., 'CPIAUCSL', 'FEDFUNDS').
        start_date (str): Date to start fetching from (default '2017-01-01').

    Returns:
        pd.DataFrame: DataFrame indexed by date with the series values.
    """
    try:
        df = web.DataReader(series_id, "fred", start=start_date)
        df.columns = [series_id]
        df.index = pd.to_datetime(df.index)
        return df
    except Exception as e:
        print(f"Failed to fetch {series_id} from FRED: {e}")
        return pd.DataFrame()

# Example usage (for testing only):
if __name__ == "__main__":
    cpi = get_fred_macro_series("CPIAUCSL")
    print(cpi.tail())
