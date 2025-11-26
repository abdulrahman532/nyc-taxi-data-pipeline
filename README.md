# 🚕 NYC Taxi Data Pipeline

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![dbt](https://img.shields.io/badge/dbt-1.0+-orange.svg)](https://getdbt.com)
[![Airflow](https://img.shields.io/badge/Apache%20Airflow-2.0+-green.svg)](https://airflow.apache.org)
[![Snowflake](https://img.shields.io/badge/Snowflake-Data%20Cloud-29B5E8.svg)](https://snowflake.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A production-ready **ELT data pipeline** for NYC Yellow Taxi trip data, featuring automated data ingestion from AWS S3, transformation with dbt, and analytics-ready data marts in Snowflake.

## 📋 Table of Contents

- [🎯 Overview](#-overview)
- [🏗️ Architecture](#️-architecture)
- [📁 Project Structure](#-project-structure)
- [📊 Data Models](#-data-models)
- [🚀 Setup & Installation](#-setup--installation)
- [💻 Usage](#-usage)
- [✅ Data Quality](#-data-quality)
- [🤝 Contributing](#-contributing)

## 🎯 Overview

This project implements a complete data pipeline that:

- **Extracts** NYC Yellow Taxi trip data from the TLC public dataset
- **Loads** raw Parquet files into Snowflake via AWS S3
- **Transforms** data using dbt with a medallion architecture (staging → intermediate → marts)
- **Orchestrates** workflows with Apache Airflow
- **Delivers** analytics-ready datasets for business intelligence and machine learning

### Key Features

✅ Incremental data loading with sync state management  
✅ Data quality tests and validation  
✅ Dimensional modeling with fact and dimension tables  
✅ Pre-built analytics for business insights  
✅ ML-ready feature engineering  
✅ Infrastructure as Code with AWS Lambda  

## 🏗️ Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   NYC TLC       │────▶│    AWS S3       │────▶│   Snowflake     │
│   Open Data     │     │   Raw Storage   │     │   Data Cloud    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                        │
                               ┌────────────────────────┤
                               │                        │
                               ▼                        ▼
                        ┌─────────────┐          ┌─────────────┐
                        │     dbt     │          │   Airflow   │
                        │ Transforms  │◀────────▶│   Orchestr  │
                        └─────────────┘          └─────────────┘
                               │
           ┌───────────────────┼───────────────────┐
           ▼                   ▼                   ▼
    ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
    │  Staging    │────▶│Intermediate │────▶│    Marts    │
    │   Layer     │     │   Layer     │     │   Layer     │
    └─────────────┘     └─────────────┘     └─────────────┘
```

## 📁 Project Structure

```
nyc-taxi-data-pipeline/
├── airflow/
│   └── dags/
│       ├── deploy_infrastructure_dag.py  # Infrastructure deployment
│       ├── nyc_taxi_sync_dag.py          # Main data sync DAG
│       └── scripts/
│           └── sync_manager.py           # Sync state management
├── infrastructure/
│   ├── deploy_lambda.py                  # Lambda deployment script
│   └── lambda_function.py                # S3 data ingestion Lambda
├── nyc_taxi_dbt/
│   ├── dbt_project.yml
│   ├── models/
│   │   ├── staging/                      # Raw data cleaning
│   │   │   ├── stg_trips.sql
│   │   │   └── stg_zones.sql
│   │   ├── intermediate/                 # Data validation & enrichment
│   │   │   └── int_trips_validated.sql
│   │   └── marts/
│   │       ├── core/                     # Dimensional models
│   │       │   ├── fct_trips.sql
│   │       │   ├── dim_zones.sql
│   │       │   ├── dim_payment_types.sql
│   │       │   └── dim_rate_codes.sql
│   │       ├── aggregations/             # Pre-aggregated metrics
│   │       │   ├── agg_monthly.sql
│   │       │   ├── agg_quarterly.sql
│   │       │   └── agg_yearly.sql
│   │       └── insights/                 # Business analytics (11 models)
│   │           ├── insight_covid_recovery.sql
│   │           ├── insight_uber_effect.sql
│   │           ├── insight_industry_evolution.sql
│   │           ├── insight_airport_lifeline.sql
│   │           ├── insight_fee_impact.sql
│   │           ├── insight_manhattan_share.sql
│   │           ├── insight_payment_shift.sql
│   │           ├── insight_route_pricing.sql
│   │           ├── insight_tipping_patterns.sql
│   │           ├── insight_anomaly_breakdown.sql
│   │           └── insight_zone_heatmap.sql
├── scripts/
│   └── download_zone_lookup.py           # Zone data download
├── snowflake/
│   └── setup.sql                         # Snowflake infrastructure
└── README.md
```

## 📊 Data Models

> **Dataset Stats:** 1.1 billion trips | 2013-01-01 to 2025-09-30 | 21 dbt models

### Staging Layer
| Model | Description |
|-------|-------------|
| `stg_trips` | Raw trip records with timestamp conversion (microseconds → datetime) |
| `stg_zones` | NYC taxi zone reference data (265 zones) |

### Intermediate Layer
| Model | Description |
|-------|-------------|
| `int_trips_validated` | Validated trips with data quality filters, calculated fields (duration, speed, time of day) |

### Marts Layer

#### Core (Dimensional Model)
| Model | Type | Description |
|-------|------|-------------|
| `fct_trips` | Fact | Core trip transactions with all metrics and dimensions |
| `dim_zones` | Dimension | Pickup/dropoff location with borough info |
| `dim_payment_types` | Dimension | Payment method lookup (Cash, Credit, etc.) |
| `dim_rate_codes` | Dimension | Rate code descriptions (Standard, JFK, Newark, etc.) |

#### Aggregations
| Model | Description |
|-------|-------------|
| `agg_monthly` | Monthly KPIs: trips, revenue, avg fare, avg distance |
| `agg_quarterly` | Quarterly aggregations with YoY comparisons |
| `agg_yearly` | Yearly summary metrics |

#### Insights (11 Analytics Models)
| Model | Description |
|-------|-------------|
| `insight_covid_recovery` | COVID-19 impact and recovery analysis (2019-2023) |
| `insight_uber_effect` | Uber/rideshare disruption impact on yellow taxi industry |
| `insight_industry_evolution` | Long-term industry trends (2013-present) |
| `insight_airport_lifeline` | Airport trips analysis (JFK, LaGuardia, Newark) |
| `insight_fee_impact` | Congestion surcharge and fee impact analysis |
| `insight_manhattan_share` | Manhattan vs outer borough trip distribution |
| `insight_payment_shift` | Cash to credit card payment transition |
| `insight_route_pricing` | Popular routes and pricing patterns |
| `insight_tipping_patterns` | Tipping behavior analysis by time, location, payment |
| `insight_anomaly_breakdown` | Data quality anomalies and outliers |
| `insight_zone_heatmap` | Zone-level pickup/dropoff heatmap data |

## 🚀 Setup & Installation

### Prerequisites

- Python 3.9+
- Snowflake account
- AWS account (for S3 storage)
- Apache Airflow 2.0+

### 1. Clone the Repository

```bash
git clone https://github.com/abdulrahman532/nyc-taxi-data-pipeline.git
cd nyc-taxi-data-pipeline
```

### 2. Set Up Python Environment

```bash
python -m venv dbt_venv
source dbt_venv/bin/activate
pip install dbt-snowflake apache-airflow boto3
```

### 3. Configure Snowflake

Run the setup script in Snowflake:

```sql
-- Execute snowflake/setup.sql in Snowflake Worksheets
```

### 4. Configure dbt Profile

Create `~/.dbt/profiles.yml`:

```yaml
nyc_taxi:
  target: dev
  outputs:
    dev:
      type: snowflake
      account: <your_account>
      user: <your_user>
      password: <your_password>
      role: DATA_ENGINEER
      database: NYC_TAXI_DB
      warehouse: TAXI_WH
      schema: RAW
      threads: 4
```

### 5. Install dbt Packages

```bash
cd nyc_taxi_dbt
dbt deps
```

## 💻 Usage

### Run dbt Models

```bash
cd nyc_taxi_dbt

# Run all models
dbt run

# Run specific layer
dbt run --select staging
dbt run --select intermediate
dbt run --select marts

# Run with tests
dbt build
```

### Run Data Tests

```bash
dbt test
```

### Generate Documentation

```bash
dbt docs generate
dbt docs serve
```

### Trigger Airflow DAGs

```bash
# Via Airflow CLI
airflow dags trigger nyc_taxi_sync_dag

# Or use the Airflow Web UI
```

## ✅ Data Quality

The pipeline includes comprehensive data quality checks:

- **Schema Tests**: Not null, unique, accepted values
- **Freshness Tests**: Data recency monitoring
- **Custom Tests**: Business rule validation
- **Row Count Validation**: Source-to-target reconciliation

## 📈 Sample Queries

### Monthly Revenue Trend
```sql
SELECT * FROM NYC_TAXI_DB.RAW_marts.agg_monthly
ORDER BY pickup_year, pickup_month;
```

### Top Pickup Locations
```sql
SELECT 
    pickup_location_id,
    COUNT(*) as trip_count,
    SUM(total_amount) as total_revenue
FROM NYC_TAXI_DB.RAW_marts.fct_trips
GROUP BY 1
ORDER BY trip_count DESC
LIMIT 10;
```

### Uber Effect Analysis
```sql
SELECT * FROM NYC_TAXI_DB.RAW_insights.insight_uber_effect
ORDER BY pickup_year;
```

### COVID Recovery
```sql
SELECT * FROM NYC_TAXI_DB.RAW_insights.insight_covid_recovery
ORDER BY pickup_year, pickup_month;
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [NYC Taxi & Limousine Commission](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page) for the open dataset
- [dbt Labs](https://www.getdbt.com/) for the amazing transformation framework
- [Snowflake](https://www.snowflake.com/) for the cloud data platform

---

**Built with ❤️ by [Abdulrahman](https://github.com/abdulrahman532)**