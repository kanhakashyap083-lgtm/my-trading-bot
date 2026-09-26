import streamlit as st
import pandas as pd
import yfinance as yf
import requests
import warnings
import os
from datetime import date
from streamlit_autorefresh import st_autorefresh

warnings.filterwarnings("ignore")
st.set_page_config(page_title="Nifty God-Mode AI", layout="wide", page_icon="📈")
st_autorefresh(interval=60000, limit=1000, key="india_refresh")

# --- TELEGRAM SETUP ---
TELEGRAM_TOKEN = "8657774899:AAGKqx2_TgaoYAbUljSAXt5l9BzL_cnyCPE"
TELEGRAM_CHAT_ID = "8900320752"

def send_telegram_alert(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
        requests.post(url, json=payload)
    except: pass

if "india_telegram_tested" not in st.session_state:
    send_telegram_alert("✅ System Test: Indian Market (Nifty) God-Mode AI is Online! 🚀")
    st.session_state["india_telegram_tested"] = True

st.sidebar.title("⚡ Indian Market AI")
app_mode = st.sidebar.radio("📁 Menu:", ["🔍 Market Auto-Scanner", "📓 Tracker (Scoreboard & TSL)"])

stock_list = {"NIFTY 50": "^NSEI", "BANK NIFTY": "^NSEBANK", "RELIANCE": "RELIANCE.NS", "HDFC BANK": "HDFCBANK.NS"}
TRADE_FILE = f"india_trades_{date.today()}.csv"

def save_trade(name, symbol, action, entry, target, sl):
    if os.path.exists(TRADE_FILE):
        df = pd.read_csv(TRADE_FILE)
        if not df[(df['Stock'] == name) & (df['Status'].str.contains('Active|Trailing'))].empty: return False
    else:
        df = pd.DataFrame(columns=["Stock", "Symbol", "Action", "Entry", "Target", "SL", "Status"])
    
    new_trade = pd.DataFrame([{"Stock": name, "Symbol": symbol, "Action": action, "Entry": round(entry, 2), "Target": round(target, 2), "SL": round(sl, 2), "Status": "⏳ Active"}])
    df = pd.concat([df, new_trade], ignore_index=True)
    df.to_csv(TRADE_FILE, index=False)
    return True

if app_mode == "🔍 Market Auto-Scanner":
    st.title("📈 Nifty & BankNifty Auto-Scanner")
    
    with st.spinner("Market Trend & Smart Money Scanning..."):
        results = []
        for name, ticker_symbol in stock_list.items():
            try:
                data = yf.Ticker(ticker_symbol).history(period="5d", interval="15m")
                if not data.empty:
                    curr = float(data['Close'].iloc[-1])
                    sma_20 = data['Close'].rolling(window=20).mean().iloc[-1]
                    std_20 = data['Close'].rolling(window=20).std().iloc[-1]
                    upper_band = sma_20 + (std_20 * 2)
                    lower_band = sma_20 - (std_20 * 2)
                    
                    bullish = (curr > upper_band)
                    bearish = (curr < lower_band)
                    
                    tgt_pts = 100 if "NIFTY" in name else 20
                    sl_pts = 50 if "NIFTY" in name else 10
                    
                    if bullish:
                        is_new = save_trade(name, ticker_symbol, "🟢 BUY (CE)", curr, curr + tgt_pts, curr - sl_pts)
                        results.append({"Stock": name, "Action": "🟢 BUY (CE)", "Entry": f"₹{curr:.2f}", "Target": f"₹{curr + tgt_pts:.2f}", "SL": f"₹{curr - sl_pts:.2f}"})
                        if is_new:
                            send_telegram_alert(f"🚀 NEW BUY SIGNAL (CE): {name}\nEntry: ₹{curr:.2f}\nTarget: ₹{curr + tgt_pts:.2f}\nSL: ₹{curr - sl_pts:.2f}")
                    elif bearish:
                        is_new = save_trade(name, ticker_symbol, "🔴 SELL (PE)", curr, curr - tgt_pts, curr + sl_pts)
                        results.append({"Stock": name, "Action": "🔴 SELL (PE)", "Entry": f"₹{curr:.2f}", "Target": f"₹{curr - tgt_pts:.2f}", "SL": f"₹{curr + sl_pts:.2f}"})
                        if is_new:
                            send_telegram_alert(f"📉 NEW SELL SIGNAL (PE): {name}\nEntry: ₹{curr:.2f}\nTarget: ₹{curr - tgt_pts:.2f}\nSL: ₹{curr + sl_pts:.2f}")
            except: continue
        
        if results:
            st.success(f"🔥 {len(results)} God-Mode Trades Found!")
            st.dataframe(pd.DataFrame(results), use_container_width=True)
        else:
            st.warning("⚖️ Market Closed ya Side-ways hai. AI wait kar raha hai...")

elif app_mode == "📓 Tracker (Scoreboard & TSL)":
    st.title("🎯 Indian Market Scoreboard (0-Risk)")
    
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
                            send_telegram_alert(f"🏆 TARGET HIT: {row['Stock']} (CE) ne profit book kar liya at ₹{curr_price:.2f}!")
                        elif curr_price <= float(row['SL']): 
                            df.at[index, 'Status'] = "💔 SL Hit"
                        elif curr_price >= halfway and float(row['SL']) < entry:
                            df.at[index, 'SL'] = entry
                            df.at[index, 'Status'] = "🚀 Trailing (0 Risk)"
                            if old_status != "🚀 Trailing (0 Risk)":
                                send_telegram_alert(f"🛡️ ZERO RISK MODE: {row['Stock']} (CE) SL ab Entry price par aa gaya hai!")
                                
                    elif "SELL" in row['Action']:
                        halfway = entry - (entry - target) * 0.5
                        if curr_price <= target: 
                            df.at[index, 'Status'] = "🏆 Target Hit"
                            send_telegram_alert(f"🏆 TARGET HIT: {row['Stock']} (PE) ne profit book kar liya at ₹{curr_price:.2f}!")
                        elif curr_price >= float(row['SL']): 
                            df.at[index, 'Status'] = "💔 SL Hit"
                        elif curr_price <= halfway and float(row['SL']) > entry:
                            df.at[index, 'SL'] = entry
                            df.at[index, 'Status'] = "🚀 Trailing (0 Risk)"
                            if old_status != "🚀 Trailing (0 Risk)":
                                send_telegram_alert(f"🛡️ ZERO RISK MODE: {row['Stock']} (PE) SL ab Entry price par aa gaya hai!")
                except: continue
        df.to_csv(TRADE_FILE, index=False)
        
        col1, col2, col3 = st.columns(3)
        col1.success(f"🏆 Win: {len(df[df['Status'] == '🏆 Target Hit'])}")
        col2.error(f"💔 Loss: {len(df[df['Status'] == '💔 SL Hit'])}")
        col3.warning(f"🚀 Running: {len(df[df['Status'].str.contains('Active|Trailing')])}")
        
        display_df = df.drop(columns=['Symbol'])
        st.dataframe(display_df, use_container_width=True)
    else:
        st.info("📉 Abhi tak koi naya trade nahi mila hai.")
