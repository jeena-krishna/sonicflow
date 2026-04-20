# SonicFlow — Music Streaming Analytics Data Platform

A complete end-to-end data engineering project that simulates a Spotify-like music streaming platform. Built to demonstrate real-world data engineering skills: ETL pipelines, data warehousing, distributed processing, cloud infrastructure, data quality, and analytics dashboards.

## Architecture

```
Raw Data Sources                ETL Pipeline                    Data Warehouse
┌──────────────┐    ┌─────────────────────────┐    ┌──────────────────────┐
│ Kaggle Track  │───▶│  Extract & Profile      │    │    Star Schema       │
│ Metadata      │    │  (profile_data.py)      │    │                      │
│ (114K tracks) │    │         │                │    │  ┌──────────────┐   │
└──────────────┘    │         ▼                │    │  │  dim_tracks   │   │
                     │  Clean & Transform      │    │  │  dim_users    │   │
┌──────────────┐    │  (clean_data.py)         │───▶│  │  dim_artists  │   │
│ Synthetic     │    │         │                │    │  │  dim_dates    │   │
│ Streaming     │    │         ▼                │    │  │              │   │
│ Events        │    │  Load to PostgreSQL     │    │  │ fact_streams  │   │
│ (500K events) │    │  (load_to_db.py)        │    │  └──────────────┘   │
└──────────────┘    └─────────────────────────┘    └──────────────────────┘
        │                                                     │
        ▼                                                     ▼
┌──────────────────┐    ┌────────────────┐    ┌──────────────────────────┐
│  Apache Spark    │    │  AWS Services  │    │   Analytics & Serving    │
│  (PySpark)       │    │                │    │                          │
│  • Parquet       │    │  • S3 Data Lake│    │  • Metabase Dashboard    │
│  • Partitioning  │    │  • Glue Catalog│    │  • Data Validation      │
│  • Optimization  │    │  • Athena      │    │  • ML Feature Prep      │
│  • Spark UI      │    │  • Lambda      │    │                          │
└──────────────────┘    │  • Step Funcs  │    └──────────────────────────┘
                        └────────────────┘
```

## Project Phases

### Phase 1–2: ETL Pipeline with Python & PostgreSQL
- Profiled 114,000 Spotify tracks from Kaggle — identified 24,259 duplicate track_ids, multi-artist parsing issues, and data quality problems
- Designed a star schema with `fact_streams` at the center, connected to `dim_tracks`, `dim_users`, `dim_artists`, `dim_dates`, and `track_genres`
- Built Python ETL scripts for extraction, cleaning (deduplication, null handling, type casting), and loading into PostgreSQL
- Generated 500,000 realistic synthetic streaming events with weighted distributions for popularity, time-of-day, geography, and device type

### Phase 3: Apache Spark
- Rebuilt the ETL pipeline in PySpark to understand distributed data processing
- Explored lazy evaluation, execution plans, and the Spark UI for performance debugging
- Compared CSV vs Parquet: **2.3x faster reads, 2.2x smaller file size**
- Implemented data partitioning by year/month — achieved **1.8x faster** filtered queries through partition pruning
- Analyzed join strategies: broadcast hash join vs sort-merge join and their impact on shuffle operations

### Phase 4: AWS Cloud Infrastructure
- **S3 Data Lake**: Three-zone architecture (raw → cleaned → curated) with Hive-style partitioning
- **Glue Data Catalog**: Central metadata registry with automated schema discovery via Glue Crawlers
- **Athena**: Serverless SQL queries directly on S3 data — joined Parquet + CSV across tables
- **Lambda**: Serverless validation function triggered by S3 uploads — checks file existence, format, size, and data zone compliance
- **Step Functions**: Orchestrated ETL pipeline with validation → transformation → success/failure branching

### Phase 5: Data Validation & Anomaly Detection
- Built a 20-check validation framework covering:
  - Schema validation (column presence and types)
  - Volume checks (row counts within expected bounds)
  - Null rate monitoring per critical column
  - Data freshness verification
  - Referential integrity (orphan foreign keys)
  - Statistical anomaly detection (listen duration, skip rate, distribution CV)
