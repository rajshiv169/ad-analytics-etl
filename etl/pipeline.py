from celery import Celery
import clickhouse_driver
import os
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from dotenv import load_dotenv

load_dotenv()

# Initialize Celery
celery_app = Celery('ad_analytics_etl',
                    broker=os.getenv('REDIS_URL', 'redis://localhost:6379/0'))

# ClickHouse connection
clickhouse_client = clickhouse_driver.Client(
    host=os.getenv("CLICKHOUSE_HOST", "localhost"),
    port=int(os.getenv("CLICKHOUSE_PORT", 9000)),
    database=os.getenv("CLICKHOUSE_DB", "ad_analytics"),
    user=os.getenv("CLICKHOUSE_USER", "admin"),
    password=os.getenv("CLICKHOUSE_PASSWORD", "admin123")
)

@celery_app.task
def process_metrics(start_time: str, end_time: str):
    """
    Process metrics for a given time range
    - Aggregates metrics
    - Calculates derived metrics
    - Stores results in aggregated tables
    """
    try:
        # Fetch raw metrics
        query = """
        SELECT
            timestamp,
            campaign_id,
            ad_id,
            impressions,
            clicks,
            conversions,
            spend
        FROM ad_analytics.ad_metrics
        WHERE timestamp BETWEEN %(start_time)s AND %(end_time)s
        """
        
        result = clickhouse_client.execute(query, {
            'start_time': start_time,
            'end_time': end_time
        })
        
        # Convert to pandas DataFrame for easier processing
        df = pd.DataFrame(result, columns=[
            'timestamp', 'campaign_id', 'ad_id', 'impressions',
            'clicks', 'conversions', 'spend'
        ])
        
        # Calculate hourly aggregations
        hourly_agg = df.groupby([
            pd.Grouper(key='timestamp', freq='H'),
            'campaign_id'
        ]).agg({
            'impressions': 'sum',
            'clicks': 'sum',
            'conversions': 'sum',
            'spend': 'sum'
        }).reset_index()
        
        # Calculate derived metrics
        hourly_agg['ctr'] = hourly_agg['clicks'] / hourly_agg['impressions']
        hourly_agg['cpc'] = hourly_agg['spend'] / hourly_agg['clicks']
        hourly_agg['cvr'] = hourly_agg['conversions'] / hourly_agg['clicks']
        
        # Store aggregated results
        insert_query = """
        INSERT INTO ad_analytics.hourly_metrics
        (timestamp, campaign_id, impressions, clicks, conversions, spend, ctr, cpc, cvr)
        VALUES
        """
        
        values = [
            (row['timestamp'], row['campaign_id'], row['impressions'],
             row['clicks'], row['conversions'], row['spend'],
             float(row['ctr']), float(row['cpc']), float(row['cvr']))
            for _, row in hourly_agg.iterrows()
        ]
        
        clickhouse_client.execute(insert_query, values)
        
        return {
            'success': True,
            'message': f'Processed metrics from {start_time} to {end_time}',
            'records_processed': len(df)
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

@celery_app.task
def cleanup_old_data(days_to_keep: int = 90):
    """
    Clean up raw metrics older than specified days
    """
    try:
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        query = """
        ALTER TABLE ad_analytics.ad_metrics
        DELETE WHERE timestamp < %(cutoff_date)s
        """
        
        clickhouse_client.execute(query, {'cutoff_date': cutoff_date})
        
        return {
            'success': True,
            'message': f'Cleaned up data older than {cutoff_date}'
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

# Schedule periodic tasks
@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # Process metrics every hour
    sender.add_periodic_task(
        3600.0,
        process_metrics.s(
            (datetime.now() - timedelta(hours=1)).isoformat(),
            datetime.now().isoformat()
        ),
        name='process-hourly-metrics'
    )
    
    # Clean up old data weekly
    sender.add_periodic_task(
        7 * 24 * 3600.0,  # 7 days
        cleanup_old_data.s(90),
        name='cleanup-old-data'
    )