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
- **dbt Staging Cloud Materialization (Verified):** The staging model was materialized as a BigQuery VIEW (`careflow_staging.stg_hospital_events`) on October 24, 2026, confirmed returning 3,140 events across 500 cases with 100% simulated provenance. Offline process mining operates completely and deterministically on the verified local normalized dataset (`data/cleaned/stg_hospital_events.csv`), which maintains 100% parity with the cloud staging view. Further materializations of physical warehouse tables remain deferred under zero-spend policies.

---

## Week 3: Process Mining & Analysis

### Objectives
- [x] Discover process flow and variant frequencies
- [x] Detect bottlenecks and rank transition times
- [x] Measure observed elapsed times across clinical milestones
- [x] Implement workflow conformance checking and audit rules
- [x] Model hypothetical As-Is vs. To-Be operational improvement scenarios
- [x] Build business insights, visual charts, and executive progress report

### Day 11–12: Bottleneck Analysis Engine
- [x] Build `src/bottleneck_analyzer.py` with data quality and timing consistency checks
- [x] Export ranked transition metrics to `outputs/bottleneck_analysis_summary.csv`
- [x] Add 20 automated unit tests in `tests/test_bottleneck_analyzer.py`

### Day 13: Bottleneck Visualization & Findings Report
- [x] Implement `src/bottleneck_visualizer.py` generating `outputs/bottleneck_analysis.png`
- [x] Compile detailed analytical report `outputs/bottleneck_findings.md`
- [x] Add 32 tests across `tests/test_bottleneck_visualization.py` and `tests/test_bottleneck_findings.py`

### Day 14: Patient Pathway Conformance Checking
- [x] Implement `src/conformance_checker.py` evaluating 7 clinical workflow rules
- [x] Classify 60 re-triage encounters as operational review candidates
- [x] Export case-level results and JSON/Markdown summaries (`outputs/conformance_*`)
- [x] Add 23 unit tests in `tests/test_conformance_checker.py`

### Day 15: As-Is vs. To-Be Improvement Engine & Full Audit
- [x] Build `src/pathway_improvement.py` modeling queue coordination and administrative streamlining
- [x] Recalculate duration percentiles and variant distributions from simulated traces
- [x] Export comparison CSV, JSON summary, Markdown report, and PNG chart (`outputs/pathway_improvement_*`)
- [x] Add 28 unit tests in `tests/test_pathway_improvement.py` (interim Week 3 baseline: 171 passed, 8 subtests passed; finalized at 175 passed, 8 subtests passed in Week 4)
- [x] Complete Week 3 Progress Report (`reports/WEEK_3_PROGRESS_REPORT.md`)

---

## Week 4: Dashboard & Final Submission

### Objectives
- [x] Build final dashboard (3-page standalone PBIP with TMSL semantic model: 10 total tables, 19 DAX measures, 16 data visuals, 6 textboxes, custom CY26SU05 theme)
- [x] Prepare presentation (`reports/FINAL_PRESENTATION.md` covering 12 slides with speaker notes and visual references)
- [x] Write final report (`reports/FINAL_INTERNSHIP_REPORT.md` covering all project phases)
- [x] Final demo and presentation walkthrough preparation
- [ ] Official internship sign-off and mentor final approval (pending external review)

### Day 16–17: Power BI Project (PBIP) Architecture & Visual Overhaul
- [x] Resolved VertiPaq evaluation cycle by decoupling `stg_hospital_events (2)` into direct independent CSV import
- [x] Implemented relative percentage change formula `(proposed - baseline) / baseline` with `+0.0%;-0.0%;0.0%` formatting
- [x] Configured Segoe UI healthcare design system (`CY26SU05.json`) with deep navy (`#102A43`) and clinical teal (`#14B8A6`)
- [x] Built 3 interactive analytical pages (Hospital Overview, Patient Flow, Transition Analysis & Process Improvement)
- [x] Created standalone automated validator (`powerbi/test_validate_pbip.py`) verifying all 22 visual containers and TMSL model integrity

### Day 18–19: CI/CD Pipeline & Dependency Hardening
- [x] Established GitHub Actions CI workflow (`.github/workflows/ci.yml`) on Ubuntu Python 3.12
- [x] Resolved dbt-core 1.12.6 package constraints (`click==8.3.1`, `google-cloud-bigquery==3.46.1`, `python-dotenv==1.2.4`, `python-dateutil==2.9.0.post0`)
- [x] Resolved NumPy 1.x integer JSON serialization in `src/process_miner.py` via `_json_serial_default` and dataclass integer casting
- [x] Resolved dbt offline parse isolation in `tests/test_dbt_setup.py` via ephemeral profile generation in temporary directories
- [x] Verified test pass rate (175 passed with 14 warnings in GitHub Actions Run #42456452180 at commit a67f88d; 175 passed, 8 subtests passed locally)

### Day 20: Final Technical Reporting & Presentation Deck
- [x] Authored technical internship report (`reports/FINAL_INTERNSHIP_REPORT.md`)
- [x] Prepared 12-slide presentation outline (`reports/FINAL_PRESENTATION.md`) with speaker delivery notes
- [x] Documented technical evaluation of doctor-only and demographic filtering boundaries
- [x] Conducted full repository factual-accuracy audit and whitespace verification

---

## Daily Commit Guidance
- Commit after each meaningful task
- Use format: `feat: ...`, `data: ...`, `analysis: ...`, `docs: ...`
- Push updates to GitHub daily
