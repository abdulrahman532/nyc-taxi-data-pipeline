"""Maps Page - All geographic visualizations"""

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

st.set_page_config(page_title="Maps", page_icon="🗺️", layout="wide")
st.title("🗺️ NYC Taxi Maps")

redis_client = RedisClient()
zone_lookup = ZoneLookup()

# Zone coordinates for NYC
ZONE_COORDS = {
    1: (40.6895, -74.1745), 2: (40.6670, -73.7890), 3: (40.6715, -73.8413),
    4: (40.6800, -73.8550), 7: (40.6472, -73.9763), 8: (40.6485, -73.9605),
    9: (40.6361, -73.9652), 10: (40.6445, -73.9485), 11: (40.6550, -73.9365),
    12: (40.6610, -73.9235), 13: (40.6693, -73.9425), 14: (40.6745, -73.9520),
    17: (40.6565, -73.9875), 18: (40.6495, -73.9765), 19: (40.6350, -73.9485),
    21: (40.6135, -73.9875), 22: (40.6180, -73.9720), 24: (40.7400, -73.8350),
    25: (40.7510, -73.8560), 32: (40.6850, -73.9165), 33: (40.6910, -73.9055),
    36: (40.6780, -73.8495), 37: (40.6895, -73.8610), 40: (40.6645, -73.8430),
    41: (40.6975, -73.8120), 42: (40.7140, -73.7970), 43: (40.7680, -73.7495),
    45: (40.6495, -73.7655), 48: (40.7505, -73.9375), 49: (40.7385, -73.9195),
    50: (40.7720, -73.8765), 52: (40.7295, -73.7940), 56: (40.8010, -73.9310),
    61: (40.7040, -73.9345), 62: (40.7135, -73.9535), 63: (40.7265, -73.9475),
    65: (40.7095, -73.9455), 66: (40.7170, -73.9630), 67: (40.7245, -73.9615),
    68: (40.7185, -73.9510), 69: (40.7245, -73.9285), 70: (40.7280, -73.9160),
    74: (40.7450, -73.9055), 75: (40.7395, -73.9015), 76: (40.7450, -73.8830),
    79: (40.7580, -73.9035), 80: (40.7665, -73.9095), 82: (40.7720, -73.9545),
    83: (40.7785, -73.9555), 87: (40.6715, -73.9935), 88: (40.6850, -73.9880),
    90: (40.7400, -73.9920), 100: (40.7549, -73.9913), 107: (40.7379, -73.9825),
    113: (40.7336, -74.0027), 114: (40.7282, -74.0060), 125: (40.7557, -74.0020),
    132: (40.6413, -73.7781), 137: (40.7466, -73.9789), 138: (40.7769, -73.8740),
    140: (40.7687, -73.9580), 141: (40.7741, -73.9565), 142: (40.7734, -73.9870),
    143: (40.7741, -73.9830), 144: (40.7191, -73.9973), 148: (40.7157, -73.9861),
    151: (40.7946, -73.9674), 158: (40.7420, -74.0086), 161: (40.7580, -73.9855),
    162: (40.7549, -73.9679), 163: (40.7505, -73.9934), 164: (40.7614, -73.9776),
    166: (40.8115, -73.9600), 170: (40.7831, -73.9493), 186: (40.7741, -73.9535),
    209: (40.7233, -74.0030), 224: (40.7177, -74.0086), 229: (40.7580, -73.9855),
    230: (40.7484, -73.9967), 231: (40.7128, -74.0060), 232: (40.7128, -74.0028),
    233: (40.7527, -73.9679), 234: (40.7527, -73.9712), 236: (40.7946, -73.9535),
    237: (40.7831, -73.9535), 238: (40.7946, -73.9712), 239: (40.7831, -73.9754),
    246: (40.7520, -74.0020), 249: (40.7336, -74.0086), 261: (40.7128, -74.0146),
    262: (40.7741, -73.9412), 263: (40.7831, -73.9493),
}

def get_coord(zone_id):
    """Get coordinates for a zone ID"""
    if zone_id in ZONE_COORDS:
        return ZONE_COORDS[zone_id]
    import hashlib
    h = int(hashlib.md5(str(zone_id).encode()).hexdigest()[:8], 16)
    return (40.7128 + (h % 1000) / 15000 - 0.033, -74.0060 + (h % 1500) / 15000 - 0.05)

