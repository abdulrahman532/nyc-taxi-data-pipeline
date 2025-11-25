"""
AWS Lambda function for NYC Taxi data ingestion.

Downloads NYC TLC trip data files from the public source
and uploads them directly to S3 using streaming.
"""

import json
import os

import boto3
import requests

s3_client = boto3.client("s3")
BUCKET_NAME = os.environ.get("BUCKET_NAME")
SOURCE_URL_TEMPLATE = "https://d37ci6vzurychx.cloudfront.net/trip-data/{file_name}"


def lambda_handler(event, context):
    """Main Lambda handler."""
    print(f"[INFO] Event received: {event}")

    year = event.get("year", "2025")
    month = event.get("month", "09")

    file_name = f"yellow_tripdata_{year}-{month}.parquet"
    source_url = SOURCE_URL_TEMPLATE.format(file_name=file_name)
    s3_key = f"raw_data/{file_name}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    print(f"[INFO] Starting download for: {file_name}")

    try:
        with requests.get(source_url, headers=headers, stream=True) as response:
            if response.status_code == 200:
                print("[INFO] Streaming to S3...")
                s3_client.upload_fileobj(response.raw, BUCKET_NAME, s3_key)
                print(f"[SUCCESS] Uploaded to s3://{BUCKET_NAME}/{s3_key}")
                return {
                    "statusCode": 200,
                    "body": json.dumps({"message": "Upload successful", "path": s3_key})
                }
            elif response.status_code == 404:
                return {"statusCode": 404, "body": json.dumps({"message": "File not found"})}
            else:
                raise Exception(f"Unexpected status: {response.status_code}")
    except Exception as error:
        print(f"[ERROR] {str(error)}")
        raise
