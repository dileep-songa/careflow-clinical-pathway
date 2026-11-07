# CareFlow Clinical Pathway Analytics
## Mid-Project Technical Review & Progress Assessment

- **Project:** CareFlow Clinical Pathway Analytics
- **Intern / Analyst:** Data Analyst Intern
- **Repository:** `c:\project\careflow-clinical-pathway`
- **Scope:** Weeks 1-2 Results & Weeks 3-4 Roadmap
- **Status:** Complete (Weeks 1-2 Verified in BigQuery & PM4Py) / Weeks 3-4 Pending

> [!NOTE]
> **Historical Milestone Notice:** This document represents the historical Mid-Project milestone report authored at the conclusion of Week 2. It documents the verified state of Weeks 1–2 (synthetic data generation, BigQuery staging, dbt transformations, and initial PM4Py process discovery). The Week 3 deliverables (bottleneck detection, transition duration ranking, conformance checking, and As-Is vs. To-Be simulation) and Week 4 deliverables (3-page Power BI PBIP dashboard) described herein as forward-looking roadmap items were subsequently implemented, verified, and delivered in full.

---

## 1. Executive Summary

The CareFlow Clinical Pathway Analytics project has reached its Mid-Project milestone. Covering the scope of Weeks 1-2 results and establishing the Weeks 3-4 roadmap, the project successfully established the end-to-end data pipeline foundation and executed offline process discovery on the synthetic emergency department encounter log.

### Key Achievements to Date:
1. **Synthetic EHR Data Generation:** Generated a canonical dataset of 500 patient encounters and 3,140 chronological events (`data/raw/hospital_events_simulated.csv`) with verified schema integrity and deterministic reproducibility.
2. **Data Warehouse & dbt Architecture:** Designed the raw BigQuery schema contract (`schema_hospital_events_raw.sql`), developed the Python ingestion module (`src/bq_loader.py`), materialized the staging model as a BigQuery VIEW (`careflow_staging.stg_hospital_events`), and verified all 20 dbt data tests passing in the warehouse.
3. **Environment Hardening & Dependency Pinning:** Stabilized all 24 dependencies with prebuilt wheels for Python 3.12, locked `pm4py==2.7.8` in `requirements.txt`, and verified zero C-compiler dependencies.
4. **Offline Process Mining Engine (`src/process_miner.py`):** Implemented an automated process discovery pipeline that parses timestamps, enforces deterministic multi-key sorting, interfaces with PM4Py, extracts pathway variants, computes directly-follows transitions, and exports summary statistics.
5. **Rigorous Test Suite:** Built a comprehensive test suite of 68 automated unit tests and 8 subtests (100% pass rate) covering data generation, schema validation, dbt modeling, process mining metrics, and normalized schema parity.

---

## 2. Milestone Roadmap Assessment

| Roadmap Milestone | Original Schedule | Status | Implementation Evidence |
| :--- | :--- | :--- | :--- |
| **Week 1: Synthetic Event Log & Warehouse Setup** | Days 1-5 | **COMPLETED** | `src/data_generator.py`, `src/bq_loader.py`, `careflow_dbt/`, 37 unit tests passing (historical Week 1 snapshot). |
| **Week 2: Data Cleaning & Process Discovery** | Days 6-10 | **COMPLETED** | `src/staging_transform.py`, `src/normalize_event_log.py`, `src/process_miner.py`, `outputs/`, BigQuery staging view materialized, 20 dbt tests passed, full suite of 68 tests + 8 subtests passing. |
| **Mid-Project Review** | End of Week 2 | **COMPLETED** | This comprehensive report (`reports/MID_PROJECT_REVIEW.md`) validating discovery outputs and pipeline boundaries. |
| **Week 3: Bottleneck Modeling & Dashboarding** | Days 11-15 | **NOT STARTED** | Transition duration summaries ready for dimensional modeling and Power BI ingestion. |
| **Week 4: Conformance Checking & Final Report** | Days 16-20 | **PLANNED** | Ground-truth pathway variants documented for normative token-replay conformance checking. |

---

## 3. Data Pipeline Architecture & Verification

The CareFlow data pipeline bridges raw event ingestion, analytical transformation, and algorithmic process mining:

