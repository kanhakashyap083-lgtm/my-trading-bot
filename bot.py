import streamlit as st
import pandas as pd
import yfinance as yf
import warnings
from streamlit_autorefresh import st_autorefresh

warnings.filterwarnings("ignore")
st.set_page_config(page_title="Mega Trading Terminal", layout="wide", page_icon="🚀")

# Auto refresh har 1 minute mein
st_autorefresh(interval=60000, limit=200, key="fando_refresh")

st.sidebar.title("⚡ Mega Terminal")
st.sidebar.info("All-in-One Market Data")

# 1. Categories ko alag karna
category = st.sidebar.radio("📁 Kya Dekhna Hai?", ["📊 Main Indices", "🏢 Sub-Sectors", "📈 Top Stocks", "⛓️ Option Chain"])

# 2. Market ka sara data yahan hai
market_data = {
    "📊 Main Indices": {
        "NIFTY 50": "^NSEI", 
        "BANK NIFTY": "^NSEBANK", 
        "SENSEX": "^BSESN", 
        "INDIA VIX": "^INDIAVIX"
    },
    "🏢 Sub-Sectors": {
        "NIFTY IT": "^CNXIT", 
        "NIFTY AUTO": "^CNXAUTO", 
        "NIFTY PHARMA": "^CNXPHARMA", 
        "NIFTY METAL": "^CNXMETAL", 
        "NIFTY FMCG": "^CNXFMCG"
    },
    "📈 Top Stocks": {
        "RELIANCE": "RELIANCE.NS", 
        "HDFC BANK": "HDFCBANK.NS", 
        "TCS": "TCS.NS", 
        "SBI": "SBIN.NS", 
        "INFOSYS": "INFY.NS"
    }
}

if category == "⛓️ Option Chain":
    st.title("⛓️ Advanced Option Chain")
    st.write("---")
    st.warning("⚠️ Option Chain ka structure ready hai! Kyunki ab hum API use nahi kar rahe, agle step mein hum seedha **NSE India** ki website se live Open Interest (OI) aur PCR laane ka jugaad (scraper) yahan daalenge.")
    st.info("Tab tak aap baaki **Indices, Sectors aur Stocks** ke live signals check kar sakte hain.")

else:
    st.title(f"🚀 {category} Signal Bot")
    
    # User jo asset select karega
    selected_asset = st.sidebar.selectbox("Kiska Signal Chahiye?", list(market_data[category].keys()))
    ticker_symbol = market_data[category][selected_asset]
    
    st.subheader(f"📊 Live Status: {selected_asset}")
    
    try:
        ticker = yf.Ticker(ticker_symbol)
        data = ticker.history(period="5d", interval="5m")
        
        if not data.empty:
            # AI Logic
            data['EMA_9'] = data['Close'].ewm(span=9, adjust=False).mean()
            data['EMA_21'] = data['Close'].ewm(span=21, adjust=False).mean()
            
            delta = data['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            data['RSI'] = 100 - (100 / (1 + rs))
            
            current_price = float(data['Close'].iloc[-1])
            ema_9_val = float(data['EMA_9'].iloc[-1])
            ema_21_val = float(data['EMA_21'].iloc[-1])
            rsi_val = float(data['RSI'].iloc[-1])
            
            st.metric(label=f"{selected_asset} Current Price", value=f"₹{current_price:.2f}")
            
            # Smart Target/SL logic (Index ke liye alag point, Stocks ke liye alag)
            if "^" in ticker_symbol: 
                # Index ke liye (0.2% SL, 0.4% Target) - Nifty mein 40-50 pts, BankNifty mein 100 pts banega
                sl_points = current_price * 0.002
                target_points = current_price * 0.004
            else:
                # Stocks ke liye (0.5% SL, 1% Target)
                sl_points = current_price * 0.005
                target_points = current_price * 0.01

            if ema_9_val > ema_21_val and rsi_val > 55:
                trend = "🟢 Bullish (Uptrend)"
                action = "🚀 BUY CALL (CE) / LONG"
                color = "success"
                sl_value = current_price - sl_points
                target_value = current_price + target_points
            elif ema_9_val < ema_21_val and rsi_val < 45:
                trend = "🔴 Bearish (Downtrend)"
                action = "📉 BUY PUT (PE) / SHORT"
                color = "error"
                sl_value = current_price + sl_points
                target_value = current_price - target_points
            else:
                trend = "🟡 Sideways (Choppy)"
                action = "⏳ WAIT (No Trade Zone)"
                color = "warning"
                sl_value = 0
                target_value = 0
            
            st.markdown("---")
            st.header("🎯 AI Trading Signals")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.info(f"💡 **Trend:** {trend}")
            with col2:
                if color == "success":
                    st.success(f"⚡ **Action:** {action}")
                    st.write(f"**🎯 Target:** ₹{target_value:.2f} | **🛑 SL:** ₹{sl_value:.2f}")
                elif color == "error":
                    st.error(f"⚡ **Action:** {action}")
                    st.write(f"**🎯 Target:** ₹{target_value:.2f} | **🛑 SL:** ₹{sl_value:.2f}")
                else:
                    st.warning(f"⚡ **Action:** {action}")
            with col3:
                st.metric(label="RSI (Momentum)", value=f"{rsi_val:.1f}")
                
        else:
            st.warning("Data load ho raha hai...")
            
    except Exception as e:
        st.error(f"Data laane mein error aaya: {e}")

st.markdown("---")
st.caption("Disclaimer: Trade hamesha apne risk par lein aur Stop-Loss zaroor maintain karein.")
