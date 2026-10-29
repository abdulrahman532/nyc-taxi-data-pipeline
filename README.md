# NYC Taxi Data Pipeline: Hybrid Batch ELT & Real-Time Streaming Platform

A production-grade data engineering platform built for the New York City Taxi & Limousine Commission (TLC) dataset. The system integrates automated batch ELT ingestion into Snowflake using Apache Airflow and dbt with an event-driven real-time streaming pipeline powered by FastAPI, Apache Kafka (KRaft), Apache Spark Structured Streaming, Redis, and Streamlit.

---

## Architecture Overview

The platform is designed around two complementary data pipelines:

1. **Batch ELT Pipeline:** Ingests monthly high-volume Parquet archives from NYC TLC via AWS Lambda into AWS S3, stages data in Snowflake, and executes a multi-layer dbt medallion transformation model orchestrated by Apache Airflow.
2. **Real-Time Streaming Pipeline:** Ingests live ride event telemetry via a FastAPI webhook, streams events through Apache Kafka, executes fraud detection and anomaly scoring in Apache Spark Structured Streaming, persists aggregations in Redis, and serves a live analytical monitoring dashboard.

```
===================================================================================
                                BATCH ELT PIPELINE
===================================================================================
+------------------+       +---------------+       +------------------------------+
|  NYC TLC Public  | ----> |    AWS S3     | ----> |     Snowflake Data Cloud     |
|   Data Sources   |       |  Raw Storage  |       |   (Staging Tables & Views)   |
+------------------+       +---------------+       +--------------+---------------+
                                                                  |
                         +--------------------+                   |
                         |   Apache Airflow   | <-----------------+
                         |   (Orchestrator)   |
                         +---------+----------+
                                   |
                                   v
                         +--------------------+
                         |   dbt Core Model   |
                         |  - Staging Layer   |
                         |  - Dimensional Mart|
                         |  - 11 Insight Marts|
                         |  - One Big Table   |
                         +--------------------+

===================================================================================
                            REAL-TIME STREAMING PIPELINE
===================================================================================
+------------------+       +---------------+       +------------------------------+
|   Trip Telemetry | ----> |    FastAPI    | ----> |         Apache Kafka         |
|    Simulator     |       |    Webhook    |       |         (KRaft Mode)         |
+------------------+       +---------------+       +--------------+---------------+
                                                                  |
                                                                  v
+------------------+       +---------------+       +------------------------------+
|  Streamlit UI    | <---- |     Redis     | <---- |         Apache Spark         |
|   (TaxiPulse)    |       | In-Memory DB  |       |     Structured Streaming     |
|                  |       | (Alerts & KPIs|       |  (15+ Fraud Scoring Rules)   |
+------------------+       +---------------+       +------------------------------+
```

---

## Technical Specifications

| Subsystem | Technology | Function |
|---|---|---|
| Cloud Storage | Amazon Web Services (S3, Lambda) | Raw storage and serverless ingestion automation |
| Data Warehouse | Snowflake Data Cloud | Cloud analytical warehousing and columnar compute |
| Orchestration | Apache Airflow 2.x | Directed Acyclic Graph (DAG) scheduling and monitoring |
| Data Modeling | dbt Core (Snowflake Adapter) | Medallion modeling (Staging, Intermediate, Marts) |
| Message Broker | Apache Kafka (KRaft mode) | Distributed event log with zero ZooKeeper dependency |
| Stream Engine | Apache Spark 3.x (PySpark) | Low-latency stateful streaming and fraud evaluation |
| In-Memory Cache | Redis 7.x | Sub-millisecond metrics store and sliding window alerts |
| Ingestion API | FastAPI + Uvicorn | Schema-validated HTTP webhook for trip event ingestion |
| Monitoring UI | Streamlit + PyDeck | Real-time geospatial mapping and operational dashboards |
| Containerization | Docker & Docker Compose | Multi-container reproducible deployment |

---

## Batch Pipeline Architecture (ELT)

### Ingestion and Orchestration

Batch workflows are automated via three Apache Airflow DAGs located in `airflow/dags/`:

