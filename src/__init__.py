# CareFlow Data Schema Documentation

## Overview
This document defines the structure of hospital event logs that we'll collect, clean, and analyze for process mining.

---

## Event Log Table Schema

### Table Name: `hospital_events` (Raw Data)

```sql
CREATE TABLE hospital_events (
    event_id STRING,              -- Unique identifier for each event
    patient_id STRING,            -- De-identified patient ID
    case_id STRING,               -- Unique hospital visit ID
    event_type STRING,            -- Type of event (admission, triage, consultation, etc.)
    event_timestamp TIMESTAMP,    -- When the event occurred
    department STRING,            -- Department/location (ER, ICU, Surgery, etc.)
    resource STRING,              -- Person involved (doctor, nurse ID)
    duration_minutes INT64,       -- How long the event took
    patient_age INT64,            -- Patient age category
    severity_level STRING,        -- Triage level (critical, urgent, moderate, minor)
    diagnosis_code STRING,        -- ICD-10 code (if available)
    notes STRING,                 -- Event-specific notes
    created_timestamp TIMESTAMP   -- When this record was created
);
```

### Field Descriptions

| Field | Type | Description | Example |
|-------|------|-------------|----------|
| `event_id` | STRING | Unique event identifier | EVT_20241001_000123 |
| `patient_id` | STRING | De-identified patient | P_12345 |
| `case_id` | STRING | Hospital visit/admission | CASE_20241001_001 |
| `event_type` | STRING | Event category | admission, triage, doctor_consultation |
| `event_timestamp` | TIMESTAMP | Date & time event occurred | 2024-10-01 08:15:30 |
| `department` | STRING | Hospital location | Emergency Room, ICU, Radiology |
| `resource` | STRING | Staff member involved | DOC_001, NURSE_05 |
| `duration_minutes` | INT64 | Event duration | 25 |
| `patient_age` | INT64 | Age of patient | 45 |
| `severity_level` | STRING | Triage acuity | Critical, Urgent, Moderate, Minor |
| `diagnosis_code` | STRING | Medical diagnosis code | J44.9 (COPD) |
| `notes` | STRING | Additional context | "Patient had chest pain" |
| `created_timestamp` | TIMESTAMP | Record creation time | 2024-10-01 10:30:00 |

---

## Event Types (Standardized)

We will standardize all event names to these types:

```python
EVENT_TYPES = {
    'admission': 'Patient enters hospital',
    'triage': 'Initial nursing assessment',
    'doctor_consultation': 'Doctor evaluation',
    'lab_test': 'Laboratory test ordered/completed',
    'imaging': 'Radiology/imaging test',
    'treatment': 'Medical treatment provided',
    'medication': 'Drug administered',
    'specialist_referral': 'Sent to specialist',
    'discharge': 'Patient leaves hospital',
    're_triage': 'Patient reassessed (re-routing)',
    'waiting': 'Idle time between events',
    'admission_hold': 'Waiting for bed/admission'
}
```

---

## Departments (Standard Mapping)

```python
DEPARTMENT_MAPPING = {
    'ER': 'Emergency Room',
    'ICU': 'Intensive Care Unit',
    'WARD_A': 'General Ward A',
    'WARD_B': 'General Ward B',
    'RADIOLOGY': 'Radiology Department',
    'LAB': 'Laboratory',
    'SURGERY': 'Operating Theatre',
    'CARDIO': 'Cardiology',
    'NEURO': 'Neurology',
    'ORTHO': 'Orthopedics',
    'PHARMACY': 'Pharmacy',
}
```

---

## Severity Levels (Triage Classification)

| Level | Code | Description | Expected Action Time |
|-------|------|-------------|----------------------|
| Critical | 1 | Life-threatening, immediate intervention needed | 0-10 mins |
| Urgent | 2 | Serious, needs prompt evaluation | 10-30 mins |
| Moderate | 3 | Stable but needs medical attention | 30-90 mins |
| Minor | 4 | Non-urgent, can wait longer | 90+ mins |
| Non-urgent | 5 | Walk-in, self-limiting condition | No time constraint |

---

## Cleaned/Processed Table Schema

### Table Name: `hospital_events_cleaned`

After data cleaning, we'll have a standardized table:

```sql
CREATE TABLE hospital_events_cleaned (
    event_sequence INT64,        -- Sequential order in patient journey
    case_id STRING,              -- Unique visit ID (primary key for process mining)
    event_type STRING,           -- Standardized event type
    event_timestamp TIMESTAMP,   -- Standardized datetime
    department STRING,           -- Mapped department name
    resource STRING,             -- Standardized resource ID
    duration_minutes INT64,      -- Cleaned duration
    severity_level STRING,       -- Normalized severity
    patient_demographic STRING,  -- Age group (0-18, 19-40, 41-65, 65+)
    time_since_admission INT64,  -- Minutes elapsed since admission
    time_to_next_event INT64,    -- Wait time until next event
    day_of_week STRING,          -- day name for trend analysis
    hour_of_day INT64,           -- Hour of day (0-23)
    PRIMARY KEY (case_id, event_sequence)
);
```

