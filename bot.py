import streamlit as st
import pandas as pd
import yfinance as yf
import warnings
from streamlit_autorefresh import st_autorefresh

warnings.filterwarnings("ignore")
st.set_page_config(page_title="Mega Trading Terminal (Pro AI)", layout="wide", page_icon="🤖")

st_autorefresh(interval=60000, limit=200, key="fando_refresh")

st.sidebar.title("⚡ Mega Terminal")
st.sidebar.info("Pro-Trader AI Mode (Live)")

# Option Chain yahan se hata diya hai taaki mobile app clean rahe
category = st.sidebar.radio("📁 Kya Dekhna Hai?", ["📊 Main Indices", "🏢 Sub-Sectors", "📈 Top Stocks", "🔍 Auto-Scanner"])

market_data = {
    "📊 Main Indices": {"NIFTY 50": "^NSEI", "BANK NIFTY": "^NSEBANK", "SENSEX": "^BSESN", "INDIA VIX": "^INDIAVIX"},
    "🏢 Sub-Sectors": {"NIFTY IT": "^CNXIT", "NIFTY AUTO": "^CNXAUTO", "NIFTY PHARMA": "^CNXPHARMA", "NIFTY METAL": "^CNXMETAL", "NIFTY FMCG": "^CNXFMCG"},
    "📈 Top Stocks": {"RELIANCE": "RELIANCE.NS", "HDFC BANK": "HDFCBANK.NS", "TCS": "TCS.NS", "SBI": "SBIN.NS", "INFOSYS": "INFY.NS"}
}

def calculate_indicators(data):
    data['EMA_9'] = data['Close'].ewm(span=9, adjust=False).mean()
    data['EMA_21'] = data['Close'].ewm(span=21, adjust=False).mean()
    data['EMA_50'] = data['Close'].ewm(span=50, adjust=False).mean()
    data['EMA_200'] = data['Close'].ewm(span=200, adjust=False).mean()
    
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

if category == "🔍 Auto-Scanner":
    st.title("🤖 Pro-AI Stock Scanner (Triple Filtered)")
    st.write("Yeh bot ek Professional Trader ki tarah sochta hai. Yeh tabhi signal dega jab **EMA, RSI, aur MACD teeno ek sath agree karenge**.")
    
    trade_type = st.radio("⏳ Trading Style Select Karein:", ["🚀 Intraday (Aaj hi Buy/Sell)", "📆 Swing / Positional (1-2 Hafte Hold)"])
    
    scan_list = {
        "RELIANCE": "RELIANCE.NS", "HDFC BANK": "HDFCBANK.NS", "ICICI BANK": "ICICIBANK.NS", 
        "INFOSYS": "INFY.NS", "TCS": "TCS.NS", "SBI": "SBIN.NS", "ITC": "ITC.NS", 
        "BHARTI AIRTEL": "BHARTIARTL.NS", "L&T": "LT.NS", "BAJAJ FINANCE": "BAJFINANCE.NS",
        "AXIS BANK": "AXISBANK.NS", "KOTAK BANK": "KOTAKBANK.NS", "TATA MOTORS": "TATAMOTORS.NS", 
        "SUN PHARMA": "SUNPHARMA.NS", "MARUTI": "MARUTI.NS", "M&M": "M&M.NS"
    }
    
    if st.button("🚀 Run Pro-Trader Scan"):
        with st.spinner("AI is analyzing charts like a Pro... strict filtering active..."):
            results = []
            for name, ticker_symbol in scan_list.items():
                try:
                    ticker = yf.Ticker(ticker_symbol)
                    
                    if "Intraday" in trade_type:
                        data = ticker.history(period="5d", interval="5m")
                        tgt_pct, sl_pct, hold_text = 0.01, 0.005, "Intraday (Same Day)"
                    else:
                        data = ticker.history(period="1y", interval="1d")
                        tgt_pct, sl_pct, hold_text = "5-8%", "2-3%", "1-2 Weeks (Swing)"
                        
                    if not data.empty:
                        data = calculate_indicators(data)
                        
                        curr = float(data['Close'].iloc[-1])
                        e9, e21, e200 = float(data['EMA_9'].iloc[-1]), float(data['EMA_21'].iloc[-1]), float(data['EMA_200'].iloc[-1])
                        rsi = float(data['RSI'].iloc[-1])
                        macd, macd_sig = float(data['MACD'].iloc[-1]), float(data['Signal_Line'].iloc[-1])
                        
                        bullish_condition = (e9 > e21) and (rsi > 55) and (macd > macd_sig)
                        bearish_condition = (e9 < e21) and (rsi < 45) and (macd < macd_sig)
                        
                        sl_val = curr * (0.005 if "Intraday" in trade_type else 0.02)
                        tgt_val = curr * (0.01 if "Intraday" in trade_type else 0.05)
                        
                        if "Swing" in trade_type:
                            if curr > e200 and bullish_condition:
                                results.append({"Stock": name, "Action": "🟢 STRONG BUY", "Entry": f"₹{curr:.2f}", "Target": f"₹{curr + tgt_val:.2f}", "SL": f"₹{curr - sl_val:.2f}", "Hold": hold_text})
                            elif curr < e200 and bearish_condition:
                                results.append({"Stock": name, "Action": "🔴 STRONG SELL", "Entry": f"₹{curr:.2f}", "Target": f"₹{curr - tgt_val:.2f}", "SL": f"₹{curr + sl_val:.2f}", "Hold": hold_text})
                        else:
                            if bullish_condition:
                                results.append({"Stock": name, "Action": "🟢 STRONG BUY", "Entry": f"₹{curr:.2f}", "Target": f"₹{curr + tgt_val:.2f}", "SL": f"₹{curr - sl_val:.2f}", "Hold": hold_text})
                            elif bearish_condition:
                                results.append({"Stock": name, "Action": "🔴 STRONG SELL", "Entry": f"₹{curr:.2f}", "Target": f"₹{curr - tgt_val:.2f}", "SL": f"₹{curr + sl_val:.2f}", "Hold": hold_text})
                except:
                    continue
            
            if results:
                df = pd.DataFrame(results)
                st.success(f"🎯 Perfect Trader AI found {len(results)} high-probability setups:")
                st.dataframe(df, use_container_width=True)
            else:
                st.warning("⚖️ Pro-Trader AI says: 'Koi strong setup nahi hai. Capital bacha kar rakho!'")

