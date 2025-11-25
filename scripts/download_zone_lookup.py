"""
Standalone script to download NYC Taxi Zone Lookup CSV.

This script downloads the taxi zone lookup file from NYC TLC website
and uploads it to S3, then optionally loads it to Snowflake.

Requirements:
    pip install boto3 requests snowflake-connector-python

Usage:
    python download_zone_lookup.py
    python download_zone_lookup.py --load-snowflake
"""

import argparse
import logging
import os

import boto3
import requests

# =============================================================================
# Configuration
# =============================================================================
ZONE_LOOKUP_URL = "https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv"
AWS_REGION = "us-east-1"
S3_BUCKET_NAME = "nyc-tlc-data-raw-prod"
S3_KEY = "reference/taxi_zone_lookup.csv"

SNOWFLAKE_CONFIG = {
    "account": os.environ.get("SNOWFLAKE_ACCOUNT", "<your_account>"),
    "user": os.environ.get("SNOWFLAKE_USER", "<your_user>"),
    "password": os.environ.get("SNOWFLAKE_PASSWORD", "<your_password>"),
    "database": "NYC_TAXI_DB",
    "schema": "RAW",
    "warehouse": "TAXI_WH",
    "role": "DATA_ENGINEER"
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def download_zone_lookup():
    """Download zone lookup CSV from NYC TLC website."""
    logger.info(f"Downloading zone lookup from {ZONE_LOOKUP_URL}")
    response = requests.get(ZONE_LOOKUP_URL)
    response.raise_for_status()
    logger.info(f"Downloaded {len(response.content)} bytes")
    return response.text


def upload_to_s3(csv_content):
    """Upload CSV content to S3."""
    logger.info(f"Uploading to s3://{S3_BUCKET_NAME}/{S3_KEY}")
    s3_client = boto3.client("s3", region_name=AWS_REGION)
    s3_client.put_object(
        Bucket=S3_BUCKET_NAME,
        Key=S3_KEY,
        Body=csv_content.encode("utf-8"),
        ContentType="text/csv"
    )
    logger.info("Upload complete")


def load_to_snowflake():
    """Load zone lookup from S3 to Snowflake."""
    try:
        import snowflake.connector
    except ImportError:
        logger.error("snowflake-connector-python not installed")
        return

    logger.info("Connecting to Snowflake...")
    conn = snowflake.connector.connect(**SNOWFLAKE_CONFIG)
    cursor = conn.cursor()

    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS RAW.TAXI_ZONES (
                location_id INT,
                borough VARCHAR,
                zone_name VARCHAR,
                service_zone VARCHAR,
                _loaded_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
            )
        """)
        cursor.execute("TRUNCATE TABLE RAW.TAXI_ZONES")
        cursor.execute(f"""
            COPY INTO RAW.TAXI_ZONES (location_id, borough, zone_name, service_zone)
            FROM @NYC_TAXI_DB.RAW.NYC_TAXI_S3_STAGE/../reference/taxi_zone_lookup.csv
            FILE_FORMAT = (TYPE = 'CSV' SKIP_HEADER = 1 FIELD_OPTIONALLY_ENCLOSED_BY = '"')
            ON_ERROR = 'CONTINUE'
        """)
        cursor.execute("SELECT COUNT(*) FROM RAW.TAXI_ZONES")
        count = cursor.fetchone()[0]
        logger.info(f"Loaded {count} zones to Snowflake")
    finally:
        cursor.close()
        conn.close()


def main():
    parser = argparse.ArgumentParser(description="Download NYC Taxi Zone Lookup")
    parser.add_argument("--load-snowflake", action="store_true", help="Load to Snowflake")
    args = parser.parse_args()

    try:
        csv_content = download_zone_lookup()
        upload_to_s3(csv_content)
        if args.load_snowflake:
            load_to_snowflake()
        logger.info("Zone lookup sync complete!")
    except Exception as e:
        logger.error(f"Failed: {str(e)}")
        raise


if __name__ == "__main__":
    main()
