"""Redis Client for Dashboard"""

import redis
import json
import os
from datetime import datetime

class RedisClient:
    def __init__(self):
        self.client = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            decode_responses=True
        )
    
    def get_today_metrics(self) -> dict:
        today = datetime.now(). strftime("%Y-%m-%d")
        return {
            'trips': int(self.client. get(f"metrics:{today}:trips") or 0),
            'revenue': float(self.client. get(f"metrics:{today}:revenue") or 0),
            'fraud_alerts': int(self.client.get(f"metrics:{today}:fraud_alerts") or 0),
            'day_trips': int(self.client.get(f"metrics:{today}:day_trips") or 0),
            'night_trips': int(self.client.get(f"metrics:{today}:night_trips") or 0)
        }
    
    def get_hourly_stats(self) -> dict:
        today = datetime.now(). strftime("%Y-%m-%d")
        return {
            'trips': self.client.hgetall(f"metrics:{today}:hourly:trips"),
            'revenue': self.client.hgetall(f"metrics:{today}:hourly:revenue")
        }
    
    def get_fraud_alerts(self, limit=100) -> list:
        today = datetime. now().strftime("%Y-%m-%d")
        alerts = self.client. lrange(f"fraud:alerts:{today}", 0, limit - 1)
        return [json.loads(a) for a in alerts]
    
    def get_top_fraud_zones(self, limit=10) -> list:
        return self.client.zrevrange("fraud:by_zone", 0, limit - 1, withscores=True)
    
    def get_top_fraud_routes(self, limit=10) -> list:
        return self.client.zrevrange("fraud:by_route", 0, limit - 1, withscores=True)