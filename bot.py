import streamlit as st
import pandas as pd
import yfinance as yf
import requests
import warnings
import os
from datetime import date, datetime
import pytz
from streamlit_autorefresh import st_autorefresh

warnings.filterwarnings("ignore")
st.set_page_config(page_title="Indian Stocks Pro AI", layout="wide", page_icon="🇮🇳")

# Auto Scan - हर 2 मिनट (120 seconds) में रिफ्रेश
st_autorefresh(interval=120000, limit=10000, key="indian_stocks_refresh") 

# --- TELEGRAM SETUP ---
TELEGRAM_TOKEN = "8657774899:AAGKqx2_TgaoYAbUljSAXt5l9BzL_cnyCPE"
TELEGRAM_CHAT_ID = "8900320752"

def send_telegram_alert(message):
    try:
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", json={"chat_id": TELEGRAM_CHAT_ID, "text": message})
    except: pass

def play_sound_alarm():
    st.markdown("""<audio autoplay><source src="https://www.soundjay.com/buttons/sounds/beep-07a.mp3" type="audio/mpeg"></audio>""", unsafe_allow_html=True)

# 🚨 50+ ALL SECTORS MEGA MASTER LIST 🚨
mega_stock_list = {
    "NIFTY 50": "^NSEI", "BANK NIFTY": "^NSEBANK", "SENSEX": "^BSESN",
    "HAL (Defence)": "HAL.NS", "BEL (Defence)": "BEL.NS", "MAZAGON DOCK": "MAZDOCK.NS", 
    "IRFC (Rail)": "IRFC.NS", "RVNL (Rail)": "RVNL.NS", "TITAGARH": "TITAGARH.NS",
    "NTPC": "NTPC.NS", "TATA POWER": "TATAPOWER.NS", "ADANI GREEN": "ADANIGREEN.NS",
    "TCS": "TCS.NS", "INFOSYS": "INFY.NS", "TECH MAHINDRA": "TECHM.NS",
    "HDFC BANK": "HDFCBANK.NS", "SBI": "SBIN.NS", "ICICI BANK": "ICICIBANK.NS", "BAJAJ FINANCE": "BAJFINANCE.NS",
    "TATA MOTORS": "TATAMOTORS.NS", "MARUTI": "MARUTI.NS", "M&M": "M&M.NS",
    "ITC": "ITC.NS", "HUL": "HINDUNILVR.NS", "VARUN BEVERAGES": "VBL.NS",
    "BALRAMPUR CHINI": "BALRAMCHIN.NS", "UPL (Agri)": "UPL.NS", 
    "ASIAN PAINTS": "ASIANPAINT.NS", "ULTRATECH CEMENT": "ULTRACEMCO.NS", 
    "ASTRAL (Plastic)": "ASTRAL.NS", "PIDILITE": "PIDILITIND.NS", 
    "DLF (Real Estate)": "DLF.NS", "GODREJ PROP": "GODREJPROP.NS",
    "SUN PHARMA": "SUNPHARMA.NS", "APOLLO HOSPITALS": "APOLLOHOSP.NS",
    "TATA STEEL": "TATASTEEL.NS", "JSW STEEL": "JSWSTEEL.NS", 
    "RELIANCE": "RELIANCE.NS", "BHARTI AIRTEL": "BHARTIARTL.NS",
    "INDIGO (Aviation)": "INDIGO.NS", "CONCOR (Logistics)": "CONCOR.NS",
    "HAVELLS": "HAVELLS.NS", "DIXON TECH": "DIXON.NS",
    "TITAN (Jewellery)": "TITAN.NS", "TRENT (Apparel)": "TRENT.NS", "D-MART": "DMART.NS",
    "ZOMATO": "ZOMATO.NS", "PAYTM": "PAYTM.NS"
}

# Indian trades के लिए अलग डेटाबेस फाइल
TRADE_FILE = f"indian_trades_{date.today()}.csv"

def save_trade(name, symbol, action, entry, target, sl, strategy):
    if os.path.exists(TRADE_FILE):
        df = pd.read_csv(TRADE_FILE)
        if not df[(df['Stock'] == name) & (df['Status'].str.contains('Active|Trailing'))].empty: return False
    else:
        df = pd.DataFrame(columns=["Stock", "Symbol", "Action", "Strategy", "Entry", "Target", "SL", "Status"])
    
    new_trade = pd.DataFrame([{"Stock": name, "Symbol": symbol, "Action": action, "Strategy": strategy, "Entry": round(entry, 2), "Target": round(target, 2), "SL": round(sl, 2), "Status": "⏳ Active"}])
    df = pd.concat([df, new_trade], ignore_index=True)
    df.to_csv(TRADE_FILE, index=False)
    return True

def calculate_rsi(data, period=14):
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# --- MARKET HEALTH & ALIGNMENT ---
def get_market_health():
    try:
        vix_data = yf.Ticker("^INDIAVIX").history(period="1d")
        nifty_data = yf.Ticker("^NSEI").history(period="5d", interval="15m")
        vix = vix_data['Close'].iloc[-1] if not vix_data.empty else 15.0
        nifty_ema9 = nifty_data['Close'].ewm(span=9).mean().iloc[-1]
        nifty_ema21 = nifty_data['Close'].ewm(span=21).mean().iloc[-1]
        nifty_trend = "🟢 BULLISH" if nifty_ema9 > nifty_ema21 else "🔴 BEARISH"
        return vix, nifty_trend
    except: return 15.0, "🟡 NEUTRAL"

