"""
Smart synchronization manager for NYC Taxi data.

Handles intelligent sync by checking S3 for existing files
and triggering Lambda for missing ones.
"""

import json
import time
from datetime import datetime

import boto3
from botocore.exceptions import ClientError
from dateutil.relativedelta import relativedelta

AWS_REGION = "us-east-1"
S3_BUCKET_NAME = "nyc-tlc-data-raw-prod"
LAMBDA_FUNCTION_NAME = "NYCTaxiIngestionLambda"
S3_RAW_DATA_PREFIX = "raw_data"
DATA_START_DATE = datetime(2013, 1, 1)
DATA_AVAILABILITY_BUFFER_MONTHS = 2


def smart_sync_logic():
    """Execute smart synchronization logic."""
    s3_client = boto3.client("s3", region_name=AWS_REGION)
    lambda_client = boto3.client("lambda", region_name=AWS_REGION)

    current_date = DATA_START_DATE
    limit_date = datetime.now() - relativedelta(months=DATA_AVAILABILITY_BUFFER_MONTHS)
    processed_files = []

    while current_date <= limit_date:
        year, month = current_date.strftime("%Y"), current_date.strftime("%m")
        file_name = f"yellow_tripdata_{year}-{month}.parquet"
        s3_key = f"{S3_RAW_DATA_PREFIX}/{file_name}"

        try:
            s3_client.head_object(Bucket=S3_BUCKET_NAME, Key=s3_key)
            print(f"[EXISTS] {file_name}")
            processed_files.append(file_name)
        except ClientError:
            print(f"[MISSING] {file_name} - Triggering Lambda...")
            try:
                response = lambda_client.invoke(
                    FunctionName=LAMBDA_FUNCTION_NAME,
                    InvocationType="RequestResponse",
                    Payload=json.dumps({"year": year, "month": month})
                )
                if json.loads(response["Payload"].read()).get("statusCode") == 200:
                    processed_files.append(file_name)
            except Exception as e:
                print(f"[ERROR] {e}")
            time.sleep(1)

        current_date += relativedelta(months=1)

    return processed_files