1. **`deploy_infrastructure_dag.py`**: Verifies and deploys AWS Lambda extraction functions responsible for querying upstream TLC endpoints and transferring Parquet files to AWS S3.
2. **`nyc_taxi_sync_dag.py`**: Manages state-aware ingestion from S3 into Snowflake staging tables, maintaining watermark records to avoid duplicate data transfer.
3. **`dbt_transformation_dag.py`**: Triggers dependent dbt transformations and asserts data contract integrity via automated test suites.

### dbt Medallion Data Modeling

The analytical schema in Snowflake is structured into distinct medallion tiers:

```
nyc_taxi_dbt/models/
├── staging/
│   ├── _sources.yml            # Source definitions and freshness constraints
│   ├── schema.yml              # Column assertions and schema tests
│   ├── stg_trips.sql           # Raw trip event normalization and casting
│   └── stg_zones.sql           # Taxi zone taxonomy lookup
├── intermediate/
│   └── int_trips_enhanced.sql  # Trip duration, speed, and fare feature generation
└── marts/
    ├── core/
    │   ├── dim_date.sql         # Temporal dimension with calendar attributes
    │   ├── dim_payment_types.sql# Normalized payment method dimension
    │   ├── dim_rate_codes.sql   # TLC rate code lookup dimension
    │   ├── dim_vendors.sql      # Fleet vendor dimension
    │   ├── dim_zones.sql        # Geographic borough and zone boundaries
    │   ├── fct_trips.sql        # Fact table keyed on dimensional surrogate keys
    │   └── obt_trips.sql        # One Big Table (OBT) denormalized for OLAP
    └── insights/
        ├── insight_airport_lifeline.sql   # Airport corridor traffic analysis
        ├── insight_anomaly_breakdown.sql  # Systematic operational outlier aggregation
        ├── insight_covid_recovery.sql     # Pre- and post-pandemic volume comparisons
        ├── insight_fee_impact.sql         # Impact of surcharge and congestion pricing
        ├── insight_industry_evolution.sql # Multi-year fleet performance trajectories
        ├── insight_manhattan_share.sql    # Intra-borough vs. peripheral travel trends
        ├── insight_payment_shift.sql      # Cash-to-card adoption metrics over time
        ├── insight_route_pricing.sql      # Per-mile revenue across popular corridors
        ├── insight_tipping_patterns.sql   # Spatial and temporal tip behavior
        ├── insight_uber_effect.sql        # Ride-share market competition trends
        └── insight_zone_heatmap.sql       # High-density origin-destination routing
```

### Data Quality Framework

Automated validation is enforced through singular and generic dbt tests:

- **`assert_valid_trip_duration.sql`**: Validates trip duration is strictly greater than 0 seconds and within physical operating bounds.
- **`assert_valid_speed.sql`**: Enforces average calculated speed cannot exceed physically plausible vehicle limits.
- **`assert_positive_fares.sql`**: Verifies core fare and metered revenue fields contain non-negative amounts.
- **`assert_pickup_before_dropoff.sql`**: Asserts temporal chronological sequence between pickup and dropoff timestamps.

---

## Real-Time Streaming Pipeline

### Event Flow and Ingestion

1. **Telemetry Simulation (`streaming/simulator/`)**: Reads historical Parquet partitions and streams realistic, timestamp-adjusted trip events to the ingestion endpoint.
2. **FastAPI Ingestion Gateway (`streaming/api/`)**: Validates inbound JSON payloads against Pydantic schemas (`schemas.py`) and publishes events directly to the Kafka topic `nyc.taxi.trips.raw`.

### Spark Streaming Fraud Detection Engine

The Spark engine (`streaming/spark/fraud_detector.py`) consumes raw telemetry from Kafka in micro-batches and runs a vectorized User-Defined Function (UDF) evaluating 15+ composite fraud and anomaly conditions:

| Detection Rule | Trigger Condition | Severity Score |
|---|---|---|
| `impossible_speed` | Average calculated speed > 100 mph | +30 |
| `stationary_trip` | Average speed < 2 mph for duration > 10 min | +25 |
| `same_location_high_fare` | Pickup zone equals dropoff zone with fare > $5.00 | +25 |
| `tip_exceeds_fare` | Tip amount strictly exceeds base fare | +25 |
| `zero_distance_with_fare` | Metered distance equals 0 with positive fare | +20 |
| `fake_airport_fee` | Airport surcharge applied outside JFK (132) or LGA (138) | +20 |
| `fake_jfk_rate` | Flat JFK rate code applied without touching zone 132 | +20 |
| `fare_too_high` | Calculated fare per mile > $10.50 / mile | +20 |
| `voided_trip` | Trip marked with voided or disputed payment status | +20 |
| `excessive_tip` | Credit card tip percentage > 50% of base fare | +15 |
| `too_many_passengers` | Passenger count exceeds vehicle maximum (> 6) | +15 |
| `negative_fare` | Total fare amount recorded below zero | +15 |
| `night_cash_trip` | Unmetered cash payment during late night hours | +10 |
| `night_high_tip` | Night trip tip percentage > 30% | +10 |
| `zero_passengers` | Zero passenger count recorded on active metered trip | +10 |

