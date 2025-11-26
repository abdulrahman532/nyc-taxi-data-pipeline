"""Fraud Monitor Page"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.redis_client import RedisClient
from utils.zone_lookup import ZoneLookup

st.set_page_config(page_title="Fraud Monitor", page_icon="🔍", layout="wide")
st.title("🔍 Fraud Monitor")

redis_client = RedisClient()
zone_lookup = ZoneLookup()

refresh_rate = st.sidebar.slider("Refresh Rate (sec)", 1, 30, 3)
auto_refresh = st.sidebar.checkbox("Auto Refresh", value=True)
min_score = st.sidebar.slider("Min Fraud Score", 0, 100, 30)

ZONE_COORDS = {
    132: (40.6413, -73.7781), 138: (40.7769, -73.8740), 161: (40.7580, -73.9855),
    162: (40.7549, -73.9679), 163: (40.7505, -73.9934), 164: (40.7614, -73.9776),
    230: (40.7484, -73.9967), 234: (40.7527, -73.9712), 236: (40.7946, -73.9535),
    237: (40.7831, -73.9535), 238: (40.7946, -73.9712), 239: (40.7831, -73.9754),
    249: (40.7336, -74.0086), 261: (40.7128, -74.0146), 262: (40.7741, -73.9412),
    263: (40.7831, -73.9493), 170: (40.7831, -73.9493), 186: (40.7741, -73.9535),
    90: (40.7400, -73.9920), 100: (40.7549, -73.9913), 107: (40.7379, -73.9825),
    113: (40.7336, -74.0027), 114: (40.7282, -74.0060), 125: (40.7557, -74.0020),
    137: (40.7466, -73.9789), 140: (40.7687, -73.9580), 141: (40.7741, -73.9565),
    142: (40.7734, -73.9870), 143: (40.7741, -73.9830), 144: (40.7191, -73.9973),
    148: (40.7157, -73.9861), 151: (40.7946, -73.9674), 158: (40.7420, -74.0086),
    166: (40.8115, -73.9600), 209: (40.7233, -74.0030), 224: (40.7177, -74.0086),
    229: (40.7580, -73.9855), 231: (40.7128, -74.0060), 232: (40.7128, -74.0028),
    233: (40.7527, -73.9679), 246: (40.7520, -74.0020),
}

def get_coord(zone_id):
    if zone_id in ZONE_COORDS:
        return ZONE_COORDS[zone_id]
    import hashlib
    h = int(hashlib.md5(str(zone_id).encode()).hexdigest()[:8], 16)
    return (40.7128 + (h % 1000) / 15000 - 0.033, -74.0060 + (h % 1500) / 15000 - 0.05)

placeholder = st.empty()

def render():
    alerts = redis_client.get_fraud_alerts()
    top_zones = redis_client.get_top_fraud_zones(10)
    
    with placeholder.container():
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Alerts", len(alerts))
        with col2:
            high = sum(1 for a in alerts if a.get('fraud_score', 0) >= 70)
            st.metric("High Risk (70+)", high)
        with col3:
            med = sum(1 for a in alerts if 50 <= a.get('fraud_score', 0) < 70)
            st.metric("Medium Risk", med)
        with col4:
            low = sum(1 for a in alerts if a.get('fraud_score', 0) < 50)
            st.metric("Low Risk", low)
        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if alerts:
                df = pd.DataFrame(alerts)
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df = df.sort_values('timestamp')
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=df['timestamp'], y=df['fraud_score'],
                    mode='lines+markers',
                    line=dict(color='#ff6b6b', width=2),
                    marker=dict(size=10, color=df['fraud_score'], colorscale='Reds', showscale=True)
                ))
                fig.add_hline(y=70, line_dash="dash", line_color="red")
                fig.add_hline(y=50, line_dash="dash", line_color="orange")
                fig.update_layout(title="Fraud Score Timeline", template="plotly_dark", height=350)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No fraud alerts yet")
        
        with col2:
            if top_zones:
                df = pd.DataFrame(top_zones, columns=['Zone ID', 'Count'])
                df['Zone'] = df['Zone ID'].apply(lambda x: zone_lookup.get_zone_name(int(x)))
                df['Count'] = df['Count'].astype(int)
                df = df.sort_values('Count', ascending=True)
                
                fig = px.bar(df, x='Count', y='Zone', orientation='h', color='Count',
                           color_continuous_scale='Reds', title="Top Fraud Zones")
                fig.update_layout(template="plotly_dark", height=350, showlegend=False, yaxis_title="")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No fraud zone data")
        
        st.markdown("---")
        
        # Link to Maps page
        st.info("🗺️ For detailed fraud route maps, go to **Maps** page and select **Fraud Routes**")
        
        st.markdown("---")
        
        if alerts:
            flags = {}
            for a in alerts:
                for f in a.get('fraud_flags', []):
                    flags[f] = flags.get(f, 0) + 1
            
            if flags:
                df = pd.DataFrame(list(flags.items()), columns=['Flag', 'Count'])
                df['Flag'] = df['Flag'].apply(lambda x: x.replace('_', ' ').title())
                df = df.sort_values('Count', ascending=True)
                
                fig = px.bar(df, x='Count', y='Flag', orientation='h', color='Count',
                           color_continuous_scale='Reds', title="Fraud Indicators")
                fig.update_layout(template="plotly_dark", height=250, showlegend=False, yaxis_title="")
                st.plotly_chart(fig, use_container_width=True)
        
        st.caption(f"Updated: {datetime.now().strftime('%H:%M:%S')}")

render()

if auto_refresh:
    time.sleep(refresh_rate)
    st.rerun()
