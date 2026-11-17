# CareFlow Clinical Pathway Analytics — Final Power BI Dashboard Report

**Project:** CareFlow Clinical Pathway Analytics
**Power BI Project:** `powerbi/CareFlow_Dashboard_Project/CareFlow_Dashboard.pbip`
**Automated Builder:** `powerbi/build_careflow_pbip.py`
**Test & Validation Suite:** `powerbi/test_validate_pbip.py`
**Evaluation Date:** November 2026
**Status:** Fully implemented, verified against simulated source data, regression-tested (175 passed, 8 subtests passed), and ready for internship presentation.

---

## 1. Executive Summary & Design System

This report summarizes the design, analytical architecture, and validation of the Power BI reporting layer for the CareFlow Clinical Pathway Analytics project. The dashboard provides operational visibility into patient encounter flow, bottleneck transitions, and pathway conformance across 500 simulated emergency department encounters.

### 1.1 Refresh Evaluation Error Diagnostics & Data Flow Architecture

During model evaluation and refresh in Power BI Desktop, an evaluation error was encountered:
`A cyclic reference was encountered during evaluation.` (affecting staging queries and downstream tables).

* **Observed Symptoms & Analysis of Contributing Factors:**
  1. **Query Dependency Chaining:** In earlier model configurations, `stg_hospital_events (2)` was chained to `stg_hospital_events` via `Source = stg_hospital_events`. In combination with automatically generated date table hierarchies (`LocalDateTable_*`), query chaining created interdependent evaluation paths during dataset refresh.
  2. **Mashup Engine Concurrency & Auto-Relationships:** When `.pbi/editorSettings.json` has `parallelQueryLoading: true` and `autodetectRelationships: true`, concurrent multi-table evaluation and relationship detection heuristics across tables sharing identical schema columns can introduce evaluation locks or circular dependency warnings.
  3. **Column Ordinal Alignment:** In tables with progressively appended calculated columns (such as `bottleneck_analysis_summary`), lacking an explicit terminal column selection step (`Table.SelectColumns`) can leave partition column orders misaligned with `model.bim` schema declarations.

* **Implemented Resolutions:**
  1. **Decoupled Staging Ingestion:** Decoupled `stg_hospital_events (2)` completely from `stg_hospital_events`, configuring both staging queries with direct, independent CSV import expressions: `Csv.Document(File.Contents("<repo>/data/cleaned/stg_hospital_events.csv"), ...)`.
  2. **Strict One-Directional Data Flow:** Established a clean, decoupled dependency graph where each staging query reads its source CSV file independently without cross-query referencing: Local CSV files $\rightarrow$ independent Power Query M staging partitions $\rightarrow$ VertiPaq semantic model tables.
  3. **Deterministic Evaluation Settings:** Configured `.pbi/editorSettings.json` with `parallelQueryLoading: false` and `autodetectRelationships: false` to ensure sequential, deterministic query evaluation and prevent unintended heuristic relationship loops.
  4. **Explicit Partition Column Selection:** Standardized partition M expressions with explicit `Table.SelectColumns` matching the exact column list and ordinal sequence declared in `model.bim`.

### 1.2 Healthcare Visual Design System

The visual design system establishes a clean, modern aesthetic:

* **Primary Palette:**
  * **Deep Navy (`#102A43`):** Visual titles, primary headers, bold callout numerals, and high-emphasis labels.
  * **Secondary Navy (`#183B56`):** Secondary headers and table column groupings.
  * **Clinical Teal (`#14B8A6`):** Primary metric accents, positive compliance indicators, and primary visual data series.
  * **Light Teal (`#CCFBF1`):** Subtle highlight backgrounds and gradient baselines.
  * **Canvas Background (`#F4F7FA`):** Neutral healthcare off-white canvas eliminating eye fatigue.
  * **Card Container Background (`#FFFFFF`):** High-contrast white card tiles with rounded 6 px borders and subtle outline borders (`#E2E8F0`).
  * **Primary Text (`#172B4D`):** High-legibility charcoal for body text and table cell contents.
  * **Secondary Text (`#64748B`):** Muted slate for subtitles, field restatements, and metadata context.
  * **Warning Amber (`#F59E0B`):** Re-triage loops and secondary assessment indicators.
  * **Critical Coral (`#DC6B6B`):** Bottleneck delay alerts and transition friction points.
