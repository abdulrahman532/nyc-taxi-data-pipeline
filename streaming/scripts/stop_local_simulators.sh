#!/usr/bin/env bash
# Stop any running local simulator scripts (send_trips.py / stream_from_parquet.py)
set -euo pipefail
pkill -f send_trips.py || true
pkill -f stream_from_parquet.py || true
pkill -f send_trips || true
pkill -f stream_from_parquet || true
echo "Attempted to stop local simulator processes."