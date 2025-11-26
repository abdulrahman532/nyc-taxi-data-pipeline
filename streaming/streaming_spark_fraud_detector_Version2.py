"""Spark Streaming Job for NYC Taxi Fraud Detection"""

from pyspark.sql import SparkSession
from pyspark.sql. functions import col, from_json, when, hour, unix_timestamp, udf
from pyspark.sql.types import (
    StructType, StructField, StringType, IntegerType,
    DoubleType, TimestampType, ArrayType
)
import redis
import json
import logging
import os
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging. getLogger(__name__)

KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
KAFKA_TOPIC = os.getenv('KAFKA_TOPIC', 'nyc.taxi.trips. raw')
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os. getenv('REDIS_PORT', 6379))

trip_schema = StructType([
    StructField("trip_id", StringType(), True),
    StructField("VendorID", IntegerType(), True),
    StructField("tpep_pickup_datetime", StringType(), True),
    StructField("tpep_dropoff_datetime", StringType(), True),
    StructField("passenger_count", IntegerType(), True),
    StructField("trip_distance", DoubleType(), True),
    StructField("RatecodeID", IntegerType(), True),
    StructField("store_and_fwd_flag", StringType(), True),
    StructField("PULocationID", IntegerType(), True),
    StructField("DOLocationID", IntegerType(), True),
    StructField("payment_type", IntegerType(), True),
    StructField("fare_amount", DoubleType(), True),
    StructField("extra", DoubleType(), True),
    StructField("mta_tax", DoubleType(), True),
    StructField("tip_amount", DoubleType(), True),
    StructField("tolls_amount", DoubleType(), True),
    StructField("improvement_surcharge", DoubleType(), True),
    StructField("total_amount", DoubleType(), True),
    StructField("congestion_surcharge", DoubleType(), True),
    StructField("airport_fee", DoubleType(), True),
    StructField("cbd_congestion_fee", DoubleType(), True),
    StructField("received_at", StringType(), True)
])


class RedisClient:
    def __init__(self, host=REDIS_HOST, port=REDIS_PORT):
        self.client = redis.Redis(host=host, port=port, decode_responses=True)
    
    def update_metrics(self, metrics: dict):
        pipe = self.client. pipeline()
        today = datetime.now(). strftime("%Y-%m-%d")
        
        if 'trip_count' in metrics:
            pipe.incr(f"metrics:{today}:trips", metrics['trip_count'])
        if 'total_revenue' in metrics:
            pipe.incrbyfloat(f"metrics:{today}:revenue", metrics['total_revenue'])
        if 'fraud_count' in metrics:
            pipe.incr(f"metrics:{today}:fraud_alerts", metrics['fraud_count'])
        if 'day_trips' in metrics:
            pipe.incr(f"metrics:{today}:day_trips", metrics['day_trips'])
        if 'night_trips' in metrics:
            pipe. incr(f"metrics:{today}:night_trips", metrics['night_trips'])
        
        for key in ['trips', 'revenue', 'fraud_alerts', 'day_trips', 'night_trips']:
            pipe.expire(f"metrics:{today}:{key}", 7 * 24 * 3600)
        
        pipe.execute()
    
    def add_fraud_alert(self, alert: dict):
        today = datetime.now(). strftime("%Y-%m-%d")
        self.client.lpush(f"fraud:alerts:{today}", json.dumps(alert))
        self.client.ltrim(f"fraud:alerts:{today}", 0, 99)
        self.client.expire(f"fraud:alerts:{today}", 7 * 24 * 3600)
        
        zone_id = alert. get('PULocationID', 0)
        self.client.zincrby("fraud:by_zone", 1, str(zone_id))
        
        route = f"{alert. get('PULocationID', 0)}->{alert.get('DOLocationID', 0)}"
        self.client.zincrby("fraud:by_route", 1, route)
    
    def update_hourly_stats(self, hour_val: int, count: int, revenue: float):
        today = datetime. now().strftime("%Y-%m-%d")
        self.client.hset(f"metrics:{today}:hourly:trips", str(hour_val), count)
        self. client.hset(f"metrics:{today}:hourly:revenue", str(hour_val), revenue)


def process_batch(batch_df, batch_id):
    if batch_df.isEmpty():
        return
    
    logger.info(f"📦 Processing batch {batch_id} with {batch_df.count()} records")
    redis_client = RedisClient()
    pdf = batch_df.toPandas()
    
    trip_count = len(pdf)
    total_revenue = pdf['total_amount'].sum()
    day_trips = pdf[~pdf['is_night']].shape[0]
    night_trips = pdf[pdf['is_night']].shape[0]
    fraud_df = pdf[pdf['fraud_score'] >= 50]
    fraud_count = len(fraud_df)
    
    redis_client.update_metrics({
        'trip_count': trip_count,
        'total_revenue': total_revenue,
        'fraud_count': fraud_count,
        'day_trips': day_trips,
        'night_trips': night_trips
    })
    
    for _, row in fraud_df.iterrows():
        alert = {
            'trip_id': row['trip_id'],
            'fraud_score': int(row['fraud_score']),
            'fraud_flags': row['fraud_flags'],
            'PULocationID': int(row['PULocationID']),
            'DOLocationID': int(row['DOLocationID']),
            'fare_amount': float(row['fare_amount']),
            'is_night': bool(row['is_night']),
            'timestamp': datetime.now().isoformat()
        }
        redis_client.add_fraud_alert(alert)
    
    if 'pickup_hour' in pdf.columns:
        for hr, group in pdf.groupby('pickup_hour'):
            redis_client.update_hourly_stats(int(hr), len(group), float(group['total_amount']. sum()))
    
    logger.info(f"✅ Batch {batch_id}: {trip_count} trips, ${total_revenue:.2f}, {fraud_count} fraud alerts")


