# CareFlow Clinical Pathway — Power BI DAX Measures Reference

**Project:** CareFlow Clinical Pathway Process Mining
**File Name:** `powerbi/powerbi_measures_reference.md`
**Target Application:** Power BI Desktop / Service
**Data Provenance:** 100% Synthetic Event Log (`SIMULATED`)

---

## 1. Overview & Measure Organization

This document provides verified, copy-paste ready DAX (Data Analysis Expressions) formulas designed for the CareFlow Clinical Pathway Power BI Dashboard.

All measures reference verified columns and tables present in the CareFlow project:
- **`FactHospitalEvents`** (from `stg_hospital_events.csv` or BigQuery view)
- **`DimPatientCase`** (from `conformance_case_results.csv`)
- **`DimPathwayVariants`** (from `pathway_variants_summary.csv`)
- **`FactBottlenecks`** (from `bottleneck_analysis_summary.csv`)
- **`FactImprovementScenario`** (from `pathway_improvement_comparison.csv`)
- **`DimDate`** (Calculated Date Table)

> [!TIP]
> **Best Practice:** Create an empty dedicated table in Power BI to organize your measures.
> In Power BI Desktop: Click **Enter Data** $\rightarrow$ Name the table `_CareFlowMeasures` $\rightarrow$ Click **Load**.
> Store all your DAX measures inside this folder for easy navigation.

---

## 2. Calculated Columns & Supporting Tables

Before creating measures, create these two calculated structures:

### A. Calculated Column: `case_duration_minutes` in `DimPatientCase`
Calculates total elapsed encounter duration for each patient case by summing transition times across related event records:
```dax
case_duration_minutes =
SUMX(
    RELATEDTABLE(FactHospitalEvents),
    FactHospitalEvents[transition_minutes_from_previous]
)
```
- **Table:** `DimPatientCase`
- **Data Type:** Decimal Number
- **Format:** `0.0`
- **Verification:** Verified to yield `Mean = 202.54 min`, `Median = 211.00 min` across the 500 cases.

### B. Calculated Column: `transition_label` in `FactBottlenecks`
Creates a clean, human-readable transition name for charts:
```dax
transition_label =
FactBottlenecks[source_activity] & " -> " & FactBottlenecks[target_activity]
```
- **Table:** `FactBottlenecks`
- **Data Type:** Text

---

## 3. Core Volume & Census Measures

### Measure 1: `[Total Cases]`
Calculates the total distinct patient encounter volume in the cohort.
```dax
Total Cases =
DISTINCTCOUNT(FactHospitalEvents[case_id])
```
- **Format:** `#,##0`
- **Expected Baseline:** `500`
- **Canvas Placement:** Page 1 (Card), Page 2 (Donut), Page 4 (Card).

---

### Measure 2: `[Total Events]`
Counts the total number of clinical and administrative activities logged across all cases.
```dax
Total Events =
COUNTROWS(FactHospitalEvents)
```
- **Format:** `#,##0`
- **Expected Baseline:** `3,140`
- **Canvas Placement:** Page 1 (Card, Department Chart).

---

### Measure 3: `[Total Pathway Variants]`
Counts the number of distinct clinical pathway journeys discovered across the cohort.
```dax
Total Pathway Variants =
DISTINCTCOUNT(DimPatientCase[observed_pathway])
```
- **Format:** `#,##0`
- **Expected Baseline:** `6` (As-Is baseline)
- **Canvas Placement:** Page 2 (Card).

---

## 4. Duration & Timing Measures

> [!IMPORTANT]
> **Clinical Definition:** Transition and case durations measure total elapsed intervals between recorded event timestamps. They capture active service, specimen handling, transit, and review times. They must **not** be presented as pure idle waiting times.

### Measure 4: `[Avg Case Cycle Time (Mins)]`
Calculates the mean total patient encounter duration from initial registration to final discharge.
```dax
Avg Case Cycle Time (Mins) =
AVERAGE(DimPatientCase[case_duration_minutes])
```
- **Format:** `0.0 "Mins"`
- **Expected Baseline:** `202.5 Mins`
- **Canvas Placement:** Page 1 (Card), Page 2 (Variant tooltip).

