import streamlit as st
import pandas as pd
import yfinance as yf
import requests
import warnings
import os
from datetime import date
from streamlit_autorefresh import st_autorefresh

warnings.filterwarnings("ignore")
st.set_page_config(page_title="Pro-Trader Master AI", layout="wide", page_icon="👑")
# लैपटॉप और मोबाइल पर अपने आप रिफ्रेश होगा (हर 2 मिनट में)
st_autorefresh(interval=120000, limit=10000, key="mega_pro_refresh") 

# --- TELEGRAM SETUP ---
TELEGRAM_TOKEN = "8657774899:AAGKqx2_TgaoYAbUljSAXt5l9BzL_cnyCPE"
TELEGRAM_CHAT_ID = "8900320752"

def send_telegram_alert(message):
    try:
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", json={"chat_id": TELEGRAM_CHAT_ID, "text": message})
    except: pass

# --- AUDIO ALARM FOR LAPTOP ---
def play_sound_alarm():
    # यह लैपटॉप ब्राउज़र में बीप की आवाज़ करेगा
    st.markdown("""<audio autoplay><source src="https://www.soundjay.com/buttons/sounds/beep-07a.mp3" type="audio/mpeg"></audio>""", unsafe_allow_html=True)

st.sidebar.title("👑 Pro-Trader Master AI")
app_mode = st.sidebar.radio("📁 Menu:", ["🔍 Mega Market Scanner", "📓 Tracker (Zero-Risk TSL)"])
timeframe_mode = st.sidebar.radio("⏱️ Strategy:", ["Intraday (15 Min)", "Swing (1 Day)"])

# 🚨 ALL SECTORS MEGA MASTER LIST (Top 50+ Pro Stocks) 🚨
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
    "ASTRAL (Plastic)": "ASTRAL.NS", "PIDILITE": "PIDILITIND.NS", "TATA CHEMICALS": "TATACHEM.NS",
    "DLF (Real Estate)": "DLF.NS", "GODREJ PROP": "GODREJPROP.NS",
    "SUN PHARMA": "SUNPHARMA.NS", "APOLLO HOSPITALS": "APOLLOHOSP.NS",
    "TATA STEEL": "TATASTEEL.NS", "JSW STEEL": "JSWSTEEL.NS", "HINDALCO": "HINDALCO.NS",
    "RELIANCE": "RELIANCE.NS", "BHARTI AIRTEL": "BHARTIARTL.NS", "ZEEL": "ZEEL.NS",
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

# --- RSI CALCULATION FUNCTION ---
def calculate_rsi(data, period=14):
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

if app_mode == "🔍 Mega Market Scanner":
    st.title("👑 Master Pro-Trader AI Scanner")
    st.markdown("""
    **4-Layer AI Checking Active:** 
    ✅ Breakout (Bollinger Bands) | ✅ Trend (9 & 21 EMA) | ✅ Momentum (RSI) | ✅ Smart Money (Volume Spike)
    """)
    
    scan_period = "10d" if timeframe_mode == "Intraday (15 Min)" else "100d"
    scan_interval = "15m" if timeframe_mode == "Intraday (15 Min)" else "1d"
    hold_time_text = "Same Day (Intraday)" if timeframe_mode == "Intraday (15 Min)" else "3 to 15 Days (Swing)"
    
    progress_bar = st.progress(0)
    
    with st.spinner(f"X-Ray Scanning {len(mega_stock_list)} Stocks across All Sectors..."):
        results = []
        items = list(mega_stock_list.items())
        total_items = len(items)
        
        for i, (name, ticker_symbol) in enumerate(items):
            try:
                data = yf.Ticker(ticker_symbol).history(period=scan_period, interval=scan_interval)
                if len(data) > 30:
                    curr = float(data['Close'].iloc[-1])
                    curr_vol = float(data['Volume'].iloc[-1])
                    
                    # 1. Bollinger Bands
                    sma_20 = data['Close'].rolling(window=20).mean().iloc[-1]
                    std_20 = data['Close'].rolling(window=20).std().iloc[-1]
                    upper_bb = sma_20 + (std_20 * 2)
                    lower_bb = sma_20 - (std_20 * 2)
                    
                    # 2. EMA Trend
                    ema_9 = data['Close'].ewm(span=9, adjust=False).mean().iloc[-1]
                    ema_21 = data['Close'].ewm(span=21, adjust=False).mean().iloc[-1]
                    
                    # 3. RSI Momentum
                    rsi_14 = calculate_rsi(data).iloc[-1]
                    
                    # 4. Volume Spike (Smart Money)
                    avg_vol_20 = data['Volume'].rolling(window=20).mean().iloc[-1]
                    volume_spike = curr_vol > (avg_vol_20 * 1.5) # 50% more than average
                    
                    # Dynamic ATR for SL/Target
                    atr = (data['High'].iloc[-1] - data['Low'].iloc[-1]) * 1.5
                    
                    # --- GOD-MODE LOGIC ---
                    # Indices me volume check nahi hota isliye unhe alag rakha hai
                    is_index = "NIFTY" in name or "SENSEX" in name
                    
                    # BUY CONDITION: Breakout + Up Trend + Healthy RSI + High Volume
                    bullish = (curr > upper_bb) and (ema_9 > ema_21) and (45 < rsi_14 < 75) and (volume_spike or is_index)
                    
                    # SELL CONDITION: Breakdown + Down Trend + Healthy RSI + High Volume
                    bearish = (curr < lower_bb) and (ema_9 < ema_21) and (25 < rsi_14 < 55) and (volume_spike or is_index)
                    
                    if is_index:
                        tgt_pts, sl_pts = 100, 50
                    else:
                        tgt_multiplier = 4.0 if timeframe_mode == "Intraday (15 Min)" else 8.0
                        sl_multiplier = 2.0 if timeframe_mode == "Intraday (15 Min)" else 4.0
                        tgt_pts, sl_pts = atr * tgt_multiplier, atr * sl_multiplier
                    
                    if bullish:
                        is_new = save_trade(name, ticker_symbol, "🟢 BUY", curr, curr + tgt_pts, curr - sl_pts, timeframe_mode)
                        results.append({"Stock": name, "Action": "🟢 BUY", "Entry": f"₹{curr:.2f}", "Target": f"₹{curr + tgt_pts:.2f}", "SL": f"₹{curr - sl_pts:.2f}", "Hold": hold_time_text})
                        if is_new:
                            play_sound_alarm()
                            send_telegram_alert(f"🚀 PRO BUY: {name} ({timeframe_mode})\nEntry: ₹{curr:.2f}\nTarget: ₹{curr + tgt_pts:.2f}\nSL: ₹{curr - sl_pts:.2f}\n📊 RSI: {rsi_14:.0f} | Vol Spike: Yes\n⏳ Hold: {hold_time_text}")
                            
                    elif bearish:
                        is_new = save_trade(name, ticker_symbol, "🔴 SELL", curr, curr - tgt_pts, curr + sl_pts, timeframe_mode)
                        results.append({"Stock": name, "Action": "🔴 SELL", "Entry": f"₹{curr:.2f}", "Target": f"₹{curr - tgt_pts:.2f}", "SL": f"₹{curr + sl_pts:.2f}", "Hold": hold_time_text})
                        if is_new:
                            play_sound_alarm()
                            send_telegram_alert(f"📉 PRO SELL: {name} ({timeframe_mode})\nEntry: ₹{curr:.2f}\nTarget: ₹{curr - tgt_pts:.2f}\nSL: ₹{curr + sl_pts:.2f}\n📊 RSI: {rsi_14:.0f} | Vol Spike: Yes\n⏳ Hold: {hold_time_text}")
            except: pass
            
            progress_bar.progress((i + 1) / total_items)
            
        if results:
            st.success(f"🔥 {len(results)} Pro Setups Found!")
            st.dataframe(pd.DataFrame(results), use_container_width=True)
        else:
            st.warning("⚖️ Scanning Complete. Operator/Smart Money abhi shant hai. AI wait kar raha hai...")

