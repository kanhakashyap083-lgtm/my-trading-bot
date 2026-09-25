import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import plotly.graph_objects as go
import warnings

warnings.filterwarnings("ignore")
st.set_page_config(page_title="AI Alpha Screener Pro", layout="wide", page_icon="⚡")

# ================= SIDEBAR =================
st.sidebar.title("⚡ Alpha Screener Pro")
category = st.sidebar.selectbox(
    "Sector Select Karein",
    ["Nifty 50 (Top Stocks)", "Bank Nifty", "IT Sector", "Auto Sector", "Pharma Sector", "FMCG Sector", "Metal Sector", "ETFs (Safe)"]
)

only_buys = st.sidebar.checkbox("🎯 Sirf BUY Signals Dikhayein", value=False)
min_rsi = st.sidebar.slider("RSI Oversold Filter (Buy Range)", min_value=20, max_value=45, value=35)

market_data = {
    "Nifty 50 (Top Stocks)": ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS", "SBIN.NS", "ITC.NS", "LT.NS", "BHARTIARTL.NS", "BAJFINANCE.NS", "HINDUNILVR.NS", "ASIANPAINT.NS"],
    "Bank Nifty": ["HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "AXISBANK.NS", "KOTAKBANK.NS", "INDUSINDBK.NS", "PNB.NS", "BANKBARODA.NS", "FEDERALBNK.NS", "IDFCFIRSTB.NS"],
    "IT Sector": ["TCS.NS", "INFY.NS", "HCLTECH.NS", "WIPRO.NS", "TECHM.NS", "LTIM.NS", "PERSISTENT.NS", "COFORGE.NS"],
    "Auto Sector": ["TATAMOTORS.NS", "M&M.NS", "MARUTI.NS", "BAJAJ-AUTO.NS", "HEROMOTOCO.NS", "EICHERMOT.NS", "TVSMOTOR.NS"],
    "Pharma Sector": ["SUNPHARMA.NS", "CIPLA.NS", "DRREDDY.NS", "DIVISLAB.NS", "LUPIN.NS", "AUROPHARMA.NS", "BIOCON.NS"],
    "FMCG Sector": ["ITC.NS", "HINDUNILVR.NS", "NESTLEIND.NS", "BRITANNIA.NS", "TATACONSUM.NS", "DABUR.NS", "GODREJCP.NS"],
    "Metal Sector": ["TATASTEEL.NS", "HINDALCO.NS", "JSWSTEEL.NS", "COALINDIA.NS", "VEDL.NS", "SAIL.NS"],
    "ETFs (Safe)": ["NIFTYBEES.NS", "BANKBEES.NS", "GOLDBEES.NS", "ITBEES.NS", "PHARMABEES.NS", "AUTOBEES.NS", "MID150BEES.NS"]
}

stocks_list = market_data[category]
results = []
stock_charts = {}

progress_bar = st.progress(0, text="Institutional scans underway...")

for i, ticker in enumerate(stocks_list):
    try:
        data = yf.Ticker(ticker).history(period="6mo")
        if data.empty or len(data) < 50:
            continue

        # Technical Indicators
        data['RSI'] = ta.momentum.RSIIndicator(data['Close'], window=14).rsi()
        data['SMA_20'] = ta.trend.SMAIndicator(data['Close'], window=20).sma_indicator()
        data['SMA_50'] = ta.trend.SMAIndicator(data['Close'], window=50).sma_indicator()
        data['ATR'] = ta.volatility.AverageTrueRange(data['High'], data['Low'], data['Close'], window=14).average_true_range()
        
        # MACD
        macd = ta.trend.MACD(data['Close'])
        data['MACD'] = macd.macd()
        data['MACD_Signal'] = macd.macd_signal()
        
        # Volume Spike
        data['Vol_SMA'] = data['Volume'].rolling(window=20).mean()

        latest = data.iloc[-1]
        prev = data.iloc[-2]
        current_price = latest['Close']
        target = current_price * 1.04
        stop_loss = current_price * 0.98

        daily_movement = (latest['ATR'] / current_price) * 100
        holding_days = int((4.0 / daily_movement)) + 1 if daily_movement > 0 else 5
        hold_str = "15+ Din" if holding_days > 15 else f"{holding_days} to {holding_days+3} Din"

        vol_spike = "⚡ High" if latest['Volume'] > (1.5 * latest['Vol_SMA']) else "Normal"
        macd_bullish = latest['MACD'] > latest['MACD_Signal']

        # Dual Confirmation Logic
        if latest['RSI'] < min_rsi or (macd_bullish and prev['MACD'] <= prev['MACD_Signal']):
            signal = "🟢 STRONG BUY"
            t_str, sl_str = f"₹{target:.1f}", f"₹{stop_loss:.1f}"
        elif latest['RSI'] > 70 or (not macd_bullish and prev['MACD'] >= prev['MACD_Signal']):
            signal = "🔴 STRONG SELL"
            t_str, sl_str, hold_str = "-", "-", "-"
        elif latest['SMA_20'] > latest['SMA_50']:
            signal = "📈 UPTREND"
            t_str, sl_str = f"₹{target:.1f}", f"₹{stop_loss:.1f}"
        else:
            signal = "🟡 CONSOLIDATION"
            t_str, sl_str, hold_str = "-", "-", "-"

        clean_symbol = ticker.replace('.NS', '')
        stock_charts[clean_symbol] = data

        results.append({
            "Stock": clean_symbol,
            "Price": f"₹{current_price:.2f}",
            "Signal": signal,
            "RSI": round(latest['RSI'], 1),
            "Volume": vol_spike,
            "Target (+4%)": t_str,
            "Stop-Loss (-2%)": sl_str,
            "Est. Hold": hold_str
        })
    except:
        pass
    
    progress_bar.progress(int(((i + 1) / len(stocks_list)) * 100), text=f"Checking {ticker}...")

progress_bar.empty()

# ================= DASHBOARD UI =================
st.title(f"📊 Market Scanner: {category}")

df = pd.DataFrame(results)

if not df.empty:
    # Summary Metrics Cards
    buy_count = len(df[df['Signal'].str.contains("BUY")])
    sell_count = len(df[df['Signal'].str.contains("SELL")])
    uptrend_count = len(df[df['Signal'].str.contains("UPTREND")])
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Scanned", len(df))
    col2.metric("🟢 Active Buy Calls", buy_count)
    col3.metric("📈 Uptrend Stocks", uptrend_count)
    col4.metric("🔴 Overbought/Sell", sell_count)

    st.divider()

    # Filtered Table
    display_df = df[df['Signal'].str.contains("BUY")] if only_buys else df
    st.dataframe(display_df, width='stretch')

    # ================= PRO CHART ENGINE =================
    st.subheader("🔍 Deep Dive: Interactive Stock Analysis")
    selected_stock = st.selectbox("Chart dekhne ke liye stock chunein:", list(stock_charts.keys()))

    if selected_stock:
        chart_data = stock_charts[selected_stock]
        fig = go.Figure()

        # Candlestick
        fig.add_trace(go.Candlestick(
            x=chart_data.index,
            open=chart_data['Open'], high=chart_data['High'],
            low=chart_data['Low'], close=chart_data['Close'],
            name="Price"
        ))

        # Moving Averages
        fig.add_trace(go.Scatter(x=chart_data.index, y=chart_data['SMA_20'], line=dict(color='orange', width=1.5), name="SMA 20"))
        fig.add_trace(go.Scatter(x=chart_data.index, y=chart_data['SMA_50'], line=dict(color='blue', width=1.5), name="SMA 50"))

        fig.update_layout(
            title=f"{selected_stock} Technical Chart (20 & 50 Days SMA)",
            xaxis_rangeslider_visible=False,
            height=450,
            template="plotly_dark"
        )
        st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("Data fetch nahi ho saka. Kripya page refresh karein.")

if st.button("🔄 Instant Refresh"):
    st.rerun()
