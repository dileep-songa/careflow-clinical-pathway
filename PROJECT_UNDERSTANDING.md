# CareFlow Project Understanding - Day 1 Analysis

## Project Context
**Project Name:** CareFlow: Clinical Pathway Process Mining  
**Domain:** Healthcare Operations & Process Analytics  
**Company:** Infotact Solutions  
**Internship Type:** Data Analytics & Process Mining  
**Timeline:** 4 weeks

---

## Business Problem

### The Challenge
Hospital administrators struggle to understand why Emergency Room (ER) wait times are inconsistently high. The raw data from Electronic Health Records (EHRs) shows timestamps but does not reveal:
- Why certain patient pathways take longer than others
- Where bottlenecks occur in the clinical workflow
- Hidden patterns in patient journeys (e.g., 40% of patients are sent back to triage)
- Operational inefficiencies that impact patient care

### Current Situation
- Standard dashboards show "Average ER wait time: 3 hours"
- But they don't answer: What causes the variation? Which departments are slow? When does delay happen?
- Process mining can uncover the actual patient flow and reveal root causes

---

## What is Process Mining?

Process Mining is a data analysis technique that:
1. **Extracts** event sequences from logs (e.g., patient admitted → triage → doctor → treatment → discharge)
2. **Discovers** the actual process flow (not the intended one)
3. **Detects** deviations, loops, and bottlenecks
4. **Measures** time, resources, and compliance

**Example:** Instead of just knowing "average wait time = 45 mins", process mining reveals:
- Path A (70% of patients): 30 mins
- Path B (20% of patients): 90 mins (includes re-triage)
- Path C (10% of patients): 2 hours (includes radiology, then re-evaluation)

This enables targeted solutions.

---

## Hospital Workflow - Key Events

Based on the project requirements, the hospital patient journey includes these events:

| Event | Description | Key Data |
|-------|-------------|----------|
| **Admission** | Patient enters hospital | timestamp, patient_id, admission_type, priority |
| **Triage** | Initial assessment (vital signs, complaints) | timestamp, severity_level, department_assigned |
| **Doctor Consultation** | Clinical evaluation | timestamp, doctor_id, findings, treatment_plan |
| **Treatment** | Medical intervention provided | timestamp, treatment_type, duration, department |
| **Lab/Imaging** | Diagnostic tests (optional path) | timestamp, test_type, result, time_to_result |
| **Discharge** | Patient leaves hospital | timestamp, outcome, follow_up_plan |

### Optional Paths (Variations)
- **Re-triage:** Patient reassigned after initial assessment (causes delays)
- **Waiting:** Time between events
- **Specialist Consultation:** Routed to cardiology, orthopedics, etc.

---

## Data We'll Work With

### Event Log Structure
Our data will be in this format (Event Log):

```
patient_id  | case_id | event_type      | department  | timestamp           | duration_mins | doctor_id
----------- | ------- | --------------- | ----------- | ------------------- | ------------- | ---------
P001        | C001    | admission       | ER          | 2024-10-01 08:15:00 | 5             | NULL
P001        | C001    | triage          | ER          | 2024-10-01 08:20:00 | 15            | NURSE_01
P001        | C001    | doctor_consult  | ER          | 2024-10-01 08:35:00 | 20            | DOC_002
P001        | C001    | treatment       | ER          | 2024-10-01 08:55:00 | 30            | DOC_002
P001        | C001    | discharge       | ER          | 2024-10-01 09:25:00 | 5             | DOC_002
```

Key insights from this log:
- **Patient P001's journey:** 70 minutes total (admission to discharge)
- **Wait times:** Between events
- **Department movement:** All events in ER (no specialist visit)
- **Staffing involved:** NURSE_01, DOC_002

---

## Week-by-Week Breakdown (From Project Doc)

### Week 1: EHR Data Simulation & Setup
**Left Side (Event Log Engineering):**
- Create Python script to generate mock hospital event logs
- Simulate realistic patient pathways with variations
- Include operational inefficiencies (long waits, re-triages, loops)

**Right Side (Warehouse Setup):**
- Load raw event data into BigQuery
- Configure data warehouse schema
- Set up tables for efficient querying

### Week 2: Data Normalization & Process Discovery
**Left Side:**
- Standardize event names (e.g., "DR_VISIT" → "doctor_consultation")
- Convert timestamps to standard format
- Validate data integrity

