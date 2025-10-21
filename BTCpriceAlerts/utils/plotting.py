import plotly.graph_objects as go


def plot_dual_axis(df, x_col, y1_col, y2_col, y1_name="Primary", y2_name="Secondary"):
    """
    Plots two y-axes: one for BTC price, one for macro indicator.
    """
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=df[x_col], y=df[y1_col],
            name=y1_name,
            yaxis='y1',
            line=dict(color='blue')
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df[x_col], y=df[y2_col],
            name=y2_name,
            yaxis='y2',
            line=dict(color='orange')
        )
    )

    fig.update_layout(
        title=f"{y1_name} vs {y2_name}",
        xaxis=dict(title='Date'),
        yaxis=dict(title=y1_name, side='left'),
        yaxis2=dict(title=y2_name, overlaying='y', side='right'),
        legend=dict(x=0.01, y=0.99)
    )

    return fig


def plot_candlestick(
    df,
    open_col="Open",
    high_col="High",
    low_col="Low",
    close_col="Close",
    x_col=None,
    title="BTC Candlestick Chart",
):
    """
    Render a Plotly candlestick chart given OHLC columns.
    """
    required = {open_col, high_col, low_col, close_col}
    if not required.issubset(df.columns):
        missing = ", ".join(sorted(required - set(df.columns)))
        raise ValueError(f"Candlestick data missing columns: {missing}")

    x_values = df.index if x_col is None else df[x_col]

    fig = go.Figure(
        data=[
            go.Candlestick(
                x=x_values,
                open=df[open_col],
                high=df[high_col],
                low=df[low_col],
                close=df[close_col],
                name="BTC",
            )
        ]
    )

    fig.update_layout(
        title=title,
        xaxis_title="Date",
        yaxis_title="Price",
        xaxis_rangeslider_visible=False,
    )

    return fig
