from datetime import datetime, timedelta
import numpy as np
import pandas as pd

try:
    import yfinance as yf
except ImportError:  # yfinance is optional at runtime
    yf = None


def _fallback_series(periods: int, interval: str) -> pd.DataFrame:
    """
    Build a deterministic fallback time series if live data cannot be fetched.
    """
    freq_map = {"1d": "D", "1h": "H"}
    freq = freq_map.get(interval, "D")
    end = pd.Timestamp.utcnow().floor(freq)
    dates = pd.date_range(end=end, periods=periods, freq=freq)

    base = np.linspace(20000, 32000, len(dates))
    oscillation = 1500 * np.sin(np.linspace(0, 10 * np.pi, len(dates)))
    close = base + oscillation
    open_price = close * (1 + 0.001 * np.sin(np.linspace(0, 5 * np.pi, len(dates))))
    high = np.maximum(open_price, close) + 200
    low = np.minimum(open_price, close) - 200
    volume = 2000 + 400 * np.cos(np.linspace(0, 8 * np.pi, len(dates)))

    df = pd.DataFrame(
        {
            "Open": open_price,
            "High": high,
            "Low": low,
            "Close": close,
            "Volume": volume,
        },
        index=dates,
    )
    df.index.name = "Date"
    return df


def get_btc_price_data(
    days: int = 180, interval: str = "1d", ticker: str = "BTC-USD"
) -> pd.DataFrame:
    """
    Fetch historical BTC price data.

    Tries live data via yfinance first, and falls back to a generated series when
    offline or when dependencies are missing.
    """
    if days <= 0:
        raise ValueError("`days` must be a positive integer.")

    if yf is None:
        return _fallback_series(days, interval)

    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=days)

    try:
        df = yf.download(
            ticker,
            start=start_time,
            end=end_time,
            interval=interval,
            progress=False,
            auto_adjust=False,
        )
    except Exception as exc:  # pragma: no cover - best-effort logging
        print(f"Failed to fetch BTC data via yfinance: {exc}")
        return _fallback_series(days, interval)

    if df.empty:
        return _fallback_series(days, interval)

    df.index = pd.to_datetime(df.index)
    df.index.name = "Date"
    return df[["Open", "High", "Low", "Close", "Volume"]]
