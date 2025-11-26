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
│   │   │   └── stg_taxi_zones.sql
│   │   ├── intermediate/                 # Business logic
│   │   │   ├── int_trips_cleaned.sql
│   │   │   └── int_trips_enriched.sql
│   │   └── marts/
│   │       ├── core/                     # Dimensional models
│   │       │   ├── fct_trips.sql
│   │       │   ├── dim_zones.sql
│   │       │   ├── dim_vendors.sql
│   │       │   ├── dim_payment_types.sql
│   │       │   └── dim_rate_codes.sql
│   │       ├── aggregations/             # Pre-aggregated metrics
│   │       │   ├── agg_monthly_overview.sql
│   │       │   └── agg_monthly_by_borough.sql
│   │       ├── insights/                 # Business analytics
│   │       │   ├── insight_covid_recovery.sql
│   │       │   ├── insight_congestion_pricing_impact.sql
│   │       │   └── insight_industry_evolution.sql
│   │       └── ml_features/              # ML feature store
│   │           ├── ml_trip_features.sql
│   │           └── ml_customer_segments.sql
├── scripts/
│   └── download_zone_lookup.py           # Zone data download
├── snowflake/
│   └── setup.sql                         # Snowflake infrastructure
└── README.md
```

## 📊 Data Models

### Staging Layer
| Model | Description |
|-------|-------------|
| `stg_trips` | Cleaned raw trip records with standardized column names |
| `stg_taxi_zones` | NYC taxi zone reference data |

### Intermediate Layer
| Model | Description |
|-------|-------------|
| `int_trips_cleaned` | Filtered trips with data quality rules applied |
| `int_trips_enriched` | Trips enriched with zone and temporal attributes |

### Marts Layer

#### Core (Dimensional Model)
| Model | Type | Description |
|-------|------|-------------|
| `fct_trips` | Fact | Core trip transactions with metrics |
| `dim_zones` | Dimension | Pickup/dropoff location attributes |
| `dim_vendors` | Dimension | Taxi vendor information |
| `dim_payment_types` | Dimension | Payment method lookup |
| `dim_rate_codes` | Dimension | Rate code descriptions |

#### Aggregations
| Model | Description |
|-------|-------------|
| `agg_monthly_overview` | Monthly KPIs: trips, revenue, avg fare |
| `agg_monthly_by_borough` | Borough-level monthly metrics |

#### Insights
| Model | Description |
|-------|-------------|
| `insight_covid_recovery` | COVID-19 impact and recovery analysis |
| `insight_congestion_pricing_impact` | Manhattan congestion pricing effects |
| `insight_industry_evolution` | Long-term industry trends (2013-present) |

#### ML Features
| Model | Description |
|-------|-------------|
| `ml_trip_features` | Feature vectors for trip prediction models |
| `ml_customer_segments` | Customer segmentation features |

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
SELECT * FROM NYC_TAXI_DB.MARTS.AGG_MONTHLY_OVERVIEW
ORDER BY year, month;
```

### Top Pickup Locations
```sql
SELECT 
    pickup_zone,
    pickup_borough,
    COUNT(*) as trip_count,
    SUM(total_amount) as total_revenue
FROM NYC_TAXI_DB.MARTS.FCT_TRIPS
GROUP BY 1, 2
ORDER BY trip_count DESC
LIMIT 10;
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