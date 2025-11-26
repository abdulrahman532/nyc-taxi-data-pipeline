"""
NYC Taxi Data Streamer
Downloads parquet file and streams trips to the API

This script downloads real NYC taxi data and streams it to your API endpoint.
Perfect for testing the streaming pipeline with real data!
"""

import os
import sys
import time
import argparse
import requests
import pandas as pd
from datetime import datetime

# ============================================ #
# CONFIGURATION
# ============================================ #

# Default parquet URL (September 2024 Yellow Taxi data)
PARQUET_URL = "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2024-09.parquet"

# Default API endpoint
DEFAULT_API_URL = "http://localhost:8000/api/v1/trips"

# Data directory
DATA_DIR = "data"
PARQUET_FILE = "yellow_tripdata.parquet"


def download_parquet(url: str, filepath: str) -> bool:
    """Download parquet file from NYC TLC"""
    print("📥 Downloading data from NYC TLC...")
    print(f"   URL: {url}")

    try:
        os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else '.', exist_ok=True)

        response = requests.get(url, stream=True)
        response.raise_for_status()

        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0

        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                downloaded += len(chunk)
                if total_size > 0:
                    pct = (downloaded / total_size) * 100
                    print(f"\r   Progress: {pct:.1f}% ({downloaded // 1024 // 1024} MB)", end="")

        print(f"\n✅ Downloaded successfully: {filepath}")
        print(f"   Size: {os.path.getsize(filepath) // 1024 // 1024} MB")

        return True

    except Exception as e:
        print(f"❌ Download failed: {e}")
        return False


def load_parquet(filepath: str) -> pd.DataFrame:
    """Load parquet file into DataFrame"""
    print("\n📂 Loading parquet file...")

    try:
        df = pd.read_parquet(filepath)
        print(f"✅ Loaded {len(df):,} trips")
        print(f"   Columns: {list(df.columns)}")

        if "tpep_pickup_datetime" in df.columns:
            date_range = f"{df['tpep_pickup_datetime'].min()} to {df['tpep_pickup_datetime'].max()}"
            print(f"   Date range: {date_range}")

        return df

    except Exception as e:
        print(f"❌ Failed to load: {e}")
        return None


def prepare_trip(row: pd.Series) -> dict:
    """Convert DataFrame row to API-compatible dict"""

    def safe_float(val, default=0.0):
        try:
            result = float(val) if pd.notna(val) else default
            return result if not pd.isna(result) else default
        except:
            return default

    def safe_int(val, default=1):
        try:
            result = int(val) if pd.notna(val) else default
            return result if not pd.isna(result) else default
        except:
            return default

    def format_datetime(val):
        try:
            if isinstance(val, str):
                return val
            elif hasattr(val, 'isoformat'):
                return val.isoformat()
            else:
                return datetime.now().isoformat()
        except:
            return datetime.now().isoformat()

    trip = {
        "VendorID": safe_int(row.get('VendorID'), 1),
        "tpep_pickup_datetime": format_datetime(row.get('tpep_pickup_datetime')),
        "tpep_dropoff_datetime": format_datetime(row.get('tpep_dropoff_datetime')),
        "passenger_count": safe_int(row.get('passenger_count'), 1),
        "trip_distance": safe_float(row.get('trip_distance'), 0.0),
        "RatecodeID": safe_int(row.get('RatecodeID'), 1),
        "PULocationID": safe_int(row.get('PULocationID'), 1),
        "DOLocationID": safe_int(row.get('DOLocationID'), 1),
        "payment_type": safe_int(row.get('payment_type'), 1),
        "fare_amount": safe_float(row.get('fare_amount'), 0.0),
        "extra": safe_float(row.get('extra'), 0.0),
        "mta_tax": safe_float(row.get('mta_tax'), 0.5),
        "tip_amount": safe_float(row.get('tip_amount'), 0.0),
        "tolls_amount": safe_float(row.get('tolls_amount'), 0.0),
        "improvement_surcharge": safe_float(row.get('improvement_surcharge'), 0.3),
        "total_amount": safe_float(row.get('total_amount'), 0.0),
        "congestion_surcharge": safe_float(row.get('congestion_surcharge'), 0.0),
        "airport_fee": safe_float(row.get('Airport_fee', row.get('airport_fee')), 0.0),
        "cbd_congestion_fee": safe_float(row.get('cbd_congestion_fee'), 0.0),
    }

    # Validate VendorID
    if trip["VendorID"] not in [1, 2, 6, 7]:
        trip["VendorID"] = 1

    # Validate location IDs (1-265)
    trip['PULocationID'] = max(1, min(265, trip['PULocationID']))
    trip['DOLocationID'] = max(1, min(265, trip['DOLocationID']))

    # Validate payment type
    if trip['payment_type'] not in [0, 1, 2, 3, 4, 5, 6]:
        trip['payment_type'] = 1

    return trip