---

### Measure 5: `[Median Case Cycle Time (Mins)]`
Calculates the median encounter duration, offering a robust metric that resists outlier skewness.
```dax
Median Case Cycle Time (Mins) =
MEDIAN(DimPatientCase[case_duration_minutes])
```
- **Format:** `0.0 "Mins"`
- **Expected Baseline:** `211.0 Mins`
- **Canvas Placement:** Page 1 (Card).

---

### Measure 6: `[Avg Observed Transition Time (Mins)]`
Calculates the average elapsed duration between preceding and succeeding activities.
```dax
Avg Observed Transition Time (Mins) =
AVERAGE(FactHospitalEvents[transition_minutes_from_previous])
```
- **Format:** `0.0 "Mins"`
- **Canvas Placement:** Page 3 (Transition visual / Table).

---

### Measure 7: `[Median Observed Transition Time (Mins)]`
Calculates the median elapsed duration between preceding and succeeding activities.
```dax
Median Observed Transition Time (Mins) =
MEDIAN(FactHospitalEvents[transition_minutes_from_previous])
```
- **Format:** `0.0 "Mins"`
- **Canvas Placement:** Page 3 (Transition visual / Table).

---

## 5. Workflow Conformance & Quality Measures

### Measure 8: `[Conformant Cases Count]`
Counts cases that strictly adhered to normative clinical pathway rules.
```dax
Conformant Cases Count =
CALCULATE(
    [Total Cases],
    DimPatientCase[is_conformant] = TRUE()
)
```
- **Format:** `#,##0`
- **Expected Baseline:** `440`
- **Canvas Placement:** Page 2 (Card / Donut).

---

### Measure 9: `[Review Cases Count]`
Counts cases flagged for operational review due to rule deviations (repeated triage loops).
```dax
Review Cases Count =
CALCULATE(
    [Total Cases],
    DimPatientCase[is_conformant] = FALSE()
)
```
- **Format:** `#,##0`
- **Expected Baseline:** `60`
- **Canvas Placement:** Page 2 (Card / Donut).

---

### Measure 10: `[Conformance Rate %]`
Computes the percentage of the cohort that followed standard workflow sequences.
```dax
Conformance Rate % =
DIVIDE(
    [Conformant Cases Count],
    [Total Cases],
    0
)
```
- **Format:** `0.0%`
- **Expected Baseline:** `88.0%`
- **Canvas Placement:** Page 2 (KPI Card).

---

### Measure 11: `[Re-Triage Rate %]`
Computes the proportion of patients who experienced an operational re-triage loop before doctor consultation.
```dax
Re-Triage Rate % =
DIVIDE(
    [Review Cases Count],
    [Total Cases],
    0
)
```
- **Format:** `0.0%`
- **Expected Baseline:** `12.0%`
- **Canvas Placement:** Page 1 (KPI Card), Page 2 (KPI Card).

---

## 6. Bottleneck & Milestone Transition Measures

### Measure 12: `[Top Bottleneck Mean Duration]`
Retrieves the mean observed duration of the #1 ranked bottleneck (`Laboratory -> Consultation`).
```dax
Top Bottleneck Mean Duration =
CALCULATE(
    MAX(FactBottlenecks[mean_observed_transition_minutes]),
    FactBottlenecks[rank] = 1
)
```
- **Format:** `0.0 "Mins"`
- **Expected Value:** `67.4 Mins`
- **Canvas Placement:** Page 3 (Highlight Card).

---

### Measure 13: `[Re-Triage Loop Mean Duration]`
Retrieves the mean observed duration of the #2 ranked bottleneck (`Triage -> Triage`).
```dax
Re-Triage Loop Mean Duration =
CALCULATE(
    MAX(FactBottlenecks[mean_observed_transition_minutes]),
    FactBottlenecks[rank] = 2
)
```
- **Format:** `0.0 "Mins"`
- **Expected Value:** `65.6 Mins`
- **Canvas Placement:** Page 3 (Highlight Card).

