import random
from datetime import datetime, timedelta
import uuid
from typing import List, Dict
import clickhouse_driver
import os
from dotenv import load_dotenv
import time

load_dotenv()

class AdMetricsGenerator:
    def __init__(self):
        self.campaigns = [f"campaign_{i}" for i in range(1, 6)]
        self.ads_per_campaign = 5
        self.client = clickhouse_driver.Client(
            host=os.getenv("CLICKHOUSE_HOST", "localhost"),
            port=int(os.getenv("CLICKHOUSE_PORT", 9000)),
            database=os.getenv("CLICKHOUSE_DB", "ad_analytics"),
            user=os.getenv("CLICKHOUSE_USER", "admin"),
            password=os.getenv("CLICKHOUSE_PASSWORD", "admin123")
        )

    def generate_metrics(self, timestamp: datetime) -> List[Dict]:
        metrics = []
        
        for campaign_id in self.campaigns:
            for ad_num in range(self.ads_per_campaign):
                ad_id = f"{campaign_id}_ad_{ad_num}"
                
                # Generate realistic metrics
                impressions = random.randint(1000, 10000)
                # Click-through rate between 0.5% and 5%
                clicks = int(impressions * random.uniform(0.005, 0.05))
                # Conversion rate between 1% and 10% of clicks
                conversions = int(clicks * random.uniform(0.01, 0.1))
                # Cost per click between $0.5 and $2
                spend = clicks * random.uniform(0.5, 2.0)
                
                metrics.append({
                    "timestamp": timestamp,
                    "campaign_id": campaign_id,
                    "ad_id": ad_id,
                    "impressions": impressions,
                    "clicks": clicks,
                    "conversions": conversions,
                    "spend": round(spend, 2)
                })
        
        return metrics

    def insert_metrics(self, metrics: List[Dict]):
        query = """
        INSERT INTO ad_analytics.ad_metrics 
        (timestamp, campaign_id, ad_id, impressions, clicks, conversions, spend)
        VALUES
        """
        
        values = []
        for metric in metrics:
            values.append((
                metric["timestamp"],
                metric["campaign_id"],
                metric["ad_id"],
                metric["impressions"],
                metric["clicks"],
                metric["conversions"],
                metric["spend"]
            ))
        
        self.client.execute(query, values)

def run_generator(interval_seconds: int = 60):
    generator = AdMetricsGenerator()
    
    while True:
        current_time = datetime.now()
        try:
            metrics = generator.generate_metrics(current_time)
            generator.insert_metrics(metrics)
            print(f"Generated and inserted metrics for {current_time}")
        except Exception as e:
            print(f"Error generating metrics: {str(e)}")
        
        time.sleep(interval_seconds)

if __name__ == "__main__":
    interval = int(os.getenv("MOCK_DATA_INTERVAL_SECONDS", 60))
    print(f"Starting mock data generator with {interval} seconds interval")
    run_generator(interval)