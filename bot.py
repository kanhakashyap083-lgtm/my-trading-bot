import streamlit as st
import pandas as pd
import yfinance as yf
import requests
import warnings
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

# --- 🚀 CONNECTION TEST (App khulte hi Telegram par test message aayega) ---
if "india_telegram_tested" not in st.session_state:
    send_telegram_alert("✅ System Test: Indian Market (Nifty) God-Mode AI is Online & Ready for Monday! 🚀")
    st.session_state["india_telegram_tested"] = True

st.sidebar.title("⚡ Indian Market AI")
stock_list = {"NIFTY 50": "^NSEI", "BANK NIFTY": "^NSEBANK", "RELIANCE": "RELIANCE.NS", "HDFC BANK": "HDFCBANK.NS"}

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
                    results.append({"Index/Stock": name, "Action": "🟢 BUY (CE)", "Entry": f"₹{curr:.2f}", "Target": f"₹{curr + tgt_pts:.2f}", "SL": f"₹{curr - sl_pts:.2f}"})
                    send_telegram_alert(f"🚀 INDIAN MARKET BUY: {name}\nEntry: ₹{curr:.2f}\nTarget: ₹{curr + tgt_pts:.2f}\nSL: ₹{curr - sl_pts:.2f}")
                elif bearish:
                    results.append({"Index/Stock": name, "Action": "🔴 SELL (PE)", "Entry": f"₹{curr:.2f}", "Target": f"₹{curr - tgt_pts:.2f}", "SL": f"₹{curr + sl_pts:.2f}"})
                    send_telegram_alert(f"📉 INDIAN MARKET SELL: {name}\nEntry: ₹{curr:.2f}\nTarget: ₹{curr - tgt_pts:.2f}\nSL: ₹{curr + sl_pts:.2f}")
        except: continue
    
    if results:
        st.success(f"🔥 {len(results)} God-Mode Trades Found!")
        st.dataframe(pd.DataFrame(results), use_container_width=True)
    else:
        st.warning("⚖️ Market Closed (ya Side-ways) hai. AI wait kar raha hai...")