Events with an aggregate score greater than or equal to **50** are flagged as high-risk anomalies, categorized with specific flag tags, and dispatched to Redis for real-time triage.

### In-Memory Storage & TaxiPulse Dashboard

- **Redis**: Maintains rolling 7-day sorted sets for zone-level and route-level fraud rankings, time-series metrics counters, and historical incident lists.
- **TaxiPulse Monitoring UI (`streaming/dashboard/`)**: Built on Streamlit, providing sub-second autorefresh, geospatial trip paths rendered with PyDeck `TripsLayer`, real-time incident queues, and hourly rush-hour heatmaps.

---

## Project Structure

```
nyc-taxi-data-pipeline/
├── airflow/
│   └── dags/
│       ├── dbt_transformation_dag.py
│       ├── deploy_infrastructure_dag.py
│       ├── nyc_taxi_sync_dag.py
│       └── scripts/
├── infrastructure/
│   ├── deploy_lambda.py
│   └── lambda_function.py
├── nyc_taxi_dbt/
│   ├── dbt_project.yml
│   ├── packages.yml
│   ├── macros/
│   ├── models/
│   │   ├── staging/
│   │   ├── intermediate/
│   │   └── marts/
│   └── tests/
├── scripts/
│   └── download_zone_lookup.py
├── snowflake/
│   └── setup.sql
└── streaming/
    ├── api/                    # FastAPI Kafka producer service
    ├── dashboard/              # Streamlit TaxiPulse application
    ├── docker/                 # Docker Compose orchestrating Kafka, Spark, Redis
    ├── scripts/                # Operational and process management utilities
    ├── simulator/              # Trip event generator from Parquet data
    └── spark/                  # PySpark Structured Streaming fraud detection
```

---

## Setup and Deployment

### Prerequisites

- Docker and Docker Compose (v2.x+)
- Python 3.9+
- Apache Airflow 2.x
- Snowflake account with account administration privileges
- AWS CLI configured with S3 and Lambda permissions

### 1. Database Initialization

Execute the SQL initialization script against your Snowflake instance:

```bash
snowsql -f snowflake/setup.sql
```

This creates the required databases, warehouses, schemas, and external stages.

### 2. Configure Environment Variables

Create `.env` configurations for dbt and Snowflake access:

```bash
export SNOWFLAKE_ACCOUNT="your_account"
export SNOWFLAKE_USER="your_user"
export SNOWFLAKE_PASSWORD="your_password"
export SNOWFLAKE_ROLE="ACCOUNTADMIN"
export SNOWFLAKE_DATABASE="NYC_TAXI"
export SNOWFLAKE_WAREHOUSE="COMPUTE_WH"
```

Verify dbt connectivity:

```bash
cd nyc_taxi_dbt
dbt deps
dbt debug
dbt run
dbt test
```

### 3. Start Streaming Infrastructure

Launch the full streaming stack via Docker Compose:

```bash
cd streaming/docker
docker compose up -d
```

This provisions:
- Kafka broker running in KRaft mode (`localhost:9092`)
- Kafka UI interface (`http://localhost:8085`)
- Redis in-memory cache (`localhost:6379`)
- Spark Master and Worker instances (`http://localhost:8080`)
- FastAPI Ingestion Webhook (`http://localhost:8000`)
- TaxiPulse Dashboard (`http://localhost:8501`)

### 4. Run Telemetry Simulation

Generate live streaming trip events from historical Parquet files:

```bash
cd streaming/simulator
pip install -r requirements.txt
python stream_from_parquet.py --rate 10
```

Access the TaxiPulse dashboard at `http://localhost:8501` to view live trip paths and real-time fraud detections.

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for full details.
