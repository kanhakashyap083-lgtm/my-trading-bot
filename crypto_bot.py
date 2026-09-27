import streamlit as st
import pandas as pd
import yfinance as yf
import requests
import warnings
import os
from datetime import date
from streamlit_autorefresh import st_autorefresh

warnings.filterwarnings("ignore")
st.set_page_config(page_title="Crypto AI Sniper", layout="wide", page_icon="🪙")

# Auto Scan - 3 Minutes
st_autorefresh(interval=180000, limit=10000, key="crypto_refresh") 

TELEGRAM_TOKEN = "8657774899:AAGKqx2_TgaoYAbUljSAXt5l9BzL_cnyCPE"
TELEGRAM_CHAT_ID = "8900320752"

def send_telegram_alert(message):
    try:
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", json={"chat_id": TELEGRAM_CHAT_ID, "text": message})
    except: pass

crypto_list = {
    "Bitcoin": "BTC-USD", "Ethereum": "ETH-USD", "Solana": "SOL-USD", 
    "BNB": "BNB-USD", "Ripple": "XRP-USD", "Dogecoin": "DOGE-USD",
    "Cardano": "ADA-USD", "Avalanche": "AVAX-USD", "Chainlink": "LINK-USD", 
    "Polkadot": "DOT-USD", "Polygon": "MATIC-USD", "Shiba Inu": "SHIB-USD",
    "Litecoin": "LTC-USD", "Bitcoin Cash": "BCH-USD", "Uniswap": "UNI-USD"
}

TRADE_FILE = f"crypto_trades_{date.today()}.csv"

def save_trade(name, symbol, action, entry, target, sl, strategy):
    if os.path.exists(TRADE_FILE):
        df = pd.read_csv(TRADE_FILE)
        if not df[(df['Coin'] == name) & (df['Status'].str.contains('Active|Trailing'))].empty: return False
    else:
        df = pd.DataFrame(columns=["Coin", "Symbol", "Action", "Strategy", "Entry", "Target", "SL", "Status"])
    
    new_trade = pd.DataFrame([{"Coin": name, "Symbol": symbol, "Action": action, "Strategy": strategy, "Entry": round(entry, 4), "Target": round(target, 4), "SL": round(sl, 4), "Status": "⏳ Active"}])
    df = pd.concat([df, new_trade], ignore_index=True)
    df.to_csv(TRADE_FILE, index=False)
    return True

def calculate_rsi(data, period=14):
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# ================= APP UI START =================
st.title("🪙 Global Crypto Pro-Scanner AI")
st.sidebar.title("⚙️ Crypto Settings")
timeframe_mode = st.sidebar.radio("⏱️ Strategy:", ["Scalping (15 Min)", "Swing (4 Hour)", "Long Term (1 Day)"])

tab1, tab2 = st.tabs(["🔍 Top 15 Scanner", "🎯 Live Scoreboard & Radar"])

# --- SCANNING LOGIC ---
if timeframe_mode == "Scalping (15 Min)":
    scan_period, scan_interval = "5d", "15m"
elif timeframe_mode == "Swing (4 Hour)":
    scan_period, scan_interval = "30d", "1h" 
else:
    scan_period, scan_interval = "100d", "1d"

live_market_data = [] # Radar ke liye data store karenge

