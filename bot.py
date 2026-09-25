import streamlit as st
import pandas as pd
import yfinance as yf
import warnings
import os
from datetime import date
from streamlit_autorefresh import st_autorefresh

warnings.filterwarnings("ignore")
st.set_page_config(page_title="Mega Trading Terminal (God Mode)", layout="wide", page_icon="👑")

st_autorefresh(interval=60000, limit=200, key="fando_refresh")

st.sidebar.title("⚡ Mega Terminal")
st.sidebar.info("God-Mode: Auto-Trade Tracker")

category = st.sidebar.radio("📁 Kya Dekhna Hai?", ["📊 Main Indices", "🏢 Sub-Sectors", "📈 Top Stocks", "🔍 Auto-Scanner", "📓 Auto-Trade Tracker"])

market_data = {
    "📊 Main Indices": {"NIFTY 50": "^NSEI", "BANK NIFTY": "^NSEBANK", "SENSEX": "^BSESN", "INDIA VIX": "^INDIAVIX"},
    "🏢 Sub-Sectors": {"NIFTY IT": "^CNXIT", "NIFTY AUTO": "^CNXAUTO", "NIFTY PHARMA": "^CNXPHARMA", "NIFTY METAL": "^CNXMETAL", "NIFTY FMCG": "^CNXFMCG"},
    "📈 Top Stocks": {"RELIANCE": "RELIANCE.NS", "HDFC BANK": "HDFCBANK.NS", "TCS": "TCS.NS", "SBI": "SBIN.NS", "INFOSYS": "INFY.NS"}
}

scan_list = {
    "RELIANCE": "RELIANCE.NS", "HDFC BANK": "HDFCBANK.NS", "ICICI BANK": "ICICIBANK.NS", 
    "INFOSYS": "INFY.NS", "TCS": "TCS.NS", "SBI": "SBIN.NS", "ITC": "ITC.NS", 
    "BHARTI AIRTEL": "BHARTIARTL.NS", "L&T": "LT.NS", "BAJAJ FINANCE": "BAJFINANCE.NS",
    "AXIS BANK": "AXISBANK.NS", "KOTAK BANK": "KOTAKBANK.NS", "TATA MOTORS": "TATAMOTORS.NS", 
    "SUN PHARMA": "SUNPHARMA.NS", "MARUTI": "MARUTI.NS", "M&M": "M&M.NS"
}

TRADE_FILE = f"trades_{date.today()}.csv"

def save_trade(stock, symbol, action, entry, target, sl):
    if os.path.exists(TRADE_FILE):
        df = pd.read_csv(TRADE_FILE)
        if stock in df['Stock'].values:
            return  # Aaj ke liye already track ho raha hai
    else:
        df = pd.DataFrame(columns=["Stock", "Symbol", "Action", "Entry", "Target", "SL", "Status"])
    
    new_trade = pd.DataFrame([{"Stock": stock, "Symbol": symbol, "Action": action, "Entry": entry, "Target": target, "SL": sl, "Status": "⏳ Active"}])
    df = pd.concat([df, new_trade], ignore_index=True)
    df.to_csv(TRADE_FILE, index=False)

def calculate_advanced_indicators(data):
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

