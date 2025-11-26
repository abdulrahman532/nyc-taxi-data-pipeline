# 📝 Changelog

All notable changes to the NYC Taxi Streaming Pipeline.

---

## [2.0.0] - November 27, 2025

### 🚀 Major Updates

#### Technology Upgrades
- **Apache Kafka**: Upgraded to **4.1.1** (KRaft mode - no Zookeeper)
- **Apache Spark**: Upgraded to **4.0.1** (Scala 2.13)
- **Python**: Using **3.12** slim images

#### Dashboard Redesign
- Complete UI overhaul with 3 pages
- Removed all tables - **charts only**
- Added emoji icons to page names

#### New Maps Page
- **6 different map types** selectable from sidebar
- Trip Routes with pickup/dropoff lines
- Pickup Hotspots (bubble map)
- Dropoff Hotspots (bubble map)  
- Fraud Routes (color-coded by risk)
- Revenue by Zone
- Zone Activity heatmap
- Increased map height to **800px**

### ✨ Features Added

- `get_metrics()` method in RedisClient
- `get_zone_stats()` method for maps data
- Zone coordinates for 60+ NYC taxi zones
- Auto-refresh with configurable rate (1-30 seconds)
- Fraud score filter in Fraud Monitor

### 🐛 Bug Fixes

- Fixed `stream_from_parquet.py` to accept status codes **200 AND 201**
- Fixed Redis `INCRBYFLOAT` error by proper data handling
- Fixed Streamlit deprecation warnings for `use_container_width`

### 📚 Documentation

- Comprehensive README with all features documented
- API reference with endpoints and schemas
- Fraud detection rules explained
- Redis data schema documented
- Troubleshooting guide
- External user guide for ngrok access

---

## [1.5.0] - November 26, 2025

### ✨ Features

- Enhanced fraud detection with 15+ rules
- Added more Redis aggregations:
  - Top pickup/dropoff zones
  - Payment type distribution
  - Vendor statistics
  - Distance stats
  - Passenger count stats

### 🔧 Changes

- Refresh rate changed from 10 seconds to 3 seconds
- Dashboard now shows more aggregations

---

## [1.0.0] - November 2025

### 🎉 Initial Release

- Real-time streaming pipeline with Kafka
- Spark Structured Streaming for processing
- Fraud detection system
- Streamlit dashboard
- Redis for metrics storage
- Docker Compose deployment
- FastAPI for data ingestion
- ngrok support for external access

---

## Version History Summary

| Version | Date | Highlights |
|---------|------|------------|
| 2.0.0 | Nov 27, 2025 | Major UI redesign, 6 maps, charts only |
| 1.5.0 | Nov 26, 2025 | Enhanced aggregations, fraud rules |
| 1.0.0 | Nov 2025 | Initial release |

---

*For detailed documentation, see [README.md](README.md)*
