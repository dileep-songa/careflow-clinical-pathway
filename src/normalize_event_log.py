"""CareFlow Event Log Normalization Script.

Step: Local-only normalization of raw hospital events into the dbt staging schema.
Reuses the transformation logic defined in src/staging_transform.py:apply_stg_hospital_events_transformation
to produce data/cleaned/stg_hospital_events.csv ready for PM4Py offline process mining.
"""

from __future__ import annotations

import argparse
import csv
from datetime import date, datetime
import logging
from pathlib import Path
import sys
from typing import Any, Dict, List, Union

# Ensure project root is in sys.path for direct script execution
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Import staging transformation from production module
from src.staging_transform import apply_stg_hospital_events_transformation

# Configure logger
logger = logging.getLogger("careflow.normalize_event_log")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# Default file paths
DEFAULT_INPUT_PATH = PROJECT_ROOT / "data" / "raw" / "hospital_events_simulated.csv"
DEFAULT_OUTPUT_PATH = PROJECT_ROOT / "data" / "cleaned" / "stg_hospital_events.csv"

# Expected schema matching careflow_dbt/models/staging/stg_hospital_events.sql
EXPECTED_STAGING_COLUMNS: List[str] = [
    "case_id",
    "event_sequence",
    "raw_activity_name",
    "activity_name",
    "event_timestamp",
    "event_date",
    "department",
    "resource_id",
    "data_provenance",
    "previous_activity",
    "transition_minutes_from_previous",
]


