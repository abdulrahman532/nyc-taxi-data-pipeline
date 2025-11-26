"""Fraud Detection Page"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import time
import sys
import os

sys. path.insert(0, os.path. dirname(os.path.dirname(os. path.abspath(__file__))))
from utils.redis_client import RedisClient
from utils.zone_lookup import ZoneLookup

st. set_page_config(page_title="Fraud Detection", page_icon="🕵️", layout="wide")
st. title("🕵️ Fraud Detection")

@st. cache_resource
def get_redis_client():
    return RedisClient()

@st.cache_resource
def get_zone_lookup():
    return ZoneLookup()

redis_client = get_redis_client()
zone_lookup = get_zone_lookup()

refresh_rate = st. sidebar.slider("Refresh Rate (seconds)", 5, 60, 10)
auto_refresh = st.sidebar.checkbox("Auto Refresh", value=True)
min_score = st.sidebar. slider("Min Fraud Score", 0, 100, 50)

placeholder = st.empty()

def render_fraud_dashboard():
    alerts = redis_client. get_fraud_alerts()
    top_zones = redis_client. get_top_fraud_zones(10)
    top_routes = redis_client.get_top_fraud_routes(10)
    
    with placeholder.container():
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("⚠️ Total Alerts Today", len(alerts))
        with col2:
            high_risk = sum(1 for a in alerts if a. get('fraud_score', 0) >= 70)
            st. metric("🔴 High Risk (70+)", high_risk)
        with col3:
            night_fraud = sum(1 for a in alerts if a.get('is_night', False))
            st.metric("🌙 Night Fraud", night_fraud)
        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🔥 Top Fraud Zones")
            if top_zones:
                df = pd. DataFrame(top_zones, columns=['Zone ID', 'Count'])
                df['Zone Name'] = df['Zone ID'].apply(lambda x: zone_lookup.get_zone_name(int(x)))
                st.dataframe(df[['Zone Name', 'Count']], use_container_width=True)
            else:
                st.info("No fraud zones yet")
        
        with col2:
            st.subheader("🛤️ Top Fraud Routes")
            if top_routes:
                df = pd. DataFrame(top_routes, columns=['Route', 'Count'])
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No fraud routes yet")
        
        st.markdown("---")
        st.subheader("📋 Recent Fraud Alerts")
        
        if alerts:
            filtered = [a for a in alerts if a.get('fraud_score', 0) >= min_score]
            if filtered:
                df = pd.DataFrame(filtered)
                df['pickup_zone'] = df['PULocationID'].apply(lambda x: zone_lookup.get_zone_name(x))
                df['dropoff_zone'] = df['DOLocationID'].apply(lambda x: zone_lookup.get_zone_name(x))
                st.dataframe(
                    df[['timestamp', 'fraud_score', 'fraud_flags', 'pickup_zone', 'dropoff_zone', 'fare_amount', 'is_night']],
                    use_container_width=True
                )
            else:
                st.info(f"No alerts with score >= {min_score}")
        else:
            st. info("No fraud alerts yet")
        
        st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

render_fraud_dashboard()

if auto_refresh:
    time.sleep(refresh_rate)
    st.rerun()