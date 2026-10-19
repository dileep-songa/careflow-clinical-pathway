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
├── outputs/
│   ├── dfg_transitions_summary.csv
│   ├── pathway_variants_summary.csv
│   └── process_mining_summary.json
├── reports/
│   └── MID_PROJECT_REVIEW.md
├── sql/
│   └── schema_hospital_events_raw.sql
├── src/
│   ├── constants.py
│   ├── data_generator.py
│   ├── bq_loader.py
│   ├── process_miner.py
│   └── project_config.py
├── tests/
│   ├── test_data_generator.py
│   ├── test_bq_loader.py
│   ├── test_dbt_setup.py
│   └── test_process_miner.py
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
- Week 1: Synthetic event log generation, BigQuery raw ingestion foundation & dbt setup (Complete)
- Week 2: Data cleaning, normalization, and offline PM4Py process discovery (Complete; live warehouse execution deferred pending GCP credentials)
- Week 3: Process mining, bottleneck analysis, and dashboarding
- Week 4: Conformance checking and final report

## Getting Started

### 1. Environment Setup
```bash
git clone https://github.com/dileep-songa/careflow-clinical-pathway.git
cd careflow-clinical-pathway
python -m venv .venv
# Activate virtual environment:
# On Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# On Windows (cmd.exe):
.\.venv\Scripts\activate.bat
# On Mac/Linux:
source .venv/bin/activate

pip install -r requirements.txt
pip install dbt-core==1.12.6 dbt-bigquery==1.12.1 PyYAML==6.0.3
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

#### A. Offline Validation Mode (Zero Cloud Credentials / Free)
Validates the dbt project manifest, model syntax, and source configurations offline without connecting to BigQuery:
```bash
dbt parse --project-dir careflow_dbt --profiles-dir careflow_dbt
```
*Note: `dbt parse` succeeds offline without network or credentials. In contrast, `dbt compile` attempts to inspect warehouse relations and stops with a credential error when Google Cloud credentials are unavailable.*

#### B. Live BigQuery Staging (Week 2 Live Run)
Once raw event logs are staged in BigQuery and GCP credentials are authenticated:
1. Navigate to the dbt project directory:
   ```bash
   cd careflow_dbt
   ```
2. Compile, run, and test the staging models in the warehouse:
   ```bash
   dbt compile
   dbt run
   dbt test
   ```
   *The staging model (`stg_hospital_events`) cleans column names, formats timestamps, sequences events (1..N per case), and computes transition durations for PM4Py.*

### 5. Process Mining & Pathway Discovery (PM4Py)
Execute the offline process mining pipeline to discover clinical pathway variants, compute directly-follows graph (DFG) transitions, and calculate observed transition and case durations:
```bash
python -m src.process_miner --input data/raw/hospital_events_simulated.csv --output-dir outputs
```

Key outputs generated in `outputs/`:
- `dfg_transitions_summary.csv`: 10 direct process transitions with frequency counts, median observed transition durations, and mean observed transition durations in minutes.
- `pathway_variants_summary.csv`: 6 discovered pathway variants across 500 patient journeys, case counts, cohort percentages, and complete activity sequence traces.
- `process_mining_summary.json`: Structured cohort summary covering total cases (500), events (3,140), start/end activity distributions (100% Registration / 100% Discharge), re-triage case volume (60 cases / 12.0%), and case duration statistics (Min: 95.0m, Median: 211.0m, Mean: 202.54m, Max: 354.0m, Std: 62.44m).

### 6. Running Automated Tests
Run the complete unit test suite across data generator, BigQuery loader, dbt setup, and process miner:
```bash
pytest -v
```

Current test coverage: **56 passing tests + 8 subtests** (100% pass rate).

## Status
- 🟢 **Week 1:** Data Generator, BigQuery Ingestion Foundation & dbt Cleaning Configured (37/37 tests passing, 8 subtests passing)
- 🟢 **Week 2:** Offline Process Mining Module, DFG Discovery, and Test Suite Expansion (56/56 tests passing, 8 subtests passing; live BigQuery run deferred pending GCP credentials)
