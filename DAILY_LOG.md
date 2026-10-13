# Daily Work Log - CareFlow Internship

## Day 1 - Project Initialization & Requirement Analysis
**Date:** October 1, 2024
**Time Spent:** 3 hours
**Status:** ✅ Complete

### Objectives for Day 1
- [x] Understand the project requirements and business context
- [x] Learn about process mining concepts
- [x] Document hospital workflow and data structure
- [x] Set up project repository and folder structure
- [x] Create initial documentation

### What I Did

#### 1. Project Understanding (45 mins)
**Task:** Read and analyze the project brief thoroughly

**Key Activities:**
- Reviewed the CareFlow project document focusing on healthcare operations
- Understood the core business problem: Hospital ER wait times are unpredictably high
- Identified that this is NOT just a data analysis project—it's about discovering **why** things take time
- Recognized key insight: Process mining reveals hidden patterns (e.g., 40% of patients sent back to triage)

**Key Takeaway:**
The goal is not just to report "average wait time = 45 mins" but to discover:
- Which patient pathways are slow
- Where bottlenecks occur
- Hidden loops and re-routing (re-triage)
- Actionable recommendations (e.g., "Add 2 nurses to reduce wait time by 15%")

#### 2. Hospital Workflow Documentation (60 mins)
**Task:** Document the patient journey and event types

**Deliverable:** `PROJECT_UNDERSTANDING.md`

**Content Created:**
- Documented hospital events: Admission → Triage → Doctor → Treatment/Lab → Discharge
- Identified key variations: Re-triage, specialist consultation, diagnostic tests
- Explained event log format with real examples
- Traced example patient journey (P001: 70-minute journey)
- Bottleneck identified: 15-minute wait between triage and doctor

**What I Learned:**
Process mining converts timestamps into **sequence patterns** that reveal behavior:
```
Admission → [5 min wait] → Triage → [15 min wait] → Doctor → [0 min] → Treatment
```
This shows where delays cluster.

#### 3. Data Schema Design (60 mins)
**Task:** Design the data structure we'll work with

**Deliverable:** `DATA_SCHEMA.md`

**Content Created:**
- Raw Event Log Schema: event_id, patient_id, case_id, event_type, timestamp, department, duration
- Cleaned Data Schema: standardized, validated, with calculated fields
- Data Quality Rules: Validation checks (no nulls, chronological order, valid departments)
- KPI Metrics: Formulas for cycle time, wait time, throughput, re-triage rate
- Example Data: Raw and cleaned versions of sample journey

**Data Dictionary Created:**
| Field | Purpose | Type |
|-------|---------|------|
| case_id | Hospital visit identifier | STRING |
| event_type | What happened (admission, triage, etc) | STRING |
| event_timestamp | When it happened | TIMESTAMP |
| department | Where it happened | STRING |
| duration_minutes | How long it took | INT |
| severity_level | Patient urgency (1-5) | INT |

#### 4. Project Structure & Configuration (30 mins)
**Task:** Set up the technical foundation

**Deliverables Created:**
- `.gitignore` - Exclude unnecessary files (*.pyc, data files, venv)
- `src/constants.py` - Standardized event types, departments, severity levels
- `src/__init__.py` - Package initialization

**Configuration Defined:**
```python
Event Types: 13 types (admission, triage, doctor_consultation, etc)
Departments: 11 departments (ER, ICU, WARD, LAB, RADIOLOGY, etc)
Severity Levels: 5 levels (Critical → Non-urgent)
Process Mining Settings: Min support 5%, Min confidence 60%
Time Benchmarks: Expected times for key transitions
```

#### 5. Documentation & Project Planning (30 mins)
**Task:** Create reference documents and week-by-week plan

**Final Outputs:**
- **PROJECT_UNDERSTANDING.md** (2.5 KB)
  - Business context and problem statement
  - Hospital workflow explanation
  - Week-by-week breakdown
  - Key questions to answer
  - Success criteria

- **DATA_SCHEMA.md** (3.2 KB)
  - Complete schema definitions
  - Data quality rules
  - KPI calculations
  - Example data (raw and cleaned)
  - Data pipeline flow

- **DAILY_LOG.md** (this file)
  - Tracks progress and learnings
  - Documents daily activities
  - Maintains accountability

### Deliverables Created

