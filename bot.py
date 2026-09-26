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
st.set_page_config(page_title="Pro-Trader Ultimate AI", layout="wide", page_icon="👑")
# Auto Scan - Har 2 minute me refresh
st_autorefresh(interval=120000, limit=10000, key="mega_pro_refresh") 

# --- TELEGRAM SETUP ---
TELEGRAM_TOKEN = "8657774899:AAGKqx2_TgaoYAbUljSAXt5l9BzL_cnyCPE"
TELEGRAM_CHAT_ID = "8900320752"

def send_telegram_alert(message):
    try:
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", json={"chat_id": TELEGRAM_CHAT_ID, "text": message})
    except: pass

def play_sound_alarm():
    st.markdown("""<audio autoplay><source src="https://www.soundjay.com/buttons/sounds/beep-07a.mp3" type="audio/mpeg"></audio>""", unsafe_allow_html=True)

# 🚨 ALL SECTORS MEGA MASTER LIST 🚨
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

TRADE_FILE = f"pro_trades_{date.today()}.csv"

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

def get_nse_option_data(symbol):
    headers = {'User-Agent': 'Mozilla/5.0', 'Accept-Encoding': 'gzip, deflate', 'Accept-Language': 'en-US,en;q=0.9'}
    session = requests.Session()
    try:
        session.get("https://www.nseindia.com", headers=headers, timeout=5)
        response = session.get(f"https://www.nseindia.com/api/option-chain-indices?symbol={symbol}", headers=headers, timeout=5)
        if response.status_code == 200: return response.json()
    except: pass
    return None

# ================= APP UI START =================
st.title("👑 Pro-Trader Master AI")
st.sidebar.title("⚙️ Settings")
timeframe_mode = st.sidebar.radio("⏱️ Strategy:", ["Intraday (15 Min)", "Swing (1 Day)"])

# 📁 YAHAN FOLDERS (TABS) BANAYE GAYE HAIN
tab1, tab2, tab3 = st.tabs(["🔍 Stocks Auto-Scanner", "📊 Options Pro-Radar", "📓 Live Scoreboard"])

# FOLDER 1: STOCKS SCANNER
with tab1:
    st.subheader("📈 All-India Market Scanner")
    vix, nifty_trend = get_market_health()
    col1, col2, col3 = st.columns(3)
    with col1: st.metric("Broad Market Trend", nifty_trend)
    with col2: st.metric("INDIA VIX (Fear Meter)", f"{vix:.2f}", "⚠️ High Danger" if vix > 22 else "✅ Safe to Trade")
    with col3: 
        current_time = datetime.now(pytz.timezone('Asia/Kolkata'))
        st.metric("Market Time Zone", current_time.strftime("%I:%M %p"), "🚫 Trap Time" if current_time.hour == 9 and current_time.minute < 30 else "✅ Safe Time")
        
    st.divider()
    scan_period = "10d" if timeframe_mode == "Intraday (15 Min)" else "100d"
    scan_interval = "15m" if timeframe_mode == "Intraday (15 Min)" else "1d"
    
    with st.spinner(f"X-Ray Scanning {len(mega_stock_list)} Stocks..."):
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
                    volume_spike = curr_vol > (data['Volume'].rolling(window=20).mean().iloc[-1] * 1.5)
                    atr = (data['High'].iloc[-1] - data['Low'].iloc[-1]) * 1.5
                    is_index = "NIFTY" in name or "SENSEX" in name
                    
                    trend_aligned_buy = True if "BULLISH" in nifty_trend or timeframe_mode == "Swing (1 Day)" else False
                    trend_aligned_sell = True if "BEARISH" in nifty_trend or timeframe_mode == "Swing (1 Day)" else False
                    
                    bullish = (curr > upper_bb) and (ema_9 > ema_21) and (45 < rsi_14 < 75) and (volume_spike or is_index) and trend_aligned_buy
                    bearish = (curr < lower_bb) and (ema_9 < ema_21) and (25 < rsi_14 < 55) and (volume_spike or is_index) and trend_aligned_sell
                    
                    tgt_pts, sl_pts = (100, 50) if is_index else (atr * (4.0 if timeframe_mode == "Intraday (15 Min)" else 8.0), atr * (2.0 if timeframe_mode == "Intraday (15 Min)" else 4.0))
                    
                    if bullish or bearish:
                        action = "🟢 BUY" if bullish else "🔴 SELL"
                        is_new = save_trade(name, ticker_symbol, action, curr, curr + tgt_pts if bullish else curr - tgt_pts, curr - sl_pts if bullish else curr + sl_pts, timeframe_mode)
                        results.append({"Stock": name, "Action": action, "Entry": f"₹{curr:.2f}", "Target": f"₹{curr + tgt_pts if bullish else curr - tgt_pts:.2f}", "SL": f"₹{curr - sl_pts if bullish else curr + sl_pts:.2f}"})
                        if is_new:
                            play_sound_alarm()
                            send_telegram_alert(f"🚀 {action}: {name}\nEntry: ₹{curr:.2f}\nTarget: ₹{curr + tgt_pts if bullish else curr - tgt_pts:.2f}\nSL: ₹{curr - sl_pts if bullish else curr + sl_pts:.2f}")
            except: pass
        if results: st.dataframe(pd.DataFrame(results), use_container_width=True)
        else: st.warning("⚖️ Scanning Complete. Operator abhi shant hai.")

