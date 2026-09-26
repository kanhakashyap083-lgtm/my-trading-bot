import streamlit as st
import pandas as pd
import yfinance as yf
import requests
import warnings
import os
from datetime import date
from streamlit_autorefresh import st_autorefresh

warnings.filterwarnings("ignore")
st.set_page_config(page_title="All India Master Scanner", layout="wide", page_icon="🔥")
st_autorefresh(interval=120000, limit=1000, key="mega_refresh") # 2 min refresh

TELEGRAM_TOKEN = "8657774899:AAGKqx2_TgaoYAbUljSAXt5l9BzL_cnyCPE"
TELEGRAM_CHAT_ID = "8900320752"

def send_telegram_alert(message):
    try:
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", json={"chat_id": TELEGRAM_CHAT_ID, "text": message})
    except: pass

st.sidebar.title("⚡ All India Mega AI")
app_mode = st.sidebar.radio("📁 Menu:", ["🔍 Mega Market Scanner", "📓 Tracker (Scoreboard & TSL)"])
timeframe_mode = st.sidebar.radio("⏱️ Strategy:", ["Intraday (15 Min)", "Swing (1 Day)"])

# 🚨 ALL SECTORS MEGA MASTER LIST 🚨
mega_stock_list = {
    "NIFTY 50": "^NSEI", "BANK NIFTY": "^NSEBANK", "SENSEX": "^BSESN",
    "HAL (Defence)": "HAL.NS", "BEL (Defence)": "BEL.NS", "MAZAGON DOCK": "MAZDOCK.NS", "BDL": "BDL.NS",
    "IRFC (Rail)": "IRFC.NS", "RVNL (Rail)": "RVNL.NS", "IRCON": "IRCON.NS", "TITAGARH": "TITAGARH.NS",
    "NTPC": "NTPC.NS", "TATA POWER": "TATAPOWER.NS", "POWERGRID": "POWERGRID.NS", "ADANI GREEN": "ADANIGREEN.NS", "GAIL (Gas)": "GAIL.NS",
    "TCS": "TCS.NS", "INFOSYS": "INFY.NS", "WIPRO": "WIPRO.NS", "HCL TECH": "HCLTECH.NS", "TECH MAHINDRA": "TECHM.NS",
    "HDFC BANK": "HDFCBANK.NS", "SBI": "SBIN.NS", "ICICI BANK": "ICICIBANK.NS", "BAJAJ FINANCE": "BAJFINANCE.NS", "LIC (Insurance)": "LICI.NS",
    "TATA MOTORS": "TATAMOTORS.NS", "MARUTI": "MARUTI.NS", "M&M": "M&M.NS", "MRF (Tyre)": "MRF.NS", "BOSCH (Ancillary)": "BOSCHLTD.NS",
    "ITC": "ITC.NS", "HUL": "HINDUNILVR.NS", "NESTLE": "NESTLEIND.NS", "BRITANNIA": "BRITANNIA.NS", "VARUN BEVERAGES": "VBL.NS",
    "BALRAMPUR CHINI": "BALRAMCHIN.NS", "SHREE RENUKA (Sugar)": "RENUKA.NS", "UPL (Agri)": "UPL.NS", "COROMANDEL": "COROMANDEL.NS",
    "ASIAN PAINTS": "ASIANPAINT.NS", "BERGER PAINTS": "BERGEPAINT.NS", "ULTRATECH CEMENT": "ULTRACEMCO.NS", "AMBUJA CEMENTS": "AMBUJACEM.NS",
    "ASTRAL (Plastic)": "ASTRAL.NS", "SUPREME IND": "SUPREMEIND.NS", "PIDILITE": "PIDILITIND.NS", "SRF (Chemical)": "SRF.NS", "TATA CHEMICALS": "TATACHEM.NS",
    "DLF (Real Estate)": "DLF.NS", "GODREJ PROP": "GODREJPROP.NS", "MACROTECH (LODHA)": "LODHA.NS", "EMBASSY REIT": "EMBASSY.NS",
    "SUN PHARMA": "SUNPHARMA.NS", "CIPLA": "CIPLA.NS", "APOLLO HOSPITALS": "APOLLOHOSP.NS", "DR REDDYS": "DRREDDY.NS",
    "TATA STEEL": "TATASTEEL.NS", "JSW STEEL": "JSWSTEEL.NS", "COAL INDIA (Mining)": "COALINDIA.NS", "HINDALCO": "HINDALCO.NS",
    "BHARTI AIRTEL": "BHARTIARTL.NS", "RELIANCE (Jio/Retail)": "RELIANCE.NS", "ZEEL (Media)": "ZEEL.NS", "PVR INOX": "PVRINOX.NS",
    "INDIGO (Aviation)": "INDIGO.NS", "CONCOR (Logistics)": "CONCOR.NS", "DELHIVERY": "DELHIVERY.NS", "COCHIN SHIPYARD": "COCHINSHIP.NS",
    "HAVELLS": "HAVELLS.NS", "POLYCAB": "POLYCAB.NS", "DIXON TECH (Electronics)": "DIXON.NS",
    "TITAN (Jewellery)": "TITAN.NS", "TRENT (Apparel)": "TRENT.NS", "BATA INDIA (Footwear)": "BATAINDIA.NS", "D-MART (Retail)": "DMART.NS",
    "ZOMATO": "ZOMATO.NS", "PAYTM": "PAYTM.NS", "NYKAA": "NYKAA.NS", "PB FINTECH (PolicyBazaar)": "POLICYBZR.NS"
}

