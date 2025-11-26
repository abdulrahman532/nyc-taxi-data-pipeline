# 🚕 NYC Taxi Real-Time Streaming Pipeline

Real-time taxi trip analytics with fraud detection using Apache Kafka, Spark Streaming, and Streamlit.

## 🏗️ Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Taxi App   │────▶│   FastAPI   │────▶│    Kafka    │────▶│    Spark    │────▶│   Redis     │
│  (Webhook)  │     │   Server    │     │   Broker    │     │  Streaming  │     │   Cache     │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
                                                                                       │
                                                                                       ▼
                                                                                ┌─────────────┐
                                                                                │  Streamlit  │
                                                                                │  Dashboard  │
                                                                                └─────────────┘
```

## 📁 Project Structure

```
streaming/
├── docker/
│   └── docker-compose.yml      # Kafka, Redis, Zookeeper, Kafka UI
├── api/
│   ├── main.py                 # FastAPI webhook server
│   ├── schemas.py              # Pydantic models
│   ├── kafka_producer.py       # Kafka producer client
│   └── requirements.txt
├── spark/
│   ├── fraud_detector.py       # Spark Streaming fraud detection
│   └── requirements.txt
├── dashboard/
│   ├── app.py                  # Streamlit main app
│   ├── pages/
│   │   ├── 1_📊_Live_Overview.py
│   │   └── 2_🕵️_Fraud_Detection.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── redis_client.py
│   │   └── zone_lookup.py
│   ├── data/
│   │   └── taxi_zone_lookup.csv
│   └── requirements.txt
├── simulator/
│   ├── send_trips.py           # Test data generator
│   └── requirements.txt
└── README.md
```

## 🚀 Quick Start

### 1. Start Infrastructure (Kafka + Redis)

```bash
cd streaming/docker
docker-compose up -d
```

This starts:
- **Zookeeper** (port 2181)
- **Kafka** (port 9092)
- **Redis** (port 6379)
- **Kafka UI** (port 8080)

### 2. Start FastAPI Server

```bash
cd streaming/api
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. (Optional) Expose with ngrok

```bash
ngrok http 8000
```

### 4. Start Spark Streaming

```bash
cd streaming/spark
pip install -r requirements.txt
spark-submit --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0 fraud_detector.py
```

### 5. Start Dashboard

```bash
cd streaming/dashboard
pip install -r requirements.txt
streamlit run app.py
```

### 6. Test with Simulator

```bash
cd streaming/simulator
pip install -r requirements.txt
python send_trips.py --api-url http://localhost:8000/api/v1/trips
```

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Health check |
| `GET` | `/health` | Detailed health status |
| `POST` | `/api/v1/trips` | Submit single trip |
| `POST` | `/api/v1/trips/batch` | Submit multiple trips |

### Example Request

```bash
curl -X POST http://localhost:8000/api/v1/trips \
  -H "Content-Type: application/json" \
  -d '{
    "VendorID": 1,
    "tpep_pickup_datetime": "2024-01-15T10:30:00",
    "tpep_dropoff_datetime": "2024-01-15T10:45:00",
    "passenger_count": 2,
    "trip_distance": 3.5,
    "PULocationID": 142,
    "DOLocationID": 236,
    "payment_type": 1,
    "fare_amount": 15.50,
    "total_amount": 20.30
  }'
```

## 🕵️ Fraud Detection Rules

The system detects fraud using 15+ rules:

| Rule | Score | Description |
|------|-------|-------------|
| `impossible_speed` | +30 | Speed > 100 mph |
| `stationary_trip` | +25 | Speed < 2 mph for > 10 min |
| `zero_distance_with_fare` | +20 | No distance but charged |
| `fare_too_high` | +20 | Fare > $10.50/mile |
| `tip_exceeds_fare` | +25 | Tip > Fare amount |
| `same_location_high_fare` | +25 | Same pickup/dropoff, high fare |
| `fake_airport_fee` | +20 | Airport fee from non-airport |
| `night_cash_trip` | +15 | Night + Cash payment |
| `fake_jfk_rate` | +20 | JFK rate from non-JFK location |
| `voided_trip` | +20 | Payment type = voided |

**Fraud Score Thresholds:**
- 🟢 0-49: Normal
- 🟡 50-69: Suspicious
- 🔴 70-100: High Risk

## 📊 Dashboard Pages

### 1. 📈 Live Overview
- Real-time trip count
- Revenue tracking
- Fraud alerts count
- Day vs Night distribution
- Hourly trip charts

### 2. 🕵️ Fraud Detection
- High-risk alerts
- Top fraud zones
- Top fraud routes
- Recent fraud alerts table

## 🔧 Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `KAFKA_BOOTSTRAP_SERVERS` | `localhost:9092` | Kafka broker address |
| `KAFKA_TOPIC` | `nyc.taxi.trips.raw` | Kafka topic name |
| `REDIS_HOST` | `localhost` | Redis host |
| `REDIS_PORT` | `6379` | Redis port |

## 🐳 Docker Services

| Service | Port | Description |
|---------|------|-------------|
| Zookeeper | 2181 | Kafka coordination |
| Kafka | 9092, 29092 | Message broker |
| Redis | 6379 | Metrics cache |
| Kafka UI | 8080 | Web UI for Kafka |

## 📈 Metrics Stored in Redis

```
metrics:{date}:trips          # Daily trip count
metrics:{date}:revenue        # Daily revenue
metrics:{date}:fraud_alerts   # Daily fraud count
metrics:{date}:day_trips      # Day trips count
metrics:{date}:night_trips    # Night trips count
metrics:{date}:hourly:trips   # Hourly breakdown
fraud:alerts:{date}           # Recent fraud alerts
fraud:by_zone                 # Fraud count by zone
fraud:by_route                # Fraud count by route
```

## 🛠️ Troubleshooting

### Kafka not connecting
```bash
# Check if Kafka is running
docker ps | grep kafka

# Check Kafka logs
docker logs kafka
```

### Redis connection issues
```bash
# Test Redis connection
redis-cli ping
```

### Spark job failing
```bash
# Make sure Kafka packages are included
spark-submit --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0 fraud_detector.py
```

---

**Built with ❤️ for real-time taxi analytics**
