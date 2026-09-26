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

# Auto Scan - 3 Minutes (180 seconds) API block se bachne ke liye
st_autorefresh(interval=180000, limit=10000, key="crypto_refresh") 

# --- TELEGRAM SETUP ---
TELEGRAM_TOKEN = "8657774899:AAGKqx2_TgaoYAbUljSAXt5l9BzL_cnyCPE"
TELEGRAM_CHAT_ID = "8900320752"

def send_telegram_alert(message):
    try:
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", json={"chat_id": TELEGRAM_CHAT_ID, "text": message})
    except: pass

def play_sound_alarm():
    st.markdown("""<audio autoplay><source src="https://www.soundjay.com/buttons/sounds/beep-07a.mp3" type="audio/mpeg"></audio>""", unsafe_allow_html=True)

# 🚨 TOP 15 GLOBAL COINS MASTER LIST 🚨
crypto_list = {
    "Bitcoin (King)": "BTC-USD", "Ethereum (Smart Contracts)": "ETH-USD",
    "Solana (High Speed)": "SOL-USD", "Binance Coin (Exchange)": "BNB-USD",
    "Ripple (Payments)": "XRP-USD", "Dogecoin (Meme)": "DOGE-USD",
    "Cardano (DeFi)": "ADA-USD", "Avalanche (Layer 1)": "AVAX-USD",
    "Chainlink (Oracles)": "LINK-USD", "Polkadot (Web3)": "DOT-USD",
    "Polygon (Layer 2)": "MATIC-USD", "Shiba Inu (Meme)": "SHIB-USD",
    "Litecoin (Payments)": "LTC-USD", "Bitcoin Cash": "BCH-USD",
    "Uniswap (DEX)": "UNI-USD"
}

# Crypto Trades ke liye alag database
TRADE_FILE = f"crypto_trades_{date.today()}.csv"

def save_trade(name, symbol, action, entry, target, sl, strategy):
    if os.path.exists(TRADE_FILE):
        df = pd.read_csv(TRADE_FILE)
        if not df[(df['Coin'] == name) & (df['Status'].str.contains('Active|Trailing'))].empty: return False
    else:
        df = pd.DataFrame(columns=["Coin", "Symbol", "Action", "Strategy", "Entry", "Target", "SL", "Status"])
    
    # 4-Decimal Precision for Crypto
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

# --- BTC KING ALIGNMENT (Layer 1 for Crypto) ---
def get_btc_health():
    try:
        btc_data = yf.Ticker("BTC-USD").history(period="5d", interval="1h")
        btc_ema9 = btc_data['Close'].ewm(span=9).mean().iloc[-1]
        btc_ema21 = btc_data['Close'].ewm(span=21).mean().iloc[-1]
        btc_trend = "🟢 BULLISH" if btc_ema9 > btc_ema21 else "🔴 BEARISH"
        curr_price = btc_data['Close'].iloc[-1]
        return btc_trend, curr_price
    except: return "🟡 NEUTRAL", 0.0

# ================= APP UI START =================
st.title("🪙 Global Crypto Pro-Scanner AI")
st.sidebar.title("⚙️ Crypto Settings")
timeframe_mode = st.sidebar.radio("⏱️ Strategy:", ["Scalping (15 Min)", "Swing (4 Hour)", "Long Term (1 Day)"])

# 2 Tabs for Crypto (No Mixup)
tab1, tab2 = st.tabs(["🔍 Top 15 Coins Scanner", "🎯 Zero-Risk Scoreboard"])