# FOLDER 2: OPTIONS RADAR
with tab2:
    st.subheader("🏦 Options Smart-Money Radar")
    selected_index = st.selectbox("Select Index:", ["NIFTY", "BANKNIFTY"])
    
    with st.spinner("Fetching Live NSE Option Chain Data..."):
        data = get_nse_option_data(selected_index)
        if data and 'records' in data:
            records = data['records']['data']
            current_price = data['records']['underlyingValue']
            tot_ce_oi, tot_pe_oi = data['filtered']['CE']['totOI'], data['filtered']['PE']['totOI']
            pcr = tot_pe_oi / tot_ce_oi if tot_ce_oi else 0
            
            ce_list = [{"Strike": item['strikePrice'], "OI": item['CE']['openInterest']} for item in records if 'CE' in item]
            pe_list = [{"Strike": item['strikePrice'], "OI": item['PE']['openInterest']} for item in records if 'PE' in item]
            highest_ce = max(ce_list, key=lambda x: x['OI'])
            highest_pe = max(pe_list, key=lambda x: x['OI'])
            
            st.markdown(f"**Live Spot Price:** ₹{current_price}")
            col1, col2, col3 = st.columns(3)
            with col1: st.metric("Put-Call Ratio (PCR)", round(pcr, 2), "🟢 Bullish" if pcr > 1.1 else "🔴 Bearish" if pcr < 0.8 else "🟡 Neutral")
            with col2: st.metric("🚧 Mega Resistance (CE)", f"{highest_ce['Strike']}", f"OI: {highest_ce['OI']}")
            with col3: st.metric("🛡️ Mega Support (PE)", f"{highest_pe['Strike']}", f"OI: {highest_pe['OI']}")
            
            st.divider()
            if current_price >= highest_ce['Strike']: st.error("🚀 **MEGA SHORT COVERING ALERT!** Buy CE on dips.")
            elif current_price <= highest_pe['Strike']: st.error("📉 **MEGA LONG UNWINDING ALERT!** Buy PE on bounce.")
            elif pcr > 1.2: st.success("📈 **BULLISH GRIP:** Buy CE near Support.")
            elif pcr < 0.8: st.warning("📉 **BEARISH GRIP:** Buy PE near Resistance.")
        else: st.error("⚠️ NSE Server blocked direct request. Try during Live Market hours.")

# FOLDER 3: LIVE SCOREBOARD
with tab3:
    st.subheader("🎯 Live Scoreboard (Zero-Risk Tracker)")
    if os.path.exists(TRADE_FILE):
        df = pd.read_csv(TRADE_FILE)
        for index, row in df.iterrows():
            if "Active" in row['Status'] or "Trailing" in row['Status']:
                try:
                    curr_price = float(yf.Ticker(row['Symbol']).history(period="1d", interval="1m")['Close'].iloc[-1])
                    entry, target, sl = float(row['Entry']), float(row['Target']), float(row['SL'])
                    halfway = entry + (target - entry) * 0.5 if "BUY" in row['Action'] else entry - (entry - target) * 0.5
                    
                    if ("BUY" in row['Action'] and curr_price >= target) or ("SELL" in row['Action'] and curr_price <= target): df.at[index, 'Status'] = "🏆 Target Hit"
                    elif ("BUY" in row['Action'] and curr_price <= sl) or ("SELL" in row['Action'] and curr_price >= sl): df.at[index, 'Status'] = "💔 SL Hit"
                    elif ("BUY" in row['Action'] and curr_price >= halfway and sl < entry) or ("SELL" in row['Action'] and curr_price <= halfway and sl > entry):
                        df.at[index, 'SL'], df.at[index, 'Status'] = entry, "🚀 Trailing (0 Risk)"
                except: continue
        df.to_csv(TRADE_FILE, index=False)
        st.dataframe(df.drop(columns=['Symbol']), use_container_width=True)
    else: st.info("📉 No active trades today.")
