# CareFlow Development Plan

## Week 1: Data Setup & Exploration

### Day 1: Project Understanding
- [x] Read project requirements thoroughly
- [x] Understand hospital workflow and patient journey
- [x] Identify key event types (admission, triage, treatment, discharge)
- [x] Document data schema

### Day 2: Environment Setup & Data Generation
- [x] Install Python libraries
- [x] Create synthetic hospital event logs (500 cases, 3,140 events)
- [x] Validate data structure and schema constraints
- [x] Add automated unit tests for generator

### Day 3: BigQuery Ingestion & Offline Validation
- [x] Build BigQuery raw table schema (partitioned & clustered)
- [x] Create offline CSV schema validator
- [x] Implement BigQuery loader with safe write-disposition defaults
- [x] Add offline validation test suite

### Day 4: dbt Staging Configuration
- [x] Set up careflow_dbt project structure
- [x] Configure source mappings and staging model (`stg_hospital_events`)
- [x] Add schema tests for null checks and accepted values
- [x] Test SQL transformation logic against canonical baseline

### Day 5: Quality Hardening & Test Expansion
- [x] Harden generator boundary validation (reject invalid case counts)
- [x] Add secondary deterministic ordering to dbt window functions
- [x] Add intra-file duplicate-key rejection to offline loader
- [x] Expand regression test suite to 35 passing tests

### Day 6: dbt Validation & Integration Readiness
- [x] Verify Python 3.12 compatibility with dbt Core and dbt-bigquery
- [x] Resolve dbt profile discovery and protect profiles in `.gitignore`
- [x] Validate project manifest offline using `dbt parse`
- [x] Expand test suite to 37 passing tests (+8 subtests) [Week 1 milestone snapshot]


---

## Week 2: Data Cleaning, Normalization & Process Discovery

### Day 8: Environment Hardening & PM4Py Integration
- [x] Audit repository and lock exact Python 3.12 wheel pins in `requirements.txt`
- [x] Add directory structure placeholders (`data/cleaned/`, `notebooks/`, `reports/`)
- [x] Create cleanup commit `a8d21d3` and push to remote
- [x] Perform controlled installation of `pm4py==2.7.8` in `.venv`
- [x] Verify PM4Py import and ensure zero regressions across 37 existing tests

### Day 9: Offline Process Mining & DFG Discovery
- [x] Implement `src/process_miner.py` with defensive validation and PM4Py formatting
- [x] Calculate cohort metrics and observed case duration statistics (Mean: 202.5 min, Median: 211.0 min)
- [x] Discover Directly-Follows Graph (DFG) across all 10 transitions with observed transition times
- [x] Extract and rank 6 clinical pathway variants (including 60 re-triage encounters)
- [x] Add graceful fallback when Graphviz system binary is missing
- [x] Export reproducible summary tables to `outputs/`
- [x] Add 19 automated unit tests in `tests/test_process_miner.py` (total: 56 passing tests + 8 subtests at Day 9 snapshot)
- [x] Create commit `5e1e134` and push to remote

### Day 10: Event Normalization, Schema Adapter & As-Is Visualization
- [x] Extract staging transformation logic into production module `src/staging_transform.py`
- [x] Create standalone event log normalization script `src/normalize_event_log.py`
- [x] Generate and validate normalized event log `data/cleaned/stg_hospital_events.csv` (3,140 events across 500 cases)
- [x] Extend `src/process_miner.py` to support normalized dbt staging schema
- [x] Add 12 unit tests for normalized schema validation and metric parity (current full suite: 68 passing tests + 8 subtests)
- [x] Render and export As-Is clinical process map diagram (`outputs/dfg_visualization.png`) via commit `05b4d21`
- [x] Complete comprehensive Mid-Project Review report (`reports/MID_PROJECT_REVIEW.md`)

### Cloud Integration Status
- **Raw BigQuery Table (Verified):** The canonical table `exalted-mode-467509-h1.careflow_raw.hospital_events_raw` is provisioned in BigQuery and populated with all 3,140 simulated events across 500 cases with 100% verified schema integrity (zero missing values across all six columns, zero missing timestamps, and 100% tagged as `SIMULATED`).
- **dbt Resource Discovery & Offline Verification (Verified):** The dbt staging model, source definitions, and schema tests are fully configured and verified offline (`dbt parse` succeeds with 0 errors; `dbt ls` discovers 1 staging model, 20 data tests, and 1 source).
- **dbt Staging Cloud Materialization (Deferred / Optional):** Live execution of `dbt run` and `dbt test` against BigQuery to materialize `careflow_staging.stg_hospital_events` is optional, has not been executed, and is not part of the current zero-spend workflow. Offline process mining operates completely and deterministically on the verified local normalized dataset (`data/cleaned/stg_hospital_events.csv`).

---

## Week 3: Process Mining & Analysis

### Objectives
- Discover process flow
- Detect bottlenecks
- Calculate wait times and cycle times
- Build business insights

---

## Week 4: Dashboard & Final Submission

### Objectives
- Build final dashboard
- Prepare presentation
- Write final report
- Final demo

---

## Daily Commit Guidance
- Commit after each meaningful task
- Use format: `feat: ...`, `data: ...`, `analysis: ...`, `docs: ...`
- Push updates to GitHub daily
