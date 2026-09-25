import streamlit as st
import pandas as pd
import yfinance as yf
import warnings
from streamlit_autorefresh import st_autorefresh

warnings.filterwarnings("ignore")
st.set_page_config(page_title="Mega Trading Terminal (God Mode)", layout="wide", page_icon="👑")

st_autorefresh(interval=60000, limit=200, key="fando_refresh")

st.sidebar.title("⚡ Mega Terminal")
st.sidebar.info("God-Mode: VWAP + S&R + ATR Targets")

category = st.sidebar.radio("📁 Kya Dekhna Hai?", ["📊 Main Indices", "🏢 Sub-Sectors", "📈 Top Stocks", "🔍 Auto-Scanner"])

market_data = {
    "📊 Main Indices": {"NIFTY 50": "^NSEI", "BANK NIFTY": "^NSEBANK", "SENSEX": "^BSESN", "INDIA VIX": "^INDIAVIX"},
    "🏢 Sub-Sectors": {"NIFTY IT": "^CNXIT", "NIFTY AUTO": "^CNXAUTO", "NIFTY PHARMA": "^CNXPHARMA", "NIFTY METAL": "^CNXMETAL", "NIFTY FMCG": "^CNXFMCG"},
    "📈 Top Stocks": {"RELIANCE": "RELIANCE.NS", "HDFC BANK": "HDFCBANK.NS", "TCS": "TCS.NS", "SBI": "SBIN.NS", "INFOSYS": "INFY.NS"}
}

def calculate_advanced_indicators(data):
    # EMAs
    data['EMA_9'] = data['Close'].ewm(span=9, adjust=False).mean()
    data['EMA_21'] = data['Close'].ewm(span=21, adjust=False).mean()
    data['EMA_200'] = data['Close'].ewm(span=200, adjust=False).mean()
    
    # RSI & MACD
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    data['RSI'] = 100 - (100 / (1 + rs))
    
    exp1 = data['Close'].ewm(span=12, adjust=False).mean()
    exp2 = data['Close'].ewm(span=26, adjust=False).mean()
    data['MACD'] = exp1 - exp2
    data['Signal_Line'] = data['MACD'].ewm(span=9, adjust=False).mean()
    
    # Dynamic ATR
    data['H-L'] = data['High'] - data['Low']
    data['H-PC'] = abs(data['High'] - data['Close'].shift(1))
    data['L-PC'] = abs(data['Low'] - data['Close'].shift(1))
    data['TR'] = data[['H-L', 'H-PC', 'L-PC']].max(axis=1)
    data['ATR'] = data['TR'].rolling(window=14).mean()
    
    # Intraday VWAP
    data['Date'] = data.index.date
    data['Typical_Price'] = (data['High'] + data['Low'] + data['Close']) / 3
    data['VWAP'] = data.groupby('Date').apply(lambda x: (x['Volume'] * x['Typical_Price']).cumsum() / x['Volume'].cumsum()).reset_index(level=0, drop=True)
    
    # Auto Support & Resistance (Recent 20-candle swing highs/lows)
    data['Support'] = data['Low'].rolling(window=20).min()
    data['Resistance'] = data['High'].rolling(window=20).max()
    
    return data

if category == "🔍 Auto-Scanner":
    st.title("👑 God-Mode Scanner (VWAP + Triple Confirm)")
    st.write("Is mode mein bot **VWAP (Volume)** ko check karega aur aapko stock ka **Support & Resistance** bhi batayega.")
    
    trade_type = st.radio("⏳ Trading Style Select Karein:", ["🚀 Intraday (Aaj hi Buy/Sell)", "📆 Swing / Positional (1-2 Hafte Hold)"])
    
    scan_list = {
        "RELIANCE": "RELIANCE.NS", "HDFC BANK": "HDFCBANK.NS", "ICICI BANK": "ICICIBANK.NS", 
        "INFOSYS": "INFY.NS", "TCS": "TCS.NS", "SBI": "SBIN.NS", "ITC": "ITC.NS", 
        "BHARTI AIRTEL": "BHARTIARTL.NS", "L&T": "LT.NS", "BAJAJ FINANCE": "BAJFINANCE.NS",
        "AXIS BANK": "AXISBANK.NS", "KOTAK BANK": "KOTAKBANK.NS", "TATA MOTORS": "TATAMOTORS.NS", 
        "SUN PHARMA": "SUNPHARMA.NS", "MARUTI": "MARUTI.NS", "M&M": "M&M.NS"
    }
    
    if st.button("🚀 Run God-Mode Scan"):
        with st.spinner("Analyzing VWAP, Volumes, and Pivot Points..."):
            results = []
            for name, ticker_symbol in scan_list.items():
                try:
                    ticker = yf.Ticker(ticker_symbol)
                    
                    if "Intraday" in trade_type:
                        data = ticker.history(period="5d", interval="5m")
                    else:
                        data = ticker.history(period="1y", interval="1d")
                        
                    if not data.empty:
                        data = calculate_advanced_indicators(data)
                        
                        curr = float(data['Close'].iloc[-1])
                        e9, e21 = float(data['EMA_9'].iloc[-1]), float(data['EMA_21'].iloc[-1])
                        rsi, macd, macd_sig = float(data['RSI'].iloc[-1]), float(data['MACD'].iloc[-1]), float(data['Signal_Line'].iloc[-1])
                        vwap = float(data['VWAP'].iloc[-1]) if not pd.isna(data['VWAP'].iloc[-1]) else curr
                        sup, res = float(data['Support'].iloc[-2]), float(data['Resistance'].iloc[-2]) # taking previous candle to avoid current fluctuation
                        atr = float(data['ATR'].iloc[-1])
                        
                        # VWAP Condition Added (Price must be above VWAP for Buy, below for Sell)
                        bullish_condition = (e9 > e21) and (rsi > 55) and (macd > macd_sig) and (curr > vwap)
                        bearish_condition = (e9 < e21) and (rsi < 45) and (macd < macd_sig) and (curr < vwap)
                        
                        sl_val = atr * (1.0 if "Intraday" in trade_type else 1.5)
                        tgt_val = atr * (2.0 if "Intraday" in trade_type else 3.0)
                        
                        if bullish_condition:
                            results.append({"Stock": name, "Action": "🟢 BUY (Above VWAP)", "Entry": f"₹{curr:.2f}", "Target": f"₹{curr + tgt_val:.2f}", "Stop-Loss": f"₹{curr - sl_val:.2f}", "Resistance (R1)": f"₹{res:.2f}", "Support (S1)": f"₹{sup:.2f}"})
                        elif bearish_condition:
                            results.append({"Stock": name, "Action": "🔴 SELL (Below VWAP)", "Entry": f"₹{curr:.2f}", "Target": f"₹{curr - tgt_val:.2f}", "Stop-Loss": f"₹{curr + sl_val:.2f}", "Resistance (R1)": f"₹{res:.2f}", "Support (S1)": f"₹{sup:.2f}"})
                except:
                    continue
            
            if results:
                df = pd.DataFrame(results)
                st.success(f"👑 God-Mode Active! VWAP filtered {len(results)} strongest setups:")
                st.dataframe(df, use_container_width=True)
            else:
                st.warning("⚖️ VWAP filter ne sabko reject kar diya. Operators abhi shaant hain, koi strong trade nahi hai!")

else:
    st.title(f"🚀 {category} AI Signals")
    st.write("Select from sidebar to run the God-Mode Auto Scanner.")