```
✅ PROJECT_UNDERSTANDING.md    - Business requirements & workflow
✅ DATA_SCHEMA.md              - Data structure documentation
✅ src/constants.py            - Standardized configurations
✅ src/__init__.py             - Package setup
✅ .gitignore                  - Git configuration
✅ DAILY_LOG.md                - Progress tracking
```

### Code Quality Notes

- All documentation is **original work** (no copy-paste from external sources)
- Followed healthcare domain standards (event log format is industry-standard)
- Used clear, professional language suitable for business stakeholders
- Included examples and diagrams to aid understanding
- Organized information logically (Problem → Solution → Implementation)

### Learning Outcomes

1. **Process Mining Concept:** Understood how event logs become process insights
2. **Healthcare Workflow:** Learned hospital operations terminology and flow
3. **Data Structure:** Designed a schema suitable for analysis
4. **Project Planning:** Broke down 4-week project into manageable weekly goals
5. **Professional Documentation:** Created clear, stakeholder-friendly docs

### Challenges & Solutions

| Challenge | Solution |
|-----------|----------|
| Not familiar with healthcare terminology | Researched common event types and clinical workflows |
| Unclear data structure from brief | Created detailed schema with examples |
| Large project scope | Broke into 4 weekly milestones with clear deliverables |

### Next Steps (Day 2-3)

- [ ] Set up Python development environment (pandas, pm4py, jupyter)
- [ ] Create mock data generator (synthetic hospital event logs)
- [ ] Load and explore sample data
- [ ] Generate initial exploratory data analysis report
- [ ] Validate data quality rules

### Reflection

**Progress:** ✅ Successfully completed Day 1 objectives

**Understanding Gained:**
- This project is about turning raw event timestamps into **business insights**
- Process mining reveals "hidden" patterns that simple averages miss
- Documentation is as important as code for stakeholder communication

**Confidence Level:** 🟢 High
- Clear understanding of what we're building
- Well-defined data structure
- Realistic weekly timeline

---

## Day 2 - Simulated Hospital Dataset Generation & Validation
**Date:** October 11, 2026
**Status:** ✅ Complete

### Objectives for Day 2
- [x] Implement synthetic clinical pathway event log generator in `src/data_generator.py`
- [x] Model realistic operational inefficiencies, wait times, and re-triage loop-backs
- [x] Enforce data quality and schema compliance (500 cases, 3,140 events)
- [x] Create comprehensive automated test suite in `tests/test_data_generator.py`

### What Was Done
- Built probabilistic clinical pathway simulator generating 6 pathways:
  - Standard Routine (40%, 200 cases)
  - Diagnostic Lab (22%, 110 cases)
  - Diagnostic X-Ray (16%, 80 cases)
  - Comprehensive Lab + X-Ray (10%, 50 cases)
  - Re-Triage Routine (7%, 35 cases)
  - Re-Triage Diagnostic Lab (5%, 25 cases)
- Simulated 60 re-triage loops (12% of cohort) with average reassessment delay of 65.6 minutes.
- Verified deterministic reproducibility using random seed 42.
- 11 unit tests created and passing.

---

## Day 3 - BigQuery Ingestion Foundation & Offline Schema Validation
**Date:** October 12, 2026
**Status:** ✅ Complete

### Objectives for Day 3
- [x] Build BigQuery raw ingestion module with offline validation (`src/bq_loader.py`)
- [x] Author BigQuery DDL schema specification (`sql/schema_hospital_events_raw.sql`)
- [x] Create environment configuration template (`.env.example`)
- [x] Build automated test suite covering schema, offline mode, and mocked live loads (`tests/test_bq_loader.py`)
- [x] Run regression checks against existing data generator tests

### What Was Done

#### 1. Ingestion Module (`src/bq_loader.py`)
- Implemented pure offline validation (`validate_csv_for_bigquery`) using Python standard library (zero network calls, zero credentials needed).
- Defined BigQuery schema matching generator contract (`Case_ID`, `Activity_Name`, `Timestamp`, `Department`, `Resource`, `Data_Type`).
- Implemented `load_to_bigquery` supporting official Google Cloud BigQuery client with:
  - Pre-load offline validation check (aborts before calling cloud if invalid).
  - Explicit configuration requirement for project, dataset, table.
  - Safe default `write_disposition = 'WRITE_EMPTY'` to prevent silent data overwrite.
  - Safe credential and error handling without printing secrets.
