# External Client Ingestion Guide: NYC Taxi Streaming Pipeline

This guide details how external producers, edge devices, and client applications submit telemetry events to the NYC Taxi real-time streaming pipeline.

---

## Endpoint Configuration

The ingestion gateway exposes an HTTP REST endpoint accessible via local host or external tunneling (e.g., ngrok):

- **Local:** `http://localhost:8000/api/v1/trips`
- **Tunnel:** `https://<tunnel-subdomain>.ngrok-free.dev/api/v1/trips`
- **Batch Endpoint:** `https://<tunnel-subdomain>.ngrok-free.dev/api/v1/trips/batch`

---

## Schema Reference

### Required Fields

| Field | Type | Bounds / Allowed Values | Description |
|---|---|---|---|
| `VendorID` | Integer | `1`, `2`, `6`, `7` | TLC fleet vendor identifier |
| `tpep_pickup_datetime` | String | ISO 8601 format | Trip start timestamp |
| `tpep_dropoff_datetime` | String | ISO 8601 format | Trip conclusion timestamp |
| `passenger_count` | Integer | `0` to `9` | Number of vehicle occupants |
| `trip_distance` | Float | `>= 0.0` | Trip distance in statute miles |
| `PULocationID` | Integer | `1` to `265` | Pickup taxi zone LocationID |
| `DOLocationID` | Integer | `1` to `265` | Dropoff taxi zone LocationID |
| `payment_type` | Integer | `1` to `6` | Payment method code (1: Credit, 2: Cash) |
| `fare_amount` | Float | Real number | Metered base fare |
| `total_amount` | Float | Real number | Total transaction charge |

### Optional Fields

| Field | Type | Default | Description |
|---|---|---|---|
| `RatecodeID` | Integer | `1` | Rate calculation code (1: Standard, 2: JFK, etc.) |
| `tip_amount` | Float | `0.0` | Discretionary gratuity |
| `extra` | Float | `0.0` | Rush hour and overnight surcharges |
| `mta_tax` | Float | `0.5` | Standard MTA state tax |
| `tolls_amount` | Float | `0.0` | Bridge and highway tolls |
| `improvement_surcharge` | Float | `0.3` | Vehicle improvement surcharge |
| `congestion_surcharge` | Float | `0.0` | Congestion zone entry fee |
| `airport_fee` | Float | `0.0` | Airport pickup/dropoff access fee |

---

## Ingestion Methods

### 1. Python Request Example

```python
import requests

API_URL = "https://<tunnel-subdomain>.ngrok-free.dev/api/v1/trips"

payload = {
    "VendorID": 1,
    "tpep_pickup_datetime": "2025-11-26T14:30:00",
    "tpep_dropoff_datetime": "2025-11-26T14:45:00",
    "passenger_count": 2,
    "trip_distance": 3.5,
    "PULocationID": 142,
    "DOLocationID": 236,
    "payment_type": 1,
    "fare_amount": 15.50,
    "tip_amount": 3.00,
    "total_amount": 20.30
}

response = requests.post(API_URL, json=payload)
print(response.status_code, response.json())
```

### 2. cURL CLI Example

```bash
curl -X POST https://<tunnel-subdomain>.ngrok-free.dev/api/v1/trips \
  -H "Content-Type: application/json" \
  -d '{
    "VendorID": 1,
    "tpep_pickup_datetime": "2025-11-26T14:30:00",
    "tpep_dropoff_datetime": "2025-11-26T14:45:00",
    "passenger_count": 2,
    "trip_distance": 3.5,
    "PULocationID": 142,
    "DOLocationID": 236,
    "payment_type": 1,
    "fare_amount": 15.50,
    "tip_amount": 3.00,
    "total_amount": 20.30
  }'
```

### 3. High-Volume Parquet Replay

To stream historical TLC Parquet datasets through the ingestion pipeline:

```bash
pip install requests pandas pyarrow

python stream_from_parquet.py \
  --api-url "https://<tunnel-subdomain>.ngrok-free.dev/api/v1/trips" \
  --rate 10 \
  --count 1000
```

---

## Response Payloads

### Success Response (`201 Created`)

```json
{
  "status": "success",
  "message": "Trip received",
  "trip_id": "b491786a-aa0f-43ee-b81e-493dac13c338",
  "timestamp": "2025-11-26T21:07:20.450344"
}
```

### Validation Error (`422 Unprocessable Entity`)

```json
{
  "detail": [
    {
      "loc": ["body", "VendorID"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

## Anomaly Simulation Test Payload

To verify that the Spark streaming fraud engine actively flags suspicious patterns, transmit an event with synthetic anomaly attributes:

```json
{
  "VendorID": 1,
  "tpep_pickup_datetime": "2025-11-26T02:30:00",
  "tpep_dropoff_datetime": "2025-11-26T02:35:00",
  "passenger_count": 0,
  "trip_distance": 0.0,
  "PULocationID": 142,
  "DOLocationID": 142,
  "payment_type": 2,
  "fare_amount": 500.00,
  "tip_amount": 600.00,
  "total_amount": 1100.00
}
```

This event triggers multiple fraud flags (`zero_distance_with_fare`, `same_location_high_fare`, `tip_exceeds_fare`, `zero_passengers`), resulting in a score exceeding the threshold of 50 and routing to the active alert queue in Redis.
