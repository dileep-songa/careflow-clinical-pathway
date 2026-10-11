"""Simulated Hospital Dataset Generator for CareFlow.

Step 2: Synthetic Clinical Pathway Event Log Generation.

IMPORTANT SAFETY NOTICE:
------------------------
This module generates an entirely SYNTHETIC, SIMULATED hospital event log.
All patient journeys, timestamps, departments, and resources are artificially
generated using probabilistic simulation models for educational process mining.
NO real patient data (EHR/PHI) is used, and the generated bottleneck patterns
must NOT be interpreted as actual hospital operational findings.
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timedelta
from pathlib import Path
from random import Random
from typing import Any, Dict, List, Tuple

# Project root resolution relative to this script
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT_PATH = PROJECT_ROOT / "data" / "raw" / "hospital_events_simulated.csv"

# Required CSV Schema
CSV_COLUMNS = [
    "Case_ID",
    "Activity_Name",
    "Timestamp",
    "Department",
    "Resource",
    "Data_Type",
]

DATA_TYPE_VALUE = "SIMULATED"

# Standard Clinical Activities and Default Departments
ACTIVITY_DEPARTMENT_MAP = {
    "Registration": "ER",
    "Triage": "ER",
    "Consultation": "ER",
    "Laboratory": "LAB",
    "X-Ray": "RADIOLOGY",
    "Treatment": "ER",
    "Discharge": "ER",
}

# Synthetic De-identified Resource Pools
RESOURCE_POOLS = {
    "Registration": ["REG_CLERK_01", "REG_CLERK_02", "REG_CLERK_03", "REG_CLERK_04"],
    "Triage": ["NURSE_01", "NURSE_02", "NURSE_03", "NURSE_04", "NURSE_05"],
    "Consultation": ["DOC_01", "DOC_02", "DOC_03", "DOC_04", "DOC_05", "DOC_06"],
    "Laboratory": ["LAB_TECH_01", "LAB_TECH_02", "LAB_TECH_03", "LAB_TECH_04"],
    "X-Ray": ["RAD_TECH_01", "RAD_TECH_02", "RAD_TECH_03"],
    "Treatment": [
        "NURSE_01",
        "NURSE_02",
        "NURSE_03",
        "NURSE_04",
        "DOC_01",
        "DOC_02",
    ],
    "Discharge": ["DOC_01", "DOC_02", "DOC_03", "ADMIN_01", "ADMIN_02"],
}

# Realistic activity duration ranges (minutes)
ACTIVITY_DURATIONS = {
    "Registration": (3, 8),
    "Triage": (5, 15),
    "Consultation": (15, 30),
    "Laboratory": (25, 50),
    "X-Ray": (20, 40),
    "Treatment": (20, 55),
    "Discharge": (5, 12),
}

# Normal waiting time ranges between steps (minutes)
DEFAULT_WAIT_RANGE = (5, 25)

# Bottleneck waiting time ranges for intentional pathway variations (minutes)
BOTTLENECK_WAIT_RANGE = (35, 75)


def get_pathway_definitions(total_cases: int = 500) -> List[Tuple[str, List[str], int]]:
    """Define clinical pathway variants and assign case counts.

    Pathway variants and clinical rationales:
    1. Variant 1 - Standard Routine ER Pathway (40%):
       Registration -> Triage -> Consultation -> Treatment -> Discharge
       Plausible for straightforward acute complaints without specialized diagnostics.

    2. Variant 2 - Diagnostic Laboratory Pathway (22%):
       Registration -> Triage -> Consultation -> Laboratory -> Consultation -> Treatment -> Discharge
       Doctor orders lab panels, reviews results in follow-up consultation, treats, and discharges.

    3. Variant 3 - Diagnostic Radiology (X-Ray) Pathway (16%):
       Registration -> Triage -> Consultation -> X-Ray -> Consultation -> Treatment -> Discharge
       Suspected trauma or fracture requiring imaging, follow-up consult for radiologist findings, treatment, discharge.

    4. Variant 4 - Comprehensive Diagnostic Pathway (Lab + X-Ray) (10%):
       Registration -> Triage -> Consultation -> Laboratory -> X-Ray -> Consultation -> Treatment -> Discharge
       Complex acute presentations requiring both laboratory and imaging diagnostics.

    5. Variant 5A - Routine with Re-Triage Reassessment (7%):
       Registration -> Triage -> Triage -> Consultation -> Treatment -> Discharge
       Operational wait-time delay causes vital signs / condition reassessment before physician consultation.

    6. Variant 5B - Diagnostic with Re-Triage Reassessment (5%):
       Registration -> Triage -> Triage -> Consultation -> Laboratory -> Consultation -> Treatment -> Discharge
       Prolonged waiting time triggers repeat triage, followed by clinical investigation.

    Args:
        total_cases: Target total number of patient cases (default: 500).

    Returns:
        List of tuples: (variant_name, activity_sequence, case_count)
    """
    # Proportions matching clinical assumptions
    v1_count = int(round(total_cases * 0.40))  # 200
    v2_count = int(round(total_cases * 0.22))  # 110
    v3_count = int(round(total_cases * 0.16))  # 80
    v4_count = int(round(total_cases * 0.10))  # 50
    v5a_count = int(round(total_cases * 0.07))  # 35
    v5b_count = total_cases - (v1_count + v2_count + v3_count + v4_count + v5a_count)  # 25

    return [
        (
            "Standard_Routine",
            ["Registration", "Triage", "Consultation", "Treatment", "Discharge"],
            v1_count,
        ),
        (
            "Diagnostic_Lab",
            ["Registration", "Triage", "Consultation", "Laboratory", "Consultation", "Treatment", "Discharge"],
            v2_count,
        ),
        (
            "Diagnostic_XRay",
            ["Registration", "Triage", "Consultation", "X-Ray", "Consultation", "Treatment", "Discharge"],
            v3_count,
        ),
        (
            "Comprehensive_Lab_XRay",
            ["Registration", "Triage", "Consultation", "Laboratory", "X-Ray", "Consultation", "Treatment", "Discharge"],
            v4_count,
        ),
        (
            "ReTriage_Routine",
            ["Registration", "Triage", "Triage", "Consultation", "Treatment", "Discharge"],
            v5a_count,
        ),
        (
            "ReTriage_Diagnostic_Lab",
            ["Registration", "Triage", "Triage", "Consultation", "Laboratory", "Consultation", "Treatment", "Discharge"],
            v5b_count,
        ),
    ]


def generate_event_log(
    num_cases: int = 500,
    seed: int = 42,
    start_time: datetime | None = None,
) -> List[Dict[str, str]]:
    """Generate synthetic hospital event log records.

    Args:
        num_cases: Total number of patient journeys to generate (default: 500).
        seed: Random seed for deterministic reproducibility.
        start_time: Initial simulation timestamp (default: 2024-10-01 08:00:00).

    Returns:
        List of event dictionary records following the CareFlow schema.
    """
    rng = Random(seed)

    if start_time is None:
        start_time = datetime(2024, 10, 1, 8, 0, 0)

    pathways = get_pathway_definitions(num_cases)

    # Build sequence of pathway variants for all cases
    assigned_variants: List[Tuple[str, List[str]]] = []
    for var_name, seq, count in pathways:
        assigned_variants.extend([(var_name, seq)] * count)

    # Deterministically shuffle assignment across case IDs
    rng.shuffle(assigned_variants)

    all_events: List[Dict[str, str]] = []
    current_case_arrival = start_time

    for case_idx, (var_name, activity_seq) in enumerate(assigned_variants, start=1):
        case_id = f"CASE_{case_idx:04d}"

        # Stagger patient arrivals with realistic inter-arrival times (10 to 45 mins)
        arrival_gap_minutes = rng.randint(10, 45)
        current_case_arrival += timedelta(minutes=arrival_gap_minutes)

        event_timestamp = current_case_arrival
        primary_doctor = rng.choice(RESOURCE_POOLS["Consultation"])
        primary_nurse = rng.choice(RESOURCE_POOLS["Triage"])

        for step_idx, activity in enumerate(activity_seq):
            department = ACTIVITY_DEPARTMENT_MAP[activity]

            # Assign plausible, context-aware resource
            if activity == "Consultation":
                resource = primary_doctor
            elif activity == "Triage":
                # For repeated triage, may be reassessed by same nurse or handover nurse
                resource = primary_nurse if (step_idx == 1 or rng.random() < 0.5) else rng.choice(RESOURCE_POOLS["Triage"])
            elif activity == "Treatment":
                resource = primary_nurse if rng.random() < 0.7 else primary_doctor
            elif activity == "Discharge":
                resource = primary_doctor if rng.random() < 0.6 else rng.choice(RESOURCE_POOLS["Discharge"])
            else:
                resource = rng.choice(RESOURCE_POOLS[activity])

            all_events.append(
                {
                    "Case_ID": case_id,
                    "Activity_Name": activity,
                    "Timestamp": event_timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    "Department": department,
                    "Resource": resource,
                    "Data_Type": DATA_TYPE_VALUE,
                }
            )

            # Advance timestamp for next activity within this case
            if step_idx < len(activity_seq) - 1:
                dur_min, dur_max = ACTIVITY_DURATIONS.get(activity, (5, 15))
                step_duration = rng.randint(dur_min, dur_max)

                # Intentional bottleneck wait before re-triage or diagnostic review
                next_activity = activity_seq[step_idx + 1]
                if activity == "Triage" and next_activity == "Triage":
                    wait_minutes = rng.randint(*BOTTLENECK_WAIT_RANGE)
                elif activity in ("Laboratory", "X-Ray") and next_activity == "Consultation":
                    wait_minutes = rng.randint(15, 45)
                else:
                    wait_minutes = rng.randint(*DEFAULT_WAIT_RANGE)

                event_timestamp += timedelta(minutes=step_duration + wait_minutes)

    return all_events


def save_event_log_to_csv(events: List[Dict[str, str]], output_path: Path) -> Path:
    """Save generated events to CSV at the designated project path.

    Args:
        events: List of event records.
        output_path: Target CSV file path.

    Returns:
        The resolved Path where the CSV was written.
    """
    output_path = Path(output_path).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(events)

    return output_path


def validate_event_log(csv_path: Path, expected_cases: int = 500) -> Dict[str, Any]:
    """Perform rigorous validation of the generated event log.

    Verification checks:
    1. CSV file exists and is non-empty.
    2. Exact required columns present in correct order.
    3. Exactly expected_cases distinct case IDs present.
    4. Every record has Data_Type == 'SIMULATED'.
    5. Every case has multiple activities (>= 2).
    6. Timestamps are valid ISO format and strictly chronological within each case.
    7. No unexpected missing/null values.
    8. No duplicate event records per case.
    9. Read back successfully using Python standard library csv module.

    Args:
        csv_path: Path to the CSV file to validate.
        expected_cases: Number of expected unique cases.

    Returns:
        Dictionary containing check results, counts, and validation status.
    """
    csv_path = Path(csv_path).resolve()
    results: Dict[str, Any] = {
        "file_exists": csv_path.is_file(),
        "file_size_bytes": 0,
        "total_records": 0,
        "unique_cases": 0,
        "header_valid": False,
        "all_simulated": True,
        "all_cases_multiple_activities": True,
        "chronological_order_valid": True,
        "no_missing_values": True,
        "no_duplicates": True,
        "can_read_back": False,
        "activity_distribution": {},
        "department_distribution": {},
        "issues": [],
    }

    if not results["file_exists"]:
        results["issues"].append(f"File not found: {csv_path}")
        return results

    results["file_size_bytes"] = csv_path.stat().st_size
    if results["file_size_bytes"] == 0:
        results["issues"].append("CSV file is empty (0 bytes)")
        return results

    records_by_case: Dict[str, List[Dict[str, str]]] = {}
    activity_counts: Dict[str, int] = {}
    dept_counts: Dict[str, int] = {}
    seen_events: set[Tuple[str, str, str]] = set()

    try:
        with open(csv_path, mode="r", newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader, None)

            if header != CSV_COLUMNS:
                results["issues"].append(
                    f"Header mismatch. Expected {CSV_COLUMNS}, got {header}"
                )
            else:
                results["header_valid"] = True

        with open(csv_path, mode="r", newline="", encoding="utf-8") as f:
            dict_reader = csv.DictReader(f)
            row_count = 0

            for row_num, row in enumerate(dict_reader, start=2):
                row_count += 1

                # Missing value check
                for col in CSV_COLUMNS:
                    val = row.get(col)
                    if val is None or val.strip() == "":
                        results["no_missing_values"] = False
                        results["issues"].append(
                            f"Missing/empty value in column '{col}' at row {row_num}"
                        )

                case_id = row.get("Case_ID", "")
                activity = row.get("Activity_Name", "")
                ts_str = row.get("Timestamp", "")
                dept = row.get("Department", "")
                data_type = row.get("Data_Type", "")

                # Data_Type check
                if data_type != DATA_TYPE_VALUE:
                    results["all_simulated"] = False
                    results["issues"].append(
                        f"Record at row {row_num} has Data_Type='{data_type}', expected '{DATA_TYPE_VALUE}'"
                    )

                # Track activities and departments
                activity_counts[activity] = activity_counts.get(activity, 0) + 1
                dept_counts[dept] = dept_counts.get(dept, 0) + 1

                # Duplicate record check within case
                event_key = (case_id, activity, ts_str)
                if event_key in seen_events:
                    results["no_duplicates"] = False
                    results["issues"].append(
                        f"Duplicate event detected: {event_key} at row {row_num}"
                    )
                seen_events.add(event_key)

                records_by_case.setdefault(case_id, []).append(row)

            results["total_records"] = row_count
            results["unique_cases"] = len(records_by_case)
            results["activity_distribution"] = activity_counts
            results["department_distribution"] = dept_counts
            results["can_read_back"] = True

    except Exception as e:
        results["issues"].append(f"Failed to read CSV: {e}")
        return results

    # Case count check
    if results["unique_cases"] != expected_cases:
        results["issues"].append(
            f"Expected {expected_cases} distinct cases, found {results['unique_cases']}"
        )

    # Per-case validation (multiple activities & chronological ordering)
    for case_id, case_rows in records_by_case.items():
        if len(case_rows) < 2:
            results["all_cases_multiple_activities"] = False
            results["issues"].append(
                f"Case '{case_id}' has only {len(case_rows)} activity (requires multiple)"
            )

        # Chronological timestamps check
        prev_ts = None
        for r in case_rows:
            try:
                curr_ts = datetime.strptime(r["Timestamp"], "%Y-%m-%d %H:%M:%S")
            except ValueError as ve:
                results["chronological_order_valid"] = False
                results["issues"].append(
                    f"Invalid timestamp format in case '{case_id}': {r['Timestamp']} ({ve})"
                )
                continue

            if prev_ts is not None and curr_ts <= prev_ts:
                results["chronological_order_valid"] = False
                results["issues"].append(
                    f"Timestamp out of order or duplicate in case '{case_id}': "
                    f"prev={prev_ts}, curr={curr_ts}"
                )
            prev_ts = curr_ts

    results["is_valid"] = (
        results["file_exists"]
        and results["header_valid"]
        and results["unique_cases"] == expected_cases
        and results["all_simulated"]
        and results["all_cases_multiple_activities"]
        and results["chronological_order_valid"]
        and results["no_missing_values"]
        and results["no_duplicates"]
        and results["can_read_back"]
        and len(results["issues"]) == 0
    )

    return results


def check_reproducibility(
    output_path: Path,
    num_cases: int = 500,
    seed: int = 42,
) -> bool:
    """Verify that re-running generation with the same seed produces the identical dataset.

    Args:
        output_path: Path to the existing CSV file.
        num_cases: Target case count.
        seed: Random seed.

    Returns:
        True if the re-generated dataset exactly matches the saved file.
    """
    new_events = generate_event_log(num_cases=num_cases, seed=seed)

    with open(output_path, mode="r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        saved_rows = list(reader)

    if len(saved_rows) != len(new_events):
        return False

    for row_saved, row_new in zip(saved_rows, new_events):
        if row_saved != row_new:
            return False

    return True


def main() -> int:
    """CLI entrypoint for dataset generation and validation."""
    parser = argparse.ArgumentParser(
        description="CareFlow Simulated Hospital Dataset Generator"
    )
    parser.add_argument(
        "--cases",
        type=int,
        default=500,
        help="Number of patient journeys (default: 500)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(DEFAULT_OUTPUT_PATH),
        help=f"Target output CSV path (default: {DEFAULT_OUTPUT_PATH})",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        default=True,
        help="Perform validation checks after generation (default: True)",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        default=False,
        help="Suppress detailed console output",
    )

    args = parser.parse_args()
    target_path = Path(args.output)

    if not args.quiet:
        print("=" * 70)
        print("CareFlow: Simulated Hospital Event Log Generator")
        print("=" * 70)
        print(f"Target Cases : {args.cases}")
        print(f"Random Seed  : {args.seed}")
        print(f"Output File  : {target_path}")
        print(f"Data_Type    : {DATA_TYPE_VALUE}")
        print("-" * 70)

    # Generate events
    events = generate_event_log(num_cases=args.cases, seed=args.seed)
    save_event_log_to_csv(events, target_path)

    if not args.quiet:
        print(f"[SUCCESS] Wrote {len(events)} events across {args.cases} cases to {target_path}")

    # Validation
    if args.validate:
        val_results = validate_event_log(target_path, expected_cases=args.cases)
        reproducible = check_reproducibility(target_path, num_cases=args.cases, seed=args.seed)

        if not args.quiet:
            print("\nValidation Summary:")
            print(f"  - File Exists                 : {val_results['file_exists']}")
            print(f"  - File Size                   : {val_results['file_size_bytes']:,} bytes")
            print(f"  - Total Event Records         : {val_results['total_records']}")
            print(f"  - Unique Case IDs             : {val_results['unique_cases']}")
            print(f"  - Header Match                : {val_results['header_valid']}")
            print(f"  - All Marked SIMULATED        : {val_results['all_simulated']}")
            print(f"  - Multi-Activity Cases        : {val_results['all_cases_multiple_activities']}")
            print(f"  - Chronological Order Valid   : {val_results['chronological_order_valid']}")
            print(f"  - No Missing Values           : {val_results['no_missing_values']}")
            print(f"  - No Duplicate Records        : {val_results['no_duplicates']}")
            print(f"  - Reproducibility (Seed={args.seed}): {reproducible}")
            print(f"  - Overall Validation Status   : {'PASSED' if val_results['is_valid'] and reproducible else 'FAILED'}")

            print("\nActivity Breakdown:")
            for act, cnt in sorted(val_results["activity_distribution"].items()):
                print(f"  - {act:<15}: {cnt:>5} events")

            print("\nDepartment Breakdown:")
            for dep, cnt in sorted(val_results["department_distribution"].items()):
                print(f"  - {dep:<15}: {cnt:>5} events")

            if val_results["issues"]:
                print("\nValidation Issues Detected:")
                for issue in val_results["issues"]:
                    print(f"  ! {issue}")

        if not (val_results["is_valid"] and reproducible):
            return 1

    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())

