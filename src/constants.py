"""Project Constants and Configurations

Defines standardized event types, departments, severity levels,
and other constants used throughout the project.
Note: Retained as the project domain dictionary for clinical mappings and process mining parameters.
"""

# Event Types (Standardized names for all hospital events)
EVENT_TYPES = {
    'admission': 'Patient enters hospital',
    'triage': 'Initial nursing assessment and vital signs check',
    'doctor_consultation': 'Doctor evaluation and diagnosis',
    'lab_test': 'Laboratory test ordered or completed',
    'imaging': 'Radiology or imaging test (X-ray, CT, MRI, etc)',
    'treatment': 'Medical treatment provided to patient',
    'medication': 'Drug or medication administered',
    'specialist_referral': 'Referred to specialty department',
    'surgery': 'Surgical procedure',
    'discharge': 'Patient leaves hospital',
    're_triage': 'Patient reassessed and re-routed',
    'admission_hold': 'Waiting for bed or room availability',
    'waiting': 'Idle time between events',
}

# Hospital Departments (Standardized names)
DEPARTMENTS = {
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
    'PEDIATRICS': 'Pediatrics',
    'MATERNITY': 'Maternity',
}

# Triage Severity Levels
SEVERITY_LEVELS = {
    1: 'Critical',      # Life-threatening, immediate intervention needed
    2: 'Urgent',        # Serious condition, prompt evaluation needed
    3: 'Moderate',      # Stable but needs medical attention
    4: 'Minor',         # Non-urgent, can wait
    5: 'Non-urgent',    # Walk-in, self-limiting condition
}

# Age Groups (for demographic analysis)
AGE_GROUPS = {
    'pediatric': (0, 18),
    'young_adult': (19, 40),
    'adult': (41, 65),
    'senior': (66, 150),
}

# Data Paths
DATA_PATHS = {
    'raw': 'data/raw/',
    'cleaned': 'data/cleaned/',
    'processed': 'data/processed/',
}

# Process Mining Configuration
PROCESS_MINING_CONFIG = {
    'min_support': 0.05,           # 5% - minimum frequency for paths
    'min_confidence': 0.60,        # 60% - minimum confidence for relationships
    'min_activity_duration': 1,    # 1 minute - minimum event duration
}

# Expected Time Benchmarks (in minutes)
# Used to identify bottlenecks
TIME_BENCHMARKS = {
    'admission_to_triage': 15,
    'triage_to_doctor': 30,
    'doctor_to_treatment': 30,
    'lab_to_results': 60,
    'imaging_to_results': 45,
    'total_er_stay': 240,  # 4 hours for critical, 6-8 hours for others
}

# Data Quality Validation Rules
QUALITY_RULES = {
    'no_null_keys': True,                  # patient_id, case_id, timestamp required
    'timestamp_order': True,               # Events must be chronological per case
    'valid_event_type': True,              # Must be in EVENT_TYPES
    'valid_department': True,              # Must be in DEPARTMENTS
    'valid_severity': True,                # Must be in SEVERITY_LEVELS
    'positive_duration': True,             # Duration must be > 0
    'no_future_dates': True,               # Timestamp cannot be in future
    'reasonable_age': True,                # Age 0-120
}

# Report Generation Settings
REPORT_CONFIG = {
    'include_summary': True,
    'include_trends': True,
    'include_bottlenecks': True,
    'include_recommendations': True,
}
