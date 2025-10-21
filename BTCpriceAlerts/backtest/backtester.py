# backtest/backtester.py

import pandas as pd

def backtest_signals(df, signal_col, price_col="Close"):
    """
    Simple backtest: Buy on 'Buy', Sell on 'Sell', no position otherwise.
    Assumes full buy/sell each signal.
    """
    capital = 10000
    position = 0
    trades = []

    for i in range(len(df)):
        row = df.iloc[i]
        signal = row[signal_col]
        price = row[price_col]

        if signal == 'Buy' and capital > 0:
            position = capital / price
            capital = 0
            trades.append(("Buy", price, row.name))
        elif signal == 'Sell' and position > 0:
            capital = position * price
            position = 0
            trades.append(("Sell", price, row.name))

    final_value = capital + position * df.iloc[-1][price_col]
    return trades, final_value
