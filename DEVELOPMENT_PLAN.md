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
- [x] Expand test suite to 37 passing tests (+8 subtests)


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
- [x] Add 19 automated unit tests in `tests/test_process_miner.py` (total: 56 passing tests + 8 subtests)
- [x] Create commit `5e1e134` and push to remote

### Cloud Integration Status (Deferred)
- Note: Live BigQuery table provisioning (`careflow_raw.hospital_events_raw`) and warehouse view materialization (`careflow_staging.stg_hospital_events` via `dbt run`) are deferred until GCP credentials are configured. Offline process mining operates completely and deterministically on the baseline dataset.

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
