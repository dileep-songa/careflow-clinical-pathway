# CareFlow Clinical Pathway — Power BI Dashboard Implementation Plan

**Project:** CareFlow Clinical Pathway Process Mining
**Target Platform:** Microsoft Power BI Desktop (May 2024 or later recommended)
**Primary Data Sources:**
- Google BigQuery View: `exalted-mode-467509-h1.careflow_staging.stg_hospital_events` (3,140 rows, 500 cases)
- Local Process Mining CSV Outputs: `outputs/` and `data/cleaned/` (100% parity with BigQuery)
**Data Provenance:** 100% Synthetic Event Log (`SIMULATED`)

---

> [!NOTE]
> **Implementation Evolution Notice:**
> This document captures the preliminary 4-page dashboard design blueprint drafted during early planning. In the finalized, validated Power BI Project (`CareFlow_Dashboard.pbip`), Pages 3 and 4 were consolidated into Page 3: **Transition Analysis & Process Improvement** (22 visual containers total: 16 data visuals + 6 textboxes across 3 pages) and the active semantic model (`model.bim`) contains **10 total tables** (5 business/data tables + 5 automatically generated date tables) and **19 DAX measures**. The Patient Encounter Audit Trail (`tbl_case_audit`) displays `Case ID`, `Event Sequence`, `Activity Name`, `Department`, and `Event Timestamp` with subtitle `"Chronological event sequence by department and timestamp"`. See [`CAREFLOW_WEEK4_FINAL_REVIEW.md`](CAREFLOW_WEEK4_FINAL_REVIEW.md) and [`CAREFLOW_PBIP_VALIDATION_REPORT.md`](CAREFLOW_PBIP_VALIDATION_REPORT.md) for the active 3-page report documentation.

---

## 1. Executive Summary & Dashboard Architecture

This implementation plan provides a beginner-friendly, step-by-step roadmap for constructing a professional 4-page Power BI executive dashboard for the CareFlow Clinical Pathway Process Mining project.