if category == "🔍 Auto-Scanner":
    st.title("👑 God-Mode Scanner (Auto-Save)")
    st.write("Yahan se mile hue saare trades apne aap **'Auto-Trade Tracker'** mein save ho jayenge.")
    
    trade_type = st.radio("⏳ Trading Style Select Karein:", ["🚀 Intraday (Aaj hi Buy/Sell)"])
    
    if st.button("🚀 Run God-Mode Scan"):
        with st.spinner("Analyzing VWAP & Saving Trades..."):
            results = []
            for name, ticker_symbol in scan_list.items():
                try:
                    ticker = yf.Ticker(ticker_symbol)
                    data = ticker.history(period="5d", interval="5m")
                        
                    if not data.empty:
                        data = calculate_advanced_indicators(data)
                        curr = float(data['Close'].iloc[-1])
                        e9, e21 = float(data['EMA_9'].iloc[-1]), float(data['EMA_21'].iloc[-1])
                        rsi, macd, macd_sig = float(data['RSI'].iloc[-1]), float(data['MACD'].iloc[-1]), float(data['Signal_Line'].iloc[-1])
                        vwap = float(data['VWAP'].iloc[-1]) if not pd.isna(data['VWAP'].iloc[-1]) else curr
                        atr = float(data['ATR'].iloc[-1])
                        
                        bullish = (e9 > e21) and (rsi > 55) and (macd > macd_sig) and (curr > vwap)
                        bearish = (e9 < e21) and (rsi < 45) and (macd < macd_sig) and (curr < vwap)
                        
                        sl_val, tgt_val = atr * 1.0, atr * 2.0
                        
                        if bullish:
                            save_trade(name, ticker_symbol, "BUY", curr, curr + tgt_val, curr - sl_val)
                            results.append({"Stock": name, "Action": "🟢 BUY", "Entry": f"₹{curr:.2f}", "Target": f"₹{curr + tgt_val:.2f}", "SL": f"₹{curr - sl_val:.2f}"})
                        elif bearish:
                            save_trade(name, ticker_symbol, "SELL", curr, curr - tgt_val, curr + sl_val)
                            results.append({"Stock": name, "Action": "🔴 SELL", "Entry": f"₹{curr:.2f}", "Target": f"₹{curr - tgt_val:.2f}", "SL": f"₹{curr + sl_val:.2f}"})
                except:
                    continue
            
            if results:
                st.success(f"👑 {len(results)} Setups mile aur Tracker mein save ho gaye!")
                st.dataframe(pd.DataFrame(results), use_container_width=True)
            else:
                st.warning("⚖️ VWAP filter ne sabko reject kar diya. Koi fresh trade nahi hai.")

elif category == "📓 Auto-Trade Tracker":
    st.title("🎯 Live Paper Trading Scoreboard")
    
    if os.path.exists(TRADE_FILE):
        df = pd.read_csv(TRADE_FILE)
        
        # Check Live Prices
        for index, row in df.iterrows():
            if row['Status'] == "⏳ Active":
                try:
                    curr_price = float(yf.Ticker(row['Symbol']).history(period="1d", interval="1m")['Close'].iloc[-1])
                    
                    if row['Action'] == "BUY":
                        if curr_price >= row['Target']: df.at[index, 'Status'] = "🏆 Target Hit"
                        elif curr_price <= row['SL']: df.at[index, 'Status'] = "💔 SL Hit"
                    
                    elif row['Action'] == "SELL":
                        if curr_price <= row['Target']: df.at[index, 'Status'] = "🏆 Target Hit"
                        elif curr_price >= row['SL']: df.at[index, 'Status'] = "💔 SL Hit"
                except:
                    continue
        
        df.to_csv(TRADE_FILE, index=False)
        
        # Calculate Score
        wins = len(df[df['Status'] == "🏆 Target Hit"])
        losses = len(df[df['Status'] == "💔 SL Hit"])
        active = len(df[df['Status'] == "⏳ Active"])
        
        st.markdown("### 📊 Aaj Ka P&L (Scoreboard)")
        col1, col2, col3 = st.columns(3)
        col1.success(f"🏆 Target Hits (Win): {wins}")
        col2.error(f"💔 SL Hits (Loss): {losses}")
        col3.warning(f"⏳ Chal Rahe Hain: {active}")
        
        st.markdown("---")
        st.write("**📝 Aaj Ke Saare Trades:**")
        
        # Drop Symbol column for clean display
        display_df = df.drop(columns=['Symbol'])
        st.dataframe(display_df, use_container_width=True)
        
    else:
        st.info("🤷‍♂️ Aaj abhi tak koi trade save nahi hua hai. Pehle 'Auto-Scanner' chalayein!")

else:
    st.title(f"🚀 {category} AI Signals")
    # Baaki menu items wahi rahenge
    selected_asset = st.sidebar.selectbox("Kiska Signal Chahiye?", list(market_data[category].keys()))
    ticker_symbol = market_data[category][selected_asset]
    try:
        data = calculate_advanced_indicators(yf.Ticker(ticker_symbol).history(period="1mo", interval="5m"))
        curr = data['Close'].iloc[-1]
        st.subheader(f"📊 {selected_asset}: ₹{curr:.2f} (Live)")
    except:
        st.write("Data loading...")
