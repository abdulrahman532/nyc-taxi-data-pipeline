"""TaxiPulse - NYC Real-Time Analytics Dashboard"""

import streamlit as st
from streamlit_autorefresh import st_autorefresh
import sys
import time
import os
import pydeck as pdk
import numpy as np

st.set_page_config(
    page_title="TaxiPulse - NYC Real-Time Analytics",
    page_icon="🚖",
    layout="wide"
)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Initialize navigation state
if 'nav' not in st.session_state:
    st.session_state['nav'] = "🏠 Home"
if 'realtime' not in st.session_state:
    st.session_state['realtime'] = False

# Sidebar
st.sidebar.markdown("## 🚖 TaxiPulse")
st.sidebar.markdown("---")
st.sidebar.checkbox("Realtime (live updates)", key='realtime')

# Navigation in sidebar
page = st.sidebar.radio(
    "Navigate",
    ["🏠 Home", "📊 Live Analytics", "🔍 Fraud Monitor", "🗺️ Maps"],
    index=["🏠 Home", "📊 Live Analytics", "🔍 Fraud Monitor", "🗺️ Maps"].index(st.session_state['nav'])
)

# Update session state when sidebar changes
if page != st.session_state['nav']:
    st.session_state['nav'] = page

st.sidebar.markdown("---")

