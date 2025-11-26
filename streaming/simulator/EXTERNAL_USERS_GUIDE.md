# 📤 Send Data to NYC Taxi Pipeline

This guide is for external users who want to send taxi trip data to the streaming pipeline.

## 🔗 API Endpoint

Get the API URL from the pipeline owner. It will look like:
```
https://abc123.ngrok-free.dev/api/v1/trips
```

## 📋 Requirements

```bash
pip install requests
```

## 🚀 Quick Start

### Option 1: Simple Python Script

```python
import requests
from datetime import datetime

API_URL = "https://YOUR-NGROK-URL.ngrok-free.dev/api/v1/trips"

trip = {
    "VendorID": 1,
    "tpep_pickup_datetime": "2025-11-26T14:30:00",
    "tpep_dropoff_datetime": "2025-11-26T14:45:00",
    "passenger_count": 2,
    "trip_distance": 3.5,
    "PULocationID": 142,
    "DOLocationID": 236,
    "payment_type": 1,
    "fare_amount": 15.50,
    "total_amount": 20.30
}

response = requests.post(API_URL, json=trip)
print(response.json())
```

### Option 2: Using curl

```bash
curl -X POST https://YOUR-NGROK-URL.ngrok-free.dev/api/v1/trips \
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
    "total_amount": 20.30
  }'
```

### Option 3: Stream Real NYC Data

```bash
# Download the streamer script
pip install requests pandas pyarrow

# Run it (downloads ~50MB of real taxi data)
python stream_from_parquet.py --api-url https://YOUR-NGROK-URL.ngrok-free.dev/api/v1/trips
```

## 📝 Trip Schema

### Required Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `VendorID` | int | Vendor ID (1, 2, 6, or 7) | `1` |
| `tpep_pickup_datetime` | string | Pickup time (ISO format) | `"2025-11-26T14:30:00"` |
| `tpep_dropoff_datetime` | string | Dropoff time (ISO format) | `"2025-11-26T14:45:00"` |
| `passenger_count` | int | Number of passengers (0-9) | `2` |
| `trip_distance` | float | Distance in miles | `3.5` |
| `PULocationID` | int | Pickup zone (1-265) | `142` |
| `DOLocationID` | int | Dropoff zone (1-265) | `236` |
| `payment_type` | int | 1=Credit, 2=Cash, 3=No charge, 4=Dispute | `1` |
| `fare_amount` | float | Base fare in dollars | `15.50` |
| `total_amount` | float | Total charge in dollars | `20.30` |

### Optional Fields

| Field | Type | Description | Default |
|-------|------|-------------|---------|
| `RatecodeID` | int | Rate code (1-6) | `1` |
| `tip_amount` | float | Tip amount | `0.0` |
| `extra` | float | Extra charges | `0.0` |
| `mta_tax` | float | MTA tax | `0.5` |
| `tolls_amount` | float | Tolls | `0.0` |
| `improvement_surcharge` | float | Improvement surcharge | `0.3` |
| `congestion_surcharge` | float | Congestion surcharge | `0.0` |
| `airport_fee` | float | Airport fee | `0.0` |

## ✅ Response Format

### Success

```json
{
  "status": "success",
  "message": "Trip received",
  "trip_id": "b491786a-aa0f-43ee-b81e-493dac13c338",
  "timestamp": "2025-11-26T21:07:20.450344"
}
```

### Error

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

## 🔄 Batch Upload

Send multiple trips at once:

```python
import requests

API_URL = "https://YOUR-NGROK-URL.ngrok-free.dev/api/v1/trips/batch"

trips = [
    {
        "VendorID": 1,
        "tpep_pickup_datetime": "2025-11-26T14:30:00",
        "tpep_dropoff_datetime": "2025-11-26T14:45:00",
        "passenger_count": 2,
        "trip_distance": 3.5,
        "PULocationID": 142,
        "DOLocationID": 236,
        "payment_type": 1,
        "fare_amount": 15.50,
        "total_amount": 20.30
    },
    {
        "VendorID": 2,
        "tpep_pickup_datetime": "2025-11-26T15:00:00",
        "tpep_dropoff_datetime": "2025-11-26T15:20:00",
        "passenger_count": 1,
        "trip_distance": 5.2,
        "PULocationID": 100,
        "DOLocationID": 200,
        "payment_type": 2,
        "fare_amount": 22.00,
        "total_amount": 25.50
    }
]

response = requests.post(API_URL, json=trips)
print(response.json())
```

## 🎲 Random Trip Generator

```python
import requests
import random
from datetime import datetime, timedelta

API_URL = "https://YOUR-NGROK-URL.ngrok-free.dev/api/v1/trips"

def generate_random_trip():
    pickup = datetime.now() - timedelta(minutes=random.randint(5, 30))
    dropoff = pickup + timedelta(minutes=random.randint(5, 45))
    distance = round(random.uniform(0.5, 15.0), 2)
    fare = round(distance * random.uniform(2.0, 4.0) + 2.50, 2)
    
    return {
        "VendorID": random.choice([1, 2]),
        "tpep_pickup_datetime": pickup.isoformat(),
        "tpep_dropoff_datetime": dropoff.isoformat(),
        "passenger_count": random.randint(1, 4),
        "trip_distance": distance,
        "PULocationID": random.randint(1, 265),
        "DOLocationID": random.randint(1, 265),
        "payment_type": random.choice([1, 2]),
        "fare_amount": fare,
        "tip_amount": round(fare * random.uniform(0, 0.25), 2),
        "total_amount": round(fare * 1.15, 2)
    }

# Send 100 random trips
for i in range(100):
    trip = generate_random_trip()
    response = requests.post(API_URL, json=trip)
    print(f"Trip {i+1}: {response.json()['status']}")
```

## 🕵️ Test Fraud Detection

Send a suspicious trip to trigger fraud detection:

```python
import requests
from datetime import datetime

API_URL = "https://YOUR-NGROK-URL.ngrok-free.dev/api/v1/trips"

# This trip will be flagged as fraud!
# Reasons: zero distance, same pickup/dropoff, high fare, tip > fare, night time, cash
fraud_trip = {
    "VendorID": 1,
    "tpep_pickup_datetime": "2025-11-26T02:30:00",  # Night time
    "tpep_dropoff_datetime": "2025-11-26T02:35:00",
    "passenger_count": 0,
    "trip_distance": 0,                             # Zero distance
    "PULocationID": 142,
    "DOLocationID": 142,                            # Same location
    "payment_type": 2,                              # Cash
    "fare_amount": 500.00,                          # High fare
    "tip_amount": 600.00,                           # Tip > fare
    "total_amount": 1100.00
}

response = requests.post(API_URL, json=fraud_trip)
print(response.json())
```

## ❓ Troubleshooting

### Connection Error
- Check if the ngrok URL is correct
- Ask the pipeline owner if the server is running

### 422 Validation Error
- Check your JSON format
- Ensure all required fields are present
- Verify field types (int vs float vs string)

### Check API Health
```bash
curl https://YOUR-NGROK-URL.ngrok-free.dev/health
```

---

**Need help?** Contact the pipeline owner.
