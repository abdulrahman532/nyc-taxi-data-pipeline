"""Kafka Producer Client"""

from kafka import KafkaProducer
from kafka.errors import KafkaError
import json
import logging
import os

logger = logging.getLogger(__name__)

class KafkaProducerClient:
    def __init__(self):
        self.bootstrap_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
        self.topic = os.getenv('KAFKA_TOPIC', 'nyc.taxi.trips.raw')
        self.producer = None
        self._connected = False
    
    def connect(self) -> bool:
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers.split(','),
                value_serializer=lambda x: json.dumps(x).encode('utf-8'),
                key_serializer=lambda x: x.encode('utf-8') if x else None,
                acks='all',
                retries=3,
                max_block_ms=10000
            )
            self._connected = True
            logger.info(f"✅ Connected to Kafka at {self.bootstrap_servers}")
            return True
        except KafkaError as e:
            logger.error(f"❌ Failed to connect: {str(e)}")
            self._connected = False
            return False
    
    def is_connected(self) -> bool:
        return self._connected and self.producer is not None
    
    def send_trip(self, trip_data: dict) -> bool:
        if not self.is_connected():
            if not self.connect():
                return False
        try:
            key = str(trip_data.get('PULocationID', 'unknown'))
            future = self.producer.send(topic=self.topic, key=key, value=trip_data)
            future.get(timeout=10)
            return True
        except Exception as e:
            logger.error(f"❌ Failed to send: {str(e)}")
            return False
    
    def close(self):
        if self.producer:
            self.producer.flush()
            self.producer.close()
            self._connected = False