* **Typography & Layout Hierarchy:**
  * Strict adherence to **Segoe UI Semibold** (12 pt visual titles, 11 pt headers, 24 pt KPI values) and **Segoe UI** (9 pt subtitles and cell values).
  * Standard 16:9 widescreen canvas (**1280 × 720 px**) with uniform 20 px page margins and balanced inter-card spacing.

---

## 2. Multi-Page Analytical Architecture

### 2.1 Page 1: Hospital Overview (10 Containers: 8 Data Visuals + 2 Textboxes)
An executive healthcare operations overview balancing cohort scale, turnaround times, and departmental workload (referenced as *Hospital Operations Overview* in README documentation):

* **Top KPI Row (5 Symmetrical Cards, Width: 236 px, Gap: 15 px):**
  1. **Total Cases:** 500 patient encounters (`#,##0`) | Subtitle: *Total Patient Volume*
  2. **Total Events:** 3,140 clinical steps (`#,##0`, display units explicitly set to None `1D`, never truncated to 3K) | Subtitle: *Total Recorded Actions*
  3. **Average Case Cycle Time:** 202.5 mins (`0.0 "mins"`, full label displayed) | Subtitle: *Mean Encounter Duration*
  4. **Median Case Cycle Time:** 211.0 mins (`0.0 "mins"`, full label displayed) | Subtitle: *Median Encounter Duration*
  5. **Re-Triage Rate:** 12.0% (`0.0%`) | Subtitle: *Secondary Assessment Rate*
* **Core Analytical Visuals (`y = 170`, `height = 445 px`):**
  * **Department Workload (`donut_dept_breakdown`, w: 380 px):** Donut chart detailing exact department volume with data labels explicitly configured to `labelStyle: 'Both'`, `displayUnits: 1D` (None), and `labelPrecision: 0D`. Displays exact counts: Emergency Department (2,825; 89.97%), Laboratory (185; 5.89%), and Radiology (130; 4.14%) without rounding to 3K or 0K.
  * **Clinical Activity Volume (`bar_activity_breakdown`, w: 430 px):** Ranked horizontal bar chart sorted descending by event count. Direct data labels verify: Consultation (765), Triage (560), Registration (500), Treatment (500), Discharge (500), Laboratory (185), and X-Ray (130). Category axis title is explicitly configured as *Clinical Activity* (`showAxisTitle: true`) and value axis title is explicitly configured as *Event Count* (`showAxisTitle: true`), with Registration, Treatment, and Discharge exhibiting equal bar lengths.
  * **Daily Event Volume Trend (`col_daily_trend`, w: 400 px):** Clustered column chart tracking total daily recorded clinical events sorted chronologically by date (peaking at 354 events on October 6, 2024; reflects milestone activity load rather than unique patient arrival census).
* **Executive Operations Insights Banner (`y = 635`, `w = 1240 px`):**
  Dynamically grounded operational findings detailing highest-volume actions, departmental workload share, re-triage loop prevalence (12.0%), and data provenance notes.

---

### 2.2 Page 2: Patient Flow (8 Containers: 6 Data Visuals + 2 Textboxes)
Demonstrates process-mining trace classification, pathway conformance, and granular encounter auditing (referenced as *Patient Journey & Pathway Conformance* in README documentation):

* **Conformance KPI Row (4 Symmetrical Cards, Width: 295 px, Gap: 20 px):**
  1. **Conformant Cases Count:** 440 encounters (`#,##0`) | Subtitle: *Forward Pathway Volume*
  2. **Repeat Triage Cases Count:** 60 encounters (`#,##0`) | Subtitle: *Operational Re-Triage Volume*
  3. **Conformance Rate %:** 88.0% (`0.0%`) | Subtitle: *Workflow Compliance Rate*
  4. **Total Pathway Variants:** 6 variants (`#,##0`) | Subtitle: *Distinct Process Routes*