---

## 7. As-Is vs. Hypothetical To-Be Scenario Measures

These measures read from the `FactImprovementScenario` table to drive Page 4 comparative visuals:

### Measure 14: `[Baseline Mean Duration]`
```dax
Baseline Mean Duration =
CALCULATE(
    MAX(FactImprovementScenario[baseline_value]),
    FactImprovementScenario[metric_name] = "Mean Encounter Duration"
)
```
- **Format:** `0.0 "Mins"`
- **Expected Value:** `202.5 Mins`
- **Canvas Placement:** Page 4 (Comparison Card).

---

### Measure 15: `[To-Be Mean Duration]`
```dax
To-Be Mean Duration =
CALCULATE(
    MAX(FactImprovementScenario[proposed_value]),
    FactImprovementScenario[metric_name] = "Mean Encounter Duration"
)
```
- **Format:** `0.0 "Mins"`
- **Expected Value:** `181.8 Mins`
- **Canvas Placement:** Page 4 (Comparison Card).

---

### Measure 16: `[Mean Duration Reduction %]`
```dax
Mean Duration Reduction % =
CALCULATE(
    MAX(FactImprovementScenario[percentage_difference]),
    FactImprovementScenario[metric_name] = "Mean Encounter Duration"
) / 100
```
- **Format:** `+0.0%;-0.0%;0.0%`
- **Expected Value:** `-10.3%`
- **Canvas Placement:** Page 4 (Callout Difference Card).

---

### Measure 17: `[Baseline Median Duration]`
```dax
Baseline Median Duration =
CALCULATE(
    MAX(FactImprovementScenario[baseline_value]),
    FactImprovementScenario[metric_name] = "Median Encounter Duration"
)
```
- **Format:** `0.0 "Mins"`
- **Expected Value:** `211.0 Mins`
- **Canvas Placement:** Page 4 (Comparison Card).

---

### Measure 18: `[To-Be Median Duration]`
```dax
To-Be Median Duration =
CALCULATE(
    MAX(FactImprovementScenario[proposed_value]),
    FactImprovementScenario[metric_name] = "Median Encounter Duration"
)
```
- **Format:** `0.0 "Mins"`
- **Expected Value:** `191.2 Mins`
- **Canvas Placement:** Page 4 (Comparison Card).

---

### Measure 19: `[Median Duration Reduction %]`
```dax
Median Duration Reduction % =
CALCULATE(
    MAX(FactImprovementScenario[percentage_difference]),
    FactImprovementScenario[metric_name] = "Median Encounter Duration"
) / 100
```
- **Format:** `+0.0%;-0.0%;0.0%`
- **Expected Value:** `-9.4%`
- **Canvas Placement:** Page 4 (Callout Difference Card).

---

### Measure 20: `[Baseline P90 Duration]`
```dax
Baseline P90 Duration =
CALCULATE(
    MAX(FactImprovementScenario[baseline_value]),
    FactImprovementScenario[metric_name] = "90th Percentile Duration (P90)"
)
```
- **Format:** `0.0 "Mins"`
- **Expected Value:** `284.0 Mins`
- **Canvas Placement:** Page 4 (Comparison Card).

---

### Measure 21: `[To-Be P90 Duration]`
```dax
To-Be P90 Duration =
CALCULATE(
    MAX(FactImprovementScenario[proposed_value]),
    FactImprovementScenario[metric_name] = "90th Percentile Duration (P90)"
)
```
- **Format:** `0.0 "Mins"`
- **Expected Value:** `255.2 Mins`
- **Canvas Placement:** Page 4 (Comparison Card).

---