- Tested with simulated data corruption — validator successfully caught orphan track_ids and null rate spikes

### Phase 6: Dashboard & ML Feature Prep
- Built interactive Metabase dashboard with 4 analytical views:
  - Top Artists by stream count
  - Streams by Country (donut chart)
  - Listening patterns by Hour of Day
  - Skip Rate by Device
- Dashboard connects directly to PostgreSQL star schema

## Tech Stack

| Category | Technologies |
|----------|-------------|
| Languages | Python, SQL |
| Data Processing | pandas, Apache Spark (PySpark) |
| Databases | PostgreSQL |
| Cloud (AWS) | S3, Glue Data Catalog, Athena, Lambda, Step Functions |
| File Formats | CSV, Parquet (columnar, compressed) |
| Orchestration | AWS Step Functions |
| Visualization | Metabase |
| Containers | Docker |
| Version Control | Git, GitHub |

## Project Structure

```
sonicflow/
├── profile_data.py          # Data profiling and exploration
├── clean_data.py            # Data cleaning and transformation (ETL - Transform)
├── generate_events.py       # Synthetic streaming event generator (ETL - Extract)
├── load_to_db.py            # Database schema creation and loading (ETL - Load)
├── test_queries.py          # Analytical queries to verify star schema
├── validate_data.py         # 20-check data validation framework
├── simulate_bad_data.py     # Data corruption simulator for testing validation
├── fix_bad_data.py          # Data restoration script
├── validation_results.json  # Latest validation run output
├── dataset.csv              # Raw Kaggle Spotify tracks dataset
├── dim_tracks.csv           # Cleaned tracks dimension table
├── dim_artists.csv          # Cleaned artists dimension table
├── dim_users.csv            # Generated users dimension table
├── fact_streams.csv         # Generated streaming events fact table
├── track_genres.csv         # Track-to-genre mapping table
├── streams_parquet/         # Fact streams in Parquet format
├── streams_partitioned/     # Fact streams partitioned by year/month
└── spark_learning.ipynb     # Jupyter notebook with Spark exercises
```

## Key Concepts Demonstrated

- **Star Schema Design**: Fact and dimension table modeling for analytical workloads
- **ETL Pipeline Development**: End-to-end extract, transform, load with idempotency
- **Data Lake Architecture**: Raw/cleaned/curated zones with proper partitioning
- **Distributed Processing**: Spark execution plans, shuffles, broadcast joins, partition pruning
- **File Format Optimization**: CSV to Parquet conversion for performance and storage efficiency
- **Data Quality Engineering**: Automated validation, anomaly detection, and quarantine workflows
- **Cloud-Native Data Engineering**: S3, Glue, Athena, Lambda, Step Functions integration
- **Pipeline Orchestration**: State machine-based workflow with error handling and branching
- **Analytics & BI**: Interactive dashboards connected to the data warehouse

## How to Run

### Prerequisites
- Docker Desktop
- Python 3.12+
- AWS CLI (configured with credentials)

### Setup
```bash
# Clone the repo
git clone https://github.com/jeena-krishna/sonicflow.git
cd sonicflow

# Create virtual environment
python3 -m venv venv
source venv/bin/activate
pip install pandas psycopg2-binary

# Start PostgreSQL
docker run --name sonicflow-db -e POSTGRES_USER=jeena -e POSTGRES_PASSWORD=sonicflow123 -e POSTGRES_DB=sonicflow -p 5433:5432 -d postgres:16

# Run the ETL pipeline
python3 clean_data.py
python3 generate_events.py
python3 load_to_db.py

# Run validation
python3 validate_data.py

# Start Metabase for dashboard
docker run --name metabase -p 3000:3000 -d metabase/metabase
# Open http://localhost:3000 and connect to PostgreSQL (host: host.docker.internal, port: 5433)
```

## Dataset
- **Source**: [Spotify Tracks Dataset](https://www.kaggle.com/datasets/maharshipandya/-spotify-tracks-dataset) from Kaggle
- **Size**: 114,000 tracks with audio features, 500,000 synthetic streaming events
- **Synthetic data**: Realistic user profiles (5,000 users across 10 countries) and streaming events with weighted popularity, time-of-day patterns, and device distribution