TRADE_FILE = f"mega_trades_{date.today()}.csv"

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

if app_mode == "🔍 Mega Market Scanner":
    st.title("🔥 All-India Mega Market Scanner")
    st.write(f"**Scanning {len(mega_stock_list)} Top Stocks across 50+ Sectors for {timeframe_mode}...**")
    
    scan_period = "5d" if timeframe_mode == "Intraday (15 Min)" else "60d"
    scan_interval = "15m" if timeframe_mode == "Intraday (15 Min)" else "1d"
    hold_time_text = "Same Day (Intraday)" if timeframe_mode == "Intraday (15 Min)" else "3 to 15 Days (Swing)"
    
    progress_bar = st.progress(0)
    
    with st.spinner("Finding the best God-Mode setups in ALL sectors..."):
        results = []
        items = list(mega_stock_list.items())
        total_items = len(items)
        
        for i, (name, ticker_symbol) in enumerate(items):
            try:
                data = yf.Ticker(ticker_symbol).history(period=scan_period, interval=scan_interval)
                if not data.empty:
                    curr = float(data['Close'].iloc[-1])
                    sma_20 = data['Close'].rolling(window=20).mean().iloc[-1]
                    std_20 = data['Close'].rolling(window=20).std().iloc[-1]
                    upper_band = sma_20 + (std_20 * 2)
                    lower_band = sma_20 - (std_20 * 2)
                    
                    bullish = (curr > upper_band)
                    bearish = (curr < lower_band)
                    
                    atr = (data['High'].iloc[-1] - data['Low'].iloc[-1]) * 1.5
                    
                    if "NIFTY" in name or "SENSEX" in name:
                        tgt_pts, sl_pts = 100, 50
                    else:
                        tgt_multiplier = 4.0 if timeframe_mode == "Intraday (15 Min)" else 8.0
                        sl_multiplier = 2.0 if timeframe_mode == "Intraday (15 Min)" else 4.0
                        tgt_pts, sl_pts = atr * tgt_multiplier, atr * sl_multiplier
                    
                    if bullish:
                        is_new = save_trade(name, ticker_symbol, "🟢 BUY", curr, curr + tgt_pts, curr - sl_pts, timeframe_mode)
                        results.append({"Sector/Stock": name, "Action": "🟢 BUY", "Entry": f"₹{curr:.2f}", "Target": f"₹{curr + tgt_pts:.2f}", "SL": f"₹{curr - sl_pts:.2f}", "Hold": hold_time_text})
                        if is_new:
                            send_telegram_alert(f"🚀 {timeframe_mode} BUY: {name}\nEntry: ₹{curr:.2f}\nTarget: ₹{curr + tgt_pts:.2f}\nSL: ₹{curr - sl_pts:.2f}\n⏳ Hold Time: {hold_time_text}")
                    elif bearish:
                        is_new = save_trade(name, ticker_symbol, "🔴 SELL", curr, curr - tgt_pts, curr + sl_pts, timeframe_mode)
                        results.append({"Sector/Stock": name, "Action": "🔴 SELL", "Entry": f"₹{curr:.2f}", "Target": f"₹{curr - tgt_pts:.2f}", "SL": f"₹{curr + sl_pts:.2f}", "Hold": hold_time_text})
                        if is_new:
                            send_telegram_alert(f"📉 {timeframe_mode} SELL: {name}\nEntry: ₹{curr:.2f}\nTarget: ₹{curr - tgt_pts:.2f}\nSL: ₹{curr + sl_pts:.2f}\n⏳ Hold Time: {hold_time_text}")
            except: pass
            
            progress_bar.progress((i + 1) / total_items)
            
        if results:
            st.success(f"🔥 {len(results)} Perfect Setups Found in All Sectors!")
            st.dataframe(pd.DataFrame(results), use_container_width=True)
        else:
            st.warning("⚖️ Scanning complete. Koi perfect setup nahi mila. AI agle refresh ka wait kar raha hai.")

elif app_mode == "📓 Tracker (Scoreboard & TSL)":
    st.title("🎯 All-India Tracker (Zero-Risk Mode)")
    if os.path.exists(TRADE_FILE):
        df = pd.read_csv(TRADE_FILE)
        st.dataframe(df.drop(columns=['Symbol']), use_container_width=True)
    else:
        st.info("📉 No active trades.")
