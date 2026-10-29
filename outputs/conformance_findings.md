# CareFlow Clinical Pathway: Patient Pathway Conformance Findings

- **Project:** CareFlow Clinical Pathway Analytics
- **Evaluation Date:** October 28, 2026
- **Artifact:** `outputs/conformance_findings.md`
- **Related Artifacts:** [`outputs/conformance_case_results.csv`](conformance_case_results.csv), [`outputs/conformance_findings_summary.json`](conformance_findings_summary.json)
- **Input Event Log:** `data/cleaned/stg_hospital_events.csv` (Simulated)

---

## 1. Executive Summary & Objective

The objective of this Patient Pathway Conformance Checking module is to evaluate whether simulated emergency department patient encounters adhere to defined clinical workflow guidelines. By measuring deviations against configurable operational rules, the analysis identifies encounters warranting clinical audit or operational review.

### Synthetic Data Disclaimer & Ethical Boundary
- **100% Synthetic Event Data:** All evaluated data originates from synthetic simulation models (500 encounters, 3,140 events). It contains **no real patient records, Electronic Health Records (EHR), or Protected Health Information (PHI)**.
- **Analytical Attribution Boundary:** Rule deviations are classified strictly as **operational review candidates** or **workflow audit candidates**, NOT as evidence of unsafe patient care or clinical malpractice. In emergency medicine, deviations frequently reflect clinically justified adaptations to patient acuity evolution.

---

## 2. Key Conformance Metrics Overview

The summary metrics distinguish total encounters evaluated, encounters flagged, and total rule deviations:

| Metric | Count / Value | Proportion (%) | Analytical Interpretation |
| :--- | :---: | :---: | :--- |
| **Total Cases Evaluated** | **500** | 100.0% | Complete emergency department patient cohort |
| **Conformant Cases** | **440** | **88.0%** | Fully compliant with all configured workflow rules |
| **Flagged Cases (Review Candidates)** | **60** | **12.0%** | Encounters exhibiting one or more rule deviations |
| **Total Rule Deviations** | **60** | — | Cumulative count of individual rule trigger events |

> **Methodological Note on Counts:** The count of *cases flagged* (60) and *total rule deviations* (60) are distinct analytical concepts. A single complex encounter may accumulate multiple rule deviations across different categories.

---

## 3. Conformance Evaluation by Workflow Rule

Configured workflow rules were evaluated across all patient encounters:

| Rule Identifier | Rule Name | Category | Triggered Cases ($N$) | Rate (%) | Operational Significance |
| :--- | :--- | :---: | :---: | :---: | :--- |
| `RULE_MANDATORY_ACTIVITIES` | Mandatory Activities Check | Protocol Compliance | **0** | 0.0% | Missing core milestones (Registration, Triage, Consultation, Treatment, Discharge) |
| `RULE_START_ACTIVITY` | Start Activity Check | Protocol Compliance | **0** | 0.0% | Encounter begins with an activity other than Registration |
| `RULE_END_ACTIVITY` | End Activity Check | Protocol Compliance | **0** | 0.0% | Encounter terminates without formal Discharge milestone |
| `RULE_ACTIVITY_ORDER` | Activity Ordering Check | Temporal Precedence | **0** | 0.0% | Out-of-sequence execution (e.g., Treatment before Consultation) |
| `RULE_DIAGNOSTIC_FOLLOWUP` | Diagnostic Review Check | Clinical Safety | **0** | 0.0% | Laboratory or X-Ray completed without physician Consultation review prior to Treatment |
| `RULE_REPEATED_TRIAGE` | Repeated Triage Audit | Operational Review | **60** | 12.0% | Patient reassessed while queued; signals waiting room delay / clinical acuity shift |
| `RULE_DUPLICATE_EVENTS` | Duplicate Event Check | Data Quality | **0** | 0.0% | Unexpected repetition of single-milestone events or identical timestamps |

---

## 4. Pathway Variant Conformance Breakdown

Evaluation across the 6 clinical pathway variants discovered in process mining:

