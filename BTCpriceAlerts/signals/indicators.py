# signals/indicators.py

import pandas_ta as ta
import numpy as np
import pandas as pd


def add_rsi(df, length=14):
    """
    Adds RSI (Relative Strength Index) and Buy/Sell signals.
    Buy when RSI < 30, Sell when RSI > 70.
    """
    df['RSI'] = ta.rsi(df['Close'], length=length)
    df['RSI_signal'] = np.where(df['RSI'] < 30, 'Buy',
                         np.where(df['RSI'] > 70, 'Sell', None))
    return df


def add_macd(df):
    """
    Adds MACD indicators.
    Buy when MACD line > Signal line, Sell otherwise.
    """
    macd = ta.macd(df['Close'])
    df = df.join(macd)
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
    df['EMA_short'] = ta.ema(df['Close'], length=short)
    df['EMA_long'] = ta.ema(df['Close'], length=long)
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
    bb = ta.bbands(df['Close'], length=length, std=std)
    if bb is None or bb.empty:
        # Ensure expected columns exist so downstream code does not break
        std_suffix = str(float(std)).rstrip("0").rstrip(".")
        df[f'BBL_{length}_{std_suffix}'] = np.nan
        df[f'BBU_{length}_{std_suffix}'] = np.nan
        df['BB_signal'] = None
        return df

    df = df.join(bb)

    std_suffix = str(float(std)).rstrip("0").rstrip(".")
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

    df['VWAP'] = ta.vwap(df['High'], df['Low'], df['Close'], df['Volume'])
    return df
