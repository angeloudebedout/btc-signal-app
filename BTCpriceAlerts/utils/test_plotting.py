import pandas as pd
import plotly.graph_objects as go

from utils.plotting import plot_dual_axis


def test_plot_dual_axis_returns_figure():
    df = pd.DataFrame(
        {
            "Date": pd.date_range(start="2022-01-01", periods=50),
            "BTC_Price": pd.Series(range(50)) * 100 + 20000,
            "CPI": pd.Series(range(50)) * 0.1 + 2.0,
        }
    )

    fig = plot_dual_axis(
        df, x_col="Date", y1_col="BTC_Price", y2_col="CPI", y1_name="BTC Price", y2_name="CPI"
    )

    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 2