```text
[Simulated EHR Generator]
       | (500 cases, 3,140 events)
       v
 [data/raw/hospital_events_simulated.csv]
       |
       +-----------------------------------------+
       |                                         |
       v                                         v
[Offline Validation / Schema Gate]     [BigQuery Raw Layer (Verified)]
  - src/bq_loader.py (--mode offline)    - careflow_raw.hospital_events_raw
  - Strict type & null checking          - 3,140 events, 500 cases verified
       |                                         |
       v                                         v
[dbt Staging Models (careflow_dbt/)]   [dbt Warehouse View (Verified)]
  - Offline dbt parse & dbt ls           - careflow_staging.stg_hospital_events
  - 1 model, 20 tests discovered         - 3,140 events, 20 tests passed
       |                                         |
       +------------------+----------------------+
                          |
                          v
            [PM4Py Process Mining Engine]
              - src/process_miner.py
              - Multi-key deterministic sorting
              - DFG & Variant Extraction
                          |
                          v
             [outputs/ Reproducible Tables]
              - dfg_transitions_summary.csv
              - pathway_variants_summary.csv
              - process_mining_summary.json
```

### Cloud Integration Boundary & Verification Status
To maintain strict data engineering verification standards and cloud discipline:
- **Synthetic Dataset Disclosure:** All analyzed clinical event logs are synthetic (simulated EHR encounters generated via `src/data_generator.py` with 100% `SIMULATED` provenance tags). They do not represent real patient records or real hospital performance measurements.
- **Raw BigQuery Table (Verified):** The raw table `careflow_raw.hospital_events_raw` in GCP project `exalted-mode-467509-h1` has been verified via read-only inspection: contains 3,140 events, 500 unique cases, zero missing timestamps, zero null values across all six columns, and 100% `SIMULATED` provenance tags. Note: The physical table in BigQuery Sandbox was created without native date partitioning/clustering (migration deferred to preserve data safety), and tables and views in the Sandbox are subject to a default 60-day expiration window (scheduled for 2026-12-23 UTC).
- **BigQuery Staging View Materialization (Verified Live):** On October 24, 2026, the dbt staging model was executed against BigQuery (`dbt run --select stg_hospital_events`, `PASS=1`), successfully materializing `exalted-mode-467509-h1.careflow_staging.stg_hospital_events` as a BigQuery **VIEW**. Read-only metadata inspection confirms 3,140 rows, 500 unique cases, and 11 normalized staging fields (`case_id`, `event_sequence`, `raw_activity_name`, `activity_name`, `event_timestamp`, `event_date`, `department`, `resource_id`, `data_provenance`, `previous_activity`, `transition_minutes_from_previous`).
- **Warehouse dbt Data Tests (Verified Live):** On October 24, 2026, the full dbt test suite was executed against BigQuery (`dbt test`). All 20 data tests passed with zero errors (`Done. PASS=20 WARN=0 ERROR=0 TOTAL=20`), verifying primary keys, not-null constraints, and accepted values across both raw source and staged view.
- **Process Mining Decoupling & Metric Parity (Verified):** `src/process_miner.py` operates against both raw CSVs and the locally generated normalized staging dataset (`data/cleaned/stg_hospital_events.csv`). The Python staging transformation replicates the BigQuery SQL logic, verified to yield matching reported row counts (3,140), case counts (500), schema structure (11 fields), and downstream PM4Py process-mining metrics while supporting fully offline execution. An exhaustive cell-by-cell cloud comparison was not performed.

---

## 4. Discovered Process Mining Findings

The canonical dataset was processed through `src/process_miner.py`, yielding empirical metrics across the patient cohort:

### Cohort Overview
- **Total Cases:** 500 patient encounters
- **Total Events:** 3,140 logged activities
- **Distinct Activities:** 7 (`Registration`, `Triage`, `Consultation`, `Laboratory`, `X-Ray`, `Treatment`, `Discharge`)
- **Process Start:** 100% of cases start with `Registration` (500 cases)
- **Process End:** 100% of cases terminate with `Discharge` (500 cases)
- **Case Observed Duration:**
  - Minimum: 95.0 minutes (1.58 hours)
  - 25th Percentile: 147.0 minutes
  - Median: 211.0 minutes (3.52 hours)
  - Mean: 202.54 minutes (3.38 hours)
  - 75th Percentile: 254.0 minutes
  - Maximum: 354.0 minutes (5.90 hours)
  - Standard Deviation: 62.44 minutes

### Discovered Pathway Variants
Process discovery identified exactly **6 distinct clinical pathway variants**:

| Rank | Case Volume | Cohort % | Activity Sequence Trace | Clinical Interpretation |
| :---: | :---: | :---: | :--- | :--- |
| **1** | 200 | 40.0% | `Registration -> Triage -> Consultation -> Treatment -> Discharge` | Standard low-acuity pathway (no diagnostic imaging or labs). |
| **2** | 110 | 22.0% | `Registration -> Triage -> Consultation -> Laboratory -> Consultation -> Treatment -> Discharge` | Routine diagnostic lab investigation with physician follow-up. |
| **3** | 80 | 16.0% | `Registration -> Triage -> Consultation -> X-Ray -> Consultation -> Treatment -> Discharge` | Routine radiological examination with physician follow-up. |
| **4** | 50 | 10.0% | `Registration -> Triage -> Consultation -> Laboratory -> X-Ray -> Consultation -> Treatment -> Discharge` | High-complexity multi-diagnostic pathway requiring both lab and radiology. |
| **5** | 35 | 7.0% | `Registration -> Triage -> Triage -> Consultation -> Treatment -> Discharge` | Clinical condition deterioration/re-evaluation during triage waiting interval. |
| **6** | 25 | 5.0% | `Registration -> Triage -> Triage -> Consultation -> Laboratory -> Consultation -> Treatment -> Discharge` | Re-triage encounter combined with laboratory investigation. |

### Re-Triage Operational Analysis
- **Volume:** Re-triage occurs in exactly 60 encounters (12.0% of all cases; 35 in Variant 5 + 25 in Variant 6).
- **Self-Loop Transition:** The directly-follows graph contains 60 self-loop transitions for `Triage -> Triage`.
- **Interval Duration:** Median observed duration between consecutive triages is **64.5 minutes** (Mean: 65.63 min, Min: 40.0 min, Max: 88.0 min).
- **Clinical Implication:** In clinical environments, repeat triage indicates clinical deterioration while awaiting consultation, representing a critical operational metric for patient safety audits.

### Directly-Follows Graph (DFG) Transitions
Process discovery revealed exactly **10 directed transitions** connecting the 7 activities:

| Source Activity | Target Activity | Transition Count | Median Observed Duration | Mean Observed Duration | Min Observed Duration | Max Observed Duration |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **Laboratory** | **Consultation** | 135 | **67.0 min** | 67.44 min | 42.0 min | 95.0 min |
| **Triage** | **Triage** | 60 | **64.5 min** | 65.63 min | 40.0 min | 88.0 min |
| **X-Ray** | **Consultation** | 130 | **61.0 min** | 60.36 min | 36.0 min | 85.0 min |
| **Laboratory** | **X-Ray** | 50 | **51.0 min** | 53.50 min | 36.0 min | 74.0 min |
| **Treatment** | **Discharge** | 500 | **52.0 min** | 52.01 min | 27.0 min | 80.0 min |
| **Consultation** | **X-Ray** | 80 | **39.0 min** | 38.19 min | 21.0 min | 54.0 min |
| **Consultation** | **Treatment** | 500 | **38.0 min** | 37.84 min | 21.0 min | 55.0 min |
| **Consultation** | **Laboratory** | 185 | **37.0 min** | 37.26 min | 20.0 min | 54.0 min |
| **Triage** | **Consultation** | 500 | **25.0 min** | 25.09 min | 10.0 min | 40.0 min |
| **Registration** | **Triage** | 500 | **20.0 min** | 20.58 min | 8.0 min | 33.0 min |

---

## 5. Clinical Terminology & Metric Interpretation

To maintain rigorous healthcare analytics standards, timing metrics must be correctly characterized:

1. **Observed Transition Duration vs. True Waiting Time:**
   - The event log records discrete event milestone timestamps (`Timestamp`).
   - The elapsed duration between Activity $A$ and Activity $B$ represents the *total observed transition duration*.
   - In standard EHR event logs without dual `start_timestamp` and `complete_timestamp` tracking, observed transition duration conflates:
     - Active service delivery duration (e.g., blood draw, specimen centrifuge, analysis)
     - Inter-departmental patient/specimen transit time
     - Queue waiting time awaiting an available physician
   - Therefore, `Laboratory -> Consultation` (median 67.0 min) is accurately reported as the *longest direct transition in the pathway*, but must **not** be asserted as purely "idle patient waiting time" or a definitive "clinical bottleneck" without queue-depth or capacity modeling.