- Implemented CLI supporting `--mode offline` and `--mode live`.

#### 2. BigQuery DDL Schema (`sql/schema_hospital_events_raw.sql`)
- Partitioned by `DATE(Timestamp)` for efficient time-series querying.
- Clustered by `Case_ID, Activity_Name` for fast process mining trace assembly.

#### 3. Security & Configuration (`.env.example`)
- Documented environment variables (`GCP_PROJECT_ID`, `BIGQUERY_DATASET`, `BIGQUERY_TABLE_RAW`).
- Maintained `.gitignore` exclusions for `.env`, key files, and raw CSV files.

#### 4. Automated Testing (`tests/test_bq_loader.py`)
- Built 12 unit tests covering:
  - Canonical dataset schema validation (3,140 rows, 500 cases).
  - Missing columns, invalid timestamps, empty values, and non-simulated flags.
  - Read-only preservation of raw CSV (SHA-256 hash verified).
  - Deterministic/repeatable validation results.
  - Configuration validation and error handling for missing/placeholder project IDs.
  - Mocked live-mode BigQuery load execution and load job configuration.
  - Confirmation that offline mode never calls BigQuery APIs.
- Regression check: All 11 existing tests in `tests/test_data_generator.py` remain passing (23 total tests passed in 0.37s).

#### 5. dbt Initial Cleaning Phase Setup (`careflow_dbt/`)
- Designed and initialized dbt project structure for BigQuery staging:
  - `careflow_dbt/dbt_project.yml`: Project configuration (name `careflow_dbt`, profile `careflow_bigquery`, staging materialization as `view`).
  - `careflow_dbt/profiles.yml.example`: BigQuery connection profiles supporting OAuth (ADC) and Service Account methods.
  - `careflow_dbt/models/staging/_sources.yml`: Declared `raw_hospital_data` source with table `hospital_events_raw` and `not_null` column tests.
  - `careflow_dbt/models/staging/stg_hospital_events.sql`: Non-destructive staging model:
    - Filters invalid records defensively (`Case_ID IS NOT NULL AND TRIM(Case_ID) != ''`, `Activity_Name IS NOT NULL AND TRIM(Activity_Name) != ''`, `Timestamp IS NOT NULL`).
    - Preserves case IDs and raw activity names (`Registration`, `Triage`, etc.).
    - Normalizes standard lowercase/snake_case `activity_name`.
    - Exposes UTC `event_timestamp` and calendar `event_date`.
    - Calculates 1-indexed `event_sequence` per case (`ROW_NUMBER() OVER (PARTITION BY Case_ID ORDER BY Timestamp ASC)`) for PM4Py trace reconstruction.
    - Calculates `previous_activity` and `transition_minutes_from_previous` using window functions.
    - Preserves all 60 legitimate clinical re-triage loop-backs without silent deduplication.
  - `careflow_dbt/models/staging/_staging_models.yml`: Schema tests and accepted values documentation for staging views.
  - `careflow_dbt/README.md`: Execution documentation covering setup, compilation, and testing.
  - Resolved BigQuery dataset naming by eliminating redundant custom schema suffix, ensuring views write directly to `BIGQUERY_DATASET_STAGING` (`careflow_staging`).
- Built automated test suite (`tests/test_dbt_setup.py`) with 7 tests verifying YAML schemas, Jinja references, defensive blank/whitespace filtering, and validating SQL transformation logic against the canonical simulated dataset (3,140 events, 500 cases, 60 re-triage loop-backs preserved).

### Commands Run
```powershell
python -m src.bq_loader --mode offline
python -m src.bq_loader --mode live
pytest -v
git diff --check
```

### Test Results
- `tests/test_bq_loader.py`: 12 passed.
- `tests/test_data_generator.py`: 11 passed.
- `tests/test_dbt_setup.py`: 7 passed.
- Total: 30 passed in 0.46s.

### Blockers & Next Steps
- **Cloud Environment:** Neither `dbt-core`/`dbt-bigquery` nor a live GCP BigQuery project is currently configured in the environment. dbt project configurations, sources, and staging models are fully authored and verified offline.
- **Next Steps:** Install `dbt-bigquery` and connect to a provisioned GCP project when authorized; proceed with Week 2 data normalization and PM4Py process discovery.

---

*Last Updated: Day 3 (October 12, 2026)*