# Sidebar controls
st.sidebar.markdown("## 🗺️ Map Selection")
map_type = st.sidebar.selectbox(
    "Choose Map",
    ["🚗 Trip Routes", "📍 Pickup Hotspots", "📍 Dropoff Hotspots", 
     "🔴 Fraud Routes", "💰 Revenue by Zone", "📊 Zone Activity"]
)

st.sidebar.markdown("---")
refresh_rate = st.sidebar.slider("Refresh Rate (sec)", 1, 30, 5)
auto_refresh = st.sidebar.checkbox("Auto Refresh", value=False)

placeholder = st.empty()

def render_trip_routes():
    """Show recent trip routes on map"""
    st.subheader("🚗 Recent Trip Routes")
    
    metrics = redis_client.get_metrics()
    zone_stats = redis_client.get_zone_stats()
    
    if zone_stats:
        fig = go.Figure()
        
        # Get top pickup-dropoff pairs
        pickup_zones = zone_stats.get('pickup', {})
        dropoff_zones = zone_stats.get('dropoff', {})
        
        # Draw routes between top zones
        top_pickups = sorted(pickup_zones.items(), key=lambda x: int(x[1]), reverse=True)[:15]
        top_dropoffs = sorted(dropoff_zones.items(), key=lambda x: int(x[1]), reverse=True)[:15]
        
        colors = px.colors.qualitative.Set2
        
        for i, ((pu_zone, pu_count), (do_zone, do_count)) in enumerate(zip(top_pickups, top_dropoffs)):
            pu_coord = get_coord(int(pu_zone))
            do_coord = get_coord(int(do_zone))
            
            fig.add_trace(go.Scattermapbox(
                mode='lines',
                lon=[pu_coord[1], do_coord[1]],
                lat=[pu_coord[0], do_coord[0]],
                line=dict(width=3, color=colors[i % len(colors)]),
                opacity=0.7,
                name=f"Route {i+1}",
                showlegend=False
            ))
        
        # Add pickup markers
        pu_lats = [get_coord(int(z))[0] for z, _ in top_pickups]
        pu_lons = [get_coord(int(z))[1] for z, _ in top_pickups]
        pu_texts = [f"{zone_lookup.get_zone_name(int(z))}: {c} pickups" for z, c in top_pickups]
        
        fig.add_trace(go.Scattermapbox(
            mode='markers+text',
            lon=pu_lons, lat=pu_lats,
            marker=dict(size=15, color='#00ff00', symbol='circle'),
            text=[zone_lookup.get_zone_name(int(z))[:10] for z, _ in top_pickups],
            textposition="top center",
            textfont=dict(size=10, color='white'),
            hovertext=pu_texts,
            name='Pickups'
        ))
        
        # Add dropoff markers
        do_lats = [get_coord(int(z))[0] for z, _ in top_dropoffs]
        do_lons = [get_coord(int(z))[1] for z, _ in top_dropoffs]
        do_texts = [f"{zone_lookup.get_zone_name(int(z))}: {c} dropoffs" for z, c in top_dropoffs]
        
        fig.add_trace(go.Scattermapbox(
            mode='markers',
            lon=do_lons, lat=do_lats,
            marker=dict(size=12, color='#ff4444', symbol='circle'),
            hovertext=do_texts,
            name='Dropoffs'
        ))
        
        fig.update_layout(
            mapbox=dict(style='carto-darkmatter', center=dict(lat=40.7580, lon=-73.9855), zoom=10),
            height=700, margin={"r":0,"t":0,"l":0,"b":0},
            legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01, bgcolor="rgba(0,0,0,0.5)")
        )
        config = {'scrollZoom': True, 'displayModeBar': True}
        st.plotly_chart(fig, use_container_width=True, config=config)
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("🟢 **Green** = Pickup locations")
        with col2:
            st.markdown("🔴 **Red** = Dropoff locations")
    else:
        st.info("📊 No trip data yet. Start sending trips to see routes!")

