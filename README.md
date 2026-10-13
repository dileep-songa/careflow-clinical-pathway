# CareFlow: Clinical Pathway Process Mining

## Project Overview
This project analyzes hospital patient event logs to identify bottlenecks, inefficiencies, and opportunities to improve clinical operations.

## Objective
- Collect and clean hospital event logs
- Perform process mining to discover patient journey flows
- Identify bottlenecks and waiting time issues
- Create dashboards and visualizations
- Generate actionable insights for hospital administrators

## Key Technologies
- **Data Processing:** Python, Pandas, SQL
- **Process Mining:** PM4Py
- **Data Warehouse:** Google BigQuery
- **Visualization:** PowerBI, Looker, Matplotlib
- **Version Control:** Git & GitHub

## Project Structure
```text
careflow-clinical-pathway/
├── careflow_dbt/
│   ├── models/
│   │   └── staging/
│   │       ├── _sources.yml
│   │       ├── _staging_models.yml
│   │       └── stg_hospital_events.sql
│   ├── dbt_project.yml
│   ├── profiles.yml.example
│   └── README.md
├── data/
│   ├── raw/
│   └── cleaned/
├── notebooks/
├── sql/
│   └── schema_hospital_events_raw.sql
├── src/
│   ├── constants.py
│   ├── data_generator.py
│   ├── bq_loader.py
│   └── project_config.py
├── tests/
│   ├── test_data_generator.py
│   ├── test_bq_loader.py
│   └── test_dbt_setup.py
├── reports/
├── .env.example
├── README.md
├── .gitignore
├── requirements.txt
├── PROJECT_UNDERSTANDING.md
├── DATA_SCHEMA.md
├── DAILY_LOG.md
└── DEVELOPMENT_PLAN.md
```

## Timeline
- Week 1: Synthetic event log generation, BigQuery raw ingestion foundation & dbt setup
- Week 2: Data cleaning, normalization, and PM4Py process discovery
- Week 3: Process mining, bottleneck analysis, and dashboarding
- Week 4: Conformance checking and final report

## Getting Started

### 1. Environment Setup
```bash
git clone https://github.com/dileep-songa/careflow-clinical-pathway.git
cd careflow-clinical-pathway
python -m venv .venv
# Activate virtual environment:
# On Windows:
.venv\Scripts\activate
# On Mac/Linux:
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Generate Simulated Hospital Event Log
Generate 500 patient journeys (3,140 chronological events) containing intentional operational bottlenecks and re-triage loop-backs:
```bash
python -m src.data_generator --cases 500 --seed 42
```
*Note: Generated CSVs are stored in `data/raw/` and are automatically ignored by Git.*

### 3. BigQuery Ingestion & Schema Validation

#### A. Offline Validation Mode (Zero Cloud Credentials / Free)
Validates the generated CSV strictly against the BigQuery schema contract locally without connecting to Google Cloud:
```bash
python -m src.bq_loader --mode offline
```

#### B. Live BigQuery Ingestion (Requires GCP Configuration)
When connecting to an active Google Cloud project:
1. Copy `.env.example` to `.env` and configure your GCP project and dataset:
   ```bash
   cp .env.example .env
   ```
2. Authenticate using Application Default Credentials (ADC):
   ```bash
   gcloud auth application-default login
   ```
3. Execute the ingestion:
   ```bash
   python -m src.bq_loader --mode live --project YOUR_PROJECT_ID --dataset careflow_raw --table hospital_events_raw
   ```
   *Safety default: Uses `write_disposition = WRITE_EMPTY` to prevent accidental overwrites.*

### 4. dbt Initial Cleaning Phase (`careflow_dbt/`)
Once raw event logs are staged in BigQuery:
1. Navigate to the dbt project directory:
   ```bash
   cd careflow_dbt
   ```
2. Compile and run the staging models:
   ```bash
   dbt compile
   dbt run
   dbt test
   ```
   *The staging model (`stg_hospital_events`) cleans column names, formats timestamps, sequences events (1..N per case), and computes transition durations for PM4Py.*

### 5. Running Automated Tests
Run the complete unit test suite across data generator, BigQuery loader, and dbt setup:
```bash
pytest -v
```

## Status
🟢 Week 1: Data Generator, BigQuery Ingestion Foundation & dbt Cleaning Configured (30/30 tests passing)