def stream_trips(df: pd.DataFrame, api_url: str, rate: float, count: int, skip: int):
    """Stream trips to API endpoint"""
    print(f"\n🚀 Starting stream to: {api_url}")
    print(f"   Rate: {rate} trips/second")
    print(f"   Skip first: {skip} rows")
    print(f"   Max trips: {count if count > 0 else 'unlimited'}")
    print("\n" + "="*60)
    print("   Press Ctrl+C to stop")
    print("="*60 + "\n")

    sent = 0
    errors = 0
    start_time = time.time()

    # Apply skip and count
    if skip > 0:
        df = df.iloc[skip:]

    if count > 0:
        df = df.head(count)

    total = len(df)
    delay = 1.0 / rate if rate > 0 else 0

    for idx, row in df.iterrows():
        try:
            trip = prepare_trip(row)
            response = requests.post(api_url, json=trip, timeout=10)

            if response.status_code in [200, 201]:
                sent += 1
                elapsed = time.time() - start_time
                trips_per_sec = sent / elapsed if elapsed > 0 else 0

                # Progress display
                print(f"\r📤 Sent: {sent}/{total} | "
                      f"Rate: {trips_per_sec:.1f}/s | "
                      f"Errors: {errors} | "
                      f"Elapsed: {elapsed:.0f}s", end="")
            else:
                errors += 1
                if errors <= 5:
                    print(f"\n⚠️  Error {response.status_code}: {response.text[:100]}")

            if delay > 0:
                time.sleep(delay)

        except KeyboardInterrupt:
            print("\n\n⏹️  Stopped by user")
            break

        except requests.exceptions.ConnectionError:
            errors += 1
            print(f"\n❌ Connection error - is the API running?")
            time.sleep(2)

        except Exception as e:
            errors += 1
            if errors <= 5:
                print(f"\n❌ Error: {e}")

    # Summary
    elapsed = time.time() - start_time
    print("\n\n" + "="*60)
    print("📊 STREAMING SUMMARY")
    print("="*60)
    print(f"   ✅ Total sent: {sent:,}")
    print(f"   ❌ Errors: {errors}")
    print(f"   ⏱️  Time: {elapsed:.1f} seconds")
    print(f"   📈 Average rate: {sent/elapsed:.1f} trips/second" if elapsed > 0 else "")
    print("="*60)


def main():
    parser = argparse.ArgumentParser(
        description='Stream NYC Taxi data from Parquet to API',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Stream to local API (default)
  python stream_from_parquet.py

  # Stream to ngrok URL at 5 trips/second
  python stream_from_parquet.py --api-url https://abc123.ngrok.io/api/v1/trips --rate 5

  # Stream only 100 trips
  python stream_from_parquet.py --count 100

  # Skip first 1000 rows, send next 500
  python stream_from_parquet.py --skip 1000 --count 500

  # Use local parquet file
  python stream_from_parquet.py --file my_data.parquet
"""
    )

    parser.add_argument('--api-url', default=DEFAULT_API_URL,
                        help=f'API endpoint URL (default: {DEFAULT_API_URL})')
    parser.add_argument('--rate', type=float, default=1.0,
                        help='Trips per second (default: 1.0)')
    parser.add_argument('--count', type=int, default=0,
                        help='Number of trips to send (0 = all)')
    parser.add_argument('--skip', type=int, default=0,
                        help='Skip first N rows')
    parser.add_argument('--file', type=str, default=None,
                        help='Use local parquet file instead of downloading')
    parser.add_argument('--url', type=str, default=PARQUET_URL,
                        help='Parquet download URL')
    parser.add_argument('--no-download', action='store_true',
                        help='Skip download if file already exists')

    args = parser.parse_args()

    print("="*60)
    print("🚕 NYC TAXI DATA STREAMER")
    print("="*60)

    # Determine file path
    filepath = args.file if args.file else os.path.join(DATA_DIR, PARQUET_FILE)

    # Download if needed
    if not args.file:
        if os.path.exists(filepath) and args.no_download:
            print(f"📂 Using existing file: {filepath}")
        else:
            if not download_parquet(args.url, filepath):
                print("❌ Cannot proceed without data")
                sys.exit(1)

    # Load data
    df = load_parquet(filepath)
    if df is None:
        print("❌ Cannot proceed without data")
        sys.exit(1)

    # Check API health
    print("\n🔍 Checking API health...")
    try:
        health_url = args.api_url.replace('/api/v1/trips', '/health')
        response = requests.get(health_url, timeout=5)
        if response.status_code == 200:
            print(f"✅ API is healthy: {health_url}")
        else:
            print(f"⚠️  API returned status {response.status_code}")
    except Exception as e:
        print(f"⚠️  Could not reach API: {e}")
        confirm = input("\nContinue anyway? (y/n): ")
        if confirm.lower() != 'y':
            sys.exit(0)

    # Start streaming
    stream_trips(df, args.api_url, args.rate, args.count, args.skip)


if __name__ == "__main__":
    main()