# ==================== HOME PAGE ====================
if page == "🏠 Home":
    st.markdown("""
    <h1 style='text-align: center; color: #00d2ff;'>�� TaxiPulse</h1>
    <p style='text-align: center; color: #888; font-size: 1.2em;'>NYC Real-Time Streaming Analytics</p>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
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
    # Admin controls: clear Redis data
    if st.button("Clear Redis Data (FLUSH)", key="clear_redis"):
        try:
            redis_client.clear_all_data()
            st.success("Redis data cleared.")
        except Exception as e:
            st.error(f"Could not clear Redis data: {e}")
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### 📊 Live Analytics")
        st.markdown("Real-time monitoring of taxi operations:")
    st.markdown("- Trip volume & revenue trends\n- Hourly performance charts\n- Top pickup/dropoff zones")
    if st.button("Open Live Analytics", key="btn_analytics", type="primary", width='stretch'):
            st.session_state['nav'] = "📊 Live Analytics"
            st.rerun()
    
    with c2:
        st.markdown("### 🔍 Fraud Monitor")
        st.markdown("Advanced fraud detection system:")
        st.markdown("- Real-time anomaly detection\n- Geographic fraud map with routes\n- Risk scoring & alerts\n- Fraud indicator analysis")
    if st.button("Open Fraud Monitor", key="btn_fraud", width='stretch'):
            st.session_state['nav'] = "🔍 Fraud Monitor"
            st.rerun()
    
    st.markdown("---")
    
    st.markdown("### 🗺️ Interactive Maps")
    st.markdown("Explore NYC taxi activity through interactive maps:")
    
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown("**🚗 Trip Routes**")
        st.caption("Visualize popular routes")
    with c2:
        st.markdown("**📍 Pickup Hotspots**")
        st.caption("High activity pickup zones")
    with c3:
        st.markdown("**🎯 Dropoff Hotspots**")
        st.caption("Popular destinations")
    with c4:
        st.markdown("**⚠️ Fraud Routes**")
        st.caption("Suspicious trip patterns")
    
    if st.button("🗺️ Open Maps Dashboard", key="btn_maps", type="primary", width='stretch'):
        st.session_state['nav'] = "🗺️ Maps"
        st.rerun()
    
    st.markdown("---")
    st.markdown("### 🖥️ System Components")
    c1, c2, c3, c4 = st.columns(4)
    c1.success("✅ Kafka 4.1.1")
    c2.success("✅ Spark 4.0.1")
    c3.success("✅ Redis")
    c4.success("✅ FastAPI")

# ==================== LIVE ANALYTICS ====================
elif page == "📊 Live Analytics":
    import pandas as pd
    import plotly.express as px
    import plotly.graph_objects as go
    from datetime import datetime
    from utils.redis_client import RedisClient
    from utils.zone_lookup import ZoneLookup
    
    # Back button
    if st.button("← Back to Home", key="back_analytics"):
        st.session_state['nav'] = "🏠 Home"
        st.rerun()
    
    st.title("📊 Live Analytics")
    redis_client = RedisClient()
    zone_lookup = ZoneLookup()
    
    refresh_rate = st.sidebar.slider("Refresh Rate (sec)", 1, 30, 3)
    auto_refresh = st.sidebar.checkbox("Auto Refresh", value=True)
    
    metrics = redis_client.get_today_metrics()
    hourly = redis_client.get_hourly_stats()
    top_pickup = redis_client.get_top_pickup_zones(10)
    top_dropoff = redis_client.get_top_dropoff_zones(10)
    
    trips = metrics.get('trips', 0)
    revenue = metrics.get('revenue', 0)
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Trips", f"{trips:,}")
    col2.metric("Revenue", f"${revenue:,.2f}")
    col3.metric("Avg Fare", f"${revenue / trips if trips > 0 else 0:.2f}")
    col4.metric("Fraud Alerts", metrics.get('fraud_alerts', 0))
    
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        if hourly['trips']:
            df = pd.DataFrame(list(hourly['trips'].items()), columns=['Hour', 'Trips'])
            df['Hour'] = df['Hour'].astype(int)
            df['Trips'] = df['Trips'].astype(int)
            df = df.sort_values('Hour')
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df['Hour'], y=df['Trips'], mode='lines+markers',
                line=dict(color='#00d2ff', width=3), fill='tozeroy'))
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
            fig = px.bar(df, x='Hour', y='Revenue', color='Revenue', color_continuous_scale='Blues')
            fig.update_layout(template="plotly_dark", height=300, showlegend=False)
            st.plotly_chart(fig, width='stretch')
        else:
            st.info("No revenue data")
    
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        if top_pickup:
            df = pd.DataFrame(top_pickup, columns=['Zone ID', 'Trips'])
            df['Zone'] = df['Zone ID'].apply(lambda x: zone_lookup.get_zone_name(int(x)))
            df['Trips'] = df['Trips'].astype(int)
            df = df.sort_values('Trips', ascending=True).tail(10)
            fig = px.bar(df, x='Trips', y='Zone', orientation='h', color='Trips', color_continuous_scale='Reds')
            fig.update_layout(template="plotly_dark", height=300, showlegend=False, yaxis_title="")
            st.plotly_chart(fig, width='stretch')
    
    with col2:
        if top_dropoff:
            df = pd.DataFrame(top_dropoff, columns=['Zone ID', 'Trips'])
            df['Zone'] = df['Zone ID'].apply(lambda x: zone_lookup.get_zone_name(int(x)))
            df['Trips'] = df['Trips'].astype(int)
            df = df.sort_values('Trips', ascending=True).tail(10)
            fig = px.bar(df, x='Trips', y='Zone', orientation='h', color='Trips', color_continuous_scale='Oranges')
            fig.update_layout(template="plotly_dark", height=300, showlegend=False, yaxis_title="")
            st.plotly_chart(fig, width='stretch')
    
    st.caption(f"Updated: {datetime.now().strftime('%H:%M:%S')}")
    if auto_refresh:
        realtime_interval = 250 if st.session_state.get('realtime', False) else refresh_rate * 1000
        st_autorefresh(interval=realtime_interval, key='home_live_autorefresh')

# ==================== FRAUD MONITOR ====================
elif page == "🔍 Fraud Monitor":
    import pandas as pd
    import plotly.express as px
    import plotly.graph_objects as go
    from datetime import datetime
    from utils.redis_client import RedisClient
    from utils.zone_lookup import ZoneLookup
    
    # Back button
    if st.button("← Back to Home", key="back_fraud"):
        st.session_state['nav'] = "🏠 Home"
        st.rerun()
    
    st.title("🔍 Fraud Monitor")
    redis_client = RedisClient()
    zone_lookup = ZoneLookup()
    
    refresh_rate = st.sidebar.slider("Refresh Rate (sec)", 1, 30, 3)
    auto_refresh = st.sidebar.checkbox("Auto Refresh", value=True)
    
    alerts = redis_client.get_fraud_alerts()
    top_zones = redis_client.get_top_fraud_zones(10)
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Alerts", len(alerts))
    col2.metric("High Risk (70+)", sum(1 for a in alerts if a.get('fraud_score', 0) >= 70))
    col3.metric("Medium Risk", sum(1 for a in alerts if 50 <= a.get('fraud_score', 0) < 70))
    col4.metric("Low Risk", sum(1 for a in alerts if a.get('fraud_score', 0) < 50))
    
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        if alerts:
            df = pd.DataFrame(alerts)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp')
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df['timestamp'], y=df['fraud_score'], mode='lines+markers',
                line=dict(color='#ff6b6b', width=2),
                marker=dict(size=10, color=df['fraud_score'], colorscale='Reds', showscale=True)))
            fig.add_hline(y=70, line_dash="dash", line_color="red")
            fig.add_hline(y=50, line_dash="dash", line_color="orange")
            fig.update_layout(title="Fraud Score Timeline", template="plotly_dark", height=350)
            st.plotly_chart(fig, width='stretch')
        else:
            st.info("No fraud alerts yet")
    
    with col2:
        if top_zones:
            df = pd.DataFrame(top_zones, columns=['Zone ID', 'Count'])
            df['Zone'] = df['Zone ID'].apply(lambda x: zone_lookup.get_zone_name(int(x)))
            df['Count'] = df['Count'].astype(int)
            df = df.sort_values('Count', ascending=True)
            fig = px.bar(df, x='Count', y='Zone', orientation='h', color='Count', color_continuous_scale='Reds')
            fig.update_layout(template="plotly_dark", height=350, showlegend=False, yaxis_title="")
            st.plotly_chart(fig, width='stretch')
        else:
            st.info("No fraud zone data")
    
    st.caption(f"Updated: {datetime.now().strftime('%H:%M:%S')}")
    if auto_refresh:
        realtime_interval = 250 if st.session_state.get('realtime', False) else refresh_rate * 1000
        st_autorefresh(interval=realtime_interval, key='fraud_home_autorefresh')

# ==================== MAPS ====================
elif page == "🗺️ Maps":
    import pandas as pd
    import plotly.express as px
    import plotly.graph_objects as go
    from datetime import datetime
    import hashlib
    from utils.redis_client import RedisClient
    from utils.zone_lookup import ZoneLookup
    
    # Back button
    if st.button("← Back to Home", key="back_maps"):
        st.session_state['nav'] = "🏠 Home"
        st.rerun()
    
    st.title("🗺️ NYC Taxi Maps")
    redis_client = RedisClient()
    zone_lookup = ZoneLookup()
    
    map_type = st.sidebar.selectbox("Choose Map", ["Trip Routes", "Pickup Hotspots", "Dropoff Hotspots", "Fraud Routes", "Zone Activity"])
    auto_refresh = st.sidebar.checkbox("Auto Refresh", value=False)
    
    ZONE_COORDS = {132: (40.6413, -73.7781), 138: (40.7769, -73.8740), 161: (40.7580, -73.9855),
        162: (40.7549, -73.9679), 163: (40.7505, -73.9934), 164: (40.7614, -73.9776), 90: (40.7400, -73.9920)}
    
    def get_coord(zone_id):
        if zone_id in ZONE_COORDS:
            return ZONE_COORDS[zone_id]
        h = int(hashlib.md5(str(zone_id).encode()).hexdigest()[:8], 16)
        return (40.7128 + (h % 1000) / 15000 - 0.033, -74.0060 + (h % 1500) / 15000 - 0.05)


    def generate_path(start_coords, end_coords, duration=150):
        """Generate a linearly interpolated path between two coordinates.
        start_coords and end_coords are (lat, lon). Returns dict with path (list of [lon, lat])
        and timestamps for animation.
        """
        path = []
        timestamps = []
        if duration < 2:
            duration = 2
        for i in range(duration):
            t = i / float(duration - 1)
            lat = start_coords[0] + (end_coords[0] - start_coords[0]) * t
            lon = start_coords[1] + (end_coords[1] - start_coords[1]) * t
            path.append([lon, lat])
            timestamps.append(i)
        return {"path": path, "timestamps": timestamps}
    
    zone_stats = redis_client.get_zone_stats()
    config = {'scrollZoom': True, 'displayModeBar': True}
    
    if map_type == "Trip Routes":
        # Animated or static trip routes
        animated = st.sidebar.checkbox("Animated Trip Routes (PyDeck)", value=False)
        if animated:
            duration = st.sidebar.slider("Animation Duration (steps)", 50, 300, 150)
            trail_length = st.sidebar.slider("Trail Length", 10, 600, 300)
            autoplay = st.sidebar.checkbox("Autoplay", value=True)
            if autoplay:
                st_autorefresh(interval=500, key='dashboard_deck_autorefresh')
        if animated:
            st.subheader("🚖 Animated Trip Routes (PyDeck)")
            if zone_stats:
                pickup_zones = zone_stats.get('pickup', {})
                dropoff_zones = zone_stats.get('dropoff', {})
                top_pickups = sorted(pickup_zones.items(), key=lambda x: int(x[1]), reverse=True)[:20]
                top_dropoffs = sorted(dropoff_zones.items(), key=lambda x: int(x[1]), reverse=True)[:20]
                trips_data = []
                for ((pu_zone, _), (do_zone, _)) in zip(top_pickups, top_dropoffs):
                    pu_lat, pu_lon = get_coord(int(pu_zone))
                    do_lat, do_lon = get_coord(int(do_zone))
                    trip = generate_path((pu_lat, pu_lon), (do_lat, do_lon), duration=150)
                    trips_data.append(trip)
                if trips_data:
                    try:
                        layer = pdk.Layer(
                            "TripsLayer",
                            trips_data,
                            get_path="path",
                            get_timestamps="timestamps",
                            get_color=[255, 80, 80],
                            opacity=0.8,
                            width_min_pixels=6,
                            rounded=True,
                            trail_length=trail_length,
                            current_time=int(time.time()) % duration if autoplay else st.sidebar.slider('Current Time', 0, duration - 1, 0),
                        )
                        # Add start and end scatter layers for context
                        start_points = [{'lon': p['path'][0][0], 'lat': p['path'][0][1]} for p in trips_data]
                        end_points = [{'lon': p['path'][-1][0], 'lat': p['path'][-1][1]} for p in trips_data]
                        start_layer = pdk.Layer("ScatterplotLayer", start_points, get_position=['lon', 'lat'], get_radius=200, get_fill_color=[0,255,0])
                        end_layer = pdk.Layer("ScatterplotLayer", end_points, get_position=['lon', 'lat'], get_radius=200, get_fill_color=[255,0,0])
                        view_state = pdk.ViewState(latitude=40.7580, longitude=-73.9855, zoom=11, pitch=45, bearing=0)
                        r = pdk.Deck(layers=[layer, start_layer, end_layer], initial_view_state=view_state, map_style="carto-darkmatter", tooltip={"text": "Moving Taxi"})
                        st.pydeck_chart(r, width='stretch')
                    except Exception as e:
                        st.error(f"Could not render animated routes: {e}")
                else:
                    st.info("No trips to animate yet")
        else:
            if zone_stats:
                fig = go.Figure()
                pickup_zones = zone_stats.get('pickup', {})
                dropoff_zones = zone_stats.get('dropoff', {})
                top_pickups = sorted(pickup_zones.items(), key=lambda x: int(x[1]), reverse=True)[:10]
                top_dropoffs = sorted(dropoff_zones.items(), key=lambda x: int(x[1]), reverse=True)[:10]
                max_count = max([int(x[1]) for x in top_pickups + top_dropoffs] or [1])
                for i, ((pu_zone, pu_count), (do_zone, do_count)) in enumerate(zip(top_pickups, top_dropoffs)):
                    pu_coord, do_coord = get_coord(int(pu_zone)), get_coord(int(do_zone))
                    width_px = int(2 + (min(int(pu_count), int(do_count)) / max_count) * 10)
                    fig.add_trace(go.Scattermapbox(mode='lines', lon=[pu_coord[1], do_coord[1]], lat=[pu_coord[0], do_coord[0]], line=dict(width=width_px, color='#ff4444'), showlegend=False))
                    # add endpoints: start (green) and end (red)
                    fig.add_trace(go.Scattermapbox(mode='markers', lon=[pu_coord[1]], lat=[pu_coord[0]], marker=dict(size=8, color='#00ff00'), hovertext=[f"Start: {pu_zone} ({pu_count})"]))
                    fig.add_trace(go.Scattermapbox(mode='markers', lon=[do_coord[1]], lat=[do_coord[0]], marker=dict(size=8, color='#ff4444'), hovertext=[f"End: {do_zone} ({do_count})"]))
                fig.update_layout(mapbox=dict(style='carto-darkmatter', center=dict(lat=40.7580, lon=-73.9855), zoom=10), height=600, margin={"r":0,"t":0,"l":0,"b":0})
                st.plotly_chart(fig, width='stretch', config=config)
            else:
                st.info("No trip data yet")
    
    elif map_type == "Pickup Hotspots":
        if zone_stats and 'pickup' in zone_stats:
            data = [{'zone': zone_lookup.get_zone_name(int(z)), 'count': int(c), 'lat': get_coord(int(z))[0], 'lon': get_coord(int(z))[1]} for z, c in zone_stats['pickup'].items()]
            df = pd.DataFrame(data)
            fig = px.scatter_mapbox(
                df,
                lat='lat',
                lon='lon',
                size='count',
                color='count',
                hover_name='zone',
                color_continuous_scale='Reds',
                size_max=40,
                zoom=10,
                center={"lat": 40.7580, "lon": -73.9855}
            )
            # Clarify colorbar and ensure consistent map style
            fig.update_traces(marker=dict(showscale=True), selector=dict(mode='markers'))
            fig.update_coloraxes(colorbar_title="Pickup count")
            fig.update_layout(mapbox_style='carto-darkmatter', height=600, margin={"r":0,"t":0,"l":0,"b":0})
            st.plotly_chart(fig, width='stretch', config=config)
        else:
            st.info("No pickup data yet")
    
    elif map_type == "Dropoff Hotspots":
        if zone_stats and 'dropoff' in zone_stats:
            data = [{'zone': zone_lookup.get_zone_name(int(z)), 'count': int(c), 'lat': get_coord(int(z))[0], 'lon': get_coord(int(z))[1]} for z, c in zone_stats['dropoff'].items()]
            df = pd.DataFrame(data)
            fig = px.scatter_mapbox(df, lat='lat', lon='lon', size='count', color='count', hover_name='zone', color_continuous_scale='Reds', size_max=40, zoom=10, center={"lat": 40.7580, "lon": -73.9855})
            fig.update_layout(mapbox_style='carto-darkmatter', height=600, margin={"r":0,"t":0,"l":0,"b":0})
            st.plotly_chart(fig, width='stretch', config=config)
        else:
            st.info("No dropoff data yet")
    
    elif map_type == "Fraud Routes":
        alerts = redis_client.get_fraud_alerts()
        if alerts:
            fig = go.Figure()
            for alert in alerts:
                pu, do = alert.get('PULocationID', 1), alert.get('DOLocationID', 1)
                score = alert.get('fraud_score', 0)
                pu_coord, do_coord = get_coord(pu), get_coord(do)
                color = 'red' if score >= 70 else 'orange' if score >= 50 else 'yellow'
                fig.add_trace(go.Scattermapbox(mode='lines', lon=[pu_coord[1], do_coord[1]], lat=[pu_coord[0], do_coord[0]], line=dict(width=3, color=color), showlegend=False))
            fig.update_layout(mapbox=dict(style='carto-darkmatter', center=dict(lat=40.7580, lon=-73.9855), zoom=10), height=600, margin={"r":0,"t":0,"l":0,"b":0})
            st.plotly_chart(fig, width='stretch', config=config)
        else:
            st.info("No fraud alerts yet")
    
    elif map_type == "Zone Activity":
        if zone_stats:
            pickup_zones = zone_stats.get('pickup', {})
            dropoff_zones = zone_stats.get('dropoff', {})
            all_zones = set(pickup_zones.keys()) | set(dropoff_zones.keys())
            data = [{'zone': zone_lookup.get_zone_name(int(z)), 'total': int(pickup_zones.get(z, 0)) + int(dropoff_zones.get(z, 0)), 'lat': get_coord(int(z))[0], 'lon': get_coord(int(z))[1]} for z in all_zones]
            df = pd.DataFrame(data)
            fig = px.scatter_mapbox(df, lat='lat', lon='lon', size='total', color='total', hover_name='zone', color_continuous_scale='Turbo', size_max=45, zoom=10, center={"lat": 40.7580, "lon": -73.9855})
            fig.update_layout(mapbox_style='carto-darkmatter', height=600, margin={"r":0,"t":0,"l":0,"b":0})
            st.plotly_chart(fig, width='stretch', config=config)
        else:
            st.info("No zone data yet")
    
    st.caption(f"Updated: {datetime.now().strftime('%H:%M:%S')}")
    if auto_refresh:
        realtime_interval = 250 if st.session_state.get('realtime', False) else 5000
        st_autorefresh(interval=realtime_interval, key='maps_autorefresh')

st.markdown("---")
st.caption("TaxiPulse - NYC Real-Time Analytics | Apache Kafka • Apache Spark • Redis • FastAPI")
