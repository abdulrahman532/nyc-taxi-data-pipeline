-- =============================================================================
-- NYC Taxi Data Warehouse Setup
-- =============================================================================
-- Run this script in Snowflake Worksheets
-- =============================================================================

-- Use ACCOUNTADMIN for initial setup
USE ROLE ACCOUNTADMIN;

-- Create role for data engineers
CREATE ROLE IF NOT EXISTS DATA_ENGINEER;

-- Create warehouse
CREATE WAREHOUSE IF NOT EXISTS TAXI_WH 
    WITH WAREHOUSE_SIZE = 'X-SMALL' 
    AUTO_SUSPEND = 60 
    AUTO_RESUME = TRUE;

-- Create database and schema
CREATE DATABASE IF NOT EXISTS NYC_TAXI_DB;
CREATE SCHEMA IF NOT EXISTS NYC_TAXI_DB.RAW;

-- Grant permissions to DATA_ENGINEER role
GRANT USAGE ON WAREHOUSE TAXI_WH TO ROLE DATA_ENGINEER;
GRANT USAGE ON DATABASE NYC_TAXI_DB TO ROLE DATA_ENGINEER;
GRANT USAGE ON SCHEMA NYC_TAXI_DB.RAW TO ROLE DATA_ENGINEER;
GRANT CREATE TABLE ON SCHEMA NYC_TAXI_DB.RAW TO ROLE DATA_ENGINEER;
GRANT CREATE STAGE ON SCHEMA NYC_TAXI_DB.RAW TO ROLE DATA_ENGINEER;
GRANT CREATE FILE FORMAT ON SCHEMA NYC_TAXI_DB.RAW TO ROLE DATA_ENGINEER;
GRANT CREATE SCHEMA ON DATABASE NYC_TAXI_DB TO ROLE DATA_ENGINEER;

-- Grant role to current user
SET my_user = CURRENT_USER();
GRANT ROLE DATA_ENGINEER TO USER IDENTIFIER($my_user);

-- Switch to DATA_ENGINEER role
USE ROLE DATA_ENGINEER;
USE WAREHOUSE TAXI_WH;
USE DATABASE NYC_TAXI_DB;
USE SCHEMA RAW;

-- Create file format for Parquet files
CREATE OR REPLACE FILE FORMAT PARQUET_FORMAT 
    TYPE = 'PARQUET' 
    COMPRESSION = 'SNAPPY';

-- Create external stage pointing to S3
-- ⚠️ IMPORTANT: Replace with your AWS credentials
CREATE OR REPLACE STAGE NYC_TAXI_S3_STAGE
    URL = 's3://your-bucket-name/raw_data/'
    CREDENTIALS = (
        AWS_KEY_ID = '<YOUR_AWS_ACCESS_KEY_ID>'
        AWS_SECRET_KEY = '<YOUR_AWS_SECRET_ACCESS_KEY>'
    )
    FILE_FORMAT = PARQUET_FORMAT;

-- Create raw trips table with schema evolution enabled
CREATE OR REPLACE TABLE TRIPS (
    tpep_pickup_datetime TIMESTAMP_NTZ
) 
ENABLE_SCHEMA_EVOLUTION = TRUE;

-- Create taxi zones table
CREATE OR REPLACE TABLE TAXI_ZONES (
    location_id INT,
    borough VARCHAR,
    zone_name VARCHAR,
    service_zone VARCHAR,
    _loaded_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- Verify stage connection (run after updating credentials)
-- LIST @NYC_TAXI_S3_STAGE;
