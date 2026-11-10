# CareFlow Clinical Pathway — Power BI Project (.pbip) Validation Report

**Project:** CareFlow Clinical Pathway Process Mining
**File Path:** [`powerbi/CareFlow_Dashboard_Project/CareFlow_Dashboard.pbip`](CareFlow_Dashboard_Project/CareFlow_Dashboard.pbip)
**Execution Date:** November 2, 2026 (Updated November 7, 2026)
**Format Standard:** Microsoft Power BI Project (PBIP) with TMSL Semantic Model (`model.bim`) and Power BI Report Definition (PBIR)
**Power BI Desktop Version Target:** `2.154.956.0 (26.05)`

---

## 1. Executive Summary

A fully resolved, standalone Power BI Project (`CareFlow_Dashboard.pbip`) has been systematically debugged, updated, and validated in [`powerbi/CareFlow_Dashboard_Project/`](CareFlow_Dashboard_Project/).

All three core issues identified during forensic analysis have been definitively resolved:
1. **Power Query M Empty String Conversion Error:** In `stg_hospital_events.csv`, 500 rows (event 1 of each of the 500 patient cases) have empty strings `""` for `previous_activity` and `transition_minutes_from_previous`. Power Query M's `Table.TransformColumnTypes` was directly casting `transition_minutes_from_previous` to `Int64.Type` without first converting empty strings to `null`. This threw 500 cell-level `DataFormat.Error: We couldn't convert to Number.` exceptions, causing the VertiPaq engine to abort partition processing (`Partition.State = 3`).
   - **Resolution:** Added `Table.ReplaceValue(#"Promoted Headers", "", null, Replacer.ReplaceValue, {"previous_activity", "transition_minutes_from_previous"})` prior to `Table.TransformColumnTypes`, and configured UTF-8 encoding (`Encoding=65001`).
2. **BigQuery Authentication Barrier:** `stg_hospital_events (2)` still referenced `GoogleBigQuery.Database([Implementation="2.0"])`. Even with `excludeFromModelRefresh: true`, opening or refreshing the project in Desktop triggered pending credential evaluation prompts that blocked local table processing.
   - **Resolution:** Updated `stg_hospital_events (2)` partition M expression to `Source = stg_hospital_events` while preserving `excludeFromModelRefresh: true`. This preserves all column metadata and date variations while making the entire project 100% offline and local.
3. **Percentage Difference Scaling & Formula Correction:** In `pathway_improvement_comparison.csv`, the percentage difference column contained values already pre-scaled by 100 (e.g., `-10.25` for -10.25%). In Power BI, the column was assigned the percentage format string `+0.0%;-0.0%;0.0%`, which automatically multiplies the value by 100 again, causing values to render as `-1025.0%` instead of `-10.3%`.
   - **Resolution:** Implemented relative difference formula `([proposed_value] - [baseline_value]) / [baseline_value]` in Power Query M with safe handling of null/zero baselines. Preserved single percentage formatting (`+0.0%;-0.0%;0.0%`). Added explicit DAX measure `Relative % Difference`. Labeled table column as `"% Difference (Negative = Reduction)"` and documented sign convention in the Page 3 safety banner.
4. **DAX Syntax Error in `Conformant Cases Count`:** The formula evaluated `NOT('stg_hospital_events'[case_id] IN ReTriageCases)` inside `CALCULATE` where `ReTriageCases` was a table variable. DAX does not permit table variables in boolean filter arguments of `CALCULATE`.
   - **Resolution:** Replaced with the clean, mathematically equivalent DAX formula: `[Total Cases] - [Repeat Triage Cases Count]`.

All existing work—including the user's active session, the auto-recovery backup ([`powerbi/backup/CareFlow_AutoRecovery_Backup.pbix`](backup/CareFlow_AutoRecovery_Backup.pbix)), and raw simulated datasets—remains **100% preserved and untouched**.

---

## 2. Project Architecture & File Inventory

The Power BI deployment contains two key components: the **Active Standalone PBIP Project** (`powerbi/CareFlow_Dashboard_Project/`), and the **Reference TMDL Model Template** (`powerbi/careflow_semantic_model/`).

### Active PBIP Project Structure (`CareFlow_Dashboard_Project`)
The active project utilizes the unified TMSL semantic model (`model.bim`) and Power BI Report definition (`report.json` + `definition.pbir`):

```text
powerbi/CareFlow_Dashboard_Project/
├── CareFlow_Dashboard.pbip                          # Project entry point (settings: {})
├── CareFlow_Dashboard.SemanticModel/                # Active TMSL semantic model
│   ├── .platform                                    # Fabric platform metadata
│   ├── definition.pbism                             # Semantic model manifest (v4.2)
│   ├── diagramLayout.json                           # Model diagram layout
│   └── model.bim                                    # 67KB TMSL model definition (10 total tables: 5 business/data tables + 5 auto date tables; 19 DAX measures: stg_hospital_events: 14, pathway_variants_summary: 3, bottleneck_analysis_summary: 1, pathway_improvement_comparison: 1)
└── CareFlow_Dashboard.Report/                       # Visual layout definitions
    ├── .platform                                    # Fabric platform metadata
    ├── definition.pbir                              # Report manifest pointing to ../CareFlow_Dashboard.SemanticModel
    ├── report.json                                  # 3-page, 22-container report definition (queries, visual formatting)
    └── StaticResources/SharedResources/BaseThemes/CY26SU05.json # Power BI native design theme
```

> [!NOTE]
> **Active PBIP Model vs. Reference TMDL Template:** The active, opening project is `powerbi/CareFlow_Dashboard_Project/CareFlow_Dashboard.pbip`, which resolves its schema, M partitions, and DAX calculations through `CareFlow_Dashboard.SemanticModel/model.bim` (TMSL JSON). The separate directory `powerbi/careflow_semantic_model/` contains folder-based TMDL definitions (`database.tmdl`, `model.tmdl`, `relationships.tmdl`, `tables/*.tmdl`) preserved as a modular, git-friendly reference template.

---

## 3. Page & Visual Container Inventory (22 Containers Total: 16 Data Visuals + 6 Textboxes)

The dashboard contains 3 interactive analytical pages comprising **22 visual containers** (16 data visuals with query bounds and data transforms, plus 6 textboxes for banners, titles, and clinical disclaimers):

### Page 1: Hospital Overview (10 Containers: 8 Data Visuals + 2 Textboxes)
- **Data Visual 1 (Card):** `card_total_cases` $\rightarrow$ Measure: `stg_hospital_events.Total Cases` (**500**).
- **Data Visual 2 (Card):** `card_total_events` $\rightarrow$ Measure: `stg_hospital_events.Total Events`. **Verified Display Unit:** Configured with `displayUnits: "1D"` (None) so it explicitly renders **`3,140`** instead of `3K`.
- **Data Visual 3 (Card):** `card_avg_duration` $\rightarrow$ Measure: `stg_hospital_events.Avg Case Cycle Time (Mins)` (**202.5 Mins**, formatted `0.0 "Mins"`).
- **Data Visual 4 (Card):** `card_med_duration` $\rightarrow$ Measure: `stg_hospital_events.Median Case Cycle Time (Mins)` (**211.0 Mins**, formatted `0.0 "Mins"`).
- **Data Visual 5 (Card):** `card_retriage_rate` $\rightarrow$ Measure: `stg_hospital_events.Re-Triage Rate %` (**12.0%**, formatted `0.0%`).
- **Data Visual 6 (Donut Chart):** `donut_dept_breakdown` $\rightarrow$ Category: `department`, Values: `Total Events` (`ER`: 2,825, `LAB`: 185, `RADIOLOGY`: 130).
- **Data Visual 7 (Clustered Bar Chart):** `bar_activity_breakdown` $\rightarrow$ Category: `raw_activity_name` (labeled "Clinical Activity"), Values: `Total Events` (labeled "Event Count"). Volume across all 7 activities: Consultation, Triage, Registration, Treatment, Discharge, Laboratory, X-Ray.
- **Data Visual 8 (Clustered Column Chart):** `col_daily_trend` $\rightarrow$ Category: `event_date`, Values: `Total Events` (Total daily recorded clinical events; reflects milestone activity load rather than unique patient arrival census).
- **Textbox 1:** `hdr_page1` $\rightarrow$ Header banner: "CareFlow — Hospital Overview & Executive Summary".
- **Textbox 2:** `txt_disclaimer_page1` $\rightarrow$ Clinical provenance disclaimer (100% simulated data).

### Page 2: Patient Flow (8 Containers: 6 Data Visuals + 2 Textboxes)
- **Data Visual 1 (Card):** `card_conformant_cases` $\rightarrow$ Measure: `stg_hospital_events.Conformant Cases Count` (**440** cases / 88.0%).
- **Data Visual 2 (Card):** `card_retriage_cases` $\rightarrow$ Measure: `stg_hospital_events.Repeat Triage Cases Count` (**60** cases / 12.0%).
- **Data Visual 3 (Card):** `card_conformance_rate` $\rightarrow$ Measure: `stg_hospital_events.Conformance Rate %` (**88.0%**).
- **Data Visual 4 (Card):** `card_pathway_variants` $\rightarrow$ Measure: `pathway_variants_summary.Total Pathway Variants` (**6** variants).
- **Data Visual 5 (Clustered Bar Chart):** `bar_pathway_variants` $\rightarrow$ Category: `pathway`, Values: `Total Variant Cases` (Ranks Variants 1–6).
- **Data Visual 6 (Table):** `tbl_case_audit` $\rightarrow$ Columns: `case_id` (display: **Case ID**), `event_sequence` (display: **Event Sequence**), `raw_activity_name` (display: **Activity Name**), `department` (display: **Department**), `event_timestamp` (display: **Event Timestamp**). Subtitle: "Chronological event sequence by department and timestamp".
- **Textbox 1:** `hdr_page2` $\rightarrow$ Header banner: "CareFlow — Patient Journey & Pathway Conformance".
- **Textbox 2:** `txt_guidance_page2` $\rightarrow$ Sequential process-rule audit guidance note (repeat-triage identifies process repetition, not clinical appropriateness).

### Page 3: Transition Analysis & Process Improvement (4 Containers: 2 Data Visuals + 2 Textboxes)
- **Data Visual 1 (Clustered Bar Chart):** `bar_bottlenecks` $\rightarrow$ Category: `transition_label`, Values: `Avg Transition Duration`. Title: "Highest Observed Transition Durations" (Ranks top delays: `Laboratory -> Consultation` at 67.4m, `Triage -> Triage` at 65.6m, `X-Ray -> Consultation` at 60.4m, etc.). Layout: x: 20, y: 20, width: 480, height: 510.
- **Data Visual 2 (Table):** `tbl_improvement_comparison` $\rightarrow$ Widened to **745px** (width 745, height 510, x: 515) to comfortably display all 6 columns without horizontal clipping:
  1. `metric_name` (display: **Metric**)
  2. `baseline_value` (display: **Baseline (As-Is)**)
  3. `proposed_value` (display: **Proposed (To-Be)**)
  4. `percentage_difference` (display: **% Difference (Relative)**, formatted `+0.0%;-0.0%;0.0%`)
  5. `unit` (display: **Unit**)
  6. `interpretation` (display: **Operational Interpretation**)
- **Textbox 1:** `hdr_page3` $\rightarrow$ Header banner: "CareFlow — Bottleneck Diagnostics & Scenario Simulation".
- **Textbox 2:** `txt_safety_banner_page3` $\rightarrow$ Clinical disclaimers and explicit sign convention explanation:
  1. *Elapsed Transition Duration != Waiting Time:* Captures elapsed clock intervals between milestone completion timestamps rather than pure patient waiting room idle time. Unmeasured internal sub-processes are not tracked.
  2. *Hypothetical Scenario Disclaimer:* Re-triage removal is a simulated operational model; qualified clinical staff must validate clinical necessity before real-world adoption.
  3. *Sign Convention Note:* Relative percentage change is calculated as `(Proposed - Baseline) / Baseline`. Negative values represent operational reductions (e.g., lower encounter cycle times, eliminated repeat triage steps, or reduced variant complexity).

---

## 4. Percentage Difference Calculation Comparison

| Metric Name | Baseline | Proposed | Old PBI Display (Bug) | Correct PBI Display | Interpretation |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Total Recorded Events** | 3,140 | 3,080 | -191.0% | **-1.9%** | Elimination of 60 repeat-triage loops |
| **Clinical Pathway Variants** | 6 | 4 | -3333.0% | **-33.3%** | Pathway consolidation from 6 to 4 variants |
| **Mean Encounter Duration** | 202.54 min | 181.77 min | -1025.0% | **-10.3%** | Average patient elapsed stay savings (-20.8 min) |
| **Median Encounter Duration** | 211.00 min | 191.18 min | -939.0% | **-9.4%** | Median patient elapsed stay savings (-19.8 min) |
| **Triage -> Triage** | 65.63 min | 0.00 min | -10000.0% | **-100.0%** | Full elimination of re-triage delay loop |
| **Laboratory -> Consultation** | 67.44 min | 57.32 min | -1501.0% | **-15.0%** | Streamlined statutory lab turnaround |
| **Treatment -> Discharge** | 52.01 min | 44.21 min | -1500.0% | **-15.0%** | Bedside discharge workflow optimization |
| **Total Evaluated Cases** | 500 | 500 | 0.0% | **0.0%** | Population preserved across scenarios |

---

## 5. Test & Verification Results

| Verification Check | Target / Rule | Result |
| :--- | :--- | :--- |
| **`test_validate_pbip.py` (Local Updated)** | PBIP schema, TMSL `model.bim` 10-table structure (5 data + 5 date), 19 DAX measures, query definitions, `Table.ReplaceValue`, relative change formula | **PASS (All 10 tables, 19 DAX measures, and 4/4 test blocks verified locally)** |
| **`test_relative_percentage_difference_calculation`** | Mathematical ratios, edge cases (-10.3%, -33.3%, 0.0%, -100.0%, +25.0%, safe 0/0 and 0/50 blank handling), layout widths, display names | **PASS (100%)** |
| **Full Pytest Suite (Local Windows)** | 175 tests and 8 subtests across data gen, process miner, bottleneck analyzer, BQ loader, conformance checker, PBIP validator | **PASS (175 passed, 8 subtests passed in ~24s)** |
| **GitHub Actions CI (Run #42456452180)** | Push to `main` at commit `a67f88d`; executed full pytest suite & PBIP validator on Ubuntu Python 3.12 | **PASS (175 passed with 14 warnings, successful run; executed earlier five-business/data-table validator assertion)** |
| **dbt Model Parse** | `dbt parse` with BigQuery adapter | **PASS (clean parse)** |
| **Simulated Dataset Integrity** | 3,140 events across 500 cases in `data/cleaned/stg_hospital_events.csv` | **PASS (verified)** |
| **`Table.ReplaceValue`** | Converts `""` to `null` before numeric conversion in `stg_hospital_events` | **PASS (verified in model.bim & TMDL)** |
| **BigQuery Dependency Isolated** | Replaced with local reference and `excludeFromModelRefresh: true` | **PASS (zero BigQuery blockers)** |
| **Percentage Scaling Formula** | `([proposed_value] - [baseline_value]) / [baseline_value]` in Power Query & DAX measure | **PASS (single 100x scaling)** |
| **Table Visual Layout & Labels** | Widened to 745px; professional display names configured for all columns | **PASS (verified in report.json)** |
| **`enableAutoAuth` Absent** | PBIP root JSON schema requirement for v2.154.956.0 | **PASS (empty settings object)** |
| **Active Semantic Model (Local)** | Validated `CareFlow_Dashboard.SemanticModel/model.bim` (TMSL JSON format, 10 total tables: 5 business/data tables + 5 auto date tables; 19 DAX measures: 14 in `stg_hospital_events`, 3 in `pathway_variants_summary`, 1 in `bottleneck_analysis_summary`, 1 in `pathway_improvement_comparison`; zero circular references) | **PASS (verified TMSL locally)** |
| **Reference TMDL Model** | Validated `powerbi/careflow_semantic_model/` (folder-based TMDL definitions preserved as modular template; 14 measures in `stg_hospital_events.tmdl`) | **PASS (verified TMDL)** |
| **Active Report Definition** | `CareFlow_Dashboard.Report/report.json` with `definition.pbir` model link (22 containers: 16 data visuals + 6 textboxes) | **PASS (verified)** |
| **Total Events Card Units** | Display units explicitly set to None (`1D`) | **PASS (renders `3,140`)** |

> [!NOTE]
> **Audit Distinction — Local vs. CI Verification States:**
> - **Remote CI State:** GitHub Actions Run #42456452180 verified commit `a67f88d` on Ubuntu Python 3.12 (successful run), where `python -m pytest -q --tb=short` passed 175 tests with 14 warnings and `python powerbi/test_validate_pbip.py` checked the earlier five-business/data-table validator assertion (`[VERIFIED BIM] model.bim verified with all 5 tables and measures`).
> - **Local Working Tree State:** The local validator script (`powerbi/test_validate_pbip.py`) was subsequently enhanced to explicitly check all **10 tables** (5 business/data tables + 1 template date table + 4 local date tables) and all **19 DAX measures** (14 in `stg_hospital_events`, 3 in `pathway_variants_summary`, 1 in `bottleneck_analysis_summary`, 1 in `pathway_improvement_comparison`). This expanded 10-table / 19-measure validator check is verified in the local environment and has not been run on GitHub Actions CI.

---

## 6. How to Load and Refresh the Dashboard in Power BI Desktop

Because Power BI Desktop projects (`.pbip`) load semantic definitions from disk without storing binary data cache files:

1. **Open the Project:**
   - Double-click [`powerbi/CareFlow_Dashboard_Project/CareFlow_Dashboard.pbip`](CareFlow_Dashboard_Project/CareFlow_Dashboard.pbip), or
   - In Power BI Desktop, click **File $\rightarrow$ Open report $\rightarrow$ Browse reports** and select `CareFlow_Dashboard.pbip`.

2. **Populate Visual Data:**
   - On the top ribbon, click **Home $\rightarrow$ Refresh** (or press `F5`).
   - Power BI Desktop will read the 4 local CSV tables (`stg_hospital_events`, `bottleneck_analysis_summary`, `pathway_variants_summary`, `pathway_improvement_comparison`) directly from the workspace.
   - With the `Table.ReplaceValue` fix in place, all 3,140 rows will process without type-conversion errors.
   - With `stg_hospital_events (2)` referencing local data, no cloud authentication dialogs will appear.
   - All 22 visual containers across the 3 pages will instantly populate with their verified measures, formatted callouts, charts, and tables.

3. **Updating Local CSV Source Paths (Portability Guide):**
   If you clone or move the repository to a different folder path or drive letter:
   - **Method A (GUI — Data Source Settings):** In Power BI Desktop, click **Home $\rightarrow$ Transform data $\rightarrow$ Data source settings**. Select each file path and click **Change Source...** to browse to your local folder (`data/cleaned/stg_hospital_events.csv` or `outputs/*.csv`).
   - **Method B (Power Query Editor):** Click **Home $\rightarrow$ Transform data** to open Power Query Editor. For each query in the left pane, click the gear icon next to the **Source** step in **Applied Steps** (or open **Advanced Editor**) and update the file path inside `File.Contents("...")`.
   - Click **Close & Apply** to reload data with the updated paths.
