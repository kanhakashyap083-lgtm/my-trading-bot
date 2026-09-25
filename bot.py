import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import warnings

warnings.filterwarnings("ignore")
st.set_page_config(page_title="Master AI Trading Bot", layout="wide")

st.sidebar.header("🔍 A-to-Z Market Scanner")
category = st.sidebar.selectbox(
    "Sector ya Index Select Karein",
    ["Nifty 50 (Top Stocks)", "Bank Nifty", "IT Sector", "Auto Sector", "Pharma Sector", "FMCG Sector", "Metal Sector", "ETFs (Safe)"]
)

st.title(f"📈 AI Live Dashboard: {category}")
st.write("Live market scan chal raha hai, kripya thoda intezaar karein...")

# A-to-Z Comprehensive Market Data
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
progress_bar = st.progress(0, text="Data scan ho raha hai...")

for i, ticker in enumerate(stocks_list):
    try:
        stock_data = yf.Ticker(ticker)
        data = stock_data.history(period="6mo")
        if data.empty: continue

        data['RSI'] = ta.momentum.RSIIndicator(data['Close'], window=14).rsi()
        data['SMA_20'] = ta.trend.SMAIndicator(data['Close'], window=20).sma_indicator()
        data['SMA_50'] = ta.trend.SMAIndicator(data['Close'], window=50).sma_indicator()
        data['ATR'] = ta.volatility.AverageTrueRange(data['High'], data['Low'], data['Close'], window=14).average_true_range()

        latest = data.iloc[-1]
        current_price = latest['Close']
        target = current_price * 1.04
        stop_loss = current_price * 0.98
        
        daily_movement = (latest['ATR'] / current_price) * 100
        holding_days = int((4.0 / daily_movement)) + 1 if daily_movement > 0 else 5
        hold_str = "15+ Din" if holding_days > 15 else f"{holding_days} se {holding_days+3} Din"

        if latest['RSI'] < 30:
            signal, t_str, sl_str = "🟢 BUY! (Sasta hai)", f"₹{target:.1f}", f"₹{stop_loss:.1f}"
        elif latest['RSI'] > 70:
            signal, t_str, sl_str, hold_str = "🔴 SELL! (Mehnga hai)", "-", "-", "-"
        elif latest['SMA_20'] > latest['SMA_50']:
            signal, t_str, sl_str = "📈 UPTREND (Hold)", f"₹{target:.1f}", f"₹{stop_loss:.1f}"
        else:
            signal, t_str, sl_str, hold_str = "🟡 WAIT (Door rahein)", "-", "-", "-"

        results.append({"Stock": ticker.replace('.NS', ''), "Price": f"₹{current_price:.2f}", "Signal": signal, "Target (+4%)": t_str, "Stop-Loss (-2%)": sl_str, "Est. Hold": hold_str})
    except: pass
    
    progress_bar.progress(int(((i + 1) / len(stocks_list)) * 100), text=f"{ticker} scan ho raha hai...")

progress_bar.empty()
st.dataframe(pd.DataFrame(results), width='stretch')

if st.button("🔄 Live Refresh"): st.rerun()