else:
    st.title(f"🚀 {category} AI Signals")
    selected_asset = st.sidebar.selectbox("Kiska Signal Chahiye?", list(market_data[category].keys()))
    ticker_symbol = market_data[category][selected_asset]
    
    try:
        ticker = yf.Ticker(ticker_symbol)
        data = ticker.history(period="1mo", interval="5m") 
        
        if not data.empty:
            data = calculate_indicators(data)
            
            curr = float(data['Close'].iloc[-1])
            e9, e21, e200 = float(data['EMA_9'].iloc[-1]), float(data['EMA_21'].iloc[-1]), float(data['EMA_200'].iloc[-1])
            rsi = float(data['RSI'].iloc[-1])
            macd, macd_sig = float(data['MACD'].iloc[-1]), float(data['Signal_Line'].iloc[-1])
            
            st.subheader(f"📊 {selected_asset}: ₹{curr:.2f}")
            
            bullish = (e9 > e21) and (rsi > 55) and (macd > macd_sig)
            bearish = (e9 < e21) and (rsi < 45) and (macd < macd_sig)
            
            if "^" in ticker_symbol: 
                tgt_pts, sl_pts = curr * 0.004, curr * 0.002
            else:
                tgt_pts, sl_pts = curr * 0.01, curr * 0.005

            if bullish:
                trend, action, color = "🟢 Bullish", "🚀 STRONG BUY (CE / LONG)", "success"
                sl, tgt = curr - sl_pts, curr + tgt_pts
            elif bearish:
                trend, action, color = "🔴 Bearish", "📉 STRONG SELL (PE / SHORT)", "error"
                sl, tgt = curr + sl_pts, curr - tgt_pts
            else:
                trend, action, color = "🟡 Choppy / Unclear", "⏳ WAIT (Strict Pro-Trader Rule)", "warning"
                sl, tgt = 0, 0
            
            st.markdown("---")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.info(f"💡 **Trend:** {trend}")
                st.caption(f"MACD Status: {'Positive' if macd > macd_sig else 'Negative'}")
            with col2:
                if color == "success":
                    st.success(f"⚡ **Action:** {action}")
                    st.write(f"**🎯 TGT:** ₹{tgt:.2f} | **🛑 SL:** ₹{sl:.2f}")
                elif color == "error":
                    st.error(f"⚡ **Action:** {action}")
                    st.write(f"**🎯 TGT:** ₹{tgt:.2f} | **🛑 SL:** ₹{sl:.2f}")
                else:
                    st.warning(f"⚡ **Action:** {action}")
            with col3:
                st.metric(label="RSI", value=f"{rsi:.1f}")
                st.caption("Above 55 is Bullish, Below 45 is Bearish")
                
    except Exception as e:
        st.error(f"Error: {e}")
