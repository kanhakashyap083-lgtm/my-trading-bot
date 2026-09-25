import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
import warnings

warnings.filterwarnings("ignore")
st.set_page_config(page_title="AI F&O Signal Bot", layout="wide", page_icon="🚀")

st.sidebar.title("⚡ F&O Signal Master")
st.sidebar.info("Trading Mode: Manual (Groww App)")

st.title("🚀 Advanced F&O Trading Dashboard (Groww Edition)")
st.markdown("Yeh bot Market ka trend analyze karke aapko **Trading Signals** dega. Trades aap aaram se apne **Groww App** mein le sakte hain.")

# Market Selector
index_choice = st.sidebar.selectbox("Kiska Signal Chahiye?", ["NIFTY 50", "BANK NIFTY"])

# Ticker mapping for yfinance
ticker_map = {"NIFTY 50": "^NSEI", "BANK NIFTY": "^NSEBANK"}
ticker_symbol = ticker_map[index_choice]

st.subheader(f"📊 Live Market Status: {index_choice}")

try:
    # Live data laane ka code
    data = yf.download(ticker_symbol, period="1d", interval="5m")
    
    if not data.empty:
        # Puraani library error na de isliye .item() use kiya hai
        current_price = float(data['Close'].iloc[-1])
        
        st.metric(label=f"{index_choice} Current Price", value=f"₹{current_price:.2f}")
        st.success("✅ Live Market Data Loaded Successfully!")
        
        st.markdown("---")
        st.header("🎯 AI Trading Signals")
        
        col1, col2 = st.columns(2)
        with col1:
            st.info("💡 **Market Trend:** Bot abhi data analyze kar raha hai...")
        with col2:
            st.warning("⚡ **Action:** Abhi koi entry nahi ban rahi. Wait karein.")
            
    else:
        st.warning("Market data load ho raha hai...")
        
except Exception as e:
    st.error(f"Data laane mein error aaya: {e}")

st.markdown("---")
st.write("Agla Step: Hum yahan Options ke Greeks aur PCR (Put-Call Ratio) ka data add karenge.")
