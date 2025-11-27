"""Redis Client for Dashboard"""

import redis
import json
import os
from datetime import datetime

class RedisClient:
    def __init__(self, clear_on_start=False):
        self.client = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            decode_responses=True
        )
        if clear_on_start:
            self.clear_all_data()
    
    def clear_all_data(self):
        """Clear all Redis data"""
        self.client.flushdb()
    
    def get_today_metrics(self) -> dict:
        today = datetime.now().strftime("%Y-%m-%d")
        return {
            'trips': int(self.client.get(f"metrics:{today}:trips") or 0),
            'revenue': float(self.client.get(f"metrics:{today}:revenue") or 0),
            'fraud_alerts': int(self.client.get(f"metrics:{today}:fraud_alerts") or 0),
            'day_trips': int(self.client.get(f"metrics:{today}:day_trips") or 0),
            'night_trips': int(self.client.get(f"metrics:{today}:night_trips") or 0)
        }
    
    def get_hourly_stats(self) -> dict:
        today = datetime.now().strftime("%Y-%m-%d")
        return {
            'trips': self.client.hgetall(f"metrics:{today}:hourly:trips"),
            'revenue': self.client.hgetall(f"metrics:{today}:hourly:revenue")
        }
    
    def get_fraud_alerts(self, limit=100) -> list:
        today = datetime.now().strftime("%Y-%m-%d")
        alerts = self.client.lrange(f"fraud:alerts:{today}", 0, limit - 1)
        return [json.loads(a) for a in alerts]
    
    def get_top_fraud_zones(self, limit=10) -> list:
        return self.client.zrevrange("fraud:by_zone", 0, limit - 1, withscores=True)
    
    def get_top_fraud_routes(self, limit=10) -> list:
        return self.client.zrevrange("fraud:by_route", 0, limit - 1, withscores=True)
    
    # ============ NEW AGGREGATIONS ============
    
    def get_top_pickup_zones(self, limit=10) -> list:
        """Get top pickup zones by trip count"""
        return self.client.zrevrange("stats:pickup_zones", 0, limit - 1, withscores=True)
    
    def get_top_dropoff_zones(self, limit=10) -> list:
        """Get top dropoff zones by trip count"""
        return self.client.zrevrange("stats:dropoff_zones", 0, limit - 1, withscores=True)
    
    def get_payment_type_stats(self) -> dict:
        """Get payment type distribution"""
        today = datetime.now().strftime("%Y-%m-%d")
        return self.client.hgetall(f"stats:{today}:payment_types")
    
    def get_vendor_stats(self) -> dict:
        """Get vendor distribution"""
        today = datetime.now().strftime("%Y-%m-%d")
        return self.client.hgetall(f"stats:{today}:vendors")
    
    def get_distance_stats(self) -> dict:
        """Get distance statistics"""
        today = datetime.now().strftime("%Y-%m-%d")
        return {
            'total_distance': float(self.client.get(f"stats:{today}:total_distance") or 0),
            'avg_distance': float(self.client.get(f"stats:{today}:avg_distance") or 0)
        }
    
    def get_passenger_stats(self) -> dict:
        """Get passenger count distribution"""
        today = datetime.now().strftime("%Y-%m-%d")
        return self.client.hgetall(f"stats:{today}:passengers")
    
    def get_metrics(self) -> dict:
        """Alias for get_today_metrics"""
        return self.get_today_metrics()
    
    def get_zone_stats(self) -> dict:
        """Get zone statistics for maps"""
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Get pickup zones
        pickup_zones = {}
        pickup_data = self.client.zrevrange("stats:pickup_zones", 0, -1, withscores=True)
        for zone, count in pickup_data:
            pickup_zones[zone] = int(count)
        
        # Get dropoff zones  
        dropoff_zones = {}
        dropoff_data = self.client.zrevrange("stats:dropoff_zones", 0, -1, withscores=True)
        for zone, count in dropoff_data:
            dropoff_zones[zone] = int(count)
        
        # Get revenue by zone (if exists)
        revenue_zones = {}
        revenue_data = self.client.zrevrange("stats:revenue_by_zone", 0, -1, withscores=True)
        for zone, rev in revenue_data:
            revenue_zones[zone] = float(rev)
        
        return {
            'pickup': pickup_zones,
            'dropoff': dropoff_zones,
            'revenue': revenue_zones
        }