* **Core Analytical Visuals (`y = 170`, `height = 445 px`):**
  * **Clinical Pathway Variants (`bar_pathway_variants`, w: 700 px):** Ranked horizontal bar chart mapping the 6 discovered process variants. Demonstrates that Variant 1 (Registration → Triage → Consultation → Treatment → Discharge) represents 40.0% of cohort volume (200 cases), with `maxMargin = 55%` preventing label clipping on 94-character pathway strings.
  * **Patient Encounter Audit Trail (`tbl_case_audit`, w: 525 px):** Granular sequential audit matrix containing *Case ID*, *Event Sequence*, *Activity Name*, *Department*, and *Event Timestamp* (subtitle: *"Chronological event sequence by department and timestamp"*).
* **Patient Journey & Clinical Guidance Banner (`y = 635`, `w = 1240 px`):**
  Explains the standard linear flow (88.0%) versus secondary triage loops (12.0%), emphasizing that repeat triage represents an operational pattern that does not automatically imply clinical mismanagement.

---

### 2.3 Page 3: Transition Analysis & Process Improvement (4 Containers: 2 Data Visuals + 2 Textboxes)
The core evaluative page linking process bottlenecks to simulated operational interventions (referenced as *Operational Bottlenecks & Process Improvement* in README documentation):

* **Highest Observed Transition Durations (`bar_bottlenecks`, w: 520 px, `height = 510 px`):**
  Ranked horizontal bar chart of the longest observed workflow transitions, featuring:
  * **Laboratory → Consultation:** 67.4 mins mean elapsed duration.
  * **X-Ray → Consultation:** 60.4 mins mean elapsed duration.
  * Configured with direct data labels and `categoryAxis.maxMargin = 45%`.
* **As-Is vs. Proposed To-Be Comparison Table (`tbl_improvement_comparison`, w: 705 px, `height = 510 px`):**
  Full operational matrix comparing baseline values against hypothetical streamlined scenarios:
  * *Mean Encounter Duration:* 202.54 mins → 181.77 mins (**-10.3%**).
  * *Pathway Variants:* 6 variants → 4 variants (**-33.3%**).
  * *Repeat Triage Loop Elimination:* 65.63 mins → 0.0 mins (**-100.0%**).
  * Relative difference computed once and formatted with explicit sign convention (`+0.0%;-0.0%;0.0%`).
* **Actionable Recommendations & Clinical Safety Callout (`y = 545`, `w = 1240 px`):**
  Three evidence-based recommendations structured with observed signals, operational opportunities, and mandatory clinical validation boundaries:
  1. *Laboratory-to-Consultation Handoff (67.4 mins):* Automated critical result notifications and digital tracking.
  2. *Diagnostic Radiology Coordination (60.4 mins):* Image archiving alerts and physician review notifications.
  3. *Repeat-Triage Reassessment Context (60 cases):* Standardized secondary triage criteria and intake acuity stratification.
  * Simulation disclaimer noting that elapsed transition duration measures clock intervals between milestone timestamps rather than pure patient waiting room queue delay.

---

## 3. Verified KPI Results Table

All measures are calculated dynamically without hardcoding:

| Metric Name | Entity Table | Verified DAX Expression | Verified Value | Display Format | Operational Interpretation |
| :--- | :--- | :--- | :---: | :---: | :--- |
| **Total Cases** | `stg_hospital_events` | `DISTINCTCOUNT('stg_hospital_events'[case_id])` | **500** | `#,##0` | Discrete emergency patient encounters evaluated. |
| **Total Events** | `stg_hospital_events` | `COUNTROWS('stg_hospital_events')` | **3,140** | `#,##0` (None) | Milestone clinical actions recorded across all pathways. |
| **Avg Case Cycle Time** | `stg_hospital_events` | `AVERAGEX(VALUES(case_id), CALCULATE(SUM(transition_minutes)))` | **202.5** | `0.0 "mins"` | Mean clock turnaround time from intake to discharge. |
| **Median Case Cycle Time** | `stg_hospital_events` | `MEDIANX(VALUES(case_id), CALCULATE(SUM(transition_minutes)))` | **211.0** | `0.0 "mins"` | 50th percentile total encounter turnaround time. |
| **Re-Triage Rate %** | `stg_hospital_events` | `DIVIDE(ReTriageCases, [Total Cases], 0)` | **12.0%** | `0.0%` | Proportion of encounters undergoing secondary triage assessment. |
| **Conformant Cases Count** | `stg_hospital_events` | `[Total Cases] - [Repeat Triage Cases Count]` | **440** | `#,##0` | Encounters following standard forward pathways (Variants 1–4). |
| **Repeat Triage Cases Count** | `stg_hospital_events` | Filtered distinct count on consecutive Triage steps | **60** | `#,##0` | Encounters exhibiting repeat-triage reassessment loops. |
| **Conformance Rate %** | `stg_hospital_events` | `DIVIDE([Conformant Cases Count], [Total Cases], 0)` | **88.0%** | `0.0%` | Proportion adhering to forward non-loop clinical pathways. |
| **Mean Cycle Time Reduction** | `improvement_comparison` | `DIVIDE(Proposed - Baseline, Baseline)` | **-10.3%** | `+0.0%;-0.0%;0.0%` | Simulated impact of hypothetical queue streamlining. |
| **Pathway Variants Reduction**| `improvement_comparison` | `DIVIDE(Proposed - Baseline, Baseline)` | **-33.3%** | `+0.0%;-0.0%;0.0%` | Consolidation of repeat-triage variants in To-Be model. |

---

## 4. Technical Reliability & Exact Files Changed

### 4.1 Exact Files Modified
1. `powerbi/build_careflow_pbip.py`: Decoupled `stg_hospital_events (2)` with independent direct CSV load expression; added explicit `displayUnits: 1D` to card visuals; configured donut chart with `labelStyle: 'Both'`, `displayUnits: 1D`, and `labelPrecision: 0D`; added explicit axis titles (`Clinical Activity`, `Event Count`) to bar charts; added explicit column reordering step to partition definitions.
2. `powerbi/CareFlow_Dashboard_Project/CareFlow_Dashboard.SemanticModel/.pbi/editorSettings.json`: Configured `parallelQueryLoading: false` and `autodetectRelationships: false` for deterministic sequential evaluation.
3. `powerbi/CareFlow_Dashboard_Project/CareFlow_Dashboard.Report/StaticResources/SharedResources/BaseThemes/CY26SU05.json`: Updated with healthcare palette, Segoe UI Semibold typography, and rounded card styling.
4. `powerbi/CareFlow_Dashboard_Project/CareFlow_Dashboard.Report/report.json`: Updated visual container configurations, dataTransforms, and page styling.
5. `powerbi/CareFlow_Dashboard_Project/CareFlow_Dashboard.SemanticModel/model.bim`: Synchronized BIM measures, format strings, explicit column selection on `bottleneck_analysis_summary`, and independent CSV partitions.
6. `powerbi/CareFlow_Dashboard_Project/CareFlow_Dashboard.SemanticModel/definition/tables/stg_hospital_events (2).tmdl`: Updated partition to independent CSV load expression.
7. `powerbi/CareFlow_Dashboard_Project/CareFlow_Dashboard.SemanticModel/definition/tables/stg_hospital_events.tmdl`: Canonical `AVERAGEX` / `MEDIANX` DAX formulas and `0.0 "mins"` format string.
8. `powerbi/careflow_semantic_model/tables/stg_hospital_events (2).tmdl`: Synchronized template TMDL with independent CSV load expression.
9. `powerbi/careflow_semantic_model/tables/stg_hospital_events.tmdl`: Synchronized source semantic model template.
10. `powerbi/careflow_semantic_model/model.bim`: Synchronized source BIM template.
11. `powerbi/test_validate_pbip.py`: Regression coverage for duration iterators, activity volume chart title/labels/margins, bottleneck chart title, dataset baselines, and report JSON validation.
12. `powerbi/CAREFLOW_WEEK4_FINAL_REVIEW.md`: Power BI implementation and review documentation.

### 4.2 Local Backup and Repository Hygiene

