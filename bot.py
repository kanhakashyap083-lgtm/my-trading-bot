import streamlit as st
import pandas as pd
import yfinance as yf
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
    ticker_data = yf.Ticker(ticker_symbol)
    # Hum 5 din ka data le rahe hain taaki Indicators sahi se calculate ho sakein
    data = ticker_data.history(period="5d", interval="5m")
    
    if not data.empty:
        # --- AI TRADING LOGIC (Indicators) ---
        # 1. EMA (Exponential Moving Average) Calculation
        data['EMA_9'] = data['Close'].ewm(span=9, adjust=False).mean()
        data['EMA_21'] = data['Close'].ewm(span=21, adjust=False).mean()
        
        # 2. RSI (Relative Strength Index) Calculation
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        data['RSI'] = 100 - (100 / (1 + rs))
        
        # Latest data values nikalna
        current_price = float(data['Close'].iloc[-1])
        ema_9_val = float(data['EMA_9'].iloc[-1])
        ema_21_val = float(data['EMA_21'].iloc[-1])
        rsi_val = float(data['RSI'].iloc[-1])
        
        st.metric(label=f"{index_choice} Current Price", value=f"₹{current_price:.2f}")
        
        # --- SIGNAL GENERATOR ---
        if ema_9_val > ema_21_val and rsi_val > 55:
            trend_text = "🟢 Bullish (Uptrend)"
            action_text = "🚀 BUY CALL OPTION (CE)"
            action_color = "success"
        elif ema_9_val < ema_21_val and rsi_val < 45:
            trend_text = "🔴 Bearish (Downtrend)"
            action_text = "📉 BUY PUT OPTION (PE)"
            action_color = "error"
        else:
            trend_text = "🟡 Sideways / Choppy"
            action_text = "⏳ WAIT (No Trade Zone)"
            action_color = "warning"
        
        st.markdown("---")
        st.header("🎯 AI Trading Signals")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.info(f"💡 **Market Trend:** {trend_text}")
        with col2:
            if action_color == "success":
                st.success(f"⚡ **Action:** {action_text}")
            elif action_color == "error":
                st.error(f"⚡ **Action:** {action_text}")
            else:
                st.warning(f"⚡ **Action:** {action_text}")
        with col3:
            st.metric(label="RSI (Momentum)", value=f"{rsi_val:.1f}")

        st.caption(f"Technical Details: 9 EMA = {ema_9_val:.2f} | 21 EMA = {ema_21_val:.2f}")
            
    else:
        st.warning("Market data load ho raha hai...")
        
except Exception as e:
    st.error(f"Data laane mein error aaya: {e}")

st.markdown("---")
st.caption("Disclaimer: Yeh signals algo analysis ke basis par hain. Groww mein trade lene se pehle hamesha apna Stop-Loss (SL) zaroor lagayein.")
