import streamlit as st
import pandas as pd
import yfinance as yf
import warnings
import os
from datetime import date
from streamlit_autorefresh import st_autorefresh

warnings.filterwarnings("ignore")
st.set_page_config(page_title="Crypto God-Mode AI", layout="wide", page_icon="🪙")

st_autorefresh(interval=60000, limit=1000, key="crypto_refresh")

st.sidebar.title("⚡ Crypto Terminal")
app_mode = st.sidebar.radio("📁 Menu:", ["🔍 Crypto Auto-Scanner", "📓 Crypto Tracker (Live)"])

crypto_list = {"BITCOIN": "BTC-USD", "ETHEREUM": "ETH-USD", "SOLANA": "SOL-USD", "BINANCE COIN": "BNB-USD", "RIPPLE": "XRP-USD", "DOGECOIN": "DOGE-USD"}
TRADE_FILE = f"crypto_trades_{date.today()}.csv"

def save_trade(coin, symbol, action, entry, target, sl):
    if os.path.exists(TRADE_FILE):
        df = pd.read_csv(TRADE_FILE)
        if not df[(df['Coin'] == coin) & (df['Status'] == '⏳ Active')].empty:
            return 
    else:
        df = pd.DataFrame(columns=["Coin", "Symbol", "Action", "Entry", "Target", "SL", "Status"])
    new_trade = pd.DataFrame([{"Coin": coin, "Symbol": symbol, "Action": action, "Entry": round(entry, 4), "Target": round(target, 4), "SL": round(sl, 4), "Status": "⏳ Active"}])
    df = pd.concat([df, new_trade], ignore_index=True)
    df.to_csv(TRADE_FILE, index=False)

def calculate_crypto_indicators(data):
    data['EMA_9'] = data['Close'].ewm(span=9, adjust=False).mean()
    data['EMA_21'] = data['Close'].ewm(span=21, adjust=False).mean()
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    data['RSI'] = 100 - (100 / (1 + rs))
    exp1 = data['Close'].ewm(span=12, adjust=False).mean()
    exp2 = data['Close'].ewm(span=26, adjust=False).mean()
    data['MACD'] = exp1 - exp2
    data['Signal_Line'] = data['MACD'].ewm(span=9, adjust=False).mean()
    return data

if app_mode == "🔍 Crypto Auto-Scanner":
    st.title("🪙 Crypto AI Scanner (24/7 Fully Auto)")
    
    # Yahan se button hata diya hai, ab ye direct scan karega page khulte hi
    with st.spinner("Auto-Scanning Market..."):
        results = []
        for name, ticker_symbol in crypto_list.items():
            try:
                # Advanced 15-Min Timeframe for Global Scanner
                data = yf.Ticker(ticker_symbol).history(period="5d", interval="15m")
                if not data.empty:
                    data = calculate_crypto_indicators(data)
                    curr = float(data['Close'].iloc[-1])
                    e9, e21 = float(data['EMA_9'].iloc[-1]), float(data['EMA_21'].iloc[-1])
                    rsi, macd, macd_sig = float(data['RSI'].iloc[-1]), float(data['MACD'].iloc[-1]), float(data['Signal_Line'].iloc[-1])
                    
                    bullish = (e9 > e21) and (rsi > 55) and (macd > macd_sig)
                    bearish = (e9 < e21) and (rsi < 45) and (macd < macd_sig)
                    
                    # Safe Targets
                    atr = (data['High'].iloc[-1] - data['Low'].iloc[-1]) * 1.5
                    sl_val, tgt_val = atr * 3.0, atr * 6.0 
                    
                    if bullish:
                        save_trade(name, ticker_symbol, "🟢 BUY", curr, curr + tgt_val, curr - sl_val)
                        results.append({"Coin": name, "Action": "🟢 BUY", "Entry": f"${curr:.4f}", "Target": f"${curr + tgt_val:.4f}", "SL": f"${curr - sl_val:.4f}"})
                    elif bearish:
                        save_trade(name, ticker_symbol, "🔴 SELL", curr, curr - tgt_val, curr + sl_val)
                        results.append({"Coin": name, "Action": "🔴 SELL", "Entry": f"${curr:.4f}", "Target": f"${curr - tgt_val:.4f}", "SL": f"${curr + sl_val:.4f}"})
            except: continue
        
        if results:
            st.success(f"🔥 {len(results)} Solid Trades Found!")
            st.dataframe(pd.DataFrame(results), use_container_width=True)
        else:
            st.warning("⚖️ Market Side-ways hai. Pura auto-scan chal raha hai...")

elif app_mode == "📓 Crypto Tracker (Live)":
    st.title("🎯 Crypto Live Scoreboard")
    
    if os.path.exists(TRADE_FILE):
        df = pd.read_csv(TRADE_FILE)
        for index, row in df.iterrows():
            if row['Status'] == "⏳ Active":
                try:
                    curr_price = float(yf.Ticker(row['Symbol']).history(period="1d", interval="1m")['Close'].iloc[-1])
                    if "BUY" in row['Action']:
                        if curr_price >= row['Target']: df.at[index, 'Status'] = "🏆 Target Hit"
                        elif curr_price <= row['SL']: df.at[index, 'Status'] = "💔 SL Hit"
                    elif "SELL" in row['Action']:
                        if curr_price <= row['Target']: df.at[index, 'Status'] = "🏆 Target Hit"
                        elif curr_price >= row['SL']: df.at[index, 'Status'] = "💔 SL Hit"
                except: continue
        df.to_csv(TRADE_FILE, index=False)
        
        wins = len(df[df['Status'] == "🏆 Target Hit"])
        losses = len(df[df['Status'] == "💔 SL Hit"])
        active = len(df[df['Status'] == "⏳ Active"])
        
        col1, col2, col3 = st.columns(3)
        col1.success(f"🏆 Win: {wins}")
        col2.error(f"💔 Loss: {losses}")
        col3.warning(f"⏳ Active: {active}")
        
        display_df = df.drop(columns=['Symbol'])
        st.dataframe(display_df, use_container_width=True)
