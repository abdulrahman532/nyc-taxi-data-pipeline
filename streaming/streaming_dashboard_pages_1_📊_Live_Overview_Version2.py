"""Live Overview Page"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly. graph_objects as go
from datetime import datetime
import time
import sys
import os

sys.path.insert(0, os. path.dirname(os.path.dirname(os.path. abspath(__file__))))
from utils.redis_client import RedisClient
from utils. zone_lookup import ZoneLookup

st.set_page_config(page_title="Live Overview", page_icon="📊", layout="wide")
st.title("📊 Live Overview")

@st.cache_resource
def get_redis_client():
    return RedisClient()

@st.cache_resource
def get_zone_lookup():
    return ZoneLookup()

redis_client = get_redis_client()
zone_lookup = get_zone_lookup()

refresh_rate = st.sidebar.slider("Refresh Rate (seconds)", 5, 60, 10)
auto_refresh = st. sidebar.checkbox("Auto Refresh", value=True)

placeholder = st.empty()

def render_dashboard():
    metrics = redis_client. get_today_metrics()
    hourly = redis_client.get_hourly_stats()
    
    with placeholder.container():
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("🚕 Today's Trips", f"{metrics. get('trips', 0):,}")
        with col2:
            st.metric("💰 Revenue", f"${metrics.get('revenue', 0):,.2f}")
        with col3:
            st.metric("⚠️ Fraud Alerts", metrics.get('fraud_alerts', 0))
        with col4:
            st. metric("☀️ Day Trips", metrics.get('day_trips', 0))
        with col5:
            st. metric("🌙 Night Trips", metrics.get('night_trips', 0))
        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📈 Trips by Hour")
            if hourly['trips']:
                df = pd.DataFrame(list(hourly['trips'].items()), columns=['Hour', 'Trips'])
                df['Hour'] = df['Hour'].astype(int)
                df['Trips'] = df['Trips'].astype(int)
                df = df.sort_values('Hour')
                fig = px.bar(df, x='Hour', y='Trips', color='Trips', color_continuous_scale='Blues')
                st. plotly_chart(fig, use_container_width=True)
            else:
                st.info("No hourly data yet")
        
        with col2:
            st.subheader("🌓 Day vs Night")
            day = metrics.get('day_trips', 0)
            night = metrics.get('night_trips', 0)
            if day + night > 0:
                fig = go.Figure(data=[go. Pie(labels=['Day ☀️', 'Night 🌙'], values=[day, night], hole=. 4)])
                st. plotly_chart(fig, use_container_width=True)
            else:
                st.info("No data yet")
        
        st.caption(f"Last updated: {datetime. now().strftime('%Y-%m-%d %H:%M:%S')}")

render_dashboard()

if auto_refresh:
    time.sleep(refresh_rate)
    st.rerun()