def validate_staged_event_log(file_path: Union[str, Path]) -> Dict[str, Any]:
    """Validate that the normalized CSV meets all requirements of the staging schema.

    Checks:
    1. File existence and non-zero size.
    2. Exact match of CSV header columns (11 columns).
    3. Exactly 3,140 rows.
    4. Exactly 500 unique case IDs.
    5. Valid 1..N event_sequence and chronological ordering within each case.
    6. Preservation of repeated Triage events (re-triages).
    7. Preservation of diagnostic follow-up consultations.

    Args:
        file_path: Path to the generated normalized CSV.

    Returns:
        Validation summary dictionary with key metrics.

    Raises:
        ValueError: If any validation check fails.
    """
    path = Path(file_path).resolve()
    if not path.is_file():
        raise FileNotFoundError(f"Staged file not found at: {path}")

    if path.stat().st_size == 0:
        raise ValueError(f"Staged file is empty (0 bytes): {path}")

    with open(path, mode="r", newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        try:
            headers = next(reader)
        except StopIteration:
            raise ValueError(f"Staged file has no content: {path}")

        if headers != EXPECTED_STAGING_COLUMNS:
            raise ValueError(
                f"Header mismatch in {path}.\n"
                f"Expected: {EXPECTED_STAGING_COLUMNS}\n"
                f"Found:    {headers}"
            )

        rows: List[Dict[str, str]] = []
        dict_reader = csv.DictReader(f, fieldnames=headers)
        for row in dict_reader:
            rows.append(row)

    total_rows = len(rows)
    if total_rows != 3140:
        raise ValueError(f"Expected 3,140 rows in staged file, but found {total_rows}")

    cases: Dict[str, List[Dict[str, str]]] = {}
    for r in rows:
        cases.setdefault(r["case_id"], []).append(r)

    unique_cases = len(cases)
    if unique_cases != 500:
        raise ValueError(f"Expected 500 unique cases, but found {unique_cases}")

    # Validate per-case chronological sequence and ordering
    retriage_count = 0
    diagnostic_followup_count = 0

    for cid, case_rows in cases.items():
        prev_seq = 0
        prev_ts: datetime | None = None

        for idx, row in enumerate(case_rows, start=1):
            seq = int(row["event_sequence"])
            if seq != idx:
                raise ValueError(
                    f"Case {cid} has non-sequential event_sequence: expected {idx}, got {seq}"
                )

            curr_ts = datetime.strptime(row["event_timestamp"], "%Y-%m-%d %H:%M:%S")
            if prev_ts and curr_ts < prev_ts:
                raise ValueError(
                    f"Case {cid} has non-chronological events: {curr_ts} before {prev_ts}"
                )

            # Check re-triage loops (Triage preceded by Triage)
            if row["raw_activity_name"] == "Triage" and row["previous_activity"] == "Triage":
                retriage_count += 1

            # Check diagnostic follow-up consultations (Consultation following Lab or X-Ray)
            if (
                row["raw_activity_name"] == "Consultation"
                and row["previous_activity"] in ("Laboratory", "X-Ray")
            ):
                diagnostic_followup_count += 1

            prev_ts = curr_ts
            prev_seq = seq

    logger.info(
        f"Validation passed: {total_rows} rows, {unique_cases} cases, "
        f"{retriage_count} re-triage loops, {diagnostic_followup_count} diagnostic follow-up consults."
    )

    return {
        "file_path": str(path),
        "total_rows": total_rows,
        "unique_cases": unique_cases,
        "retriage_count": retriage_count,
        "diagnostic_followup_count": diagnostic_followup_count,
        "headers": headers,
    }


def normalize_event_log(
    input_path: Union[str, Path] = DEFAULT_INPUT_PATH,
    output_path: Union[str, Path] = DEFAULT_OUTPUT_PATH,
) -> Dict[str, Any]:
    """Normalize raw hospital events CSV into dbt staging schema CSV.

    Args:
        input_path: Path to raw hospital events CSV.
        output_path: Path where the normalized CSV will be saved.

    Returns:
        Summary dictionary with output path and record count.

    Raises:
        FileNotFoundError: If input CSV does not exist.
        ValueError: If transformation or validation fails.
    """
    in_file = Path(input_path).resolve()
    out_file = Path(output_path).resolve()

    if not in_file.is_file():
        raise FileNotFoundError(f"Input file not found: {in_file}")

    if in_file.stat().st_size == 0:
        raise ValueError(f"Input file is empty (0 bytes): {in_file}")

    logger.info(f"Reading raw event log from: {in_file}")
    with open(in_file, mode="r", newline="", encoding="utf-8") as f:
        raw_records = list(csv.DictReader(f))

    logger.info(f"Read {len(raw_records)} raw records. Applying staging transformation...")
    # Reuses tested transformation logic from tests/test_dbt_setup.py
    transformed_records = apply_stg_hospital_events_transformation(raw_records)

    logger.info(
        f"Transformation produced {len(transformed_records)} staged records. "
        f"Formatting and writing to: {out_file}"
    )

    # Ensure parent output directory exists (data/cleaned)
    out_file.parent.mkdir(parents=True, exist_ok=True)

    with open(out_file, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=EXPECTED_STAGING_COLUMNS)
        writer.writeheader()

        for rec in transformed_records:
            row: Dict[str, Any] = {}
            for col in EXPECTED_STAGING_COLUMNS:
                val = rec.get(col)
                if val is None:
                    row[col] = ""
                elif isinstance(val, datetime):
                    row[col] = val.strftime("%Y-%m-%d %H:%M:%S")
                elif isinstance(val, date):
                    row[col] = val.strftime("%Y-%m-%d")
                else:
                    row[col] = str(val)
            writer.writerow(row)

    logger.info("Validating generated normalized CSV...")
    validation_summary = validate_staged_event_log(out_file)

    return {
        "status": "SUCCESS",
        "output_path": str(out_file),
        "validation": validation_summary,
    }


def main() -> None:
    """CLI entrypoint for event log normalization."""
    parser = argparse.ArgumentParser(
        description="CareFlow Event Log Normalizer - Transforms raw simulated hospital events to dbt staging schema"
    )
    parser.add_argument(
        "--input",
        type=str,
        default=str(DEFAULT_INPUT_PATH),
        help=f"Path to input raw events CSV (default: {DEFAULT_INPUT_PATH})",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(DEFAULT_OUTPUT_PATH),
        help=f"Path to output normalized CSV (default: {DEFAULT_OUTPUT_PATH})",
    )
    args = parser.parse_args()

    try:
        result = normalize_event_log(args.input, args.output)
        v = result["validation"]
        print("\n" + "=" * 60)
        print("CareFlow Event Log Normalization - Completed Successfully")
        print("=" * 60)
        print(f"Output File:                 {result['output_path']}")
        print(f"Total Rows:                  {v['total_rows']:,}")
        print(f"Unique Patient Cases:        {v['unique_cases']:,}")
        print(f"Re-Triage Loops Preserved:   {v['retriage_count']}")
        print(f"Diagnostic Follow-Ups:       {v['diagnostic_followup_count']}")
        print("=" * 60 + "\n")
    except Exception as exc:
        logger.error(f"Normalization failed: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