def main():
    logger.info("🚀 Starting NYC Taxi Fraud Detector...")
    
    spark = (SparkSession.builder
        .appName("NYC Taxi Fraud Detector")
        . config("spark.jars. packages", "org. apache.spark:spark-sql-kafka-0-10_2.12:3. 5.0")
        .config("spark.sql.streaming.checkpointLocation", "/tmp/checkpoint")
        .getOrCreate())
    
    spark.sparkContext.setLogLevel("WARN")
    
    raw_stream = (spark.readStream. format("kafka")
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS)
        .option("subscribe", KAFKA_TOPIC)
        . option("startingOffsets", "latest")
        .load())
    
    parsed_stream = (raw_stream
        .selectExpr("CAST(value AS STRING) as json_str")
        .select(from_json(col("json_str"), trip_schema). alias("data"))
        .select("data.*"))
    
    enriched_stream = (parsed_stream
        .withColumn("pickup_ts", col("tpep_pickup_datetime").cast(TimestampType()))
        .withColumn("dropoff_ts", col("tpep_dropoff_datetime").cast(TimestampType()))
        .withColumn("duration_min", (unix_timestamp("dropoff_ts") - unix_timestamp("pickup_ts")) / 60)
        .withColumn("speed_mph", when(col("duration_min") > 0, (col("trip_distance") / col("duration_min")) * 60).otherwise(0))
        .withColumn("pickup_hour", hour("pickup_ts"))
        .withColumn("is_night", (hour("pickup_ts") >= 22) | (hour("pickup_ts") < 6))
        .withColumn("fare_per_mile", when(col("trip_distance") > 0, col("fare_amount") / col("trip_distance")). otherwise(0))
        .withColumn("tip_pct", when(col("fare_amount") > 0, (col("tip_amount") / col("fare_amount")) * 100).otherwise(0)))
    
    fraud_result_schema = StructType([
        StructField("fraud_score", IntegerType(), True),
        StructField("fraud_flags", ArrayType(StringType()), True)
    ])
    
    @udf(fraud_result_schema)
    def calculate_fraud_udf(trip_distance, fare_amount, tip_amount, passenger_count,
                            payment_type, PULocationID, DOLocationID, RatecodeID,
                            airport_fee, duration_min, speed_mph, is_night):
        score, flags = 0, []
        trip_distance = trip_distance or 0
        fare_amount = fare_amount or 0
        tip_amount = tip_amount or 0
        passenger_count = passenger_count or 0
        payment_type = payment_type or 0
        PULocationID = PULocationID or 0
        DOLocationID = DOLocationID or 0
        RatecodeID = RatecodeID or 1
        airport_fee = airport_fee or 0
        duration_min = duration_min or 0
        speed_mph = speed_mph or 0
        is_night = is_night or False
        
        fare_per_mile = fare_amount / trip_distance if trip_distance > 0 else 0
        tip_pct = (tip_amount / fare_amount * 100) if fare_amount > 0 else 0
        
        if speed_mph > 100:
            score += 30
            flags.append("impossible_speed")
        if speed_mph < 2 and duration_min > 10:
            score += 25
            flags.append("stationary_trip")
        if trip_distance == 0 and fare_amount > 0:
            score += 20
            flags.append("zero_distance_with_fare")
        if fare_per_mile > 10. 5:
            score += 20
            flags.append("fare_too_high")
        if fare_amount < 0:
            score += 15
            flags.append("negative_fare")
        if payment_type == 1:
            if tip_amount > fare_amount:
                score += 25
                flags.append("tip_exceeds_fare")
            if tip_pct > 50:
                score += 15
                flags.append("excessive_tip")
        if PULocationID == DOLocationID and fare_amount > 5:
            score += 25
            flags.append("same_location_high_fare")
        if airport_fee > 0 and PULocationID not in [132, 138]:
            score += 20
            flags.append("fake_airport_fee")
        if passenger_count > 6:
            score += 15
            flags.append("too_many_passengers")
        if passenger_count == 0 and fare_amount > 0:
            score += 10
            flags.append("zero_passengers")
        if is_night:
            score += 5
            if payment_type == 2:
                score += 10
                flags.append("night_cash_trip")
            if tip_pct > 30:
                score += 10
                flags.append("night_high_tip")
        if RatecodeID == 2 and PULocationID != 132 and DOLocationID != 132:
            score += 20
            flags.append("fake_jfk_rate")
        if payment_type == 6:
            score += 20
            flags.append("voided_trip")
        if payment_type == 4:
            score += 10
            flags.append("disputed_trip")
        
        return (min(score, 100), flags)
    
    fraud_stream = (enriched_stream
        .withColumn("fraud_result", calculate_fraud_udf(
            col("trip_distance"), col("fare_amount"), col("tip_amount"),
            col("passenger_count"), col("payment_type"), col("PULocationID"),
            col("DOLocationID"), col("RatecodeID"), col("airport_fee"),
            col("duration_min"), col("speed_mph"), col("is_night")))
        .withColumn("fraud_score", col("fraud_result. fraud_score"))
        .withColumn("fraud_flags", col("fraud_result. fraud_flags"))
        .drop("fraud_result"))
    
    query = (fraud_stream. writeStream
        . foreachBatch(process_batch)
        .outputMode("append")
        .trigger(processingTime="5 seconds")
        .start())
    
    logger.info("✅ Streaming started")
    query.awaitTermination()


if __name__ == "__main__":
    main()