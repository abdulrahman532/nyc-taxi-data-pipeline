"""
FastAPI Webhook Server
Receives taxi trip data and produces to Kafka
"""

from fastapi import FastAPI, HTTPException, status
from fastapi. middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from datetime import datetime
import uuid

from schemas import TripEvent, TripResponse
from kafka_producer import KafkaProducerClient

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

kafka_producer: KafkaProducerClient = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global kafka_producer
    logger.info("🚀 Starting FastAPI server...")
    kafka_producer = KafkaProducerClient()
    kafka_producer.connect()
    logger.info("✅ Connected to Kafka")
    yield
    logger.info("🛑 Shutting down...")
    if kafka_producer:
        kafka_producer.close()

app = FastAPI(
    title="NYC Taxi Real-Time API",
    description="Webhook receiver for taxi trip events",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "status": "healthy",
        "service": "NYC Taxi Real-Time API",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/health")
async def health_check():
    kafka_healthy = kafka_producer. is_connected() if kafka_producer else False
    return {
        "status": "healthy" if kafka_healthy else "degraded",
        "kafka": "connected" if kafka_healthy else "disconnected"
    }

@app.post("/api/v1/trips", response_model=TripResponse, status_code=status.HTTP_201_CREATED)
async def receive_trip(trip: TripEvent):
    try:
        trip_id = str(uuid.uuid4())
        message = trip.model_dump()
        message['trip_id'] = trip_id
        message['received_at'] = datetime.utcnow().isoformat()
        message['tpep_pickup_datetime'] = trip.tpep_pickup_datetime.isoformat()
        message['tpep_dropoff_datetime'] = trip.tpep_dropoff_datetime.isoformat()
        
        success = kafka_producer. send_trip(message)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Failed to produce to Kafka"
            )
        
        logger.info(f"✅ Trip received: {trip_id}")
        return TripResponse(
            status="success",
            message="Trip received",
            trip_id=trip_id,
            timestamp=datetime.utcnow()
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
        raise HTTPException(
            status_code=status. HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app. post("/api/v1/trips/batch", status_code=status. HTTP_201_CREATED)
async def receive_trips_batch(trips: list[TripEvent]):
    results = []
    for trip in trips:
        try:
            trip_id = str(uuid.uuid4())
            message = trip.model_dump()
            message['trip_id'] = trip_id
            message['received_at'] = datetime.utcnow().isoformat()
            message['tpep_pickup_datetime'] = trip.tpep_pickup_datetime.isoformat()
            message['tpep_dropoff_datetime'] = trip.tpep_dropoff_datetime. isoformat()
            success = kafka_producer. send_trip(message)
            results.append({"trip_id": trip_id, "status": "success" if success else "failed"})
        except Exception as e:
            results.append({"trip_id": None, "status": "failed", "error": str(e)})
    
    successful = sum(1 for r in results if r['status'] == 'success')
    return {
        "status": "completed",
        "total": len(trips),
        "successful": successful,
        "failed": len(trips) - successful
    }