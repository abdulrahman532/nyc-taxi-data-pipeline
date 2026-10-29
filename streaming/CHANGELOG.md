# Changelog: NYC Taxi Streaming Pipeline

All notable changes to the NYC Taxi Streaming Pipeline are documented in this file.

---

## [2.0.0] - November 27, 2025

### Technology Upgrades
- Upgraded Apache Kafka to version 4.1.1 running in KRaft consensus mode with zero ZooKeeper dependency.
- Upgraded Apache Spark to version 4.0.1 built on Scala 2.13 and Java 17.
- Standardized container runtime images on Python 3.12 slim.

### Dashboard Architecture
- Re-architected Streamlit interface into a unified modular application.
- Added 6 specialized geospatial visualization layers rendered via PyDeck and Plotly:
  - Trip Route connectivity vectors.
  - Pickup density bubble hotspots.
  - Dropoff density bubble hotspots.
  - Risk-graded fraud routes.
  - Borough-level revenue distribution.
  - Zone activity heatmaps.
- Integrated near real-time sub-second polling via `streamlit-autorefresh`.

### Functional Improvements
- Added `get_metrics()` and `get_zone_stats()` methods to `RedisClient` for efficient range queries.
- Added precise geospatial centroids for 60+ key NYC taxi zones.
- Added interactive fraud threshold filtering to the fraud monitor interface.

### Bug Fixes
- Fixed `stream_from_parquet.py` to accept both 200 and 201 HTTP status codes.
- Resolved Redis `INCRBYFLOAT` type errors through strict float coercion.
- Removed deprecated Streamlit arguments in layout containers.

---

## [1.5.0] - November 26, 2025

### Features
- Expanded fraud evaluation engine in PySpark Structured Streaming to 15+ vectorized scoring rules.
- Added Redis sorted sets for top origin and destination zones, payment type distributions, and vendor statistics.
- Adjusted telemetry refresh rates to 3-second micro-batch intervals.

---

## [1.0.0] - November 2025

### Initial Release
- Event-driven streaming architecture leveraging Apache Kafka, Apache Spark Structured Streaming, Redis, and FastAPI.
- Real-time rule-based anomaly detection engine.
- Containerized deployment managed via Docker Compose.
- Secure external tunneling integration via ngrok.
