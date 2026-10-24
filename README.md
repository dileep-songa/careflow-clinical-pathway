# CareFlow Clinical Pathway Analytics

## Project Overview
CareFlow Clinical Pathway Analytics analyzes emergency department patient event logs to discover clinical workflows, identify operational bottlenecks, and surface opportunities for clinical operations improvement. All analyzed event data is synthetic (simulated EHR encounters) designed for reproducible healthcare process analytics.

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
│   ├── dfg_visualization.png
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
│   ├── staging_transform.py
│   ├── normalize_event_log.py
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
- Week 2: Data cleaning, normalization, and offline PM4Py process discovery (Complete; raw BigQuery table and careflow_staging.stg_hospital_events VIEW verified in BigQuery; 20 dbt data tests passed)
- Week 3: Bottleneck modeling, dimensional design, and Power BI dashboarding (Not Started)
- Week 4: Conformance checking, token replay, and final internship report (Planned)

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
*Note on Offline Validation:* `dbt parse` validates project syntax, YAML configurations, and model manifests entirely offline without network access or cloud credentials. In contrast, connection-dependent commands (`dbt compile`, `dbt run`, `dbt test`) connect to the BigQuery adapter and require active Google Cloud authentication (such as Application Default Credentials via `gcloud auth application-default login`).

#### B. Live BigQuery Staging Execution & Verification (Completed October 24, 2026)
On October 24, 2026, the dbt staging pipeline was executed and validated in Google BigQuery:

1. Navigate to the dbt project directory:
    ```bash
    cd careflow_dbt
    ```
2. Execute the staging model materialization:
    ```bash
    dbt run --select stg_hospital_events
    ```
    *Result:* Materialized `careflow_staging.stg_hospital_events` as a BigQuery **VIEW** (`PASS=1, WARN=0, ERROR=0`).
3. Run the complete warehouse data test suite:
    ```bash
    dbt test
    ```
    *Result:* All **20 data tests passed** (`PASS=20, WARN=0, ERROR=0`), validating primary keys, not-null constraints, and accepted values across both source table (`hospital_events_raw`) and staging view (`stg_hospital_events`).

*Verified Cloud State:* Read-only metadata inspection confirms `exalted-mode-467509-h1.careflow_staging.stg_hospital_events` returns 3,140 rows across 500 unique cases and 11 staging fields. Offline normalization (`src/normalize_event_log.py`) replicates this SQL transformation in Python, verified to yield matching reported row counts (3,140), case counts (500), schema structure (11 fields), and downstream PM4Py process-mining metrics. An exhaustive cell-by-cell cloud comparison was not performed.

### 5. Process Mining & Pathway Discovery (PM4Py)
Execute the offline process mining pipeline to discover clinical pathway variants, compute directly-follows graph (DFG) transitions, and calculate observed transition and case durations:
```bash
python -m src.process_miner --input data/raw/hospital_events_simulated.csv --output-dir outputs
```

Key outputs generated in `outputs/`:
- `dfg_transitions_summary.csv`: 10 direct process transitions with frequency counts, median observed transition durations, and mean observed transition durations in minutes.
- `dfg_visualization.png`: Discovered As-Is clinical process map diagram generated via PM4Py Directly-Follows Graph (DFG) rendering.
- `pathway_variants_summary.csv`: 6 discovered pathway variants across 500 patient journeys, case counts, cohort percentages, and complete activity sequence traces.
- `process_mining_summary.json`: Structured cohort summary covering total cases (500), events (3,140), start/end activity distributions (100% Registration / 100% Discharge), re-triage case volume (60 cases / 12.0%), and case duration statistics (Min: 95.0m, Median: 211.0m, Mean: 202.54m, Max: 354.0m, Std: 62.44m).

### 6. Running Automated Tests
Run the complete unit test suite across data generator, BigQuery loader, dbt setup, and process miner:
```bash
pytest -v
```

Current test coverage: **68 passing tests + 8 subtests** (100% pass rate).

## Status
- 🟢 **Week 1 Milestone (Historical Snapshot):** Data Generator, BigQuery Ingestion Foundation & dbt Cleaning Configured (37/37 tests passing, 8 subtests passing at Week 1 close)
- 🟢 **Week 2 Milestone (Current Full Suite):** Data Normalization, Offline Process Mining, DFG Discovery & Visualization (68/68 Python tests passing, 8 subtests passing; raw BigQuery table and `careflow_staging.stg_hospital_events` VIEW verified live; 20/20 dbt warehouse tests passing)
- ⚪ **Week 3 Milestone:** Bottleneck Modeling & Power BI Dashboarding (Not Started)
- ⚪ **Week 4 Milestone:** Conformance Checking & Final Capstone Report (Planned)
