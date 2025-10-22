import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from data.fetch_btc import get_btc_price_data
from data.fetch_fred import get_fred_macro_series
from signals.indicators import (
    add_bollinger_bands,
    add_ema_cross,
    add_macd,
    add_ma_cross,
    add_rsi,
)

st.set_page_config(page_title="BTC Macro Dashboard", layout="wide")

st.markdown(
    """
    <style>
        .main {
            background: linear-gradient(180deg, #05070B 0%, #0B101C 100%);
            color: #E2E8F0;
        }
        section[data-testid="stSidebar"] {
            background: #060910;
            border-right: 1px solid rgba(255,255,255,0.05);
        }
        .headline {
            font-size: 2.1rem;
            font-weight: 600;
            color: #F4F5FF;
            margin-bottom: 4px;
        }
        .metric-card {
            background: rgba(23, 35, 56, 0.85);
            border: 1px solid rgba(64, 135, 255, 0.25);
            border-radius: 12px;
            padding: 16px 18px;
            box-shadow: 0 10px 25px -20px rgba(59,130,246,0.6);
        }
        .metric-label {
            font-size: 0.78rem;
            color: #92A3C3;
            text-transform: uppercase;
            letter-spacing: 0.18em;
        }
        .metric-value {
            font-size: 1.7rem;
            font-weight: 600;
            color: #F6FAFF;
            margin-top: 6px;
        }
        .metric-sub {
            font-size: 0.95rem;
            color: #9FB4D4;
        }
        .block-title {
            font-weight: 600;
            font-size: 1.1rem;
            color: #E8EEF9;
            margin-top: 18px;
            margin-bottom: 10px;
            letter-spacing: 0.02em;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="headline">BTC Macro Indicators</div>', unsafe_allow_html=True)
st.caption("Holistic market read with technical overlays and macro crosswinds.")


@st.cache_data(ttl=3600)
def load_sample_data():
    sample_path = Path(__file__).resolve().parent / "data" / "btc_sample.csv"
    if sample_path.exists():
        df = pd.read_csv(sample_path, parse_dates=["Date"]).set_index("Date")
        return df

    dates = pd.date_range(end=pd.Timestamp.utcnow().normalize(), periods=365)
    base = np.linspace(20000, 30000, len(dates))
    oscillation = 1200 * np.sin(np.linspace(0, 8 * np.pi, len(dates)))
    close = base + oscillation
    open_price = close * (1 + 0.001 * np.sin(np.linspace(0, 4 * np.pi, len(dates))))
    high = np.maximum(open_price, close) + 150
    low = np.minimum(open_price, close) - 150
    volume = 1500 + 300 * np.cos(np.linspace(0, 6 * np.pi, len(dates)))

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


@st.cache_data(ttl=3600)
def load_live_data():
    btc = get_btc_price_data(days=365)
    cpi = get_fred_macro_series("CPIAUCSL")
    fed = get_fred_macro_series("FEDFUNDS")

    df = btc.copy()
    df = df.join(cpi, how="left")
    df = df.join(fed, how="left")
    df.rename(
        columns={
            "CPIAUCSL": "CPI",
            "FEDFUNDS": "FedFundsRate",
        },
        inplace=True,
    )
    df.fillna(method="ffill", inplace=True)
    return df


st.sidebar.header("Data Feeds")
use_live = st.sidebar.checkbox("Live: Binance & FRED", value=False)

st.sidebar.header("Indicators")
use_rsi = st.sidebar.checkbox("RSI")
use_macd = st.sidebar.checkbox("MACD")
use_sma = st.sidebar.checkbox("SMA Crossover")
use_ema = st.sidebar.checkbox("EMA Crossover")
use_bb = st.sidebar.checkbox("Bollinger Bands")

df = load_live_data() if use_live else load_sample_data()

if use_rsi:
    df = add_rsi(df)
if use_macd:
    df = add_macd(df)
if use_sma:
    df = add_ma_cross(df)
if use_ema:
    df = add_ema_cross(df)
if use_bb:
    df = add_bollinger_bands(df)

# KPI banner
latest = df.iloc[-1]
prior = df.iloc[-2] if len(df) > 1 else latest
close_px = latest["Close"]
delta_px = close_px - prior["Close"]
delta_pct = (delta_px / prior["Close"]) * 100 if prior["Close"] else 0
rsi_value = latest.get("RSI")
vol = latest.get("Volume", np.nan)

kpi_cols = st.columns(4)
with kpi_cols[0]:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.markdown('<div class="metric-label">Spot BTC</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="metric-value">${close_px:,.0f}</div>', unsafe_allow_html=True)
    st.markdown(
        f"<div class='metric-sub' style='color:{'#55F2C8' if delta_px >= 0 else '#FF7A8A'};'>"
        f"{delta_px:+,.0f} | {delta_pct:+.2f}%</div>",
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

with kpi_cols[1]:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.markdown('<div class="metric-label">RSI</div>', unsafe_allow_html=True)
    rsi_disp = f"{rsi_value:.1f}" if pd.notna(rsi_value) else "N/A"
    st.markdown(f'<div class="metric-value">{rsi_disp}</div>', unsafe_allow_html=True)
    stance = "Overbought" if rsi_value and rsi_value > 70 else "Oversold" if rsi_value and rsi_value < 30 else "Balanced"
    st.markdown(f"<div class='metric-sub'>{stance}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with kpi_cols[2]:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.markdown('<div class="metric-label">Volume</div>', unsafe_allow_html=True)
    vol_disp = f"{vol/1_000_000:.1f}M" if pd.notna(vol) else "N/A"
    st.markdown(f'<div class="metric-value">{vol_disp}</div>', unsafe_allow_html=True)
    st.markdown("<div class='metric-sub'>24h turnover</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with kpi_cols[3]:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.markdown('<div class="metric-label">Signals Active</div>', unsafe_allow_html=True)
    active_signals = sum(
        pd.notna(latest.get(col))
        and latest.get(col) not in ("Neutral", None)
        for col in df.columns
        if "signal" in col.lower()
    )
    st.markdown(f'<div class="metric-value">{active_signals}</div>', unsafe_allow_html=True)
    st.markdown("<div class='metric-sub'>Bull / bear triggers</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


# Build plot
fig = go.Figure()
fig.add_trace(
    go.Scatter(
        x=df.index,
        y=df["Close"],
        name="BTC Close",
        line=dict(color="#5FD7FF", width=2.4),
    )
)

if use_rsi and "RSI" in df:
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["RSI"],
            name="RSI",
            yaxis="y2",
            line=dict(color="#9B7BFF", width=1.6, dash="dash"),
        )
    )

if use_macd and {"MACD_12_26_9", "MACDs_12_26_9"}.issubset(df.columns):
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["MACD_12_26_9"],
            name="MACD",
            yaxis="y2",
            line=dict(color="#4AF5C8", width=1.8),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["MACDs_12_26_9"],
            name="Signal",
            yaxis="y2",
            line=dict(color="#FF9A76", width=1.5),
        )
    )

if use_bb and {"BBU_20_2.0", "BBL_20_2.0"}.issubset(df.columns):
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["BBU_20_2.0"],
            name="BB Upper",
            line=dict(color="rgba(95,215,255,0.35)", width=1.3),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["BBL_20_2.0"],
            name="BB Lower",
            line=dict(color="rgba(95,215,255,0.35)", width=1.3),
        )
    )

fig.update_layout(
    template="plotly_dark",
    title=None,
    margin=dict(l=0, r=0, t=20, b=0),
    xaxis=dict(title="Date"),
    yaxis=dict(title="BTC Price", side="left"),
    yaxis2=dict(
        title="Indicators",
        overlaying="y",
        side="right",
        showgrid=False,
    ),
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1,
    ),
)

st.markdown('<div class="block-title">Price Structure & Technical Overlays</div>', unsafe_allow_html=True)
st.plotly_chart(fig, use_container_width=True)

st.markdown('<div class="block-title">Signal Tape</div>', unsafe_allow_html=True)
signal_cols = [col for col in df.columns if "signal" in col.lower()]
if signal_cols:
    display = df[signal_cols].tail(40).fillna("Neutral")
    st.dataframe(display, use_container_width=True, height=360)
else:
    st.info("Signals are off. Activate indicators in the sidebar to populate this view.")

st.markdown('<div class="block-title">Macro Context</div>', unsafe_allow_html=True)
macro_cols = st.columns(2)
with macro_cols[0]:
    st.subheader("CPI vs Price")
    if {"CPI"}.issubset(df.columns):
        st.line_chart(df[["Close", "CPI"]], use_container_width=True)
    else:
        st.info("CPI data unavailable for this session.")

with macro_cols[1]:
    st.subheader("Fed Funds Rate")
    if {"FedFundsRate"}.issubset(df.columns):
        st.area_chart(df["FedFundsRate"], use_container_width=True)
    else:
        st.info("Fed funds data unavailable for this session.")

st.caption("Powered by Binance (price), FRED (macro). Synthetic fallback series provided when feeds are offline.")
