import streamlit as st
import pandas as pd
import yfinance as yf
import warnings
import os
import requests
from datetime import date
from streamlit_autorefresh import st_autorefresh

warnings.filterwarnings("ignore")
st.set_page_config(page_title="Crypto God-Mode AI Ultra", layout="wide", page_icon="🪙")
st_autorefresh(interval=60000, limit=1000, key="crypto_refresh")

# --- TELEGRAM SETUP ---
TELEGRAM_TOKEN = "8657774899:AAGKqx2_TgaoYAbUljSAXt5l9BzL_cnyCPE"
TELEGRAM_CHAT_ID = "8900320752"

def send_telegram_alert(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
        requests.post(url, json=payload)
    except:
        pass

# --- 🚀 CONNECTION TEST (Sirf ek baar bajega jab app khulegi) ---
if "telegram_tested" not in st.session_state:
    send_telegram_alert("✅ System Test: Crypto God-Mode AI is Online and Scanning! 🚀")
    st.session_state["telegram_tested"] = True

st.sidebar.title("⚡ Crypto Terminal Ultra")
app_mode = st.sidebar.radio("📁 Menu:", ["🔍 Crypto Auto-Scanner", "📓 Tracker (TSL Zero-Risk)"])

crypto_list = {"BITCOIN": "BTC-USD", "ETHEREUM": "ETH-USD", "SOLANA": "SOL-USD", "BINANCE COIN": "BNB-USD", "RIPPLE": "XRP-USD", "DOGECOIN": "DOGE-USD"}
TRADE_FILE = f"crypto_trades_{date.today()}.csv"

def save_trade(coin, symbol, action, entry, target, sl):
    if os.path.exists(TRADE_FILE):
        df = pd.read_csv(TRADE_FILE)
        if not df[(df['Coin'] == coin) & (df['Status'].str.contains('Active|Trailing'))].empty: return False
    else:
        df = pd.DataFrame(columns=["Coin", "Symbol", "Action", "Entry", "Target", "SL", "Status"])
    
    new_trade = pd.DataFrame([{"Coin": coin, "Symbol": symbol, "Action": action, "Entry": round(entry, 4), "Target": round(target, 4), "SL": round(sl, 4), "Status": "⏳ Active"}])
    df = pd.concat([df, new_trade], ignore_index=True)
    df.to_csv(TRADE_FILE, index=False)
    return True 

if app_mode == "🔍 Crypto Auto-Scanner":
    st.title("🪙 Crypto AI Scanner (Multi-Timeframe & Telegram)")
    
    with st.spinner("Scanning Big Trends & Smart Money..."):
        results = []
        for name, ticker_symbol in crypto_list.items():
            try:
                macro_data = yf.Ticker(ticker_symbol).history(period="10d", interval="1h")
                macro_trend_up = macro_data['Close'].iloc[-1] > macro_data['Close'].ewm(span=50).mean().iloc[-1]
                
                data = yf.Ticker(ticker_symbol).history(period="5d", interval="15m")
                if not data.empty:
                    curr = float(data['Close'].iloc[-1])
                    sma_20 = data['Close'].rolling(window=20).mean().iloc[-1]
                    std_20 = data['Close'].rolling(window=20).std().iloc[-1]
                    upper_band = sma_20 + (std_20 * 2)
                    lower_band = sma_20 - (std_20 * 2)
                    
                    bullish = macro_trend_up and (curr > upper_band)
                    bearish = not macro_trend_up and (curr < lower_band)
                    
                    atr = (data['High'].iloc[-1] - data['Low'].iloc[-1]) * 1.5
                    sl_val, tgt_val = atr * 3.0, atr * 6.0 
                    
                    if bullish:
                        is_new = save_trade(name, ticker_symbol, "🟢 BUY", curr, curr + tgt_val, curr - sl_val)
                        results.append({"Coin": name, "Action": "🟢 BUY", "Entry": f"${curr:.4f}", "Target": f"${curr + tgt_val:.4f}", "SL": f"${curr - sl_val:.4f}"})
                        if is_new:
                            send_telegram_alert(f"🚀 NEW BUY SIGNAL: {name}\nEntry: ${curr:.2f}\nTarget: ${curr + tgt_val:.2f}\nSL: ${curr - sl_val:.2f}")
                    elif bearish:
                        is_new = save_trade(name, ticker_symbol, "🔴 SELL", curr, curr - tgt_val, curr + sl_val)
                        results.append({"Coin": name, "Action": "🔴 SELL", "Entry": f"${curr:.4f}", "Target": f"${curr - tgt_val:.4f}", "SL": f"${curr + sl_val:.4f}"})
                        if is_new:
                            send_telegram_alert(f"📉 NEW SELL SIGNAL: {name}\nEntry: ${curr:.2f}\nTarget: ${curr - tgt_val:.2f}\nSL: ${curr + sl_val:.2f}")
            except: continue
        
        if results:
            st.success(f"🔥 {len(results)} God-Mode Trades Found!")
            st.dataframe(pd.DataFrame(results), use_container_width=True)
        else:
            st.warning("⚖️ High Accuracy Mode: Waiting for strong Whale volume...")

elif app_mode == "📓 Tracker (TSL Zero-Risk)":
    st.title("🎯 Crypto Trailing Scoreboard")
    
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
                            send_telegram_alert(f"🏆 TARGET HIT: {row['Coin']} (BUY) ne profit book kar liya at ${curr_price:.2f}!")
                        elif curr_price <= float(row['SL']): 
                            df.at[index, 'Status'] = "💔 SL Hit"
                        elif curr_price >= halfway and float(row['SL']) < entry:
                            df.at[index, 'SL'] = entry
                            df.at[index, 'Status'] = "🚀 Trailing (0 Risk)"
                            if old_status != "🚀 Trailing (0 Risk)":
                                send_telegram_alert(f"🛡️ ZERO RISK MODE: {row['Coin']} Stop-loss ab Entry price par set ho gaya hai!")
                                
                    elif "SELL" in row['Action']:
                        halfway = entry - (entry - target) * 0.5
                        if curr_price <= target: 
                            df.at[index, 'Status'] = "🏆 Target Hit"
                            send_telegram_alert(f"🏆 TARGET HIT: {row['Coin']} (SELL) ne profit book kar liya at ${curr_price:.2f}!")
                        elif curr_price >= float(row['SL']): 
                            df.at[index, 'Status'] = "💔 SL Hit"
                        elif curr_price <= halfway and float(row['SL']) > entry:
                            df.at[index, 'SL'] = entry
                            df.at[index, 'Status'] = "🚀 Trailing (0 Risk)"
                            if old_status != "🚀 Trailing (0 Risk)":
                                send_telegram_alert(f"🛡️ ZERO RISK MODE: {row['Coin']} Stop-loss ab Entry price par set ho gaya hai!")
                except: continue
        df.to_csv(TRADE_FILE, index=False)
        
        col1, col2, col3 = st.columns(3)
        col1.success(f"🏆 Win: {len(df[df['Status'] == '🏆 Target Hit'])}")
        col2.error(f"💔 Loss: {len(df[df['Status'] == '💔 SL Hit'])}")
        col3.warning(f"🚀 Running: {len(df[df['Status'].str.contains('Active|Trailing')])}")
        
        display_df = df.drop(columns=['Symbol'])
        st.dataframe(display_df, use_container_width=True)
