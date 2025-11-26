"""NYC Taxi Real-Time Dashboard"""

import streamlit as st

st.set_page_config(
    page_title="NYC Taxi Real-Time Dashboard",
    page_icon="🚕",
    layout="wide",
    initial_sidebar_state="expanded"
)

st. title("🚕 NYC Taxi Real-Time Dashboard")
st.markdown("---")

st.markdown("""
## Welcome to the NYC Taxi Real-Time Analytics Dashboard!

### 📊 Available Pages:
- **📈 Live Overview** - Real-time trip metrics and KPIs
- **🕵️ Fraud Detection** - Fraud alerts and analysis

### 🚀 Getting Started:
1.  Make sure all services are running (Kafka, Redis, Spark)
2. Start sending trips via the API
3. Watch the metrics update in real-time! 

Select a page from the sidebar to begin. 
""")

st.sidebar.success("Select a page above.")