def render_pickup_hotspots():
    """Show pickup hotspots on map"""
    st.subheader("📍 Pickup Hotspots")
    
    zone_stats = redis_client.get_zone_stats()
    
    if zone_stats and 'pickup' in zone_stats:
        pickup_zones = zone_stats['pickup']
        
        data = []
        for zone_id, count in pickup_zones.items():
            coord = get_coord(int(zone_id))
            data.append({
                'zone_id': int(zone_id),
                'zone_name': zone_lookup.get_zone_name(int(zone_id)),
                'count': int(count),
                'lat': coord[0],
                'lon': coord[1]
            })
        
        df = pd.DataFrame(data)
        
        if not df.empty:
            fig = px.scatter_mapbox(
                df, lat='lat', lon='lon', size='count', color='count',
                hover_name='zone_name', hover_data={'count': True, 'lat': False, 'lon': False},
                color_continuous_scale='Greens', size_max=40,
                zoom=10, center={"lat": 40.7580, "lon": -73.9855}
            )
            fig.update_layout(
                mapbox_style='carto-darkmatter',
                height=700, margin={"r":0,"t":0,"l":0,"b":0}
            )
            config = {'scrollZoom': True, 'displayModeBar': True}
            st.plotly_chart(fig, use_container_width=True, config=config)
            
            st.markdown("**🟢 Larger circles = More pickups**")
        else:
            st.info("No pickup data yet")
    else:
        st.info("📊 No pickup data yet. Start sending trips!")

def render_dropoff_hotspots():
    """Show dropoff hotspots on map"""
    st.subheader("📍 Dropoff Hotspots")
    
    zone_stats = redis_client.get_zone_stats()
    
    if zone_stats and 'dropoff' in zone_stats:
        dropoff_zones = zone_stats['dropoff']
        
        data = []
        for zone_id, count in dropoff_zones.items():
            coord = get_coord(int(zone_id))
            data.append({
                'zone_id': int(zone_id),
                'zone_name': zone_lookup.get_zone_name(int(zone_id)),
                'count': int(count),
                'lat': coord[0],
                'lon': coord[1]
            })
        
        df = pd.DataFrame(data)
        
        if not df.empty:
            fig = px.scatter_mapbox(
                df, lat='lat', lon='lon', size='count', color='count',
                hover_name='zone_name', hover_data={'count': True, 'lat': False, 'lon': False},
                color_continuous_scale='Reds', size_max=40,
                zoom=10, center={"lat": 40.7580, "lon": -73.9855}
            )
            fig.update_layout(
                mapbox_style='carto-darkmatter',
                height=700, margin={"r":0,"t":0,"l":0,"b":0}
            )
            config = {'scrollZoom': True, 'displayModeBar': True}
            st.plotly_chart(fig, use_container_width=True, config=config)
            
            st.markdown("**🔴 Larger circles = More dropoffs**")
        else:
            st.info("No dropoff data yet")
    else:
        st.info("📊 No dropoff data yet. Start sending trips!")

def render_fraud_routes():
    """Show fraud routes on map"""
    st.subheader("🔴 Fraud Route Map")
    
    alerts = redis_client.get_fraud_alerts()
    
    if alerts:
        fig = go.Figure()
        
        # Draw routes
        for alert in alerts:
            pu = alert.get('PULocationID', 1)
            do = alert.get('DOLocationID', 1)
            score = alert.get('fraud_score', 0)
            
            pu_coord = get_coord(pu)
            do_coord = get_coord(do)
            
            color = 'red' if score >= 70 else 'orange' if score >= 50 else 'yellow'
            
            fig.add_trace(go.Scattermapbox(
                mode='lines',
                lon=[pu_coord[1], do_coord[1]],
                lat=[pu_coord[0], do_coord[0]],
                line=dict(width=3, color=color),
                opacity=0.7,
                showlegend=False,
                hovertext=f"Score: {score}"
            ))
        
        # Add markers
        pu_lats = [get_coord(a.get('PULocationID', 1))[0] for a in alerts]
        pu_lons = [get_coord(a.get('PULocationID', 1))[1] for a in alerts]
        scores = [a.get('fraud_score', 0) for a in alerts]
        
        fig.add_trace(go.Scattermapbox(
            mode='markers',
            lon=pu_lons, lat=pu_lats,
            marker=dict(size=12, color=scores, colorscale='Reds', showscale=True),
            hovertext=[f"Score: {s}" for s in scores],
            name='Fraud Alerts'
        ))
        
        fig.update_layout(
            mapbox=dict(style='carto-darkmatter', center=dict(lat=40.7580, lon=-73.9855), zoom=10),
            height=700, margin={"r":0,"t":0,"l":0,"b":0}
        )
        config = {'scrollZoom': True, 'displayModeBar': True}
        st.plotly_chart(fig, use_container_width=True, config=config)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("🔴 **Red** = High Risk (70+)")
        with col2:
            st.markdown("🟠 **Orange** = Medium (50-69)")
        with col3:
            st.markdown("🟡 **Yellow** = Low (<50)")
    else:
        st.info("📊 No fraud alerts yet")