with tab1:
    btc_trend, btc_price = get_btc_health()
    
    col1, col2, col3 = st.columns(3)
    with col1: st.metric("BTC King Trend (Master Filter)", btc_trend)
    with col2: st.metric("BTC Current Price", f"${btc_price:,.2f}")
    with col3: st.metric("Market Status", "🌍 24/7 Open", "✅ Live")
        
    st.divider()
    st.markdown("**Crypto AI Filters:** ✅ BTC Trend Alignment | ✅ Whale Volume (1.8x) | ✅ 4-Decimal Precision | ⏱️ 3-Min Auto-Refresh")
    
    if timeframe_mode == "Scalping (15 Min)":
        scan_period, scan_interval = "5d", "15m"
    elif timeframe_mode == "Swing (4 Hour)":
        scan_period, scan_interval = "30d", "1h" 
    else:
        scan_period, scan_interval = "100d", "1d"
    
    with st.spinner(f"X-Ray Scanning {len(crypto_list)} Crypto Coins..."):
        results = []
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
                    # 1.8x Crypto Whale Volume Filter
                    volume_spike = curr_vol > (avg_vol_20 * 1.8) 
                    
                    atr = (data['High'].iloc[-1] - data['Low'].iloc[-1]) * 1.5
                    
                    trend_aligned_buy = True if "BULLISH" in btc_trend else False
                    trend_aligned_sell = True if "BEARISH" in btc_trend else False
                    
                    bullish = (curr > upper_bb) and (ema_9 > ema_21) and (40 < rsi_14 < 70) and volume_spike and trend_aligned_buy
                    bearish = (curr < lower_bb) and (ema_9 < ema_21) and (30 < rsi_14 < 60) and volume_spike and trend_aligned_sell
                    
                    tgt_multiplier = 4.0 if timeframe_mode == "Scalping (15 Min)" else 6.0
                    sl_multiplier = 2.0 if timeframe_mode == "Scalping (15 Min)" else 3.0
                    tgt_pts, sl_pts = atr * tgt_multiplier, atr * sl_multiplier
                    
                    if bullish or bearish:
                        action = "🟢 BUY (LONG)" if bullish else "🔴 SELL (SHORT)"
                        target_price = curr + tgt_pts if bullish else curr - tgt_pts
                        sl_price = curr - sl_pts if bullish else curr + sl_pts
                        
                        is_new = save_trade(name, ticker_symbol, action, curr, target_price, sl_price, timeframe_mode)
                        results.append({"Coin": name, "Action": action, "Entry": f"${curr:,.4f}", "Target": f"${target_price:,.4f}", "SL": f"${sl_price:,.4f}"})
                        
                        if is_new:
                            play_sound_alarm()
                            send_telegram_alert(f"🚀 CRYPTO {action}: {name}\nEntry: ${curr:,.4f}\nTarget: ${target_price:,.4f}\nSL: ${sl_price:,.4f}\n📊 RSI: {rsi_14:.0f} | Whale Vol: Yes")
            except: pass
            
        if results: st.dataframe(pd.DataFrame(results), use_container_width=True)
        else: st.warning("⚖️ Scanning Complete. Crypto Whales shant hain. Waiting for next 1.8x volume spike.")

with tab2:
    st.subheader("🎯 Zero-Risk Scoreboard (Crypto)")
    if os.path.exists(TRADE_FILE):
        df = pd.read_csv(TRADE_FILE)
        for index, row in df.iterrows():
            if "Active" in row['Status'] or "Trailing" in row['Status']:
                try:
                    curr_price = float(yf.Ticker(row['Symbol']).history(period="1d", interval="1m")['Close'].iloc[-1])
                    entry, target, sl = float(row['Entry']), float(row['Target']), float(row['SL'])
                    halfway = entry + (target - entry) * 0.5 if "BUY" in row['Action'] else entry - (entry - target) * 0.5
                    
                    if ("BUY" in row['Action'] and curr_price >= target) or ("SELL" in row['Action'] and curr_price <= target): 
                        df.at[index, 'Status'] = "🏆 Target Hit"
                        send_telegram_alert(f"🏆 CRYPTO TARGET HIT: {row['Coin']} - Profit booked! 💸")
                    elif ("BUY" in row['Action'] and curr_price <= sl) or ("SELL" in row['Action'] and curr_price >= sl): 
                        df.at[index, 'Status'] = "💔 SL Hit"
                    elif ("BUY" in row['Action'] and curr_price >= halfway and sl < entry) or ("SELL" in row['Action'] and curr_price <= halfway and sl > entry):
                        df.at[index, 'SL'], df.at[index, 'Status'] = entry, "🚀 Trailing (0 Risk)"
                        send_telegram_alert(f"🛡️ ZERO RISK: {row['Coin']} SL moved to Entry (${entry}).")
                except: continue
        df.to_csv(TRADE_FILE, index=False)
        st.dataframe(df.drop(columns=['Symbol']), use_container_width=True)
    else: st.info("📉 No active trades today.")
