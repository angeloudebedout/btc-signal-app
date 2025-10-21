import numpy as np
import pandas as pd
import pytest

pytest.importorskip("pandas_ta")

from signals.indicators import add_macd, add_ma_cross


@pytest.fixture()
def price_data():
    df = pd.DataFrame(
        {
            "Close": pd.Series(np.random.normal(30000, 500, 200)),
            "Date": pd.date_range(start="2022-01-01", periods=200),
        }
    )
    return df.set_index("Date")


def test_add_macd(price_data):
    enriched = add_macd(price_data.copy())

    assert "MACD_12_26_9" in enriched.columns
    assert "MACDs_12_26_9" in enriched.columns
    assert "MACD_signal" in enriched.columns
    assert set(enriched["MACD_signal"].dropna().unique()) <= {"Buy", "Sell"}


def test_add_ma_cross(price_data):
    enriched = add_ma_cross(price_data.copy())

    assert "SMA_short" in enriched.columns
    assert "SMA_long" in enriched.columns
    assert "MA_signal" in enriched.columns
    assert set(enriched["MA_signal"].dropna().unique()) <= {"Buy", "Sell"}
