import pandas as pd
import streamlit as st

from data.fetch_btc import get_btc_price_data
from macro.fetch_cpi import get_cpi
from macro.fetch_m2 import get_m2
from macro.fetch_policy import get_policy_rate
from signals.indicators import add_macd, add_ma_cross, add_rsi
from utils.plotting import plot_candlestick


st.set_page_config(page_title="BTC Signal & Macro Dashboard", layout="wide")

# Inject a lightweight pro-style theme (deep navy background, accent green)
st.markdown(
    """
    <style>
        .main {
            background: radial-gradient(circle at top, #101623 0%, #070B12 55%, #05070B 100%);
            color: #EBECF0;
        }
        section[data-testid="stSidebar"] {
            background: #0C111C;
            border-right: 1px solid rgba(255, 255, 255, 0.08);
        }
        .metric-card {
            background: linear-gradient(135deg, rgba(28,45,68,0.85), rgba(18,28,45,0.85));
            border-radius: 12px;
            padding: 18px 20px;
            border: 1px solid rgba(76,110,245,0.3);
            box-shadow: 0 12px 24px -18px rgba(18,188,255,0.65);
        }
        .metric-title {
            font-size: 0.85rem;
            letter-spacing: 0.12em;
            color: #AEB7C5;
            text-transform: uppercase;
        }
        .metric-value {
            font-size: 1.8rem;
            font-weight: 600;
            margin-top: 6px;
            color: #F1F7FF;
        }
        .signal-chip {
            display: inline-flex;
            align-items: center;
            padding: 6px 14px;
            border-radius: 999px;
            font-size: 0.85rem;
            margin-right: 8px;
            margin-bottom: 6px;
            border: 1px solid rgba(255,255,255,0.16);
        }
        .signal-chip.bullish {
            background: rgba(0, 196, 140, 0.16);
            color: #4AF5C8;
            border-color: rgba(74, 245, 200, 0.35);
        }
        .signal-chip.bearish {
            background: rgba(255, 77, 109, 0.16);
            color: #FF6F91;
            border-color: rgba(255, 111, 145, 0.35);
        }
        .signal-chip.neutral {
            background: rgba(118, 139, 183, 0.16);
            color: #A9B8D3;
            border-color: rgba(169, 184, 211, 0.35);
        }
        .block-header {
            font-weight: 600;
            font-size: 1.2rem;
            color: #E9EDF5;
            margin-bottom: 12px;
        }
        .stTabs [data-baseweb="tab-list"] {
            gap: 12px;
        }
        .stTabs [data-baseweb="tab"] {
            background-color: rgba(29, 45, 68, 0.5);
            padding: 12px 28px;
            border-radius: 999px;
            color: #BCC6D9;
        }
        .stTabs [data-baseweb="tab"]:hover {
            background-color: rgba(47, 72, 110, 0.65);
        }
        .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg, #4C6EF5 0%, #2BB3FF 100%);
            color: #101623;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("BTC Market Signal Desk")
st.caption("Institutional-grade overview powered by live market data and macro context.")

# Sidebar configuration (filters, toggles)
st.sidebar.header("Market Settings")
date_range = st.sidebar.selectbox(
    "Historical depth",
    options=["90", "180", "365"],
    format_func=lambda d: f"{d} days",
    index=1,
)
interval = st.sidebar.selectbox(
    "Sampling interval", options=["1d", "1h"], index=0
)

st.sidebar.header("Technical Stack")
show_rsi = st.sidebar.checkbox("Relative Strength Index", True)
show_macd = st.sidebar.checkbox("MACD (12-26-9)", True)
show_ma = st.sidebar.checkbox("Moving Average Crossover", True)

# Pull BTC price history (with offline fallback)
days = int(date_range)
price_df = get_btc_price_data(days=days, interval=interval)

if price_df.empty:
    st.error("Unable to source BTC pricing data at the moment. Please retry later.")
    st.stop()

btc = price_df.copy()

if show_rsi:
    btc = add_rsi(btc)
if show_macd:
    btc = add_macd(btc)
if show_ma:
    btc = add_ma_cross(btc)

# Core derived metrics
latest_row = btc.iloc[-1]
previous_row = btc.iloc[-2] if len(btc) > 1 else latest_row
latest_close = latest_row["Close"]
previous_close = previous_row["Close"]
day_change = latest_close - previous_close
day_change_pct = (day_change / previous_close) * 100 if previous_close else 0
rsi_value = latest_row.get("RSI")
macd_signal = latest_row.get("MACD_signal", "Neutral")
ma_signal = latest_row.get("MA_signal", "Neutral")

signal_palette = {
    "Buy": "bullish",
    "Sell": "bearish",
    "Neutral": "neutral",
    None: "neutral",
}

# KPI strip
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.markdown('<div class="metric-title">BTCUSD Spot</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="metric-value">${latest_close:,.0f}</div>', unsafe_allow_html=True)
    st.markdown(
        f"<span style='color:{'#4AF5C8' if day_change >= 0 else '#FF6F91'};'>"
        f"{day_change:+,.0f} | {day_change_pct:+.2f}%</span>",
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

with col2:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.markdown('<div class="metric-title">RSI</div>', unsafe_allow_html=True)
    rsi_display = f"{rsi_value:.1f}" if pd.notna(rsi_value) else "N/A"
    st.markdown(f'<div class="metric-value">{rsi_display}</div>', unsafe_allow_html=True)
    bias = "Overbought" if rsi_value and rsi_value > 70 else "Oversold" if rsi_value and rsi_value < 30 else "Neutral"
    st.markdown(f"<span style='color:#A9B8D3;'>{bias}</span>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with col3:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.markdown('<div class="metric-title">MACD Signal</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="metric-value">{macd_signal or "Neutral"}</div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with col4:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.markdown('<div class="metric-title">MA Crossover</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="metric-value">{ma_signal or "Neutral"}</div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# Tabs for detailed exploration
chart_tab, signals_tab, macro_tab = st.tabs(["Price Action", "Signal Matrix", "Macro Lens"])

with chart_tab:
    st.markdown('<div class="block-header">Candlestick Structure</div>', unsafe_allow_html=True)
    st.plotly_chart(
        plot_candlestick(btc.tail(365 if interval == "1d" else 500)),
        use_container_width=True,
        theme="streamlit",
    )

with signals_tab:
    st.markdown('<div class="block-header">Multi-Indicator Guidance</div>', unsafe_allow_html=True)
    chips = []
    for label, signal in [("RSI", latest_row.get("RSI_signal")), ("MACD", macd_signal), ("MA X", ma_signal)]:
        tone = signal_palette.get(signal, "neutral")
        chips.append(f'<span class="signal-chip {tone}">{label}: {signal or "Neutral"}</span>')
    st.markdown("".join(chips), unsafe_allow_html=True)

    signal_cols = [col for col in btc.columns if "signal" in col.lower()]
    if signal_cols:
        latest_signals = btc[signal_cols].tail(25).fillna("Neutral")
        st.dataframe(
            latest_signals,
            use_container_width=True,
            height=400,
        )
    else:
        st.info("No signals calculated. Toggle indicators in the sidebar to activate.")

with macro_tab:
    st.markdown('<div class="block-header">Macro Backdrop</div>', unsafe_allow_html=True)
    macro_cols = st.columns(3)
    with macro_cols[0]:
        st.markdown("**US CPI (YoY)**")
        cpi = get_cpi()
        st.line_chart(cpi, use_container_width=True)
    with macro_cols[1]:
        st.markdown("**US M2 Money Supply**")
        m2 = get_m2()
        st.line_chart(m2, use_container_width=True)
    with macro_cols[2]:
        st.markdown("**Fed Funds Effective Rate**")
        policy = get_policy_rate()
        st.line_chart(policy, use_container_width=True)

st.caption(
    "Sourcing: BTC via Yahoo Finance (fallback synthetic series), Macro via FRED / fallback model."
)
