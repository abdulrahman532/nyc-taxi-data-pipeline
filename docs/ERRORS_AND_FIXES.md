# Incident Resolution and Debugging Report: NYC Taxi Data Pipeline

This document provides a post-mortem and resolution log for SQL transformation bugs, data contract violations, and containerized runtime issues identified and resolved across the batch ELT and real-time streaming subsystems.

---

## Table of Contents

1. [SQL Transformation and Logic Fixes](#1-sql-transformation-and-logic-fixes)
2. [Containerization and Runtime Operations](#2-containerization-and-runtime-operations)
3. [Deployment and Verification Workflow](#3-deployment-and-verification-workflow)
4. [Resolution Summary Matrix](#4-resolution-summary-matrix)

---

## 1. SQL Transformation and Logic Fixes

### Issue 1.1: Syntax Error in Analytical Mart (`insight_zone_heatmap.sql`)

**File:** `nyc_taxi_dbt/models/marts/insights/insight_zone_heatmap.sql`

**Problem:** A syntax error occurred in the window function clause within a `CASE WHEN` statement on line 28 due to an unclosed parenthesis and missing order modifier:

```sql
-- Defective implementation:
case
    when percent_rank() over (order by coalesce(p.pickup_count, 0) desc) >= 0.95 then 'Very Hot'
    when percent_rank() over (order by coalesce(p.pickup_count, 0) >= 0.80 then 'Hot'  -- Syntax error
    when percent_rank() over (order by coalesce(p.pickup_count, 0)) >= 0.50 then 'Warm'
    else 'Cold'
end as heat_level,
```

**Resolution:** Standardized the window ordering clause across all ranking tiers:

```sql
-- Corrected implementation:
case
    when percent_rank() over (order by coalesce(p.pickup_count, 0) desc) >= 0.95 then 'Very Hot'
    when percent_rank() over (order by coalesce(p.pickup_count, 0) desc) >= 0.80 then 'Hot'
    when percent_rank() over (order by coalesce(p.pickup_count, 0) desc) >= 0.50 then 'Warm'
    else 'Cold'
end as heat_level,
```

---

### Issue 1.2: Timestamp Representation Mismatch in Staging (`stg_trips.sql`)

**File:** `nyc_taxi_dbt/models/staging/stg_trips.sql`

**Problem:** Inconsistent data types were generated between the raw pickup and dropoff timestamp fields:

```sql
-- Defective implementation:
left(date_part(epoch_nanosecond, tpep_pickup_datetime)::varchar, 16)::bigint as pickup_datetime_raw,
tpep_dropoff_datetime as dropoff_datetime_raw,
```

Downstream consumers in `int_trips_validated.sql` expected both fields as uniform epoch integers:

```sql
to_timestamp(pickup_datetime_raw / 1000000) as pickup_datetime,
to_timestamp(dropoff_datetime_raw / 1000000) as dropoff_datetime,  -- Runtime failure
```

**Resolution:** Normalized both attributes to epoch-nanosecond bigints:

```sql
-- Corrected implementation:
left(date_part(epoch_nanosecond, tpep_pickup_datetime)::varchar, 16)::bigint as pickup_datetime_raw,
left(date_part(epoch_nanosecond, tpep_dropoff_datetime)::varchar, 16)::bigint as dropoff_datetime_raw,
```

---

### Issue 1.3: CTE Column Scope Evaluation in Intermediate Model (`int_trips_validated.sql`)

**File:** `nyc_taxi_dbt/models/intermediate/int_trips_validated.sql`

**Problem:** 
1. The `WHERE` clause attempted to evaluate `pickup_datetime` and `dropoff_datetime` before their definition in the active select block.
2. The calculated field `speed_mph` referenced `trip_duration_minutes` within the same projection list.

```sql
-- Defective implementation:
from source
where pickup_datetime is not null
  and dropoff_datetime is not null
  and dropoff_datetime >= pickup_datetime

-- Projection list within the same CTE:
case when trip_duration_minutes > 0
     then trip_distance / (trip_duration_minutes / 60.0) 
     end as speed_mph,
```

**Resolution:**
1. Evaluated raw source timestamps in the filtering stage.
2. Replaced the nested column reference with direct `datediff` evaluation:

```sql
-- Corrected implementation:
from source
where pickup_datetime_raw is not null
  and dropoff_datetime_raw is not null
  and dropoff_datetime_raw >= pickup_datetime_raw

-- Direct interval computation:
case when datediff('minute', pickup_datetime, dropoff_datetime) > 0 
     then trip_distance / (datediff('minute', pickup_datetime, dropoff_datetime) / 60.0) 
     end as speed_mph,
```

---

### Issue 1.4: Missing Column Projections in Fact Mart (`obt_trips.sql` & `fct_trips.sql`)

**File:** `nyc_taxi_dbt/models/marts/core/obt_trips.sql`

**Problem:** The One Big Table (OBT) denormalized view requested feature flags and analytical metrics that were not passed through `fct_trips.sql`:
- `is_suspicious_zero_distance`
- `is_zero_distance_high_fare`
- `is_refund`
- `is_extreme_speed`
- `tip_percentage`

**Resolution:** Updated `fct_trips.sql` to expose all intermediate feature and anomaly columns:

```sql
select
    trip_id,
    tip_percentage,
    time_of_day,
    day_type,
    is_suspicious_zero_distance,
    is_zero_distance_high_fare,
    is_refund,
    is_extreme_fare,
    is_extreme_speed,
    speed_mph,
    fare_per_mile
from trips
```

---

### Issue 1.5: Missing Aggregation Columns in Analytical Rollups (`agg_yearly.sql` & `agg_monthly.sql`)

**Problem:** 
1. `insight_airport_lifeline.sql` and `insight_industry_evolution.sql` required `airport_trips` and `trips_yoy_pct`, which were omitted in `agg_yearly.sql`.
2. `insight_fee_impact.sql` required surcharge revenue totals that were not aggregated in `agg_monthly.sql`.

**Resolution:**
1. Extended `agg_yearly.sql` with annual airport trip totals and lag-based year-over-year rate of change:

```sql
select
    pickup_year,
    sum(total_trips) as total_trips,
    sum(airport_trips) as airport_trips,
    round(
        (sum(total_trips) - lag(sum(total_trips)) over (order by pickup_year)) 
        * 100.0 / nullif(lag(sum(total_trips)) over (order by pickup_year), 0), 
        2
    ) as trips_yoy_pct
```

2. Extended `agg_monthly.sql` with congestion, airport, and CBD surcharge revenue sums:

```sql
round(sum(congestion_surcharge), 2) as congestion_revenue,
round(sum(airport_fee), 2) as airport_fee_revenue,
round(sum(cbd_congestion_fee), 2) as cbd_fee_revenue,
```

---

### Issue 1.6: Data Quality Assertion Boundary (`assert_positive_fares.sql`)

**File:** `nyc_taxi_dbt/tests/assert_positive_fares.sql`

**Problem:** The singular test was titled `assert_positive_fares`, but permitted negative balances up to -100, which obscured genuine fare discrepancies.

**Resolution:** Aligned the test condition strictly with positive balance verification:

```sql
select *
from {{ ref('fct_trips') }}
where fare_amount < 0
```

---

## 2. Containerization and Runtime Operations

### Issue 2.1: Spark Dependency Pinning

**File:** `streaming/spark/Dockerfile`

**Problem:** Hardcoded package versions (e.g., `pyarrow==22.0.0`) failed builds due to missing binary wheels on slim Debian images.

**Resolution:** Relaxed dependency version constraints to allow compatible semantic ranges:

```dockerfile
RUN apt-get update && apt-get install -y python3-pip && \
    pip3 install --no-cache-dir \
    redis>=5.0.0 \
    pandas>=2.0.0 \
    pyarrow>=14.0.0 \
    kafka-python-ng>=2.2.0
```

---

### Issue 2.2: Port Conflicts During Local Execution

**Problem:** Several services bind to standard infrastructure ports that may conflict with host services:
- 9092 (Apache Kafka)
- 8000 (FastAPI Ingestion Gateway)
- 8501 (Streamlit Dashboard)
- 6379 (Redis Cache)
- 8085 (Kafka UI)

**Resolution:** Diagnostic check before running Docker Compose:

```bash
sudo lsof -i -P -n | grep LISTEN | grep -E '(9092|8000|8501|6379|8085)'
```

---

### Issue 2.3: Redis State Persistence During Testing

**Problem:** In-memory counters and time-series metrics persisted across container restarts, skewing real-time streaming tests.

**Resolution:** 
1. Use the administrative flush endpoint within the Streamlit sidebar.
2. Or clear Redis state via CLI:

```bash
docker exec redis redis-cli FLUSHALL
```

---

## 3. Deployment and Verification Workflow

### 1. Build and Initialize Container Infrastructure

```bash
cd streaming/docker
docker compose build
docker compose up -d
docker compose ps
```

### 2. Verify Infrastructure Health

```bash
# Verify FastAPI gateway
curl -s http://localhost:8000/health

# Verify Redis responsiveness
docker exec redis redis-cli ping

# Verify Kafka broker availability
docker exec kafka /opt/kafka/bin/kafka-topics.sh \
  --bootstrap-server localhost:9092 --list
```

### 3. Transmit Synthetic Test Event

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

---

## 4. Resolution Summary Matrix

| Artifact | Classification | Status |
|---|---|---|
| `insight_zone_heatmap.sql` | Syntax Error (unbalanced window clause) | Resolved |
| `stg_trips.sql` | Schema Inconsistency (timestamp vs epoch) | Resolved |
| `int_trips_validated.sql` | Scope Evaluation Error (unbound CTE column) | Resolved |
| `fct_trips.sql` | Missing Dimensional Attributes | Resolved |
| `agg_yearly.sql` | Missing Aggregations (`airport_trips`, `trips_yoy_pct`) | Resolved |
| `agg_monthly.sql` | Missing Surcharge Totals | Resolved |
| `assert_positive_fares.sql` | Test Assertion Mismatch | Resolved |
| `streaming/spark/Dockerfile` | Dependency Resolution Constraint | Resolved |
