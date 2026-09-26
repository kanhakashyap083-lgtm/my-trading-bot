import streamlit as st
import pandas as pd
import yfinance as yf
import warnings
import os
from datetime import date
from streamlit_autorefresh import st_autorefresh

warnings.filterwarnings("ignore")
st.set_page_config(page_title="Crypto God-Mode AI", layout="wide", page_icon="🪙")

st_autorefresh(interval=60000, limit=200, key="crypto_refresh")

st.sidebar.title("⚡ Crypto Terminal")
st.sidebar.info("24/7 AI Tracker")

app_mode = st.sidebar.radio("📁 Menu:", ["🔍 Crypto Auto-Scanner", "📓 Crypto Tracker (Live)"])

# Top Crypto Coins List
crypto_list = {
    "BITCOIN": "BTC-USD", 
    "ETHEREUM": "ETH-USD", 
    "SOLANA": "SOL-USD", 
    "BINANCE COIN": "BNB-USD", 
    "RIPPLE": "XRP-USD", 
    "DOGECOIN": "DOGE-USD"
}

TRADE_FILE = f"crypto_trades_{date.today()}.csv"

def save_trade(coin, symbol, action, entry, target, sl):
    if os.path.exists(TRADE_FILE):
        df = pd.read_csv(TRADE_FILE)
        if coin in df['Coin'].values and "⏳ Active" in df['Status'].values:
            return 
    else:
        df = pd.DataFrame(columns=["Coin", "Symbol", "Action", "Entry", "Target", "SL", "Status"])
    
    new_trade = pd.DataFrame([{"Coin": coin, "Symbol": symbol, "Action": action, "Entry": entry, "Target": target, "SL": sl, "Status": "⏳ Active"}])
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
    data['H-L'] = data['High'] - data['Low']
    data['H-PC'] = abs(data['High'] - data['Close'].shift(1))
    data['L-PC'] = abs(data['Low'] - data['Close'].shift(1))
    data['TR'] = data[['H-L', 'H-PC', 'L-PC']].max(axis=1)
    data['ATR'] = data['TR'].rolling(window=14).mean()
    data['Date'] = data.index.date
    data['Typical_Price'] = (data['High'] + data['Low'] + data['Close']) / 3
    data['VWAP'] = data.groupby('Date').apply(lambda x: (x['Volume'] * x['Typical_Price']).cumsum() / x['Volume'].cumsum()).reset_index(level=0, drop=True)
    return data

if app_mode == "🔍 Crypto Auto-Scanner":
    st.title("🪙 Crypto AI Scanner (24/7)")
    st.write("Scan for Live Crypto Breakouts. Trades auto-save in Tracker!")
    
    if st.button("🚀 Run Crypto Scan"):
        with st.spinner("Analyzing Bitcoin & Altcoins..."):
            results = []
            for name, ticker_symbol in crypto_list.items():
                try:
                    ticker = yf.Ticker(ticker_symbol)
                    data = ticker.history(period="5d", interval="15m")
                        
                    if not data.empty:
                        data = calculate_crypto_indicators(data)
                        curr = float(data['Close'].iloc[-1])
                        e9, e21 = float(data['EMA_9'].iloc[-1]), float(data['EMA_21'].iloc[-1])
                        rsi, macd, macd_sig = float(data['RSI'].iloc[-1]), float(data['MACD'].iloc[-1]), float(data['Signal_Line'].iloc[-1])
                        vwap = float(data['VWAP'].iloc[-1]) if not pd.isna(data['VWAP'].iloc[-1]) else curr
                        atr = float(data['ATR'].iloc[-1])
                        
                        bullish = (e9 > e21) and (rsi > 55) and (macd > macd_sig) and (curr > vwap)
                        bearish = (e9 < e21) and (rsi < 45) and (macd < macd_sig) and (curr < vwap)
                        
                        sl_val, tgt_val = atr * 1.5, atr * 3.0
                        
                        if bullish:
                            save_trade(name, ticker_symbol, "🟢 LONG (BUY)", curr, curr + tgt_val, curr - sl_val)
                            results.append({"Coin": name, "Action": "🟢 LONG", "Entry": f"${curr:.2f}", "Target": f"${curr + tgt_val:.2f}", "SL": f"${curr - sl_val:.2f}"})
                        elif bearish:
                            save_trade(name, ticker_symbol, "🔴 SHORT (SELL)", curr, curr - tgt_val, curr + sl_val)
                            results.append({"Coin": name, "Action": "🔴 SHORT", "Entry": f"${curr:.2f}", "Target": f"${curr - tgt_val:.2f}", "SL": f"${curr + sl_val:.2f}"})
                except:
                    continue
            
            if results:
                st.success(f"🔥 {len(results)} Crypto Signals Found!")
                st.dataframe(pd.DataFrame(results), use_container_width=True)
            else:
                st.warning("⚖️ Market Side-ways hai. Koi fresh setup nahi.")

elif app_mode == "📓 Crypto Tracker (Live)":
    st.title("🎯 Crypto Live Scoreboard")
    
    if os.path.exists(TRADE_FILE):
        df = pd.read_csv(TRADE_FILE)
        
        for index, row in df.iterrows():
            if row['Status'] == "⏳ Active":
                try:
                    curr_price = float(yf.Ticker(row['Symbol']).history(period="1d", interval="1m")['Close'].iloc[-1])
                    
                    if "LONG" in row['Action']:
                        if curr_price >= row['Target']: df.at[index, 'Status'] = "🏆 Target Hit"
                        elif curr_price <= row['SL']: df.at[index, 'Status'] = "💔 SL Hit"
                    
                    elif "SHORT" in row['Action']:
                        if curr_price <= row['Target']: df.at[index, 'Status'] = "🏆 Target Hit"
                        elif curr_price >= row['SL']: df.at[index, 'Status'] = "💔 SL Hit"
                except:
                    continue
        
        df.to_csv(TRADE_FILE, index=False)
        
        wins = len(df[df['Status'] == "🏆 Target Hit"])
        losses = len(df[df['Status'] == "💔 SL Hit"])
        active = len(df[df['Status'] == "⏳ Active"])
        
        col1, col2, col3 = st.columns(3)
        col1.success(f"🏆 Win: {wins}")
        col2.error(f"💔 Loss: {losses}")
        col3.warning(f"⏳ Active: {active}")
        
        st.markdown("---")
        display_df = df.drop(columns=['Symbol'])
        st.dataframe(display_df, use_container_width=True)
        
    else:
        st.info("🤷‍♂️ Abhi tak koi Crypto trade nahi hai. Pehle Scanner chalayein!")