The dashboard translates complex process-mining findings—discovered traces, transition bottlenecks, workflow conformance audits, and hypothetical To-Be improvement simulations—into intuitive, interactive visual stories suitable for hospital administrators, clinical directors, and operations analysts.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      CareFlow Clinical Pathway Dashboard                     │
├─────────────────────┬─────────────────────┬───────────────────┬─────────────┤
│ 1. Hospital Overview│ 2. Patient Flow &   │ 3. Bottleneck     │ 4. As-Is vs.│
│    (Cohort KPIs &   │    Conformance      │    Analysis       │    To-Be    │
│    Timeline Census) │    (Traces & Audit) │    (Delays & DFG) │    Scenario │
└─────────────────────┴─────────────────────┴───────────────────┴─────────────┘
```

---

## 2. Data Sources & Loading Strategy

Power BI supports two seamless loading modes for this project:

### Strategy A: Local Cleaned CSV Files (Recommended for Offline Portability)
Import the existing CSV files directly from the repository. This requires zero cloud credentials and incurs zero latency:

1. **`data/cleaned/stg_hospital_events.csv`** $\rightarrow$ Load as **`FactHospitalEvents`** (3,140 rows, 11 columns).
2. **`outputs/conformance_case_results.csv`** $\rightarrow$ Load as **`DimPatientCase`** (500 rows, 7 columns).
3. **`outputs/pathway_variants_summary.csv`** $\rightarrow$ Load as **`DimPathwayVariants`** (6 rows, 4 columns).
4. **`outputs/bottleneck_analysis_summary.csv`** $\rightarrow$ Load as **`FactBottlenecks`** (10 rows, 8 columns).
5. **`outputs/pathway_improvement_comparison.csv`** $\rightarrow$ Load as **`FactImprovementScenario`** (21 rows, 9 columns).

### Strategy B: Google BigQuery Connector (Live Warehouse Mode)
If connecting directly to Google Cloud BigQuery:
1. In Power BI Desktop, click **Get Data** $\rightarrow$ Search **Google BigQuery** $\rightarrow$ Click **Connect**.
2. Sign in with your authorized Google Account (ADC / OAuth) under project `exalted-mode-467509-h1`.
3. In the Navigator, expand `exalted-mode-467509-h1` $\rightarrow$ `careflow_staging` $\rightarrow$ Select `stg_hospital_events`.
4. Select **Import** mode (recommended for fast visual interactions and full DAX support).
5. Load supporting CSVs from `outputs/` for the conformance, bottleneck, and scenario pages.

---

## 3. Power Query Data Transformations

Apply these lightweight transformations in Power Query Editor:

### Table 1: `FactHospitalEvents`
- **Data Types:**
  - `case_id`: Text
  - `event_sequence`: Whole Number (`Int64`)
  - `raw_activity_name`: Text
  - `activity_name`: Text
  - `event_timestamp`: Date/Time
  - `event_date`: Date
  - `department`: Text
  - `resource_id`: Text
  - `data_provenance`: Text
  - `previous_activity`: Text
  - `transition_minutes_from_previous`: Decimal Number (Replace `null` with `0` or leave null for Registration events).
- **Add Hour Column (Optional):**
  - Add Custom Column `event_hour` = `Time.Hour([event_timestamp])` (Type: Whole Number).

### Table 2: `DimPatientCase`
- **Data Types:**
  - `case_id`: Text (Ensure values match `FactHospitalEvents[case_id]`, e.g. `CASE_0001`).
  - `observed_pathway`: Text
  - `is_conformant`: True/False
  - `status`: Text (`CONFORMANT` or `UNDER_REVIEW`)
  - `rule_ids`: Text
  - `review_reasons`: Text
  - `total_deviations`: Whole Number

### Table 3: `FactBottlenecks`
- **Data Types:**
  - `rank`: Whole Number
  - `source_activity`: Text
  - `target_activity`: Text
  - `transition_count`: Whole Number
  - `mean_observed_transition_minutes`: Decimal Number
  - `median_observed_transition_minutes`: Decimal Number
  - `min_observed_transition_minutes`: Decimal Number
  - `max_observed_transition_minutes`: Decimal Number
- **Add Transition Label Column:**
  - Add Custom Column `transition_label` = `[source_activity] & " -> " & [target_activity]` (Text).

### Table 4: `FactImprovementScenario`
- **Data Types:**
  - `category`: Text
  - `metric_name`: Text
  - `baseline_value`: Decimal Number
  - `proposed_value`: Decimal Number
  - `absolute_difference`: Decimal Number
  - `percentage_difference`: Decimal Number
  - `unit`: Text
  - `provenance`: Text
  - `interpretation`: Text

---

## 4. Star Schema & Data Model Relationships

Navigate to the **Model View** in Power BI Desktop and configure the relationships:

```
┌─────────────────────────────────────────────────────────┐
│                    DimDate (Calendar)                   │
│                     [Date] (Key)                        │
└────────────────────────────┬────────────────────────────┘
                             │ 1
                             │
                             │ *
┌──────────────────┐  *   ┌──┴────────────────────────────┐   *   ┌────────────────────┐
│  DimPatientCase  ├──────┤      FactHospitalEvents       ├───────┤    DimActivity     │
│  [case_id] (Key) │ 1    │  [case_id] (FK)               │ 1     │  [activity_name]   │
└──────────────────┘      │  [event_date] (FK)            │       └────────────────────┘
                          │  [activity_name] (FK)         │
                          └───────────────────────────────┘
