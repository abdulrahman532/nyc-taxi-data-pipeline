# 🚕 NYC Taxi Real-Time Streaming Pipeline

A production-ready real-time data streaming pipeline for NYC Taxi trip data with fraud detection, interactive analytics dashboard, and geographic visualizations.

![Architecture](https://img.shields.io/badge/Architecture-Microservices-blue)
![Kafka](https://img.shields.io/badge/Kafka-4.1.1-orange)
![Spark](https://img.shields.io/badge/Spark-4.0.1-yellow)
![Python](https://img.shields.io/badge/Python-3.12-green)

---

## 📋 Table of Contents

- [Architecture Overview](#-architecture-overview)
- [Technology Stack](#-technology-stack)
- [Quick Start](#-quick-start)
- [Services & Ports](#-services--ports)
- [Dashboard Guide](#-dashboard-guide)
- [Maps Visualization](#-maps-visualization)
- [API Reference](#-api-reference)
- [Fraud Detection](#-fraud-detection)
- [External Access (ngrok)](#-external-access-ngrok)
- [Redis Data Schema](#-redis-data-schema)
- [Troubleshooting](#-troubleshooting)
- [Project Structure](#-project-structure)

---

## 🏗️ Architecture Overview

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Data Source   │────▶│    FastAPI      │────▶│     Kafka       │
│  (NYC Taxi API) │     │   (Producer)    │     │   (4.1.1)       │
└─────────────────┘     └─────────────────┘     └────────┬────────┘
                                                         │
                              ┌──────────────────────────┘
                              ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Streamlit     │◀────│     Redis       │◀────│  Spark Streaming│
│   Dashboard     │     │   (7-alpine)    │     │   (4.0.1)       │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                                               │
        ▼                                               ▼
┌─────────────────┐                             ┌─────────────────┐
│  3 Pages:       │                             │ Fraud Detector  │
│  - Analytics    │                             │ 15+ Rules       │
│  - Fraud Monitor│                             └─────────────────┘
│  - Maps (6 types)│
└─────────────────┘
```

### Data Flow

1. **Ingestion**: Trip data arrives via REST API (FastAPI on port 8000)
2. **Streaming**: Data published to Kafka topic `nyc-taxi-trips`
3. **Processing**: Spark Structured Streaming consumes and processes in real-time
4. **Fraud Detection**: Real-time fraud scoring with 15+ indicators
5. **Storage**: Metrics, alerts, and zone stats stored in Redis
6. **Visualization**: Live dashboard with charts, maps, and fraud monitoring

---

## 🛠️ Technology Stack

### Core Technologies

| Component | Technology | Version |
|-----------|------------|---------|
| Message Broker | Apache Kafka (KRaft mode) | **4.1.1** |
| Stream Processing | Apache Spark | **4.0.1** |
| API Server | FastAPI | 0.115.6+ |
| Cache/Storage | Redis | 7-alpine |
| Dashboard | Streamlit | 1.41.1+ |
| Visualization | Plotly | 5.24.1+ |
| Language | Python | 3.12 |
| Container Runtime | Docker Compose | Latest |

### Python Packages

```
pandas>=2.2.3
pyarrow>=18.1.0
redis>=5.2.1
kafka-python-ng>=2.2.3
pyspark>=3.5.4
fastapi>=0.115.6
uvicorn>=0.34.0
streamlit>=1.41.1
plotly>=5.24.1
httpx>=0.28.1
```

---

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose installed
- 8GB+ RAM recommended
- Available ports: 6379, 7077, 8000, 8080, 8081, 8082, 8501, 9092

### 1. Start All Services

```bash
cd streaming/docker
docker compose up -d --build
```

### 2. Verify Services

```bash
docker compose ps
```

All **9 services** should be running and healthy.

### 3. Access Dashboard

Open http://localhost:8501

### 4. Send Test Data

```bash
# Quick test
curl -X POST http://localhost:8000/api/v1/trips \
  -H "Content-Type: application/json" \
  -d '{
    "VendorID": 1,
    "tpep_pickup_datetime": "2025-11-27T10:30:00",
    "tpep_dropoff_datetime": "2025-11-27T10:45:00",
    "passenger_count": 2,
    "trip_distance": 3.5,
    "PULocationID": 161,
    "DOLocationID": 234,
    "payment_type": 1,
    "fare_amount": 15.50,
    "tip_amount": 3.00,
    "total_amount": 20.30
  }'
```

---

## 🔌 Services & Ports

| Service | Port | Description | Health Check |
|---------|------|-------------|--------------|
| **Kafka** | 9092, 29092 | Message broker (KRaft mode) | ✅ |
| **Spark Master** | 7077, 8081 | Spark cluster manager | ✅ |
| **Spark Worker** | 8082 | Spark executor | - |
| **Spark Job** | - | Fraud detector processor | - |
| **Redis** | 6379 | Metrics cache | ✅ |
| **FastAPI** | 8000 | REST API server | ✅ |
| **Dashboard** | 8501 | Streamlit UI | ✅ |
| **Kafka UI** | 8080 | Kafka management | - |

### Quick Access URLs

| Service | URL |
|---------|-----|
| 🖥️ Dashboard | http://localhost:8501 |
| 📖 API Docs | http://localhost:8000/docs |
| ❤️ API Health | http://localhost:8000/health |
| 📊 Kafka UI | http://localhost:8080 |
| ⚡ Spark Master | http://localhost:8081 |

---

## 📊 Dashboard Guide

The dashboard has **3 main pages**:

### 1. 📊 Live Analytics

Real-time trip metrics and visualizations.

| Chart | Type | Description |
|-------|------|-------------|
| Trips by Hour | Line Chart | Hourly trip count trend |
| Revenue by Hour | Bar Chart | Hourly revenue |
| Payment Types | Pie Chart | Credit vs Cash distribution |
| Vendor Stats | Pie Chart | Vendor distribution |
| Top Pickup Zones | Bar Chart | Busiest pickup areas |
| Top Dropoff Zones | Bar Chart | Popular destinations |

**Features:**
- Auto-refresh (configurable 1-30 seconds)
- Dark theme
- Interactive charts (zoom, hover, pan)

### 2. 🔍 Fraud Monitor

Real-time fraud detection and alerts.

| Component | Description |
|-----------|-------------|
| Metrics Cards | Total alerts, High/Medium/Low risk counts |
| Fraud Timeline | Line chart with fraud scores over time |
| Top Fraud Zones | Horizontal bar chart |
| Fraud Indicators | Common fraud flags breakdown |

**Features:**
- Minimum fraud score filter
- Color-coded risk levels (Red/Orange/Yellow)
- Live updating

### 3. 🗺️ Maps

**6 different map visualizations** - select from sidebar:

| Map | Icon | Description |
|-----|------|-------------|
| Trip Routes | 🚗 | Lines between top pickup/dropoff zones |
| Pickup Hotspots | 📍 | Bubble map of pickup locations |
| Dropoff Hotspots | 📍 | Bubble map of dropoff locations |
| Fraud Routes | 🔴 | Fraud trips with color-coded risk |
| Revenue by Zone | 💰 | Zone revenue visualization |
| Zone Activity | 📊 | Combined activity heatmap |

**Map Features:**
- **Height**: 800px (large visualization)
- **Style**: Dark theme (carto-darkmatter)
- **Interactive**: Zoom, pan, hover tooltips
- **Auto-refresh**: Optional (default off for maps)

---

## 🗺️ Maps Visualization

### Zone Coordinates

The system includes **60+ NYC taxi zone coordinates** for accurate mapping:

```python
ZONE_COORDS = {
    132: (40.6413, -73.7781),  # JFK Airport
    138: (40.7769, -73.8740),  # LaGuardia Airport
    161: (40.7580, -73.9855),  # Midtown Center
    162: (40.7549, -73.9679),  # Midtown East
    163: (40.7505, -73.9934),  # Midtown North
    164: (40.7614, -73.9776),  # Midtown South
    230: (40.7484, -73.9967),  # Times Sq/Theatre District
    234: (40.7527, -73.9712),  # UN/Turtle Bay
    # ... and more
}
```

### Map Colors

| Element | Color | Meaning |
|---------|-------|---------|
| Pickup markers | 🟢 Green | Pickup locations |
| Dropoff markers | 🔴 Red | Dropoff locations |
| Route lines | Various | Trip connections |
| Fraud High Risk | 🔴 Red | Score 70+ |
| Fraud Medium | 🟠 Orange | Score 50-69 |
| Fraud Low | 🟡 Yellow | Score <50 |

---

## 📡 API Reference

### Endpoints

| Method | Endpoint | Description | Response |
|--------|----------|-------------|----------|
| GET | `/` | Welcome message | 200 |
| GET | `/health` | Health check | 200 |
| GET | `/api/v1/status` | Detailed status | 200 |
| POST | `/api/v1/trips` | Submit trip | **201** |
| POST | `/api/v1/trips/batch` | Submit multiple | 201 |

### Trip Schema

```json
{
  "VendorID": 1,                              // Required: 1, 2, 6, or 7
  "tpep_pickup_datetime": "2025-11-27T10:30:00",
  "tpep_dropoff_datetime": "2025-11-27T10:45:00",
  "passenger_count": 2,                       // 0-9
  "trip_distance": 3.5,                       // miles
  "PULocationID": 161,                        // 1-265
  "DOLocationID": 234,                        // 1-265
  "payment_type": 1,                          // 1=Credit, 2=Cash
  "fare_amount": 15.50,
  "tip_amount": 3.00,
  "total_amount": 20.30,
  "extra": 0.0,                               // Optional
  "mta_tax": 0.5,                             // Optional
  "tolls_amount": 0.0,                        // Optional
  "airport_fee": 0.0,                         // Optional
  "congestion_surcharge": 2.5                 // Optional
}
```

### Response Example

```json
{
  "status": "success",
  "message": "Trip received",
  "trip_id": "7d05a844-14d6-48fb-ad61-c4b84dc0b65b",
  "timestamp": "2025-11-27T10:30:00.123456"
}
```

---

## 🔴 Fraud Detection

### Fraud Indicators (15+ Rules)

| Flag | Score | Condition |
|------|-------|-----------|
| `zero_distance` | +30 | Distance = 0 but fare > $10 |
| `extreme_fare` | +25 | Fare > $200 or < $2.50 |
| `impossible_speed` | +30 | Speed > 80 mph |
| `long_duration` | +20 | Trip > 3 hours |
| `suspicious_tip` | +15 | Tip > 100% of fare |
| `night_long_trip` | +10 | Night trip > 1 hour |
| `airport_anomaly` | +15 | Airport zone unusual fare |
| `stationary_trip` | +25 | Speed < 2 mph for > 10 min |
| `fare_too_high` | +20 | Fare > $10.50/mile |
| `tip_exceeds_fare` | +25 | Tip > Fare amount |
| `same_location_high_fare` | +25 | Same pickup/dropoff, high fare |
| `fake_airport_fee` | +20 | Airport fee from non-airport |
| `night_cash_trip` | +15 | Night + Cash payment |
| `fake_jfk_rate` | +20 | JFK rate from non-JFK location |
| `voided_trip` | +20 | Payment type = voided |

### Risk Levels

| Level | Score | Color | Action |
|-------|-------|-------|--------|
| Normal | 0-29 | ✅ Green | None |
| Low Risk | 30-49 | 🟡 Yellow | Monitor |
| Medium Risk | 50-69 | 🟠 Orange | Review |
| High Risk | 70+ | 🔴 Red | Alert |

---

## 🌐 External Access (ngrok)

### Setup ngrok

```bash
# Install
curl -sSL https://ngrok-agent.s3.amazonaws.com/ngrok.asc \
  | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
echo "deb https://ngrok-agent.s3.amazonaws.com buster main" \
  | sudo tee /etc/apt/sources.list.d/ngrok.list
sudo apt update && sudo apt install ngrok

# Authenticate (get token from ngrok.com)
ngrok config add-authtoken YOUR_TOKEN

# Expose API
ngrok http 8000
```

### Stream Real Data (External Users)

Download and run:

```bash
# Download script
curl -O https://raw.githubusercontent.com/abdulrahman532/nyc-taxi-data-pipeline/main/streaming/simulator/stream_from_parquet.py

# Install dependencies
pip install requests pandas pyarrow

# Stream to your API
python stream_from_parquet.py \
  --api-url "https://your-url.ngrok-free.dev/api/v1/trips" \
  --rate 5 \
  --count 1000
```

**Note:** The script automatically accepts status codes **200 AND 201**.

---

## 📦 Redis Data Schema

### Daily Metrics

```
metrics:{date}:trips           → Total trips count
metrics:{date}:revenue         → Total revenue
metrics:{date}:fraud_alerts    → Fraud alert count
metrics:{date}:day_trips       → Daytime trips
metrics:{date}:night_trips     → Nighttime trips
```

### Hourly Stats

```
metrics:{date}:hourly:trips    → Hash: hour → count
metrics:{date}:hourly:revenue  → Hash: hour → revenue
```

### Zone Statistics

```
stats:pickup_zones             → Sorted set: zone_id → count
stats:dropoff_zones            → Sorted set: zone_id → count
stats:revenue_by_zone          → Sorted set: zone_id → revenue
```

### Payment & Vendor Stats

```
stats:{date}:payment_types     → Hash: type → count
stats:{date}:vendors           → Hash: vendor_id → count
```

### Fraud Data

```
fraud:alerts:{date}            → List of fraud alert JSONs
fraud:by_zone                  → Sorted set: zone_id → fraud_count
fraud:by_route                 → Sorted set: route → fraud_count
```

---

## 🔧 Troubleshooting

### Check Service Status

```bash
cd streaming/docker
docker compose ps
docker compose logs [service_name]
```

### Common Issues

| Issue | Solution |
|-------|----------|
| API Connection Error | Check `docker compose ps fastapi` |
| Dashboard No Data | Run `docker exec redis redis-cli FLUSHALL` |
| Maps Not Loading | Rebuild: `docker compose build dashboard` |
| Spark Job Failing | Check: `docker compose logs spark-job` |
| Kafka Issues | Check: `docker compose logs kafka` |

### Restart All Services

```bash
docker compose down
docker compose up -d --build
```

### Health Checks

```bash
# API
curl http://localhost:8000/health

# Redis
docker exec redis redis-cli ping

# Kafka topics
docker exec kafka /opt/kafka/bin/kafka-topics.sh \
  --bootstrap-server localhost:9092 --list
```

---

## 📁 Project Structure

```
streaming/
├── api/                        # FastAPI Server
│   ├── main.py                # API endpoints
│   ├── kafka_producer.py      # Kafka producer
│   ├── schemas.py             # Pydantic models
│   ├── Dockerfile
│   └── requirements.txt
│
├── spark/                      # Spark Streaming
│   ├── fraud_detector.py      # Main processor + fraud detection
│   ├── Dockerfile
│   ├── Dockerfile.worker
│   └── requirements.txt
│
├── dashboard/                  # Streamlit Dashboard
│   ├── app.py                 # Main entry
│   ├── pages/
│   │   ├── 1_📊_Live_Analytics.py   # Charts & metrics
│   │   ├── 2_🔍_Fraud_Monitor.py    # Fraud alerts
│   │   └── 3_🗺️_Maps.py            # 6 map types
│   ├── utils/
│   │   ├── redis_client.py    # Redis wrapper
│   │   └── zone_lookup.py     # Zone name lookup
│   ├── data/
│   │   └── taxi_zone_lookup.csv
│   ├── Dockerfile
│   └── requirements.txt
│
├── simulator/                  # Test Data
│   ├── send_trips.py          # Simple generator
│   ├── stream_from_parquet.py # Real data streamer
│   └── requirements.txt
│
├── docker/                     # Docker Config
│   ├── docker-compose.yml     # All 9 services
│   └── KAFKA_KRAFT_DOCUMENTATION.md
│
└── README.md                   # This file
```

---

## 📈 Performance

| Metric | Value |
|--------|-------|
| Sustained Rate | 50+ trips/second |
| Peak Burst | 100+ trips/second |
| End-to-End Latency | < 3 seconds |
| Memory Usage | ~4GB (all services) |
| Disk Usage | ~2GB (images) |

---

## 🔑 Key Features

✅ **Kafka 4.1.1 KRaft Mode** - No Zookeeper needed  
✅ **Spark 4.0.1** - Latest stream processing  
✅ **Real-time Dashboard** - 3-second refresh  
✅ **6 Map Types** - Interactive geographic viz  
✅ **15+ Fraud Rules** - Comprehensive detection  
✅ **Docker Compose** - One command deployment  
✅ **ngrok Support** - External access ready  

---

## 👨‍💻 Author

**Abdul Rahman**
- GitHub: [@abdulrahman532](https://github.com/abdulrahman532)
- Repository: [nyc-taxi-data-pipeline](https://github.com/abdulrahman532/nyc-taxi-data-pipeline)

---

*📅 Last Updated: November 27, 2025*
