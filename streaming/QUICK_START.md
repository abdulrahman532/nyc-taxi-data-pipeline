# Quick Start Guide: NYC Taxi Streaming Pipeline

A five-minute operational guide for launching and verifying the real-time streaming pipeline.

---

## Prerequisites

- Docker Engine 24.x+ and Docker Compose v2.x+
- Minimum 8 GB available system memory
- Available host ports: `6379`, `7077`, `8000`, `8080`, `8081`, `8082`, `8085`, `8501`, `9092`

---

## 1. Clone and Navigate

```bash
git clone https://github.com/abdulrahman532/nyc-taxi-data-pipeline.git
cd nyc-taxi-data-pipeline/streaming/docker
```

---

## 2. Build and Launch Infrastructure

Build container images and start all multi-container services in detached mode:

```bash
docker compose build
docker compose up -d
```

Verify service status:

```bash
docker compose ps
```

All services (`kafka`, `spark-master`, `spark-worker`, `spark-job`, `redis`, `fastapi`, `dashboard`, `kafka-ui`) should report healthy or running status.

---

## 3. Service Endpoints

| Service | Address | Description |
|---|---|---|
| TaxiPulse Dashboard | `http://localhost:8501` | Real-time Streamlit analytics and fraud monitor |
| Ingestion API Docs | `http://localhost:8000/docs` | Interactive Swagger documentation for trip ingestion |
| Kafka UI | `http://localhost:8085` | Topic, partition, and consumer group inspection |
| Spark Master UI | `http://localhost:8081` | Spark cluster allocation and active streaming job metrics |

---

## 4. Ingest Sample Trip Event

Submit a sample payload via cURL to test ingestion, Kafka publication, Spark processing, and Redis caching:

```bash
curl -X POST http://localhost:8000/api/v1/trips \
  -H "Content-Type: application/json" \
  -d '{
    "VendorID": 1,
    "tpep_pickup_datetime": "2025-12-01T10:30:00",
    "tpep_dropoff_datetime": "2025-12-01T10:45:00",
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

Expected response status: `201 Created` with a unique `trip_id`.

---

## 5. Troubleshooting & Operations

### Check Service Logs

```bash
# Stream logs across all services
docker compose logs -f

# Inspect Spark streaming job output
docker compose logs -f spark-job
```

### Port Conflicts

Identify processes occupying required ports:

```bash
sudo lsof -i -P -n | grep LISTEN | grep -E '(9092|8000|8501|6379|8085)'
```

### Flush Cache State

To reset Redis metrics and fraud alerts during local testing:

```bash
docker exec redis redis-cli FLUSHALL
```

### Tear Down Infrastructure

```bash
# Stop containers
docker compose down

# Stop containers and remove persistent volumes
docker compose down -v
```