```

### Relationship Configuration Table:
| From Table (Many / `*`) | From Column (FK) | To Table (One / `1`) | To Column (PK) | Cardinality | Cross Filter Direction | Active |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `FactHospitalEvents` | `case_id` | `DimPatientCase` | `case_id` | Many to One (`*:1`) | Single (`DimPatientCase` filters `Fact`) | Yes |
| `FactHospitalEvents` | `event_date` | `DimDate` | `Date` | Many to One (`*:1`) | Single (`DimDate` filters `Fact`) | Yes |

*Note: `FactBottlenecks` and `FactImprovementScenario` are specialized analytical summary tables. They do not require physical relationships to `FactHospitalEvents` and function as decoupled reporting tables.*

### Calculated Date Table (`DimDate`)
Create using DAX in Power BI Desktop (**Modeling** $\rightarrow$ **New Table**):
```dax
DimDate =
VAR MinDate = MIN(FactHospitalEvents[event_date])
VAR MaxDate = MAX(FactHospitalEvents[event_date])
RETURN
ADDCOLUMNS (
    CALENDAR(MinDate, MaxDate),
    "Year", YEAR([Date]),
    "Month", FORMAT([Date], "mmmm"),
    "MonthNumber", MONTH([Date]),
    "DayOfMonth", DAY([Date]),
    "DayName", FORMAT([Date], "dddd"),
    "DayOfWeekNumber", WEEKDAY([Date], 2)
)
```

### Calculated Case Duration Column in `DimPatientCase`
To enable case-level duration analysis across slicers (**Modeling** $\rightarrow$ **New Column** in `DimPatientCase`):
```dax
case_duration_minutes =
SUMX(
    RELATEDTABLE(FactHospitalEvents),
    FactHospitalEvents[transition_minutes_from_previous]
)
```

---

## 5. Detailed Page-by-Page Canvas Design

### Page 1: Hospital Overview (Executive Cohort Summary)
*Goal: Provide a bird's-eye view of emergency department patient intake, activity volumes, department load, and length of stay.*

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Header: CareFlow Hospital Operations Overview | Cohort: 500 Cases (Simulated)│
├─────────────┬─────────────┬─────────────┬─────────────┬─────────────────────┤
│ Total Cases │Total Events │ Avg Stay    │ Median Stay │ Re-Triage Rate      │
│     500     │    3,140    │ 202.5 Mins  │ 211.0 Mins  │    12.0% (60 cases) │
├─────────────┴──────┬──────┴─────────────┴─────────────┴─────────────────────┤
│ Patient Volume by  │ Hourly Arrival Distribution (Event Timestamp Census)   │
│ Department (Donut) │ (Clustered Column Chart: Hour of Day 00:00 - 23:00)     │
│ - ER: 2,775        │                                                         │
│ - LAB: 185         │                                                         │
│ - RADIOLOGY: 180   │                                                         │
├────────────────────┴────────────────────────────────────────────────────────┤
│ Daily Case Volume Trend & Slicers: [Date Range Slicer] [Department Slicer]  │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Visual Specifications:**
1. **Top KPI Cards (5 single-value cards):**
   - Card 1: `[Total Cases]` (500)
   - Card 2: `[Total Events]` (3,140)
   - Card 3: `[Avg Case Cycle Time (Mins)]` (202.5 min)
   - Card 4: `[Median Case Cycle Time (Mins)]` (211.0 min)
   - Card 5: `[Re-Triage Rate %]` (12.0%)
2. **Department Distribution (Donut Chart):**
   - Legend: `FactHospitalEvents[department]`
   - Values: `[Total Events]`
3. **Hourly Event Volume (Clustered Column Chart):**
   - X-Axis: `FactHospitalEvents[event_hour]` (or derived hour)
   - Y-Axis: `[Total Events]`
4. **Interactive Filters (Slicers):**
   - Slicer 1: `DimDate[Date]` (Between range)
   - Slicer 2: `FactHospitalEvents[department]` (Dropdown)

---

### Page 2: Patient Flow & Conformance (Pathway Traces & Auditing)
*Goal: Visualize discovered clinical pathway variants and isolate non-conformant cases requiring operational review.*

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Header: Clinical Pathway Flow & Conformance Checking                        │
├─────────────────────────────────────────┬───────────────────────────────────┤
│ Clinical Pathway Variants (Bar Chart)   │ Workflow Conformance Status       │
│ - Var 1 (Routine): 200 cases (40.0%)    │ (Donut Chart)                     │
│ - Var 2 (Lab): 110 cases (22.0%)        │ - Conformant: 440 cases (88.0%)   │
│ - Var 3 (X-Ray): 80 cases (16.0%)       │ - Under Review: 60 cases (12.0%)  │
│ - Var 4 (Lab+X-Ray): 50 cases (10.0%)   │                                   │
│ - Var 5 (Re-Triage Routine): 35 (7.0%)  │                                   │
│ - Var 6 (Re-Triage Lab): 25 (5.0%)      │                                   │
├─────────────────────────────────────────┴───────────────────────────────────┤
│ Patient Case Audit Table (Table Visual):                                    │
│ [case_id] | [status] | [observed_pathway] | [review_reasons] | [stay_mins] │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Visual Specifications:**
1. **Pathway Variants Breakdown (Horizontal Clustered Bar Chart):**
   - Y-Axis: `DimPathwayVariants[pathway]` (or Variant Rank)
   - X-Axis: `DimPathwayVariants[case_count]`
   - Tooltips: `DimPathwayVariants[percentage]`, `[Avg Case Cycle Time (Mins)]`
2. **Workflow Conformance Donut Chart:**
   - Legend: `DimPatientCase[status]` (`CONFORMANT` vs `UNDER_REVIEW`)
   - Values: `[Total Cases]`
   - Data Colors: Teal/Green for `CONFORMANT`, Amber/Orange for `UNDER_REVIEW`.
3. **Case Detail Drilldown Table:**
   - Columns: `DimPatientCase[case_id]`, `DimPatientCase[status]`, `DimPatientCase[observed_pathway]`, `DimPatientCase[review_reasons]`, `DimPatientCase[case_duration_minutes]`.
4. **Interactive Slicers:**
   - Slicer 1: `DimPatientCase[status]` (Buttons: All, Conformant, Under Review).
   - Slicer 2: `DimPathwayVariants[variant_rank]` (Dropdown).

---

### Page 3: Bottleneck Analysis (Directly-Follows Transition Delays)
*Goal: Diagnose delay points across clinical milestones and highlight diagnostic turnarounds.*

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Header: Directly-Follows Transition Delays & Bottleneck Ranking             │
├─────────────────────────────────────────────────────────────────────────────┤
│ Top Observed Transitions Ranked by Mean Duration (Grouped Horizontal Bar)   │
│ 1. Laboratory -> Consultation   | 67.4 Mins (n=135)                         │
│ 2. Triage -> Triage (Loop)      | 65.6 Mins (n=60)                          │
│ 3. X-Ray -> Consultation        | 60.4 Mins (n=130)                         │
│ 4. Laboratory -> X-Ray          | 53.5 Mins (n=50)                          │
│ 5. Treatment -> Discharge       | 52.0 Mins (n=500)                         │
│ 6. Consultation -> X-Ray        | 38.2 Mins (n=80)                          │
│ 7. Consultation -> Treatment    | 37.8 Mins (n=500)                         │
│ 8. Consultation -> Laboratory   | 37.3 Mins (n=185)                         │
│ 9. Triage -> Consultation       | 25.1 Mins (n=500)                         │
│ 10. Registration -> Triage      | 20.6 Mins (n=500)                         │
├─────────────────────────────────────────────────────────────────────────────┤
│ Cautionary Callout Card: Transition Duration != Pure Waiting Time           │
│ "Observed transition duration measures total elapsed time between events,    │
│ including active diagnostic processing, specimen transit, and clinical      │
│ review. It does not establish pure idle waiting time."                       │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Visual Specifications:**
1. **Ranked Bottlenecks (Grouped Clustered Bar Chart):**
   - Data Source: `FactBottlenecks`
   - Y-Axis: `FactBottlenecks[transition_label]` (Sorted ascending by `FactBottlenecks[rank]`)
   - X-Axis: `FactBottlenecks[mean_observed_transition_minutes]` and `FactBottlenecks[median_observed_transition_minutes]`
2. **Transition Volume & Range Table:**
   - Columns: `transition_label`, `transition_count`, `min_observed_transition_minutes`, `median_observed_transition_minutes`, `mean_observed_transition_minutes`, `max_observed_transition_minutes`.
3. **Diagnostic Turnaround Focus Card:**
   - Multi-row card highlighting the top 2 diagnostic bottlenecks (`Laboratory -> Consultation` at 67.4m and `X-Ray -> Consultation` at 60.4m).

---

### Page 4: As-Is vs. Hypothetical To-Be Comparison (Scenario Analysis)
*Goal: Present the projected impact of queue-management streamlining and administrative optimizations.*

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Header: As-Is Baseline vs. Hypothetical To-Be Scenario Analysis             │
├─────────────────────┬─────────────────────┬─────────────────────────────────┤
│ Mean Encounter Time │ Median Encounter    │ P90 Encounter Time              │
│ 202.5 -> 181.8 Mins │ 211.0 -> 191.2 Mins │ 284.0 -> 255.2 Mins             │
│ (-10.25% Reduction) │ (-9.39% Reduction)  │ (-10.15% Reduction)             │
├─────────────────────┴─────────────────────┴─────────────────────────────────┤
│ Key Transition Duration Impact (Grouped Bar Chart: Baseline vs. Proposed)   │
│ - Laboratory -> Consultation : 67.4m -> 57.3m (-15.0%)                      │
│ - Triage -> Triage Loop      : 65.6m -> 0.0m (-100.0% / Eliminated)         │
│ - Treatment -> Discharge     : 52.0m -> 44.2m (-15.0%)                      │
│ - X-Ray -> Consultation      : 60.4m -> 51.3m (-15.0%)                      │
├─────────────────────────────────────────────────────────────────────────────┤
│ Clinical Safety Banner (Prominent Text Box / Card):                         │
│ "Clinical Safety Assumption: The To-Be scenario models repeated triage      │
│ removal as a hypothetical operational improvement. Simulated event logs     │
│ cannot determine whether reassessment was clinically necessary. Qualified   │
│ clinical staff must validate this assumption before real-world adoption."   │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Visual Specifications:**
1. **Comparative KPI Cards (Side-by-Side or Combined Difference Cards):**
   - Card 1: `[Baseline Mean Duration]` (202.5m) $\rightarrow$ `[To-Be Mean Duration]` (181.8m) $\rightarrow$ `[Mean Duration Reduction %]` (-10.3%)
   - Card 2: `[Baseline Median Duration]` (211.0m) $\rightarrow$ `[To-Be Median Duration]` (191.2m) $\rightarrow$ `[Median Duration Reduction %]` (-9.4%)
   - Card 3: `[Baseline P90 Duration]` (284.0m) $\rightarrow$ `[To-Be P90 Duration]` (255.2m) $\rightarrow$ `[P90 Duration Reduction %]` (-10.2%)
2. **Transition Comparison Chart (Clustered Bar Chart):**
   - Filter `FactImprovementScenario[category] = "Transition Duration (Minutes)"`
   - Y-Axis: `FactImprovementScenario[metric_name]`
   - X-Axis: `FactImprovementScenario[baseline_value]` and `FactImprovementScenario[proposed_value]`
3. **Cohort Consolidation Card:**
   - Display variant consolidation: 6 variants $\rightarrow$ 4 variants (-33.3%).

---

## 6. Color Palette & Visual Theme Guidance

To ensure clinical clarity and accessible visualization:
- **Primary Clinical Navy:** `#1A365D` (Headers, titles, default bars)
- **Clinical Teal:** `#0D9488` (Conformant cases, routine pathways)
- **Attention Amber/Orange:** `#D97706` (Bottlenecks, non-conformant/review cases)
- **Scenario Purple:** `#7C3AED` (To-Be simulated estimates)
- **Background Slate:** `#F8FAFC` (Clean, modern canvas background)

---

## 7. Author Verification & Testing Checklist

Before presenting the dashboard:
- [ ] Confirm all 500 cases are accounted for on Page 1.
- [ ] Confirm the 440 conformant and 60 review cases match on Page 2.
- [ ] Confirm `Laboratory -> Consultation` is ranked #1 on Page 3.
- [ ] Ensure the Clinical Safety Banner is prominently displayed on Page 4.
- [ ] Ensure all DAX measures format appropriately (e.g. `0.0 Mins`, `0.0%`, `#,##0`).