**Right Side:**
- Use PM4Py to discover process flow
- Generate "As-Is" process map (actual workflow)
- Identify primary paths and deviations

### Week 3: Bottleneck Analysis & Dashboarding
**Left Side:**
- Calculate wait times between departments
- Identify where patients spend most time
- Compute average cycle time from admission to discharge

**Right Side:**
- Connect cleaned data to PowerBI/Looker
- Create interactive dashboard
- Add KPI cards and filtering capabilities

### Week 4: Conformance & Final Report
**Left Side:**
- Compare actual process vs. hospital's "ideal" process
- Identify non-compliant pathways
- Flag bottleneck-causing variations

**Right Side:**
- Refine dashboard polish and drill-down features
- Prepare presentation for hospital administrators
- Document recommendations for improvement

---

## Key Deliverables (From Project Doc)

1. **Source Code**
   - Data cleaning scripts (Python/SQL)
   - Process mining engine (PM4Py)
   - Visualization generation code

2. **Project Documentation**
   - Data schema documentation
   - Process mining methodology
   - Business findings report

3. **Project Report**
   - Executive summary (1 page)
   - Findings (2-3 pages)
   - Recommendations (1 page)
   - Supporting charts and diagrams

4. **Presentation (PPT)**
   - Problem statement
   - Current workflow visualization
   - Bottleneck analysis
   - Recommended solutions

5. **Model Evaluation Results**
   - Process discovery accuracy
   - Conformance checking results
   - KPI baseline vs. expected

6. **Project Demonstration**
   - Live walkthrough of dashboard
   - Process mining outputs
   - Q&A session

---

## Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|----------|
| **Data Processing** | Python, Pandas, SQL | Clean, transform event logs |
| **Process Mining** | PM4Py (Python library) | Discover process flows |
| **Data Storage** | Google BigQuery | Cloud warehouse for EHR data |
| **Data Transformation** | DBT (optional) | Transform raw data following ELT pattern |
| **Visualization** | PowerBI or Looker | Create interactive dashboards |
| **Version Control** | Git & GitHub | Track code changes |

---

## Key Questions We'll Answer

### Week 1
- What is the raw hospital event log structure?
- How many patients flow through ER daily?
- What are the main patient pathways?

### Week 2
- What is the standardized process flow (As-Is)?
- Which paths do most patients follow?
- Are there unexpected loops or re-routing?

### Week 3
- Where do patients spend the most time?
- Which transitions are slowest?
- What is the average end-to-end time?

### Week 4
- Are patients following the intended clinical pathway?
- Where do deviations occur?
- What changes would reduce wait times most effectively?

---

## Success Criteria

✅ **Data Quality**
- 100% of timestamps are valid and in sequence
- Patient IDs are consistent throughout journey
- No duplicate events for same patient at same time

✅ **Process Mining**
- Discover at least 3 distinct patient pathways
- Identify at least 2 bottlenecks
- Calculate average wait time by department

✅ **Visualization**
- Dashboard shows process flow with wait times
- KPIs are accurate and actionable
- Administrators can filter by date, department, severity

✅ **Business Value**
- Provide at least 2 specific recommendations
- Show potential impact (e.g., "Adding 1 nurse could reduce wait time by 15%")
- Present findings in non-technical language

---

## Next Steps (Day 2-3)

1. **Set up development environment**
   - Install Python libraries (pandas, pm4py, matplotlib)
   - Set up Jupyter notebook
   - Connect to BigQuery (if using real data)

2. **Create mock data generator**
   - Write Python script to generate sample hospital events
   - Create 100-200 realistic patient journeys
   - Save to CSV for initial analysis

3. **Inspect data**
   - Load data into pandas DataFrame
   - Explore structure and statistics
   - Identify data quality issues

---

## Personal Reflection

As an intern on this project, my role is to:
- **Learn** process mining concepts and healthcare analytics
- **Apply** these skills to solve real operational problems
- **Deliver** actionable insights that hospital administrators can use
- **Document** my work professionally for the team

This is not just about writing code—it's about understanding the business problem, asking the right questions, and turning data into decisions.

---

*Document created: Day 1 of internship*  
*Reviewed: Project brief, healthcare workflow, process mining concepts*
