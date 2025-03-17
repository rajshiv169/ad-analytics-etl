# Ad Analytics ETL System

A comprehensive ETL system for ad analytics with mock data generation, ClickHouse integration, and a real-time analytics dashboard.

## Features

- Mock ad data generation (impressions, clicks, conversions)
- ETL pipeline for processing ad analytics data
- ClickHouse integration for OLAP storage
- Real-time analytics dashboard
- REST API for data access

## Project Structure

```
├── backend/           # FastAPI backend service
├── frontend/          # React dashboard
├── etl/              # ETL pipeline components
├── mock_data/        # Mock data generation scripts
├── docker/           # Docker configuration files
└── docs/             # Documentation
```

## Prerequisites

- Python 3.9+
- Node.js 16+
- Docker and Docker Compose
- ClickHouse

## Quick Start

1. Clone the repository:
```bash
git clone https://github.com/rajshiv169/ad-analytics-etl.git
cd ad-analytics-etl
```

2. Start the services using Docker Compose:
```bash
docker-compose up -d
```

3. Access the dashboard at http://localhost:3000

4. API documentation is available at http://localhost:8000/docs

## Development Setup

Refer to the README files in individual component directories for specific setup instructions.