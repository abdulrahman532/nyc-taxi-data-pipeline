"""NYC Taxi Dashboard - Main Page"""

import streamlit as st
import sys
import os

st.set_page_config(
    page_title="NYC Taxi Dashboard",
    page_icon="🚕",
    layout="wide"
)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Sidebar branding
st.sidebar.markdown("## 🚕 NYC Taxi")
st.sidebar.markdown("Real-Time Analytics")
st.sidebar.markdown("---")

# Main content
st.markdown("""
<h1 style='text-align: center; color: #00d2ff;'>NYC Taxi Analytics</h1>
<p style='text-align: center; color: #888;'>Real-Time Streaming Dashboard</p>
""", unsafe_allow_html=True)

st.markdown("---")

# Metrics
try:
    from utils.redis_client import RedisClient
    redis_client = RedisClient()
    metrics = redis_client.get_today_metrics()
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🚕 Trips", f"{metrics.get('trips', 0):,}")
    c2.metric("💰 Revenue", f"${metrics.get('revenue', 0):,.2f}")
    c3.metric("⚠️ Fraud Alerts", metrics.get('fraud_alerts', 0))
    rate = (metrics.get('fraud_alerts', 0) / max(1, metrics.get('trips', 1))) * 100
    c4.metric("📊 Fraud Rate", f"{rate:.2f}%")
except:
    st.info("Waiting for data... Start sending trips!")

st.markdown("---")

# Navigation cards
c1, c2 = st.columns(2)

with c1:
    st.markdown("""
    ### 📊 Live Analytics
    Real-time monitoring of taxi operations:
    - Trip volume & revenue trends
    - Hourly performance charts
    - Payment method distribution
    - Top pickup/dropoff zones
    """)
    if st.button("Open Live Analytics", type="primary", use_container_width=True):
        st.switch_page("pages/1_📊_Live_Analytics.py")

with c2:
    st.markdown("""
    ### 🔍 Fraud Monitor
    Advanced fraud detection system:
    - Real-time anomaly detection
    - Geographic fraud map with routes
    - Risk scoring & alerts
    - Fraud indicator analysis
    """)
    if st.button("Open Fraud Monitor", use_container_width=True):
        st.switch_page("pages/2_🔍_Fraud_Monitor.py")

st.markdown("---")

# System status
st.markdown("### 🖥️ System Components")
c1, c2, c3, c4 = st.columns(4)
c1.success("✅ Kafka 4.1.1")
c2.success("✅ Spark 4.0.1")
c3.success("✅ Redis")
c4.success("✅ FastAPI")

st.markdown("---")
st.caption("NYC Taxi Real-Time Analytics Pipeline | Apache Kafka • Apache Spark • Redis • FastAPI")
