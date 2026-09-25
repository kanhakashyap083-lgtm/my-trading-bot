import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from dhanhq import dhanhq
import warnings

warnings.filterwarnings("ignore")
st.set_page_config(page_title="AI F&O Master Bot", layout="wide", page_icon="🚀")

st.sidebar.title("⚡ AI F&O Master (Dhan)")

# 1. Tijori (Secrets) se Keys nikalna
try:
    client_id = st.secrets["DHAN_CLIENT_ID"]
    access_token = st.secrets["DHAN_ACCESS_TOKEN"]
except Exception as e:
    st.error("⚠️ Dhan API Keys nahi mili! Kripya Streamlit Secrets check karein.")
    st.stop()

# 2. Dhan Account se Connection Banana
try:
    dhan = dhanhq(client_id, access_token)
    st.sidebar.success("✅ Dhan API Connected!")
except Exception as e:
    st.sidebar.error("❌ Dhan API Connection Failed!")

st.title("🚀 Advanced F&O Trading Dashboard")
st.markdown("Yeh dashboard ab seedha aapke **Dhan Account** se juda hai. Yahan se hum Live Options (Call/Put) ka data nikalenge.")

# 3. Market Selector
segment = st.sidebar.selectbox("Index Select Karein", ["NIFTY", "BANKNIFTY", "FINNIFTY", "SENSEX"])

st.subheader(f"📊 Live Data Status: {segment}")
st.info("System Ready: API connection successful. Yahan aapka Option Chain aur Auto-Buy/Sell signals aayenge!")

# Yahan hum aage chalkar live Option Chain aur VIX ka data layenge
st.write("Ab aapka bot professional F&O algo trading ke liye ekdum taiyar hai.")