2. **Transition Priority Ranking:**
   - `Laboratory -> Consultation` exhibits the highest median transition duration across all 10 transitions (67.0 min).
   - `Triage -> Triage` exhibits the second-highest median duration (64.5 min) and indicates waiting queue reassessments.
   - `X-Ray -> Consultation` exhibits the third-highest median duration (61.0 min).
   - Diagnostic review steps (`Laboratory -> Consultation` and `X-Ray -> Consultation`) consistently require the longest transit/processing intervals before treatment can proceed.

---

## 6. Limitations of the Simulated Dataset

While the simulated dataset effectively models clinical pathway variants and diagnostic branching, its analytical scope has known boundaries:

1. **Deterministic Variation:** Pathways and duration distributions were generated using a fixed pseudorandom seed (42). Real clinical logs exhibit greater variance, extreme outliers (e.g., multi-day admissions), and non-normal distributions.
2. **Simplified Pathway Scope:** The log models 6 controlled pathways with 100% adherence to Registration start and Discharge finish. In real hospital emergency logs, departures occur (e.g., Left Without Being Seen [LWBS], Emergency Inpatient Admission, Critical Care Transfer, Expired).
3. **Absence of Concurrency / Resource Contention:** The simulator calculates durations independently per case rather than simulating real-time queue contention against finite staff (e.g., 2 triage nurses managing 40 arriving patients simultaneously).
4. **Single Timestamp Representation:** As noted, each event possesses a single point-in-time timestamp rather than lifecycle start/end intervals.

---

## 7. Weeks 3 and 4 Action Roadmap

With discovery completed and verified, the project advances to Week 3 analytics and Week 4 conformance checking:

### Week 3: Bottleneck Modeling & Power BI Dashboard (Not Started)
*Note: Week 3 dimensional modeling (`fact_patient_events`, `dim_patient`, etc.) and the final Power BI dashboard have not started. They remain planned for Week 3 pending review approval.*
- **Dimensional Modeling:** Structure star-schema data models (Fact: `fact_patient_events`, Dimensions: `dim_patient`, `dim_activity`, `dim_department`, `dim_pathway_variant`).
- **Transition Duration Metrics:** Precalculate transition durations, re-triage indicators, and case-level elapsed times in SQL/dbt staging views.
- **Power BI Dashboard Development:**
  - Executive Overview: Cohort volume, average length of stay (ALOS), variant breakdown.
  - Process Explorer: Visual DFG transition flow and pathway variant selector.
  - Operational Bottlenecks: Distribution histograms for `Laboratory -> Consultation` and `Triage -> Triage` intervals.
  - Re-Triage Audit: Dedicated safety drill-down for the 60 re-triage encounters.

### Week 4: Conformance Checking & Final Project Deliverables (Planned)
- **Normative Pathway Definition:** Formulate Variant 1 (`Registration -> Triage -> Consultation -> Treatment -> Discharge`) and standard diagnostic variants as normative clinical reference models.
- **Token-Based Replay & Alignment:** Measure fitness, precision, and deviation percentages using PM4Py conformance checking algorithms.
- **Final Report & Presentation:** Produce the formal internship capstone report and executive presentation summarizing operational insights and recommended clinical process interventions.

---

## 8. Verification & Audit Summary

- **Baseline Dataset Integrity:** `data/raw/hospital_events_simulated.csv` verified unchanged (197,844 bytes, 3,141 lines, MD5: `d8de55d0fccd116b3482c4c05a681d9e`).
- **Regression Test Coverage:** 68 unit tests + 8 subtests passing across 4 test modules:
  - `tests/test_bq_loader.py`: 14 passed
  - `tests/test_data_generator.py`: 12 passed (+ 8 subtests)
  - `tests/test_dbt_setup.py`: 11 passed
  - `tests/test_process_miner.py`: 31 passed (19 baseline + 12 normalized schema tests)
- **BigQuery Staging & Warehouse Tests:** `careflow_staging.stg_hospital_events` VIEW materialized on October 24, 2026; 20/20 dbt data tests verified passing against BigQuery (`PASS=20, WARN=0, ERROR=0`).
- **dbt Offline Verification:** Verified valid manifest via `dbt parse` (Exit code: 0) and confirmed 1 model, 20 data tests, and 1 source via `dbt ls`.
- **Code Quality:** `git diff --check` passed with 0 whitespace errors.

*Report Prepared By: Data Analyst Intern*
*Supervised By: Senior Process Mining & Data Engineering Mentor*
