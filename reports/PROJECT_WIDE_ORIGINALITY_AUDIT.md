# CareFlow: Clinical Pathway Process Mining & Operations Analytics
## Project-Wide Originality, Academic Integrity & Attribution Audit

---

**Project Title:** CareFlow Clinical Pathway Analytics
**Lead Author / Intern:** Dileep Songa
**Repository:** `C:\project\careflow-clinical-pathway`
**GitHub Repository:** [careflow-clinical-pathway](https://github.com/dileep-songa/careflow-clinical-pathway)
**Evaluation Date:** November 2026
**Audit Scope:** Complete repository-wide review (documentation, reports, code, queries, tests, schemas, and configurations)
**Verification Baseline:** 175 Pytest tests (+8 subtests) passing, PBIP structural validator passing, pip check clean

---

## 1. Executive Summary & Purpose

This audit report documents a project-wide originality, academic integrity, and factual attribution review conducted across the entire **CareFlow Clinical Pathway Analytics** codebase and documentation suite.

The purpose of this audit is to guarantee that:
1. All technical explanations, architectural decisions, and analytical findings reflect the specific, verified implementation of CareFlow.
2. External algorithms, methodologies, frameworks, and background clinical concepts are accurately attributed to their respective authors and documentation.
3. No claims of independent invention are made for standard computer science, data engineering, or process mining techniques.
4. All reported numerical metrics, transition durations, case volumes, and test counts strictly match the underlying empirical outputs.
5. All clinical disclaimers regarding synthetic data boundaries and the distinction between elapsed clock time and pure patient waiting time are rigorously maintained.

---

## 2. Files and Folders Reviewed

The audit encompassed every tracked and staged artifact across the repository:

### A. Root Markdown & Planning Documentation
- [`README.md`](../README.md): Project overview, architecture diagrams, benchmark metrics, quickstart guide, packaging guide, and author background.
- [`DEVELOPMENT_PLAN.md`](../DEVELOPMENT_PLAN.md): 4-week, 20-day chronological engineering roadmap from initial setup to final presentation.
- [`DAILY_LOG.md`](../DAILY_LOG.md): Comprehensive Day 1 to Day 10 chronological engineering journal documenting exact commands, outputs, and decisions.
- [`PROJECT_UNDERSTANDING.md`](../PROJECT_UNDERSTANDING.md): Day 1 initial problem framing, business context, and preliminary workflow event mappings.
- [`DATA_SCHEMA.md`](../DATA_SCHEMA.md): Exploratory schema dictionary and documentation of the evolution into the canonical 6-column raw and 11-column normalized contracts.
- [`requirements.txt`](../requirements.txt) & [`.github/workflows/ci.yml`](../.github/workflows/ci.yml): Dependency specifications and GitHub Actions CI workflow definition.

### B. Milestone & Technical Reports (`reports/`)
- [`reports/FINAL_INTERNSHIP_REPORT.md`](FINAL_INTERNSHIP_REPORT.md): 14-section formal technical internship report covering problem context, architecture, data engineering, process mining, bottleneck analysis, 7-rule conformance checking, To-Be simulation, Power BI architecture, QA, and references.
- [`reports/FINAL_PRESENTATION.md`](FINAL_PRESENTATION.md): 12-slide executive presentation outline with speaker notes and diagram specifications (locally excluded via `.git/info/exclude`).
- [`reports/MID_PROJECT_REVIEW.md`](MID_PROJECT_REVIEW.md): Historical milestone review authored at the conclusion of Week 2.
- [`reports/WEEK_3_PROGRESS_REPORT.md`](WEEK_3_PROGRESS_REPORT.md): Historical milestone review authored at the conclusion of Week 3.

### C. Power BI Architecture & PBIP Reporting (`powerbi/`)
- [`powerbi/CAREFLOW_PBIP_VALIDATION_REPORT.md`](../powerbi/CAREFLOW_PBIP_VALIDATION_REPORT.md): Forensic technical report detailing Power Query M `Table.ReplaceValue`, BigQuery offline decoupling, and DAX percentage scaling fixes.
- [`powerbi/CAREFLOW_WEEK4_FINAL_REVIEW.md`](../powerbi/CAREFLOW_WEEK4_FINAL_REVIEW.md): Technical review of the finalized 3-page, 22-container Power BI project (`CareFlow_Dashboard.pbip`).
- [`powerbi/powerbi_data_dictionary.md`](../powerbi/powerbi_data_dictionary.md): Semantic model entity and attribute dictionary.
- [`powerbi/powerbi_measures_reference.md`](../powerbi/powerbi_measures_reference.md): DAX measures reference documentation.
- [`powerbi/powerbi_dashboard_implementation_plan.md`](../powerbi/powerbi_dashboard_implementation_plan.md): Initial 4-page dashboard blueprint and loading guide.
- [`powerbi/build_careflow_pbip.py`](../powerbi/build_careflow_pbip.py): Automated PBIP generator script.
- [`powerbi/test_validate_pbip.py`](../powerbi/test_validate_pbip.py): Standalone PBIP validator and regression test suite.
- `powerbi/CareFlow_Dashboard_Project/CareFlow_Dashboard.SemanticModel/model.bim`: Active TMSL semantic model definition (10 total tables: 5 business/data tables + 5 auto date tables; 19 DAX measures: `stg_hospital_events`: 14, `pathway_variants_summary`: 3, `bottleneck_analysis_summary`: 1, `pathway_improvement_comparison`: 1).
- `powerbi/CareFlow_Dashboard_Project/CareFlow_Dashboard.Report/report.json`: Active report layout definition (3 pages, 22 visual containers).

### D. Data Warehouse & Transformation (`careflow_dbt/` & `sql/`)
- [`careflow_dbt/dbt_project.yml`](../careflow_dbt/dbt_project.yml): dbt Core project configuration.
- [`careflow_dbt/README.md`](../careflow_dbt/README.md): dbt staging view architecture and execution guide.
- [`careflow_dbt/models/staging/stg_hospital_events.sql`](../careflow_dbt/models/staging/stg_hospital_events.sql): SQL staging transformation with deduplication and window functions.
- [`careflow_dbt/models/staging/_sources.yml`](../careflow_dbt/models/staging/_sources.yml) & [`_staging_models.yml`](../careflow_dbt/models/staging/_staging_models.yml): Schema test assertions.
- [`sql/schema_hospital_events_raw.sql`](../sql/schema_hospital_events_raw.sql): BigQuery DDL table specification with daily partitioning and clustering.

### E. Python Source Modules (`src/`)
- [`src/data_generator.py`](../src/data_generator.py): Probabilistic synthetic patient encounter generator (500 cases, 3,140 events, seed `42`).
- [`src/normalize_event_log.py`](../src/normalize_event_log.py): Local Python normalization script mirroring dbt staging logic.
- [`src/staging_transform.py`](../src/staging_transform.py): Standalone data transformation function implementing multi-key sorting, deduplication, and lag calculations.
- [`src/bq_loader.py`](../src/bq_loader.py): BigQuery schema validator and offline CSV integrity checker.
- [`src/process_miner.py`](../src/process_miner.py): PM4Py Directly-Follows Graph discovery, variant extraction, and duration statistical engine.
- [`src/bottleneck_analyzer.py`](../src/bottleneck_analyzer.py): Transition duration quantification and delay ranking.
- [`src/bottleneck_visualizer.py`](../src/bottleneck_visualizer.py): Matplotlib 300 DPI horizontal bar chart generator.
- [`src/conformance_checker.py`](../src/conformance_checker.py): 7-rule clinical pathway conformance audit engine.
- [`src/pathway_improvement.py`](../src/pathway_improvement.py): Counterfactual As-Is vs. To-Be scenario simulation engine.
- [`src/constants.py`](../src/constants.py) & [`src/project_config.py`](../src/project_config.py): Project configuration and domain dictionary constants.

### F. Automated Test Suites (`tests/`)
- All 9 test modules in `tests/` (`test_data_generator.py`, `test_bq_loader.py`, `test_dbt_setup.py`, `test_process_miner.py`, `test_bottleneck_analyzer.py`, `test_bottleneck_visualization.py`, `test_bottleneck_findings.py`, `test_conformance_checker.py`, `test_pathway_improvement.py`) plus `powerbi/test_validate_pbip.py`.

### G. Analytical Output Artifacts (`outputs/`)
- [`outputs/bottleneck_findings.md`](../outputs/bottleneck_findings.md), [`outputs/conformance_findings.md`](../outputs/conformance_findings.md), [`outputs/pathway_improvement_report.md`](../outputs/pathway_improvement_report.md), and associated summary CSV/JSON files.

---

## 3. Scope and Exclusions

To maintain an objective, realistic audit boundary, the following categories were excluded from originality conclusions:
1. **Third-Party Dependencies & Vendor Libraries:** Code within Python standard libraries or external packages (`pandas`, `numpy`, `pm4py`, `pyarrow`, `dbt-core`, `dbt-bigquery`, `pytest`, `matplotlib`) was not audited for plagiarism, as these represent standard external tools.
2. **Standard API Syntax, Boilerplate & Design Patterns:** Common programming conventions, CLI argument parsing (`argparse`), standard DAX expressions (`CALCULATE`, `DIVIDE`, `AVERAGEX`), standard Power Query M formulas, SQL DDL/DML grammar, and Git configuration syntax were treated as foundational technical syntax, not subject to plagiarism claims.
3. **Generated Data Logs:** Raw CSV files (`hospital_events_simulated.csv`) and generated binary files (`.png`, `.pdf`) were evaluated solely for factual consistency and data integrity, not prose originality.
4. **Local Virtual Environments & Caches:** `.venv/`, `.git/`, `.pytest_cache/`, `__pycache__/`, and `.pbi/` local settings folders were strictly excluded.

---

## 4. Originality & Attribution Findings

### A. Original Engineering Contributions
CareFlow demonstrates authentic engineering solutions designed specifically to address the challenges of clinical pathway analytics:
- **Independent Staging Normalization:** The development of `src/normalize_event_log.py` and `src/staging_transform.py` provides a zero-spend offline pipeline that mirrors dbt SQL transformations byte-for-byte, resolving cloud cost barriers while maintaining analytical parity.
- **Power Query M Circular Reference Decoupling:** The architectural diagnosis and resolution of the VertiPaq refresh deadlock (by decoupling `stg_hospital_events (2)` from query-chaining into an independent direct CSV load expression) represents an original debugging accomplishment.
- **Rule-Based Clinical Conformance Engine:** Rather than relying solely on black-box Petri net token replay, CareFlow authored an explicit 7-rule clinical protocol auditor (`src/conformance_checker.py`) that outputs human-interpretable compliance flags and categorical breakdown statistics.
- **Doctor / Demographic Slicing Evaluation:** The technical investigation demonstrating why event-level doctor slicing breaks case-level triage conformance measures in DAX represents an original analytical evaluation grounded in data modeling integrity.

### B. Attribution of External Methodologies & Background Literature
All external concepts and software are attributed to their respective creators:
- **Process Mining & Directly-Follows Graphs:** Explicitly attributed to Wil van der Aalst (*Process Mining: Data Science in Action*, 2016).
- **PM4Py Framework:** Formally cited as:
  > Berti, A., van Zelst, S. J., & van der Aalst, W. M. P. (2019). *Process Mining for Python (PM4Py): Bridging the Gap Between Process- and Data Science*. Proceedings of the ICPM Demo Track 2019, 13–16. https://doi.org/10.5281/zenodo.3632867
- **Emergency Triage Background Literature:** Secondary triage reassessment concepts are referenced against background clinical literature:
  > Gilboy, N., Tanabe, T., Travers, D., & Rosenau, A. M. (2011). *Emergency Severity Index (ESI): A Triage Tool for Emergency Department Care, Version 4. Implementation Handbook 2012 Edition*. AHRQ Publication No. 12-0014. Agency for Healthcare Research and Quality, Rockville, MD.
  *(CareFlow explicitly clarifies that ESI is cited as clinical background context, not as the implementation specification of CareFlow's custom conformance checker).*
- **Healthcare Process Mining:** General methodology contextualized with:
  > Rebuge, Á., & Ferreira, D. R. (2012). *Business process analysis in healthcare environments: A methodology based on process mining*. *Information Systems*, 37(2), 99–116.
- **Data Engineering Platforms:** Official documentation from dbt Labs (dbt Core), Google Cloud (BigQuery), and Microsoft (Power BI PBIP/TMSL) is cited throughout.

---

## 5. Issues Corrected Project-Wide

During the project-wide audit, the following inconsistencies and unsubstantiated claims were identified and corrected:

| File Path | Location / Section | Issue Identified | Resolution Applied |
| :--- | :--- | :--- | :--- |
| [`reports/FINAL_INTERNSHIP_REPORT.md`](FINAL_INTERNSHIP_REPORT.md) | **Section 14.1** | Outdated PM4Py workshop citation. | Replaced with official ICPM 2019 publication citation and DOI (`10.5281/zenodo.3632867`). |
| [`reports/FINAL_INTERNSHIP_REPORT.md`](FINAL_INTERNSHIP_REPORT.md) | **Section 1.1 & 14.1** | Ambiguous reference to ESI triage protocol. | Clarified that ESI is background clinical literature, not the source code for CareFlow's conformance rules. |
| [`reports/FINAL_INTERNSHIP_REPORT.md`](FINAL_INTERNSHIP_REPORT.md) | **Section 7.1 & 7.2** | Unsupported claims regarding centrifugation, chemical assays, and mismatched bottleneck ranks 6–10. | Removed unmeasured laboratory procedures; aligned all 10 transition rows, counts, means, medians, and min-max bounds exactly with `outputs/bottleneck_analysis_summary.csv`. |
| [`reports/FINAL_INTERNSHIP_REPORT.md`](FINAL_INTERNSHIP_REPORT.md) | **Section 11.1** | Test table listed non-existent files (`test_staging_transform.py`, `test_normalize_event_log.py`). | Replaced with exact 10 test modules matching the 175 tests and 8 subtests collected by pytest. |
| [`reports/FINAL_INTERNSHIP_REPORT.md`](FINAL_INTERNSHIP_REPORT.md) | **Section 5.2 & 10.3** | Unsupported claim of BigQuery view materialization; prompt instruction phrasing ("In accordance with Phase 2"). | Clarified dbt view model as authored and validated offline via `dbt parse`; removed prompt-referencing text. |
| [`README.md`](../README.md) | **Repository Tree (line 307)** | Screenshot render dimensions labeled as `2400x1350`. | Corrected to actual exported image dimensions (`2391x1383`). |
| [`README.md`](../README.md) | **Bottleneck Table (lines 216–225)** | Speculative language implying PACS/radiology internal sub-steps were measured; minor median rounding mismatch. | Replaced with objective operational interval descriptions and aligned medians with CSV ground truth. |
| [`powerbi/CAREFLOW_PBIP_VALIDATION_REPORT.md`](../powerbi/CAREFLOW_PBIP_VALIDATION_REPORT.md) | **Lines 43, 78, 128** | Table and measure count clarification; audit table columns and subtitle alignment. | Documented 10 total tables (5 data tables + 5 auto date tables) and 19 DAX measures (`stg_hospital_events`: 14, `pathway_variants_summary`: 3, `bottleneck_analysis_summary`: 1, `pathway_improvement_comparison`: 1); aligned audit table columns (`Case ID`, `Event Sequence`, `Activity Name`, `Department`, `Event Timestamp`) and subtitle. |
| [`powerbi/CAREFLOW_WEEK4_FINAL_REVIEW.md`](../powerbi/CAREFLOW_WEEK4_FINAL_REVIEW.md) | **Title, Section 1.2, 2.2, 5.1** | Promotional "Premium" adjectives; Page 2 KPI row described as 3 cards instead of 4; data visual count stated as 15. | Removed promotional phrasing; updated Page 2 to 4 cards; corrected data visual count to 16 (22 containers total). |
| [`powerbi/powerbi_dashboard_implementation_plan.md`](../powerbi/powerbi_dashboard_implementation_plan.md) | **Section 1** | Outdated 4-page preliminary dashboard blueprint without version context. | Added callout note explaining that Pages 3 & 4 were consolidated into Page 3 in the finalized 3-page PBIP release. |
| [`powerbi/powerbi_data_dictionary.md`](../powerbi/powerbi_data_dictionary.md) | **Overview & Table 1** | Scope labeled as 4-page dashboard; speculative clinical descriptions in waiting time note. | Added 3-page PBIP consolidation context; clarified elapsed duration as clock intervals between milestone timestamps. |
| [`reports/FINAL_PRESENTATION.md`](FINAL_PRESENTATION.md) | **Slides 2, 7, 11** | Mentions of centrifugation, chemical assays, and radiologist review in speaker notes. | Replaced with objective milestone interval definitions; confirmed local Git exclusion via `.git/info/exclude`. |

---

## 6. Verification of Project-Specific Facts

Every reported empirical figure across the documentation was cross-verified against the codebase and generated outputs:

```text
====================================================================================================
CareFlow Technical Baseline Verification Matrix
====================================================================================================
• Cohort Patient Enounters       : 500 cases (VERIFIED in stg_hospital_events.csv, Case_ID C001-C500)
• Total Clinical Events          : 3,140 milestone records (VERIFIED across 7 activity types)
• Discovered Pathway Variants    : 6 empirical variants (VERIFIED in pathway_variants_summary.csv)
  - Variant 1 (Standard Linear)  : 200 cases (40.0%)
  - Variant 2 (Diagnostic Lab)   : 110 cases (22.0%)
  - Variant 3 (Diagnostic X-Ray) : 80 cases (16.0%)
  - Variant 4 (Combined Diag)    : 50 cases (10.0%)
  - Variant 5 (Routine + Re-Tri) : 35 cases (7.0%)
  - Variant 6 (Lab + Re-Triage)  : 25 cases (5.0%)
• Conformance Classification     : 440 conformant (88.0%), 60 review candidates (12.0% repeat triage)
• Diagnostic Cohort Volume       : 265 unique cases (Variants 2, 3, 4, 6: 110 + 80 + 50 + 25 = 265)
• Diagnostic Follow-up Rule      : 100.0% adherence (265 / 265 cases have follow-up consults)
• Directly-Follows Transitions   : 10 distinct edges (VERIFIED in dfg_transitions_summary.csv)
• Top 3 Bottlenecks (Mean / Med) : Lab->Consult (67.44m / 67.0m), Triage->Triage (65.63m / 64.5m),
                                   X-Ray->Consult (60.36m / 61.0m)
• Cohort Cycle Time (Baseline)   : Mean = 202.54 mins, Median = 211.00 mins, Std Dev = 62.44 mins
• To-Be Simulation Projections   : Mean = 181.77 mins (-10.25%), Median = 191.18 mins (-9.39%),
                                   Variants = 4 (-33.33%), Events = 3,080 (-1.91%)
• Test Suite Execution           : 175 passed, 8 subtests passed in pytest; exit code 0
• Power BI Visual Containers     : 3 pages, 22 visual containers (16 data visuals + 6 textboxes)
====================================================================================================
```

---

## 7. Claims That Could Not Be Verified & Transparent Boundaries

To maintain complete academic and operational honesty:
1. **Live BigQuery Transformation Execution:** Live cloud materialization (`dbt run` against BigQuery) was intentionally not executed during final testing to prevent cloud compute charges under zero-spend policies. Offline parsing (`dbt parse`) and local Python staging parity are fully verified.
2. **Actual Patient Waiting Room Idle Time:** The event log records discrete milestone completion timestamps only. Whether a patient was actively being examined, resting, in transit, or waiting passively between timestamps cannot be determined from the synthetic event log.
3. **Real-World Clinical Efficacy:** The 10.3% encounter duration reduction and elimination of repeat triage are simulated scenario projections. They demonstrate data modeling capabilities and must not be interpreted as proven clinical trial results.
4. **GitHub Actions CI Scope vs. Updated Local Validator:** Remote GitHub Actions Run #42456452180 at commit `a67f88d` verified 175 tests with 14 warnings on Ubuntu Python 3.12 (successful run), executing `powerbi/test_validate_pbip.py` against the earlier five-business/data-table validator assertion. The validator was subsequently enhanced in the local working tree to explicitly check all 10 tables (5 data + 5 date) and all 19 DAX measures. It is explicitly disclosed that CI verified the earlier five-business/data-table assertion at commit `a67f88d`, while the updated 10-table / 19-measure validator check is verified in the local environment.

---

## 8. Academic Integrity & Plagiarism Statement

> **Formal Academic Integrity Disclosure:**
> No obvious unattributed copied passages were identified during this project-wide editorial review. This review was conducted through systematic codebase inspection, git diff auditing, and reference verification; it was not performed using Turnitin, Copyscape, or another external commercial similarity-detection service. Consequently, no percentage similarity score or formal third-party plagiarism certification is claimed or provided. External methodologies, mathematical formulations, software libraries, and reference documentation remain properly attributed throughout the repository.

---

## 9. Final Verification Suite Results

The validation suite was executed across environments to verify stability:
- **Pytest Suite (Local Windows):** `python -m pytest -q --tb=short` $\rightarrow$ **175 passed, 8 subtests passed in 24.29s (Exit code 0)**.
- **Pytest Suite (Remote CI Run #42456452180 at commit `a67f88d`):** `python -m pytest -q --tb=short` $\rightarrow$ **175 passed with 14 warnings on Ubuntu Python 3.12 (Exit code 0)**.
- **Power BI PBIP Validator (Local Working Tree):** `python powerbi/test_validate_pbip.py` $\rightarrow$ **PASS (Verified all 10 tables, 19 DAX measures, 16 data visuals, 6 textboxes; exit code 0)**.
- **Power BI PBIP Validator (Remote CI):** Executed under earlier five-business/data-table assertion at commit `a67f88d` $\rightarrow$ **PASS (Exit code 0)**.
- **Pip Check:** `python -m pip check` $\rightarrow$ **No broken requirements found (Exit code 0)**.
- **Git Diff Formatting:** `git diff --check` $\rightarrow$ **Clean (0 whitespace or newline errors)**.
- **Git Exclusion Status:** `git check-ignore -v reports/FINAL_PRESENTATION.md` $\rightarrow$ **Confirmed ignored by `.git/info/exclude`**.

*Audit complete. All files verified and prepared for submission review.*