# ================= APP UI START =================
st.title("🇮🇳 Indian Stocks Pro-Scanner AI")
st.sidebar.title("⚙️ Strategy Settings")
timeframe_mode = st.sidebar.radio("⏱️ Select Style:", ["Intraday (15 Min)", "Swing (1 Day)"])

# सिर्फ 2 टैब्स (कोई ऑप्शन चेन या क्रिप्टो मिक्स नहीं)
tab1, tab2 = st.tabs(["🔍 6-Layer Auto-Scanner", "🎯 Live Scoreboard"])

with tab1:
    vix, nifty_trend = get_market_health()
    current_time = datetime.now(pytz.timezone('Asia/Kolkata'))
    is_trap_time = current_time.hour == 9 and current_time.minute < 30
    
    col1, col2, col3 = st.columns(3)
    with col1: st.metric("NIFTY Trend (Layer 5)", nifty_trend)
    with col2: st.metric("INDIA VIX (Fear Meter)", f"{vix:.2f}", "⚠️ High Danger" if vix > 22 else "✅ Safe to Trade")
    with col3: st.metric("Market Time Status", current_time.strftime("%I:%M %p"), "🚫 Operator Trap Time" if is_trap_time else "✅ Safe Time")
        
    st.divider()
    st.markdown("**Active AI Filters:** ✅ Breakout | ✅ EMA Crossover | ✅ RSI Momentum | ✅ Whale Volume (1.5x) | ✅ Nifty Alignment | 💧 **10Cr+ Liquidity**")
    
    scan_period = "10d" if timeframe_mode == "Intraday (15 Min)" else "100d"
    scan_interval = "15m" if timeframe_mode == "Intraday (15 Min)" else "1d"
    
    if is_trap_time:
        st.error("🚫 **TRAP TIME ACTIVE (9:15 AM - 9:30 AM):** AI scanning paused to avoid operator traps.")
    else:
        with st.spinner(f"X-Ray Scanning {len(mega_stock_list)} Indian Stocks..."):
            results = []
            for name, ticker_symbol in mega_stock_list.items():
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
                        # 1.5x Whale Volume (Layer 4)
                        volume_spike = curr_vol > (avg_vol_20 * 1.5)
                        
                        # Liquidity Check (Layer 6) - 5 Lakh Volume OR 10 Crore Turnover
                        avg_turnover = avg_vol_20 * curr
                        is_liquid = (avg_vol_20 > 500000) or (avg_turnover > 100000000)
                        
                        atr = (data['High'].iloc[-1] - data['Low'].iloc[-1]) * 1.5
                        is_index = "NIFTY" in name or "SENSEX" in name
                        
                        # Nifty Alignment (Layer 5)
                        trend_aligned_buy = True if "BULLISH" in nifty_trend or timeframe_mode == "Swing (1 Day)" else False
                        trend_aligned_sell = True if "BEARISH" in nifty_trend or timeframe_mode == "Swing (1 Day)" else False
                        
                        # 6-Layer Final Check
                        bullish = (curr > upper_bb) and (ema_9 > ema_21) and (45 < rsi_14 < 75) and (volume_spike or is_index) and trend_aligned_buy and (is_liquid or is_index)
                        bearish = (curr < lower_bb) and (ema_9 < ema_21) and (25 < rsi_14 < 55) and (volume_spike or is_index) and trend_aligned_sell and (is_liquid or is_index)
                        
                        tgt_pts, sl_pts = (100, 50) if is_index else (atr * (4.0 if timeframe_mode == "Intraday (15 Min)" else 8.0), atr * (2.0 if timeframe_mode == "Intraday (15 Min)" else 4.0))
                        
                        if bullish or bearish:
                            action = "🟢 BUY" if bullish else "🔴 SELL"
                            target_price = curr + tgt_pts if bullish else curr - tgt_pts
                            sl_price = curr - sl_pts if bullish else curr + sl_pts
                            
                            is_new = save_trade(name, ticker_symbol, action, curr, target_price, sl_price, timeframe_mode)
                            results.append({"Stock": name, "Action": action, "Entry": f"₹{curr:.2f}", "Target": f"₹{target_price:.2f}", "SL": f"₹{sl_price:.2f}"})
                            
                            if is_new:
                                play_sound_alarm()
                                send_telegram_alert(f"🚀 {action}: {name}\nEntry: ₹{curr:.2f}\nTarget: ₹{target_price:.2f}\nSL: ₹{sl_price:.2f}\n💧 High Liquidity Verified!")
                except: pass
            
            if results: st.dataframe(pd.DataFrame(results), use_container_width=True)
            else: st.warning("⚖️ Scanning Complete. Strict 6-Layer rules active. Operator abhi shant hai.")

with tab2:
    st.subheader("🎯 Zero-Risk Scoreboard (Indian Stocks)")
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
                        send_telegram_alert(f"🏆 TARGET HIT: {row['Stock']} - Profit booked!")
                    elif ("BUY" in row['Action'] and curr_price <= sl) or ("SELL" in row['Action'] and curr_price >= sl): 
                        df.at[index, 'Status'] = "💔 SL Hit"
                    elif ("BUY" in row['Action'] and curr_price >= halfway and sl < entry) or ("SELL" in row['Action'] and curr_price <= halfway and sl > entry):
                        df.at[index, 'SL'], df.at[index, 'Status'] = entry, "🚀 Trailing (0 Risk)"
                        send_telegram_alert(f"🛡️ ZERO RISK ACTIVATED: {row['Stock']}\nStop-loss moved to Entry Price (₹{entry}).")
                except: continue
        df.to_csv(TRADE_FILE, index=False)
        st.dataframe(df.drop(columns=['Symbol']), use_container_width=True)
    else: st.info("📉 No active trades today.")
