# CareFlow Clinical Pathway — Power BI Project (.pbip) Validation Report

**Project:** CareFlow Clinical Pathway Process Mining
**File Path:** [`powerbi/CareFlow_Dashboard_Project/CareFlow_Dashboard.pbip`](file:///c:/project/careflow-clinical-pathway/powerbi/CareFlow_Dashboard_Project/CareFlow_Dashboard.pbip)
**Execution Date:** November 2, 2026
**Format Standard:** Microsoft Power BI Project (PBIP) with Tabular Model Definition Language (TMDL) and Power BI Report Definition (PBIR)
**Power BI Desktop Version Target:** `2.154.956.0 (26.05)`

---

## 1. Executive Summary

A fully resolved, standalone Power BI Project (`CareFlow_Dashboard.pbip`) has been systematically debugged, updated, and validated in [`powerbi/CareFlow_Dashboard_Project/`](file:///c:/project/careflow-clinical-pathway/powerbi/CareFlow_Dashboard_Project).

All three core issues identified during forensic analysis have been definitively resolved:
1. **Power Query M Empty String Conversion Error:** In `stg_hospital_events.csv`, 500 rows (event 1 of each of the 500 patient cases) have empty strings `""` for `previous_activity` and `transition_minutes_from_previous`. Power Query M's `Table.TransformColumnTypes` was directly casting `transition_minutes_from_previous` to `Int64.Type` without first converting empty strings to `null`. This threw 500 cell-level `DataFormat.Error: We couldn't convert to Number.` exceptions, causing the VertiPaq engine to abort partition processing (`Partition.State = 3`).
   - **Resolution:** Added `Table.ReplaceValue(#"Promoted Headers", "", null, Replacer.ReplaceValue, {"previous_activity", "transition_minutes_from_previous"})` prior to `Table.TransformColumnTypes`, and configured UTF-8 encoding (`Encoding=65001`).
2. **BigQuery Authentication Barrier:** `stg_hospital_events (2)` still referenced `GoogleBigQuery.Database([Implementation="2.0"])`. Even with `excludeFromModelRefresh: true`, opening or refreshing the project in Desktop triggered pending credential evaluation prompts that blocked local table processing.
   - **Resolution:** Updated `stg_hospital_events (2)` partition M expression to `Source = stg_hospital_events` while preserving `excludeFromModelRefresh: true`. This preserves all column metadata and date variations while making the entire project 100% offline and local.
3. **Percentage Difference Scaling & Formula Correction:** In `pathway_improvement_comparison.csv`, the percentage difference column contained values already pre-scaled by 100 (e.g., `-10.25` for -10.25%). In Power BI, the column was assigned the percentage format string `+0.0%;-0.0%;0.0%`, which automatically multiplies the value by 100 again, causing values to render as `-1025.0%` instead of `-10.3%`.
   - **Resolution:** Implemented relative difference formula `([proposed_value] - [baseline_value]) / [baseline_value]` in Power Query M with safe handling of null/zero baselines. Preserved single percentage formatting (`+0.0%;-0.0%;0.0%`). Added explicit DAX measure `Relative % Difference`. Labeled table column as `"% Difference (Negative = Reduction)"` and documented sign convention in the Page 3 safety banner.
4. **DAX Syntax Error in `Conformant Cases Count`:** The formula evaluated `NOT('stg_hospital_events'[case_id] IN ReTriageCases)` inside `CALCULATE` where `ReTriageCases` was a table variable. DAX does not permit table variables in boolean filter arguments of `CALCULATE`.
   - **Resolution:** Replaced with the clean, mathematically equivalent DAX formula: `[Total Cases] - [Repeat Triage Cases Count]`.

All existing work—including the user's active session, the auto-recovery backup ([`powerbi/backup/CareFlow_AutoRecovery_Backup.pbix`](file:///c:/project/careflow-clinical-pathway/powerbi/backup/CareFlow_AutoRecovery_Backup.pbix)), and raw simulated datasets—remains **100% preserved and untouched**.

---

## 2. Project Architecture & File Inventory

```
powerbi/CareFlow_Dashboard_Project/
├── CareFlow_Dashboard.pbip                          # Project pointer (settings: {})
├── CareFlow_Dashboard.SemanticModel/                # Folder-based TMDL semantic model
│   ├── definition.pbism                             # Model manifest (v4.2)
│   └── definition/
│       ├── database.tmdl                            # Database compatibility definition
│       ├── model.tmdl                               # Model configuration & table references
│       ├── relationships.tmdl                       # Relationship mappings
│       ├── cultures/en-US.tmdl                      # Culture definitions
│       └── tables/
│           ├── stg_hospital_events.tmdl             # 3,140 events, 500 cases, 8 DAX measures, Table.ReplaceValue
│           ├── stg_hospital_events (2).tmdl         # Local alias, excludeFromModelRefresh: true
│           ├── pathway_variants_summary.tmdl        # 6 discovered pathway variants + Total Variant Cases measure
│           ├── bottleneck_analysis_summary.tmdl     # 10 transition delay rankings + Avg Transition Duration measure
│           ├── pathway_improvement_comparison.tmdl  # 21 As-Is vs To-Be metrics + Relative % Difference measure
│           └── DateTableTemplate_...tmdl            # Date intelligence templates
└── CareFlow_Dashboard.Report/                       # Visual layout definitions
    ├── definition.pbir                              # Report manifest referencing ../CareFlow_Dashboard.SemanticModel
    ├── report.json                                  # Full 3-page, 18-visual definition with queries & dataTransforms
    └── StaticResources/SharedResources/BaseThemes/CY26SU05.json # Extracted native theme
```

---

## 3. Page & Visual Inventory (18 Visuals Total)

### Page 1: Hospital Overview (9 Visuals)
- **Visual 1 (Card):** `card_total_cases` $\rightarrow$ Measure: `stg_hospital_events.Total Cases` (**500**).
- **Visual 2 (Card):** `card_total_events` $\rightarrow$ Measure: `stg_hospital_events.Total Events`. **Verified Display Unit:** Configured with `displayUnits: "1D"` (None) so it explicitly renders **`3,140`** instead of `3K`.
- **Visual 3 (Card):** `card_avg_duration` $\rightarrow$ Measure: `stg_hospital_events.Avg Case Cycle Time (Mins)` (**202.5 Mins**, formatted `0.0 "Mins"`).
- **Visual 4 (Card):** `card_med_duration` $\rightarrow$ Measure: `stg_hospital_events.Median Case Cycle Time (Mins)` (**211.0 Mins**, formatted `0.0 "Mins"`).
- **Visual 5 (Card):** `card_retriage_rate` $\rightarrow$ Measure: `stg_hospital_events.Re-Triage Rate %` (**12.0%**, formatted `0.0%`).
- **Visual 6 (Donut Chart):** `donut_dept_breakdown` $\rightarrow$ Category: `department`, Values: `Total Events` (`ER`: 2,825, `LAB`: 185, `RADIOLOGY`: 130).
- **Visual 7 (Bar Chart):** `bar_activity_breakdown` $\rightarrow$ Category: `raw_activity_name`, Values: `Total Events` (Volume across all 7 activities: Consultation, Triage, Registration, Treatment, Discharge, Laboratory, X-Ray).
- **Visual 8 (Column Chart):** `col_daily_trend` $\rightarrow$ Category: `event_date`, Values: `Total Events` (Daily patient intake census).
- **Visual 9 (Textbox):** `txt_disclaimer_page1` $\rightarrow$ Clinical provenance disclaimer (100% simulated data).

### Page 2: Patient Flow (6 Visuals)
- **Visual 1 (Card):** `card_conformant_cases` $\rightarrow$ Measure: `stg_hospital_events.Conformant Cases Count` (**440** cases / 88.0%).
- **Visual 2 (Card):** `card_retriage_cases` $\rightarrow$ Measure: `stg_hospital_events.Repeat Triage Cases Count` (**60** cases / 12.0%).
- **Visual 3 (Card):** `card_conformance_rate` $\rightarrow$ Measure: `stg_hospital_events.Conformance Rate %` (**88.0%**).
- **Visual 4 (Bar Chart):** `bar_pathway_variants` $\rightarrow$ Category: `pathway`, Values: `Total Variant Cases` (Ranks Variants 1–6).
- **Visual 5 (Table):** `tbl_case_audit` $\rightarrow$ Columns: `case_id` (display: **Case ID**), `event_sequence` (display: **Seq #**), `raw_activity_name` (display: **Activity**), `department` (display: **Department**), `transition_minutes_from_previous` (display: **Elapsed (Mins)**).
- **Visual 6 (Textbox):** `txt_guidance_page2` $\rightarrow$ Sequential process-rule audit guidance note (repeat-triage identifies process repetition, not clinical appropriateness).

### Page 3: Transition Analysis & Process Improvement (3 Visuals)
- **Visual 1 (Bar Chart):** `bar_bottlenecks` $\rightarrow$ Category: `transition_label`, Values: `Avg Transition Duration` (Ranks top delays: `Laboratory -> Consultation` at 67.4m, `Triage -> Triage` at 65.6m, `X-Ray -> Consultation` at 60.4m, etc.). Layout: x: 20, y: 20, width: 480, height: 510.
- **Visual 2 (Table):** `tbl_improvement_comparison` $\rightarrow$ Widened to **745px** (width 745, height 510, x: 515) to comfortably display all 6 columns without horizontal clipping. Columns:
  1. `metric_name` (display: **Metric**)
  2. `baseline_value` (display: **Baseline (As-Is)**)
  3. `proposed_value` (display: **Proposed (To-Be)**)
  4. `percentage_difference` (display: **% Difference (Relative)**, formatted `+0.0%;-0.0%;0.0%`)
  5. `unit` (display: **Unit**)
  6. `interpretation` (display: **Operational Interpretation**)
- **Visual 3 (Textbox):** `txt_safety_banner_page3` $\rightarrow$ Clinical disclaimers and explicit sign convention explanation:
  1. *Elapsed Transition Duration != Waiting Time:* Captures specimen processing, imaging turnaround, and active clinical review.
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
| **`test_validate_pbip.py`** | Folder-based PBIP schema, TMDL structure, table references, query definitions, `Table.ReplaceValue`, relative change formula | **PASS (100%)** |
| **`test_relative_percentage_difference_calculation`** | Mathematical ratios, edge cases (-10.3%, -33.3%, 0.0%, -100.0%, +25.0%, safe 0/0 and 0/50 blank handling), layout widths, display names | **PASS (100%)** |
| **Full Pytest Suite** | 173 tests across data gen, process miner, bottleneck analyzer, BQ loader, conformance checker, PBIP validator | **PASS (173/173 passed in 18.3s)** |
| **dbt Model Parse** | `dbt parse` with BigQuery adapter | **PASS (clean parse)** |
| **Simulated Dataset Integrity** | 3,140 events across 500 cases in `data/cleaned/stg_hospital_events.csv` | **PASS (verified)** |
| **`Table.ReplaceValue`** | Converts `""` to `null` before numeric conversion in `stg_hospital_events` | **PASS (verified in TMDL)** |
| **BigQuery Dependency Isolated** | Replaced with local reference and `excludeFromModelRefresh: true` | **PASS (zero BigQuery blockers)** |
| **Percentage Scaling Formula** | `([proposed_value] - [baseline_value]) / [baseline_value]` in Power Query & DAX measure | **PASS (single 100x scaling)** |
| **Table Visual Layout & Labels** | Widened to 745px; professional display names configured for all columns | **PASS (verified in report.json)** |
| **`enableAutoAuth` Absent** | PBIP root JSON schema requirement for v2.154.956.0 | **PASS (empty settings object)** |
| **Folder-Based Semantic Model** | Validated `definition/model.tmdl`, `tables/*.tmdl`, `definition.pbism` (no legacy `model.bim` dependency) | **PASS (100% TMDL)** |
| **Active Report Definition** | `CareFlow_Dashboard.Report/report.json` with `definition.pbir` model link | **PASS (verified)** |
| **Total Events Card Units** | Display units explicitly set to None (`1D`) | **PASS (renders `3,140`)** |

---

## 6. How to Load and Refresh the Dashboard in Power BI Desktop

Because Power BI Desktop projects (`.pbip`) load semantic definitions from disk without storing binary data cache files:

1. **Open the Project:**
   - Double-click [`powerbi/CareFlow_Dashboard_Project/CareFlow_Dashboard.pbip`](file:///c:/project/careflow-clinical-pathway/powerbi/CareFlow_Dashboard_Project/CareFlow_Dashboard.pbip), or
   - In Power BI Desktop, click **File $\rightarrow$ Open report $\rightarrow$ Browse reports** and select `CareFlow_Dashboard.pbip`.
2. **Populate Visual Data:**
   - On the top ribbon, click **Home $\rightarrow$ Refresh** (or press `F5`).
   - Power BI Desktop will read the 4 local CSV tables (`stg_hospital_events`, `bottleneck_analysis_summary`, `pathway_variants_summary`, `pathway_improvement_comparison`) directly from the workspace.
   - With the `Table.ReplaceValue` fix in place, all 3,140 rows will process without type-conversion errors.
   - With `stg_hospital_events (2)` referencing local data, no cloud authentication dialogs will appear.
   - All 18 visuals across the 3 pages will instantly populate with their verified measures, formatted callouts, charts, and tables.