with tab1:
    st.markdown("**Filters:** ✅ BTC Trend | ✅ Whale Volume (1.8x) | ✅ 4-Decimal Precision")
    
    with st.spinner("Scanning Top 15 Coins..."):
        results = []
        
        # Get BTC Trend for Master Filter
        try:
            btc_data = yf.Ticker("BTC-USD").history(period="5d", interval="1h")
            btc_ema9 = btc_data['Close'].ewm(span=9).mean().iloc[-1]
            btc_ema21 = btc_data['Close'].ewm(span=21).mean().iloc[-1]
            btc_trend = "BULLISH" if btc_ema9 > btc_ema21 else "BEARISH"
        except: btc_trend = "NEUTRAL"

        for name, ticker_symbol in crypto_list.items():
            try:
                data = yf.Ticker(ticker_symbol).history(period=scan_period, interval=scan_interval)
                if len(data) > 30:
                    curr = float(data['Close'].iloc[-1])
                    curr_vol = float(data['Volume'].iloc[-1])
                    
                    sma_20 = data['Close'].rolling(window=20).mean().iloc[-1]
                    std_20 = data['Close'].rolling(window=20).std().iloc[-1]
                    upper_bb, lower_bb = sma_20 + (std_20 * 2), sma_20 - (std_20 * 2)
                    
                    ema_9, ema_21 = data['Close'].ewm(span=9).mean().iloc[-1], data['Close'].ewm(span=21).mean().iloc[-1]
                    rsi_14 = calculate_rsi(data).iloc[-1]
                    
                    avg_vol_20 = data['Volume'].rolling(window=20).mean().iloc[-1]
                    volume_spike = curr_vol > (avg_vol_20 * 1.8) 
                    atr = (data['High'].iloc[-1] - data['Low'].iloc[-1]) * 1.5
                    
                    # Store data for Live Radar
                    live_market_data.append({"Coin": name, "Live Price": f"${curr:,.4f}", "RSI": round(rsi_14, 1), "Trend": "🟢 Bull" if ema_9 > ema_21 else "🔴 Bear"})
                    
                    bullish = (curr > upper_bb) and (ema_9 > ema_21) and (40 < rsi_14 < 70) and volume_spike and ("BULL" in btc_trend)
                    bearish = (curr < lower_bb) and (ema_9 < ema_21) and (30 < rsi_14 < 60) and volume_spike and ("BEAR" in btc_trend)
                    
                    tgt_mult, sl_mult = (4.0, 2.0) if timeframe_mode == "Scalping (15 Min)" else (6.0, 3.0)
                    tgt_pts, sl_pts = atr * tgt_mult, atr * sl_mult
                    
                    if bullish or bearish:
                        action = "🟢 BUY" if bullish else "🔴 SELL"
                        target_price = curr + tgt_pts if bullish else curr - tgt_pts
                        sl_price = curr - sl_pts if bullish else curr + sl_pts
                        
                        is_new = save_trade(name, ticker_symbol, action, curr, target_price, sl_price, timeframe_mode)
                        results.append({"Coin": name, "Action": action, "Entry": f"${curr:,.4f}", "Target": f"${target_price:,.4f}", "SL": f"${sl_price:,.4f}"})
                        
                        if is_new:
                            send_telegram_alert(f"🚀 CRYPTO {action}: {name}\nEntry: ${curr:,.4f}\nTarget: ${target_price:,.4f}\nSL: ${sl_price:,.4f}")
            except: pass
            
        if results: st.dataframe(pd.DataFrame(results), use_container_width=True)
        else: st.warning("⚖️ Waiting for 1.8x Whale Volume...")

with tab2:
    # 1. LIVE RADAR (यह कभी खाली नहीं रहेगा)
    st.subheader("📡 Live Market Radar (15 Coins)")
    st.caption("AI लगातार इन कॉइन्स को स्कैन कर रहा है। वॉल्यूम स्पाइक आते ही एंट्री लेगा।")
    if live_market_data:
        st.dataframe(pd.DataFrame(live_market_data), use_container_width=True)
    
    st.divider()

    # 2. ACTIVE TRADES SCOREBOARD
    st.subheader("🎯 Live Trades & Targets")
    if os.path.exists(TRADE_FILE):
        df = pd.read_csv(TRADE_FILE)
        active_trades = []
        for index, row in df.iterrows():
            if "Active" in row['Status'] or "Trailing" in row['Status']:
                active_trades.append(row)
                
        if active_trades:
            st.dataframe(pd.DataFrame(active_trades).drop(columns=['Symbol']), use_container_width=True)
        else:
            st.info("📉 No active trades triggered yet.")
    else:
        st.info("📉 Scanner is running, but no trades have hit the 1.8x volume criteria yet.")
