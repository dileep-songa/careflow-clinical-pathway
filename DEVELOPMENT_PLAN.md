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

## Week 2: Data Cleaning & Normalization

### Objectives
- Standardize event names
- Remove invalid records
- Create cleaned event log table
- Prepare for PM4Py process discovery

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