---

## KPI Calculation Fields

Derived metrics we'll calculate:

| KPI | Formula | Business Meaning |
|-----|---------|------------------|
| **Total Cycle Time** | discharge_time - admission_time | How long patient spent in hospital |
| **Triage-to-Doctor Time** | doctor_consult_time - triage_time | Speed of initial evaluation |
| **Wait Time (Department)** | next_event_time - event_end_time | Idle time between events |
| **Throughput (Department)** | # patients / 24 hours | How many patients processed daily |
| **Re-triage Rate** | (# re-triages / # admissions) × 100 | % of patients reassessed |
| **Specialist Routing %** | (# specialist visits / # admissions) × 100 | % requiring specialist |
| **Average Wait by Severity** | AVG(wait_time) GROUP BY severity | How urgency affects wait |

---

## Data Quality Rules

Validations we'll apply:

```python
DATA_QUALITY_CHECKS = {
    'no_null_keys': 'patient_id, case_id, event_timestamp must not be null',
    'timestamp_order': 'Events must be in chronological order per case',
    'valid_event_type': 'event_type must be in ALLOWED_EVENT_TYPES',
    'valid_department': 'department must be in ALLOWED_DEPARTMENTS',
    'valid_severity': 'severity_level must be in [1, 2, 3, 4, 5]',
    'positive_duration': 'duration_minutes must be > 0',
    'no_duplicates': 'No duplicate (patient_id, event_type, timestamp) combinations',
    'reasonable_age': 'patient_age must be between 0 and 120',
    'no_future_dates': 'event_timestamp cannot be in the future'
}
```

---

## Example Event Log (Raw)

```
event_id,patient_id,case_id,event_type,event_timestamp,department,resource,duration_minutes,patient_age,severity_level
EVT_001,P_ABC123,CASE_001,admission,2024-10-01 08:00:00,ER,ADMIN_01,5,42,2
EVT_002,P_ABC123,CASE_001,triage,2024-10-01 08:05:30,ER,NURSE_03,15,42,2
EVT_003,P_ABC123,CASE_001,doctor_consultation,2024-10-01 08:20:45,ER,DOC_002,25,42,2
EVT_004,P_ABC123,CASE_001,lab_test,2024-10-01 08:46:00,LAB,TECH_01,30,42,2
EVT_005,P_ABC123,CASE_001,imaging,2024-10-01 09:16:15,RADIOLOGY,TECH_02,20,42,2
EVT_006,P_ABC123,CASE_001,doctor_consultation,2024-10-01 09:37:00,ER,DOC_002,15,42,2
EVT_007,P_ABC123,CASE_001,treatment,2024-10-01 09:52:30,ER,NURSE_03,45,42,2
EVT_008,P_ABC123,CASE_001,discharge,2024-10-01 10:38:00,ER,DOC_002,5,42,2
```

### Analysis of this journey:
- **Total time:** 2 hours 38 minutes
- **Path:** Admission → Triage → Doctor → Lab → Imaging → Doctor again → Treatment → Discharge
- **Wait times:** 
  - Triage to Doctor: 15 mins
  - Doctor to Lab: 25 mins
  - Lab to Imaging: 46 mins (longest wait)
  - Imaging to Doctor: 21 mins
  - Doctor to Treatment: 15 mins
- **Key insight:** 46-minute wait between lab and imaging is a potential bottleneck

---

## Cleaned Example

```
event_sequence,case_id,event_type,event_timestamp,department,duration_minutes,severity_level,time_since_admission,time_to_next_event
1,CASE_001,admission,2024-10-01 08:00:00,ER,5,Urgent,0,5
2,CASE_001,triage,2024-10-01 08:05:30,ER,15,Urgent,5,15
3,CASE_001,doctor_consultation,2024-10-01 08:20:45,ER,25,Urgent,20,25
4,CASE_001,lab_test,2024-10-01 08:46:00,LAB,30,Urgent,46,30
5,CASE_001,imaging,2024-10-01 09:16:15,RADIOLOGY,20,Urgent,76,21
6,CASE_001,doctor_consultation,2024-10-01 09:37:00,ER,15,Urgent,97,15
7,CASE_001,treatment,2024-10-01 09:52:30,ER,45,Urgent,112,45
8,CASE_001,discharge,2024-10-01 10:38:00,ER,5,Urgent,158,0
```

---

## Data Flow Pipeline

```
Raw EHR Data (XML/CSV)
        ↓
   Load to BigQuery (hospital_events)
        ↓
  Data Cleaning & Validation
        ↓
   Standardization (hospital_events_cleaned)
        ↓
   Process Mining Analysis (PM4Py)
        ↓
  Dashboard Visualization (PowerBI)
        ↓
   Business Insights & Recommendations
```

---

## Next Steps (Day 2)

1. Create Python script to validate schema compliance
2. Generate mock data following this schema
3. Load sample data into local database or BigQuery
4. Test data quality checks
5. Generate exploratory data analysis report

---

*Data Schema v1.0 - Day 1*  
*Subject to updates as project requirements clarify*
