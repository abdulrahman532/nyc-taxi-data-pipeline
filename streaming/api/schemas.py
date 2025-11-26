"""Pydantic models for request/response validation"""

from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional

class TripEvent(BaseModel):
    VendorID: int = Field(..., ge=1, le=7)
    tpep_pickup_datetime: datetime
    tpep_dropoff_datetime: datetime
    passenger_count: Optional[int] = Field(default=1, ge=0, le=9)
    trip_distance: float = Field(..., ge=0)
    RatecodeID: Optional[int] = Field(default=1, ge=1)
    store_and_fwd_flag: Optional[str] = Field(default="N")
    PULocationID: int = Field(..., ge=1, le=265)
    DOLocationID: int = Field(..., ge=1, le=265)
    payment_type: int = Field(..., ge=0, le=6)
    fare_amount: float
    extra: Optional[float] = Field(default=0.0)
    mta_tax: Optional[float] = Field(default=0.5)
    tip_amount: Optional[float] = Field(default=0.0, ge=0)
    tolls_amount: Optional[float] = Field(default=0.0, ge=0)
    improvement_surcharge: Optional[float] = Field(default=0.3)
    total_amount: float
    congestion_surcharge: Optional[float] = Field(default=0.0)
    airport_fee: Optional[float] = Field(default=0.0)
    cbd_congestion_fee: Optional[float] = Field(default=0.0)
    
    @field_validator('store_and_fwd_flag')
    @classmethod
    def validate_store_fwd(cls, v):
        if v not in ['Y', 'N', None]:
            raise ValueError('must be Y or N')
        return v or 'N'

class TripResponse(BaseModel):
    status: str
    message: str
    trip_id: str
    timestamp: datetime
