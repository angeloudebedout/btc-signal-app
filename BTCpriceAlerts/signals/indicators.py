# signals/indicators.py

import numpy as np
import pandas as pd

try:
    import pandas_ta as ta  # type: ignore
except ModuleNotFoundError:  # Optional dependency
    ta = None


def _ema(series: pd.Series, span: int) -> pd.Series:
    return series.ewm(span=span, adjust=False).mean()


def _rsi(series: pd.Series, length: int) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window=length, min_periods=length).mean()
    avg_loss = loss.rolling(window=length, min_periods=length).mean()
    rs = avg_gain / avg_loss.replace(to_replace=0, value=np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi


def _bollinger(series: pd.Series, length: int, std: float) -> pd.DataFrame:
    ma = series.rolling(window=length, min_periods=length).mean()
    deviation = series.rolling(window=length, min_periods=length).std()
    upper = ma + std * deviation
    lower = ma - std * deviation
    df = pd.DataFrame(
        {
            f"BBM_{length}_{std}": ma,
            f"BBU_{length}_{std}": upper,
            f"BBL_{length}_{std}": lower,
        },
        index=series.index,
    )
    return df


def add_rsi(df, length=14):
    """
    Adds RSI (Relative Strength Index) and Buy/Sell signals.
    Buy when RSI < 30, Sell when RSI > 70.
    """
    if ta:
        df['RSI'] = ta.rsi(df['Close'], length=length)
    else:
        df['RSI'] = _rsi(df['Close'], length=length)
    df['RSI_signal'] = np.where(df['RSI'] < 30, 'Buy',
                         np.where(df['RSI'] > 70, 'Sell', None))
    return df


def add_macd(df):
    """
    Adds MACD indicators.
    Buy when MACD line > Signal line, Sell otherwise.
    """
    if ta:
        macd = ta.macd(df['Close'])
        df = df.join(macd)
    else:
        ema_short = _ema(df['Close'], span=12)
        ema_long = _ema(df['Close'], span=26)
        macd_line = ema_short - ema_long
        signal_line = macd_line.ewm(span=9, adjust=False).mean()
        histogram = macd_line - signal_line
        df['MACD_12_26_9'] = macd_line
        df['MACDs_12_26_9'] = signal_line
        df['MACDh_12_26_9'] = histogram
    df['MACD_signal'] = np.where(df['MACD_12_26_9'] > df['MACDs_12_26_9'], 'Buy', 'Sell')
    return df


def add_ma_cross(df, short=50, long=200):
    """
    Adds Simple Moving Average crossover signals.
    Buy when short SMA crosses above long SMA. Sell when it crosses below.
    """
    df['SMA_short'] = df['Close'].rolling(window=short).mean()
    df['SMA_long'] = df['Close'].rolling(window=long).mean()
    cross = df['SMA_short'] > df['SMA_long']
    cross = cross.fillna(False)
    df['MA_signal'] = np.where(cross & ~cross.shift(1, fill_value=False), 'Buy',
                        np.where(~cross & cross.shift(1, fill_value=False), 'Sell', None))
    return df


def add_ema_cross(df, short=12, long=26):
    """
    Adds Exponential Moving Average crossover signals.
    Buy when short EMA crosses above long EMA. Sell when it crosses below.
    """
    if ta:
        df['EMA_short'] = ta.ema(df['Close'], length=short)
        df['EMA_long'] = ta.ema(df['Close'], length=long)
    else:
        df['EMA_short'] = _ema(df['Close'], span=short)
        df['EMA_long'] = _ema(df['Close'], span=long)
    cross = df['EMA_short'] > df['EMA_long']
    cross = cross.fillna(False)
    df['EMA_signal'] = np.where(cross & ~cross.shift(1, fill_value=False), 'Buy',
                         np.where(~cross & cross.shift(1, fill_value=False), 'Sell', None))
    return df


def add_bollinger_bands(df, length=20, std=2):
    """
    Adds Bollinger Bands and signals.
    Buy when price touches lower band, Sell when price touches upper band.
    """
    if ta:
        bb = ta.bbands(df['Close'], length=length, std=std)
    else:
        bb = _bollinger(df['Close'], length=length, std=std)

    if bb is None or bb.empty:
        # Ensure expected columns exist so downstream code does not break
        df[f'BBL_{length}_{std}'] = np.nan
        df[f'BBU_{length}_{std}'] = np.nan
        df['BB_signal'] = None
        return df

    df = df.join(bb)

    lower_col = next((c for c in bb.columns if c.startswith(f'BBL_{length}_')), None)
    upper_col = next((c for c in bb.columns if c.startswith(f'BBU_{length}_')), None)

    if not lower_col or not upper_col:
        df['BB_signal'] = None
        return df

    df['BB_signal'] = np.where(df['Close'] <= df[lower_col], 'Buy',
                        np.where(df['Close'] >= df[upper_col], 'Sell', None))
    return df


def add_vwap(df):
    """
    Adds VWAP (Volume Weighted Average Price).
    Typically used for intraday data — ensure 'Volume' is present.
    """
    if 'Volume' not in df.columns:
        raise ValueError("VWAP requires 'Volume' column in the DataFrame.")

    if ta:
        df['VWAP'] = ta.vwap(df['High'], df['Low'], df['Close'], df['Volume'])
    else:
        typical_price = (df['High'] + df['Low'] + df['Close']) / 3
        cumulative_vp = (typical_price * df['Volume']).cumsum()
        cumulative_volume = df['Volume'].cumsum()
        df['VWAP'] = cumulative_vp / cumulative_volume.replace(0, np.nan)

    return df