elif app_mode == "📓 Tracker (Zero-Risk TSL)":
    st.title("🎯 Pro-Trader Scoreboard")
    st.markdown("जब ट्रेड 50% प्रॉफिट में आता है, तो आपका Stop-Loss अपने आप Entry Price पर आ जाता है (Risk = 0)")
    
    if os.path.exists(TRADE_FILE):
        df = pd.read_csv(TRADE_FILE)
        for index, row in df.iterrows():
            if "Active" in row['Status'] or "Trailing" in row['Status']:
                try:
                    curr_price = float(yf.Ticker(row['Symbol']).history(period="1d", interval="1m")['Close'].iloc[-1])
                    entry = float(row['Entry'])
                    target = float(row['Target'])
                    old_status = row['Status']
                    
                    if "BUY" in row['Action']:
                        halfway = entry + (target - entry) * 0.5
                        if curr_price >= target: 
                            df.at[index, 'Status'] = "🏆 Target Hit"
                            send_telegram_alert(f"🏆 BOOM! TARGET HIT: {row['Stock']} (BUY) - Profit booked at ₹{curr_price:.2f} 💸")
                        elif curr_price <= float(row['SL']): 
                            df.at[index, 'Status'] = "💔 SL Hit"
                        elif curr_price >= halfway and float(row['SL']) < entry:
                            df.at[index, 'SL'] = entry
                            df.at[index, 'Status'] = "🚀 Trailing (0 Risk)"
                            if old_status != "🚀 Trailing (0 Risk)":
                                send_telegram_alert(f"🛡️ SAFE MODE: {row['Stock']} (BUY) is running in profit. SL moved to Entry Price!")
                                
                    elif "SELL" in row['Action']:
                        halfway = entry - (entry - target) * 0.5
                        if curr_price <= target: 
                            df.at[index, 'Status'] = "🏆 Target Hit"
                            send_telegram_alert(f"🏆 BOOM! TARGET HIT: {row['Stock']} (SELL) - Profit booked at ₹{curr_price:.2f} 💸")
                        elif curr_price >= float(row['SL']): 
                            df.at[index, 'Status'] = "💔 SL Hit"
                        elif curr_price <= halfway and float(row['SL']) > entry:
                            df.at[index, 'SL'] = entry
                            df.at[index, 'Status'] = "🚀 Trailing (0 Risk)"
                            if old_status != "🚀 Trailing (0 Risk)":
                                send_telegram_alert(f"🛡️ SAFE MODE: {row['Stock']} (SELL) is running in profit. SL moved to Entry Price!")
                except: continue
        df.to_csv(TRADE_FILE, index=False)
        
        col1, col2, col3 = st.columns(3)
        col1.success(f"🏆 Winning: {len(df[df['Status'] == '🏆 Target Hit'])}")
        col2.error(f"💔 SL Hit: {len(df[df['Status'] == '💔 SL Hit'])}")
        col3.warning(f"🚀 Running: {len(df[df['Status'].str.contains('Active|Trailing')])}")
        
        st.dataframe(df.drop(columns=['Symbol']), use_container_width=True)
    else:
        st.info("📉 No active trades today.")
