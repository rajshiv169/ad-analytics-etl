from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import List, Optional
import clickhouse_driver
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Ad Analytics API")

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ClickHouse connection configuration
clickhouse_client = clickhouse_driver.Client(
    host=os.getenv("CLICKHOUSE_HOST", "localhost"),
    port=int(os.getenv("CLICKHOUSE_PORT", 9000)),
    database=os.getenv("CLICKHOUSE_DB", "ad_analytics"),
    user=os.getenv("CLICKHOUSE_USER", "admin"),
    password=os.getenv("CLICKHOUSE_PASSWORD", "admin123")
)

# Initialize ClickHouse tables
def init_db():
    clickhouse_client.execute("""
        CREATE DATABASE IF NOT EXISTS ad_analytics
    """)
    
    clickhouse_client.execute("""
        CREATE TABLE IF NOT EXISTS ad_analytics.ad_metrics (
            timestamp DateTime,
            campaign_id String,
            ad_id String,
            impressions UInt32,
            clicks UInt32,
            conversions UInt32,
            spend Float64,
            ctr Float64 MATERIALIZED clicks / impressions,
            cpc Float64 MATERIALIZED spend / clicks,
            date Date MATERIALIZED toDate(timestamp)
        )
        ENGINE = MergeTree()
        PARTITION BY toYYYYMM(timestamp)
        ORDER BY (timestamp, campaign_id, ad_id)
    """)

# Models
class AdMetrics(BaseModel):
    campaign_id: str
    ad_id: str
    impressions: int
    clicks: int
    conversions: int
    spend: float
    timestamp: datetime

# API Routes
@app.get("/")
async def root():
    return {"message": "Ad Analytics API is running"}

@app.get("/metrics/summary")
async def get_metrics_summary(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    campaign_id: Optional[str] = None
):
    try:
        query = """
        SELECT
            toDate(timestamp) as date,
            campaign_id,
            sum(impressions) as total_impressions,
            sum(clicks) as total_clicks,
            sum(conversions) as total_conversions,
            sum(spend) as total_spend,
            round(avg(ctr) * 100, 2) as avg_ctr,
            round(avg(cpc), 2) as avg_cpc
        FROM ad_analytics.ad_metrics
        WHERE 1=1
        """
        params = {}

        if start_date:
            query += " AND timestamp >= %(start_date)s"
            params["start_date"] = start_date

        if end_date:
            query += " AND timestamp <= %(end_date)s"
            params["end_date"] = end_date

        if campaign_id:
            query += " AND campaign_id = %(campaign_id)s"
            params["campaign_id"] = campaign_id

        query += """
        GROUP BY date, campaign_id
        ORDER BY date DESC
        """

        result = clickhouse_client.execute(query, params)
        
        return {
            "success": True,
            "data": [
                {
                    "date": str(row[0]),
                    "campaign_id": row[1],
                    "total_impressions": row[2],
                    "total_clicks": row[3],
                    "total_conversions": row[4],
                    "total_spend": float(row[5]),
                    "avg_ctr": float(row[6]),
                    "avg_cpc": float(row[7])
                }
                for row in result
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/metrics/realtime")
async def get_realtime_metrics(window_minutes: int = 5):
    try:
        query = """
        SELECT
            toStartOfMinute(timestamp) as minute,
            sum(impressions) as impressions,
            sum(clicks) as clicks,
            sum(conversions) as conversions,
            sum(spend) as spend,
            round(avg(ctr) * 100, 2) as avg_ctr
        FROM ad_analytics.ad_metrics
        WHERE timestamp >= now() - INTERVAL %(window)s MINUTE
        GROUP BY minute
        ORDER BY minute DESC
        """
        
        result = clickhouse_client.execute(query, {"window": window_minutes})
        
        return {
            "success": True,
            "data": [
                {
                    "minute": str(row[0]),
                    "impressions": row[1],
                    "clicks": row[2],
                    "conversions": row[3],
                    "spend": float(row[4]),
                    "avg_ctr": float(row[5])
                }
                for row in result
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.on_event("startup")
async def startup_event():
    init_db()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)