### Measure 22: `[P90 Duration Reduction %]`
```dax
P90 Duration Reduction % =
CALCULATE(
    MAX(FactImprovementScenario[percentage_difference]),
    FactImprovementScenario[metric_name] = "90th Percentile Duration (P90)"
) / 100
```
- **Format:** `+0.0%;-0.0%;0.0%`
- **Expected Value:** `-10.2%`
- **Canvas Placement:** Page 4 (Callout Difference Card).

---

## 8. Summary Table of All Verified Measures

| Measure Name | Return Type | Format String | Source Table & Logic | Target Page |
| :--- | :--- | :--- | :--- | :--- |
| `[Total Cases]` | Integer | `#,##0` | `DISTINCTCOUNT(FactHospitalEvents[case_id])` | Pages 1, 2, 4 |
| `[Total Events]` | Integer | `#,##0` | `COUNTROWS(FactHospitalEvents)` | Pages 1, 2 |
| `[Total Pathway Variants]` | Integer | `#,##0` | `DISTINCTCOUNT(DimPatientCase[observed_pathway])` | Page 2 |
| `[Avg Case Cycle Time (Mins)]` | Decimal | `0.0 "Mins"` | `AVERAGE(DimPatientCase[case_duration_minutes])` | Pages 1, 2 |
| `[Median Case Cycle Time (Mins)]` | Decimal | `0.0 "Mins"` | `MEDIAN(DimPatientCase[case_duration_minutes])` | Page 1 |
| `[Avg Observed Transition Time (Mins)]`| Decimal | `0.0 "Mins"` | `AVERAGE(FactHospitalEvents[transition_minutes_from_previous])` | Page 3 |
| `[Median Observed Transition Time (Mins)]`| Decimal | `0.0 "Mins"` | `MEDIAN(FactHospitalEvents[transition_minutes_from_previous])` | Page 3 |
| `[Conformant Cases Count]` | Integer | `#,##0` | `CALCULATE([Total Cases], is_conformant = TRUE)` | Page 2 |
| `[Review Cases Count]` | Integer | `#,##0` | `CALCULATE([Total Cases], is_conformant = FALSE)` | Page 2 |
| `[Conformance Rate %]` | Decimal | `0.0%` | `[Conformant Cases] / [Total Cases]` | Page 2 |
| `[Re-Triage Rate %]` | Decimal | `0.0%` | `[Review Cases] / [Total Cases]` | Pages 1, 2 |
| `[Top Bottleneck Mean Duration]` | Decimal | `0.0 "Mins"` | `FactBottlenecks[rank] = 1` | Page 3 |
| `[Re-Triage Loop Mean Duration]` | Decimal | `0.0 "Mins"` | `FactBottlenecks[rank] = 2` | Page 3 |
| `[Baseline Mean Duration]` | Decimal | `0.0 "Mins"` | `FactImprovementScenario[Mean Encounter Duration]` | Page 4 |
| `[To-Be Mean Duration]` | Decimal | `0.0 "Mins"` | `FactImprovementScenario[Mean Encounter Duration]` | Page 4 |
| `[Mean Duration Reduction %]` | Decimal | `+0.0%;-0.0%;0.0%` | Difference / Baseline | Page 4 |
| `[Baseline Median Duration]` | Decimal | `0.0 "Mins"` | `FactImprovementScenario[Median Encounter Duration]` | Page 4 |
| `[To-Be Median Duration]` | Decimal | `0.0 "Mins"` | `FactImprovementScenario[Median Encounter Duration]` | Page 4 |
| `[Median Duration Reduction %]` | Decimal | `+0.0%;-0.0%;0.0%` | Difference / Baseline | Page 4 |
| `[Baseline P90 Duration]` | Decimal | `0.0 "Mins"` | `FactImprovementScenario[P90]` | Page 4 |
| `[To-Be P90 Duration]` | Decimal | `0.0 "Mins"` | `FactImprovementScenario[P90]` | Page 4 |
| `[P90 Duration Reduction %]` | Decimal | `+0.0%;-0.0%;0.0%` | Difference / Baseline | Page 4 |
