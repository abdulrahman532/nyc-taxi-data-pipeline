# Spark Streaming Job - NYC Taxi Fraud Detector
# Latest versions as of November 2025
FROM apache/spark:4.0.1-scala2.13-java17-ubuntu

USER root

# Install pip and Python packages (Latest versions Nov 2025)
RUN apt-get update && apt-get install -y python3-pip && \
    pip3 install --no-cache-dir \
    redis==7.1.0 \
    pandas==2.3.3 \
    pyarrow==22.0.0 \
    kafka-python-ng==2.2.3 && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy application
COPY fraud_detector.py /app/spark/

USER spark

WORKDIR /app/spark