| Variant Rank | Clinical Pathway Sequence | Total Cases | Flagged Cases | Compliance Rate (%) | Review Classification |
| :---: | :--- | :---: | :---: | :---: | :--- |
| **1** | `Registration -> Triage -> Consultation -> Treatment -> Discharge` | 200 | 0 | **100.0%** | Conformant |
| **2** | `Registration -> Triage -> Consultation -> Laboratory -> Consultation -> Treatment -> Discharge` | 110 | 0 | **100.0%** | Conformant |
| **3** | `Registration -> Triage -> Consultation -> X-Ray -> Consultation -> Treatment -> Discharge` | 80 | 0 | **100.0%** | Conformant |
| **4** | `Registration -> Triage -> Consultation -> Laboratory -> X-Ray -> Consultation -> Treatment -> Discharge` | 50 | 0 | **100.0%** | Conformant |
| **5** | `Registration -> Triage -> Triage -> Consultation -> Treatment -> Discharge` | 35 | 35 | **0.0%** | Review Candidate (Re-Triage) |
| **6** | `Registration -> Triage -> Triage -> Consultation -> Laboratory -> Consultation -> Treatment -> Discharge` | 25 | 25 | **0.0%** | Review Candidate (Re-Triage) |

### Key Variant Observations
1. **Full Diagnostic Pathway Compliance (Variants 1–4):**
   - Variants 1 through 4 (accounting for 440 cases, 88.0% of the cohort) are **100% conformant** with all workflow rules.
   - **Alternative Diagnostic Pathways are Conformant:** Diagnostic pathways (Variant 2 with Laboratory, Variant 3 with X-Ray, and Variant 4 with both Lab and X-Ray) correctly incorporate physician consultation prior to diagnostic orders and follow-up physician consultation before treatment delivery.
2. **Repeated Triage Encounters (Variants 5 and 6):**
   - Variants 5 and 6 (accounting for 60 cases, 12.0% of the cohort) trigger `RULE_REPEATED_TRIAGE` due to consecutive `Triage -> Triage` milestones.
   - These encounters represent the **sole source of rule deviations** in the canonical simulated cohort.

---

## 5. Clinical & Operational Interpretation

### A. Repeated Triage as an Operational Review Target
- **Audit Focus:** The 60 encounters undergoing re-triage represent a critical operational safety metric. In clinical practice, repeated triage indicates that a patient's queuing duration exceeded protocol thresholds or that physical condition deterioration prompted nursing re-evaluation.
- **Operational Distinction:** Repeated triage is **not a clinical mistake**—it is a protective safety net. However, its occurrence highlights waiting room bottlenecks and patient queuing delays between triage and physician consultation.

### B. Diagnostic Pathway Rigor
- All 185 laboratory requests and 130 radiologic examinations in the cohort were ordered during a formal physician consultation and followed by a dedicated review consultation prior to patient treatment.
- No instances of unmonitored treatment initiation or direct discharge without diagnostic review were identified.

---

## 6. Analytical Limitations

1. **Discrete Milestone Representation:**
   - Event logs capture milestone completion timestamps but lack continuous activity durations or reason codes for re-triage.
2. **Simulated Ground Truth:**
   - Data is generated deterministically; observed deviations reflect modeled simulation parameters rather than institutional hospital practices.
3. **Lack of Dynamic Context:**
   - Triage severity score (Levels 1–5), patient vital signs, and concurrent ED bed occupancy are unobserved in the staging event log.

---

## 7. Recommended Next Steps for Clinical Operations

1. **Stratify Re-Triage by Acuity (Severity Levels 1–5):**
   - Correlate re-triage occurrences with triage acuity scores to evaluate whether deterioration occurs primarily in lower-acuity patients experiencing extended waits.
2. **Integrate Conformance Metrics into Power BI Dashboard:**
   - Ingest `outputs/conformance_case_results.csv` into the Power BI star schema.
   - Add a dedicated **Pathway Conformance & Audit** view enabling operations directors to drill down into the 60 re-triage encounters.
3. **Token-Replay Alignment (Week 4 Deliverable):**
   - Apply PM4Py token-replay conformance checking algorithms to compute formal mathematical fitness and precision scores against the normative reference model.