def render_revenue_map():
    """Show revenue by zone on map"""
    st.subheader("💰 Revenue by Zone")
    
    zone_stats = redis_client.get_zone_stats()
    
    if zone_stats and 'revenue' in zone_stats:
        revenue_zones = zone_stats['revenue']
        
        data = []
        for zone_id, revenue in revenue_zones.items():
            coord = get_coord(int(zone_id))
            data.append({
                'zone_id': int(zone_id),
                'zone_name': zone_lookup.get_zone_name(int(zone_id)),
                'revenue': float(revenue),
                'lat': coord[0],
                'lon': coord[1]
            })
        
        df = pd.DataFrame(data)
        
        if not df.empty:
            fig = px.scatter_mapbox(
                df, lat='lat', lon='lon', size='revenue', color='revenue',
                hover_name='zone_name', 
                hover_data={'revenue': ':$,.0f', 'lat': False, 'lon': False},
                color_continuous_scale='Viridis', size_max=50,
                zoom=10, center={"lat": 40.7580, "lon": -73.9855}
            )
            fig.update_layout(
                mapbox_style='carto-darkmatter',
                height=700, margin={"r":0,"t":0,"l":0,"b":0}
            )
            config = {'scrollZoom': True, 'displayModeBar': True}
            st.plotly_chart(fig, use_container_width=True, config=config)
            
            st.markdown("**💰 Larger circles = Higher revenue**")
        else:
            st.info("No revenue data yet")
    else:
        st.info("📊 No revenue data yet. Start sending trips!")

def render_zone_activity():
    """Show zone activity heatmap"""
    st.subheader("📊 Zone Activity Overview")
    
    zone_stats = redis_client.get_zone_stats()
    
    if zone_stats:
        pickup_zones = zone_stats.get('pickup', {})
        dropoff_zones = zone_stats.get('dropoff', {})
        
        # Combine pickup and dropoff
        all_zones = set(pickup_zones.keys()) | set(dropoff_zones.keys())
        
        data = []
        for zone_id in all_zones:
            coord = get_coord(int(zone_id))
            pickup_count = int(pickup_zones.get(zone_id, 0))
            dropoff_count = int(dropoff_zones.get(zone_id, 0))
            total = pickup_count + dropoff_count
            
            data.append({
                'zone_id': int(zone_id),
                'zone_name': zone_lookup.get_zone_name(int(zone_id)),
                'pickups': pickup_count,
                'dropoffs': dropoff_count,
                'total': total,
                'lat': coord[0],
                'lon': coord[1]
            })
        
        df = pd.DataFrame(data)
        
        if not df.empty:
            fig = px.scatter_mapbox(
                df, lat='lat', lon='lon', size='total', color='total',
                hover_name='zone_name',
                hover_data={'pickups': True, 'dropoffs': True, 'total': True, 'lat': False, 'lon': False},
                color_continuous_scale='Turbo', size_max=45,
                zoom=10, center={"lat": 40.7580, "lon": -73.9855}
            )
            fig.update_layout(
                mapbox_style='carto-darkmatter',
                height=700, margin={"r":0,"t":0,"l":0,"b":0}
            )
            config = {'scrollZoom': True, 'displayModeBar': True}
            st.plotly_chart(fig, use_container_width=True, config=config)
            
            # Summary stats
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Active Zones", len(data))
            with col2:
                st.metric("Total Pickups", sum(d['pickups'] for d in data))
            with col3:
                st.metric("Total Dropoffs", sum(d['dropoffs'] for d in data))
        else:
            st.info("No zone activity data yet")
    else:
        st.info("📊 No zone data yet. Start sending trips!")

def render():
    with placeholder.container():
        if map_type == "🚗 Trip Routes":
            render_trip_routes()
        elif map_type == "📍 Pickup Hotspots":
            render_pickup_hotspots()
        elif map_type == "📍 Dropoff Hotspots":
            render_dropoff_hotspots()
        elif map_type == "🔴 Fraud Routes":
            render_fraud_routes()
        elif map_type == "💰 Revenue by Zone":
            render_revenue_map()
        elif map_type == "📊 Zone Activity":
            render_zone_activity()
        
        st.caption(f"Updated: {datetime.now().strftime('%H:%M:%S')}")

render()

if auto_refresh:
    time.sleep(refresh_rate)
    st.rerun()