- Local developer backups and auto-recovery snapshots are maintained in `powerbi/backup/` (excluded from Git tracking via `.gitignore`).
- All active PBIP definitions, report manifests, semantic models, and test scripts are fully tracked, version-controlled, and validated in the repository.
---

## 5. Verification Commands & Test Results

### 5.1 PBIP Structure & Automated Validator
```powershell
.venv\Scripts\python.exe powerbi\test_validate_pbip.py
```
* **Status:** Passed (`Exit Code 0`).
* **Checks Passed:**
  * Clean JSON parsing across all PBIP manifests and reports.
  * Absence of forbidden `enableAutoAuth` setting.
  * Semantic model validated across all 10 tables (5 business/data tables + 5 automatically generated date tables; 19 DAX measures in active `model.bim`: `stg_hospital_events`: 14, `pathway_variants_summary`: 3, `bottleneck_analysis_summary`: 1, `pathway_improvement_comparison`: 1; 14 measures in reference TMDL template `stg_hospital_events.tmdl`).
  * Canonical DAX iterators (`AVERAGEX`, `MEDIANX`) on `VALUES('stg_hospital_events'[case_id])` verified.
  * All 16 data visuals validated with complete queries and dataTransforms.
  * `card_total_events` confirmed with explicit `displayUnits = 1D`.
  * `bar_activity_breakdown` confirmed with title `"Clinical Activity Volume"`, category `"Clinical Activity"`, measure `"Event Count"`, and margin `35D`.
  * `bar_bottlenecks` confirmed with title `"Highest Observed Transition Durations"`.
  * Exact baseline data verified: 500 cases, 3,140 events, 202.5m mean, 211.0m median, Registration=Treatment=Discharge=500.
  * Active `report.json` confirmed valid JSON with all 3 pages and 22 visual containers.

### 5.2 Repository Pytest Suite
```powershell
.venv\Scripts\python.exe -m pytest -q
```
* **Status:** Passed (`Exit Code 0`).
* **Result:** **175 passed, 8 subtests passed in 27.21s** (zero failures or collection errors).

### 5.3 Git Formatting & Whitespace Verification
```powershell
git diff --check
git diff --cached --check
```
* **Status:** Passed (`Exit Code 0`) with zero trailing whitespace or newline warnings.

---

## 6. Manual Verification Steps in Power BI Desktop & Honest Boundary Disclosure

> [!NOTE]
> **Headless vs. GUI Inspection Boundary:**
> Programmatic validation tools verify file schemas, abstract syntax trees, DAX calculations, field bindings, and pixel layouts. To complete visual sign-off in Microsoft Power BI Desktop on Windows:

1. **Open the Project:**
   Double-click `powerbi/CareFlow_Dashboard_Project/CareFlow_Dashboard.pbip`.
2. **Page 1: Hospital Overview (Hospital Operations Overview):**
   * Confirm the 5 top cards display **500**, **3,140**, **202.5 mins**, **211.0 mins**, and **12.0%** with their clean subtitles.
   * Verify that **"Clinical Activity Volume"** displays Consultation (765) and Triage (560) at the top, followed by Registration, Treatment, and Discharge exhibiting equal horizontal bar lengths labeled with **500**.
   * Test cross-filtering: click on the "Laboratory" slice in the department donut and observe the activity volume and census charts highlight laboratory events.
3. **Page 2: Patient Flow (Patient Journey & Pathway Conformance):**
   * Confirm the top cards display **440**, **60**, and **88.0%**.
   * Verify that the pathway variants horizontal bars display full labels without truncation.
   * Inspect the case audit trail table for sequential ordering.
4. **Page 3: Transition Analysis & Process Improvement (Operational Bottlenecks & Process Improvement):**
   * Verify the bottleneck chart is titled **"Highest Observed Transition Durations"** with Lab → Consultation (67.4 mins) leading.
   * Verify the comparison table shows **-10.3%** for Mean Encounter Duration and **-33.3%** for Pathway Variants with proper `+` / `-` sign formatting.
   * Review the 3 actionable clinical recommendations in the bottom callout.
5. **Git Hygiene Reminder:**
   * Power BI Desktop automatically creates local `.pbi/` and `.platform` folders. These remain untracked and excluded from Git staging.
