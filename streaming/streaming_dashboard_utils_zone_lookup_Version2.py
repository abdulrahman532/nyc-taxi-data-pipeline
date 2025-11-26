"""Zone Lookup Utility"""

import pandas as pd
import os

class ZoneLookup:
    def __init__(self):
        data_path = os. path.join(os.path.dirname(__file__), '..', 'data', 'taxi_zone_lookup.csv')
        try:
            self. df = pd.read_csv(data_path)
            self.zones = dict(zip(self. df['LocationID'], self.df['Zone']))
            self.boroughs = dict(zip(self.df['LocationID'], self.df['Borough']))
        except:
            self.zones = {}
            self.boroughs = {}
    
    def get_zone_name(self, location_id: int) -> str:
        return self.zones.get(location_id, f"Zone {location_id}")
    
    def get_borough(self, location_id: int) -> str:
        return self.boroughs.get(location_id, "Unknown")