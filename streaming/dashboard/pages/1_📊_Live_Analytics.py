"""Live Analytics Page"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time
from streamlit_autorefresh import st_autorefresh
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.redis_client import RedisClient
from utils.zone_lookup import ZoneLookup

st.set_page_config(page_title="Live Analytics", page_icon="📊", layout="wide")
st.title("📊 Live Analytics")

redis_client = RedisClient()
zone_lookup = ZoneLookup()

refresh_rate = st.sidebar.slider("Refresh Rate (sec)", 1, 30, 3)
auto_refresh = st.session_state.get('realtime', False) or st.sidebar.checkbox("Auto Refresh", value=False)

placeholder = st.empty()

def render():
    metrics = redis_client.get_today_metrics()
    hourly = redis_client.get_hourly_stats()
    # payment_stats and vendor_stats charts were removed per user request
    top_pickup = redis_client.get_top_pickup_zones(10)
    top_dropoff = redis_client.get_top_dropoff_zones(10)
    
    trips = metrics.get('trips', 0)
    revenue = metrics.get('revenue', 0)
    
    with placeholder.container():
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Trips", f"{trips:,}")
        with col2:
            st.metric("Revenue", f"${revenue:,.2f}")
        with col3:
            avg = revenue / trips if trips > 0 else 0
            st.metric("Avg Fare", f"${avg:.2f}")
        with col4:
            st.metric("Fraud Alerts", metrics.get('fraud_alerts', 0))
        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if hourly['trips']:
                df = pd.DataFrame(list(hourly['trips'].items()), columns=['Hour', 'Trips'])
                df['Hour'] = df['Hour'].astype(int)
                df['Trips'] = df['Trips'].astype(int)
                df = df.sort_values('Hour')
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=df['Hour'], y=df['Trips'],
                    mode='lines+markers',
                    line=dict(color='#00d2ff', width=3),
                    fill='tozeroy'
                ))
                fig.update_layout(title="Trips per Hour", template="plotly_dark", height=300)
                st.plotly_chart(fig, width='stretch')
            else:
                st.info("No hourly data")
        
        with col2:
            if hourly['revenue']:
                df = pd.DataFrame(list(hourly['revenue'].items()), columns=['Hour', 'Revenue'])
                df['Hour'] = df['Hour'].astype(int)
                df['Revenue'] = df['Revenue'].astype(float)
                df = df.sort_values('Hour')
                
                fig = px.bar(df, x='Hour', y='Revenue', color='Revenue', 
                           color_continuous_scale='Blues', title="Revenue per Hour")
                fig.update_layout(template="plotly_dark", height=300, showlegend=False)
                st.plotly_chart(fig, width='stretch')
            else:
                st.info("No revenue data")
        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        # Payment method visualization removed per user request (Credit vs Cash)
        
        # Vendor chart removed for cleaner UI (left for future dashboards if needed)
        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if top_pickup:
                df = pd.DataFrame(top_pickup, columns=['Zone ID', 'Trips'])
                df['Zone'] = df['Zone ID'].apply(lambda x: zone_lookup.get_zone_name(int(x)))
                df['Trips'] = df['Trips'].astype(int)
                df = df.sort_values('Trips', ascending=True).tail(10)
                
                fig = px.bar(df, x='Trips', y='Zone', orientation='h', color='Trips',
                           color_continuous_scale='Reds', title="Top Pickup Zones")
                fig.update_layout(template="plotly_dark", height=300, showlegend=False, yaxis_title="")
                st.plotly_chart(fig, width='stretch')
        
        with col2:
            if top_dropoff:
                df = pd.DataFrame(top_dropoff, columns=['Zone ID', 'Trips'])
                df['Zone'] = df['Zone ID'].apply(lambda x: zone_lookup.get_zone_name(int(x)))
                df['Trips'] = df['Trips'].astype(int)
                df = df.sort_values('Trips', ascending=True).tail(10)
                
                fig = px.bar(df, x='Trips', y='Zone', orientation='h', color='Trips',
                           color_continuous_scale='Oranges', title="Top Dropoff Zones")
                fig.update_layout(template="plotly_dark", height=300, showlegend=False, yaxis_title="")
                st.plotly_chart(fig, width='stretch')
        
        st.caption(f"Updated: {datetime.now().strftime('%H:%M:%S')}")

        # --------------------------- RUSH HOURS HEATMAP ---------------------------
        st.markdown("---")
        st.markdown("### 🔥 Rush Hours (Hourly traffic heatmap)")
        days = st.sidebar.slider("Aggregate last N days", 1, 14, 7)
        hourly_matrix = redis_client.get_hourly_matrix(days=days)
        # hourly_matrix is dict: weekday -> list[24]
        weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        # build DataFrame
        try:
            matrix_df = pd.DataFrame([hourly_matrix.get(d, [0]*24) for d in weekdays], index=weekdays, columns=list(range(24)))
        except Exception:
            matrix_df = None

        if matrix_df is not None and matrix_df.values.sum() > 0:
            fig = px.imshow(matrix_df, aspect='auto', color_continuous_scale='Reds', 
                            labels=dict(x='Hour of Day', y='Weekday', color='Trips'),
                            x=list(range(24)), y=weekdays)
            fig.update_layout(template='plotly_dark', height=420, margin={'t': 30})
            st.plotly_chart(fig, width='stretch')
        else:
            st.info('No hourly matrix data to display yet')

render()

if auto_refresh:
    realtime_interval = 250 if st.session_state.get('realtime', False) else refresh_rate * 1000
    st_autorefresh(interval=realtime_interval, key='live_autorefresh')
