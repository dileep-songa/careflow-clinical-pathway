"""Project configuration for CareFlow.

This file stores the base configuration used by the project modules.
Note: Retained as baseline path and category configuration for downstream analytical workflows.
"""

RAW_DATA_PATH = "data/raw/"
CLEANED_DATA_PATH = "data/cleaned/"
REPORTS_PATH = "reports/"

EVENT_TYPES = [
    "admission",
    "triage",
    "doctor_consultation",
    "lab_test",
    "imaging",
    "treatment",
    "medication",
    "specialist_referral",
    "discharge",
    "re_triage",
    "waiting",
    "admission_hold",
]

DEPARTMENTS = [
    "ER",
    "ICU",
    "WARD_A",
    "WARD_B",
    "RADIOLOGY",
    "LAB",
    "SURGERY",
    "CARDIO",
    "NEURO",
    "ORTHO",
    "PHARMACY",
]

SEVERITY_LEVELS = [1, 2, 3, 4, 5]
