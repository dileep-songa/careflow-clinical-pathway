"""CareFlow BigQuery Raw Event Log Ingestion Module.

Step 3: BigQuery raw ingestion layer with offline validation.

This module provides:
1. Pure offline schema validation for raw simulated hospital event logs
   (runs without Google Cloud credentials or network access).
2. Schema contract definitions matching the simulated dataset generator
   (Case_ID, Activity_Name, Timestamp, Department, Resource, Data_Type).
3. Secure, documented Google Cloud BigQuery load-job execution for live mode.
4. Safe failure defaults (WRITE_EMPTY by default, no silent data overwrite).
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass, field
from datetime import datetime
import os
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional, Tuple

# Try loading .env if python-dotenv is available
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

# Resolve project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_RAW_CSV_PATH = PROJECT_ROOT / "data" / "raw" / "hospital_events_simulated.csv"
DEFAULT_DDL_PATH = PROJECT_ROOT / "sql" / "schema_hospital_events_raw.sql"

# Expected CSV input contract columns (matching src/data_generator.py)
EXPECTED_COLUMNS: List[str] = [
    "Case_ID",
    "Activity_Name",
    "Timestamp",
    "Department",
    "Resource",
    "Data_Type",
]

# BigQuery Schema Field Definitions
SCHEMA_FIELD_SPECS: List[Dict[str, str]] = [
    {
        "name": "Case_ID",
        "type": "STRING",
        "mode": "REQUIRED",
        "description": "Unique patient encounter identifier (e.g. CASE_0001)",
    },
    {
        "name": "Activity_Name",
        "type": "STRING",
        "mode": "REQUIRED",
        "description": "Clinical activity name in the patient pathway",
    },
    {
        "name": "Timestamp",
        "type": "TIMESTAMP",
        "mode": "REQUIRED",
        "description": "Exact timestamp of event occurrence (UTC)",
    },
    {
        "name": "Department",
        "type": "STRING",
        "mode": "REQUIRED",
        "description": "Hospital department or clinical service unit",
    },
    {
        "name": "Resource",
        "type": "STRING",
        "mode": "REQUIRED",
        "description": "De-identified clinician or administrative staff identifier",
    },
    {
        "name": "Data_Type",
        "type": "STRING",
        "mode": "REQUIRED",
        "description": "Data provenance indicator (SIMULATED or PROD)",
    },
]

VALID_WRITE_DISPOSITIONS = ("WRITE_EMPTY", "WRITE_APPEND", "WRITE_TRUNCATE")


@dataclass
class ValidationResult:
    """Detailed summary of raw CSV schema validation."""

    is_valid: bool
    total_rows: int = 0
    unique_cases: int = 0
    earliest_timestamp: Optional[str] = None
    latest_timestamp: Optional[str] = None
    activity_distribution: Dict[str, int] = field(default_factory=dict)
    department_distribution: Dict[str, int] = field(default_factory=dict)
    issues: List[str] = field(default_factory=list)

    def summary(self) -> str:
        """Format a human-readable validation summary."""
        lines = [
            f"Validation Status      : {'PASSED' if self.is_valid else 'FAILED'}",
            f"Total Event Records    : {self.total_rows:,}",
            f"Unique Case IDs        : {self.unique_cases:,}",
            f"Earliest Timestamp     : {self.earliest_timestamp or 'N/A'}",
            f"Latest Timestamp       : {self.latest_timestamp or 'N/A'}",
            f"Unique Activities ({len(self.activity_distribution)}): "
            + ", ".join(f"{k} ({v})" for k, v in sorted(self.activity_distribution.items())),
            f"Unique Departments ({len(self.department_distribution)}): "
            + ", ".join(f"{k} ({v})" for k, v in sorted(self.department_distribution.items())),
        ]
        if self.issues:
            lines.append(f"Issues Detected ({len(self.issues)}):")
            for issue in self.issues[:10]:
                lines.append(f"  - {issue}")
            if len(self.issues) > 10:
                lines.append(f"  ... and {len(self.issues) - 10} more issues")
        return "\n".join(lines)


@dataclass
class BigQueryConfig:
    """Configuration for BigQuery dataset and table targets."""

    project_id: str
    dataset_id: str = "careflow_raw"
    table_id: str = "hospital_events_raw"
    write_disposition: str = "WRITE_EMPTY"

    @property
    def table_ref(self) -> str:
        """Fully-qualified BigQuery table reference."""
        return f"{self.project_id}.{self.dataset_id}.{self.table_id}"

    def validate(self) -> None:
        """Validate configuration values without exposing sensitive data."""
        if not self.project_id or self.project_id.strip() == "":
            raise ValueError(
                "Missing Google Cloud project_id. Set GCP_PROJECT_ID environment variable "
                "or pass --project argument."
            )
        if self.project_id.strip() in ("your-gcp-project-id", "YOUR_PROJECT_ID", "placeholder"):
            raise ValueError(
                f"Invalid project_id '{self.project_id}'. Please configure a real GCP project ID."
            )
        if not self.dataset_id or self.dataset_id.strip() == "":
            raise ValueError("BigQuery dataset_id cannot be empty.")
        if not self.table_id or self.table_id.strip() == "":
            raise ValueError("BigQuery table_id cannot be empty.")
        if self.write_disposition not in VALID_WRITE_DISPOSITIONS:
            raise ValueError(
                f"Invalid write_disposition '{self.write_disposition}'. "
                f"Must be one of: {', '.join(VALID_WRITE_DISPOSITIONS)}"
            )

    @classmethod
    def from_env_or_args(
        cls,
        project_id: Optional[str] = None,
        dataset_id: Optional[str] = None,
        table_id: Optional[str] = None,
        write_disposition: Optional[str] = None,
    ) -> "BigQueryConfig":
        """Resolve BigQuery configuration from explicit arguments or environment variables."""
        resolved_project = (
            project_id
            or os.getenv("GCP_PROJECT_ID")
            or os.getenv("GOOGLE_CLOUD_PROJECT")
            or ""
        )
        resolved_dataset = dataset_id or os.getenv("BIGQUERY_DATASET") or "careflow_raw"
        resolved_table = table_id or os.getenv("BIGQUERY_TABLE_RAW") or "hospital_events_raw"
        resolved_disposition = (
            write_disposition or os.getenv("BIGQUERY_WRITE_DISPOSITION") or "WRITE_EMPTY"
        )

        config = cls(
            project_id=resolved_project,
            dataset_id=resolved_dataset,
            table_id=resolved_table,
            write_disposition=resolved_disposition,
        )
        config.validate()
        return config


def validate_csv_for_bigquery(
    csv_path: Path | str,
    max_issues: int = 100,
) -> ValidationResult:
    """Validate a CSV file against the BigQuery schema contract offline.

    Runs entirely locally using the Python standard library without credentials
    or network connectivity. Does NOT modify the target CSV file.

    Validation checks:
    1. File existence and non-zero byte size.
    2. Header matches expected schema contract columns exactly.
    3. Required columns contain no null, empty, or whitespace-only values.
    4. Data_Type column is tagged 'SIMULATED'.
    5. Timestamps parse as ISO datetime (%Y-%m-%d %H:%M:%S).
    6. No duplicate event keys within the input file. The project intentionally
       treats (Case_ID, Activity_Name, Timestamp) as the event uniqueness key.
       Scope and limitations:
       - File-local scope: This validator inspects duplicate keys strictly within
         the local input CSV file. It does not detect whether the same batch was
         previously loaded into BigQuery (managed via write disposition or warehouse ELT).
       - Event key limitation: Legitimate clinical loops (e.g., repeated Triage or
         follow-up Consultation) possess distinct timestamps and pass cleanly.
         However, if two legitimate separate clinical events occur at the exact same
         second with the same activity name, this contract rejects them as duplicate keys.

    Args:
        csv_path: Path to the CSV file to inspect.
        max_issues: Maximum number of specific record-level issues to collect.

    Returns:
        ValidationResult detailing status, counts, timestamp span, and issues.
    """
    path = Path(csv_path).resolve()
    result = ValidationResult(is_valid=False)

    if not path.is_file():
        result.issues.append(f"CSV file does not exist: {path}")
        return result

    if path.stat().st_size == 0:
        result.issues.append(f"CSV file is empty (0 bytes): {path}")
        return result

    unique_cases: set[str] = set()
    activities: Dict[str, int] = {}
    departments: Dict[str, int] = {}
    seen_event_keys: set[Tuple[str, str, str]] = set()
    earliest_dt: Optional[datetime] = None
    latest_dt: Optional[datetime] = None
    row_count = 0

    try:
        with open(path, mode="r", newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader, None)

            if header is None:
                result.issues.append("CSV file contains no header row.")
                return result

            if header != EXPECTED_COLUMNS:
                result.issues.append(
                    f"Header mismatch. Expected {EXPECTED_COLUMNS}, got {header}"
                )
                return result

        with open(path, mode="r", newline="", encoding="utf-8") as f:
            dict_reader = csv.DictReader(f)

            for row_idx, row in enumerate(dict_reader, start=2):
                row_count += 1

                # Check required columns for missing or blank entries
                for col in EXPECTED_COLUMNS:
                    val = row.get(col)
                    if val is None or val.strip() == "":
                        if len(result.issues) < max_issues:
                            result.issues.append(
                                f"Row {row_idx}: Column '{col}' is missing or blank."
                            )

                case_id = (row.get("Case_ID") or "").strip()
                activity = (row.get("Activity_Name") or "").strip()
                timestamp_str = (row.get("Timestamp") or "").strip()
                dept = (row.get("Department") or "").strip()
                data_type = (row.get("Data_Type") or "").strip()

                if case_id:
                    unique_cases.add(case_id)

                if activity:
                    activities[activity] = activities.get(activity, 0) + 1

                if dept:
                    departments[dept] = departments.get(dept, 0) + 1

                if data_type != "SIMULATED":
                    if len(result.issues) < max_issues:
                        result.issues.append(
                            f"Row {row_idx}: Data_Type is '{data_type}', expected 'SIMULATED'."
                        )

                # Validate Timestamp parseable as ISO datetime
                if timestamp_str:
                    try:
                        dt = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                        if earliest_dt is None or dt < earliest_dt:
                            earliest_dt = dt
                        if latest_dt is None or dt > latest_dt:
                            latest_dt = dt
                    except ValueError as ve:
                        if len(result.issues) < max_issues:
                            result.issues.append(
                                f"Row {row_idx}: Invalid timestamp '{timestamp_str}' ({ve})."
                            )

                # Check duplicate event keys (Case_ID, Activity_Name, Timestamp) within this file.
                # The project intentionally defines (Case_ID, Activity_Name, Timestamp) as the event uniqueness key.
                # Scope: This validator inspects duplicates within this file; warehouse-level duplicates are handled
                # downstream by write dispositions or dbt staging deduplication.
                # Limitation: Legitimate loops with distinct timestamps pass; separate events sharing all three values
                # within the exact same second would be rejected as duplicate keys.
                if case_id and activity and timestamp_str:
                    event_key = (case_id, activity, timestamp_str)
                    if event_key in seen_event_keys:
                        if len(result.issues) < max_issues:
                            result.issues.append(
                                f"Row {row_idx}: Duplicate event key detected for Case_ID '{case_id}', "
                                f"Activity '{activity}', Timestamp '{timestamp_str}'."
                            )
                    else:
                        seen_event_keys.add(event_key)

    except Exception as exc:
        result.issues.append(f"Failed to read CSV file: {exc}")
        return result

    result.total_rows = row_count
    result.unique_cases = len(unique_cases)
    result.earliest_timestamp = (
        earliest_dt.strftime("%Y-%m-%d %H:%M:%S") if earliest_dt else None
    )
    result.latest_timestamp = (
        latest_dt.strftime("%Y-%m-%d %H:%M:%S") if latest_dt else None
    )
    result.activity_distribution = activities
    result.department_distribution = departments

    result.is_valid = (
        row_count > 0
        and len(unique_cases) > 0
        and len(result.issues) == 0
    )

    return result


def get_bigquery_schema() -> List[Any]:
    """Build BigQuery SchemaField instances for table creation or load jobs.

    Lazily imports google.cloud.bigquery so offline callers do not require
    the google-cloud-bigquery library to be installed.

    Returns:
        List of google.cloud.bigquery.SchemaField objects.

    Raises:
        ImportError: If google-cloud-bigquery is not installed.
    """
    try:
        from google.cloud import bigquery
    except ImportError as err:
        raise ImportError(
            "google-cloud-bigquery is required for BigQuery operations. "
            "Install it with 'pip install google-cloud-bigquery' or run in offline mode."
        ) from err

    return [
        bigquery.SchemaField(
            name=spec["name"],
            field_type=spec["type"],
            mode=spec["mode"],
            description=spec["description"],
        )
        for spec in SCHEMA_FIELD_SPECS
    ]


def load_to_bigquery(
    csv_path: Path | str,
    config: BigQueryConfig,
    client: Optional[Any] = None,
) -> Dict[str, Any]:
    """Execute BigQuery raw ingestion using the official Python client.

    Safely performs local offline validation first. If validation fails,
    aborts before making any API calls to prevent invalid data or cloud costs.

    Args:
        csv_path: Path to raw CSV file.
        config: BigQuery target configuration.
        client: Optional pre-configured BigQuery Client (useful for dependency injection/testing).

    Returns:
        Summary dict containing load job ID, destination table, rows loaded, and status.

    Raises:
        ValueError: If CSV validation fails or configuration is invalid.
        ImportError: If google-cloud-bigquery is not installed.
        RuntimeError: If BigQuery load job fails.
    """
    path = Path(csv_path).resolve()

    # Step 1: Pre-load local validation check
    val_result = validate_csv_for_bigquery(path)
    if not val_result.is_valid:
        error_msg = f"Cannot load to BigQuery. CSV failed validation ({len(val_result.issues)} issues): " + "; ".join(
            val_result.issues[:5]
        )
        raise ValueError(error_msg)

    # Step 2: Validate target configuration
    config.validate()

    # Step 3: Lazy import BigQuery client library
    try:
        from google.cloud import bigquery
    except ImportError as err:
        raise ImportError(
            "google-cloud-bigquery is required for live BigQuery ingestion. "
            "Install it via 'pip install google-cloud-bigquery' or use offline validation."
        ) from err

    # Step 4: Initialize client if not injected
    if client is None:
        try:
            client = bigquery.Client(project=config.project_id)
        except Exception as exc:
            # Mask any internal detail that could contain credentials
            raise RuntimeError(
                "Failed to authenticate with Google Cloud BigQuery. Ensure Application Default "
                "Credentials (ADC) are configured via 'gcloud auth application-default login' "
                f"or set GOOGLE_APPLICATION_CREDENTIALS. (Error: {type(exc).__name__})"
            ) from exc

    # Step 5: Configure load job with safe, explicit parameters
    schema = get_bigquery_schema()
    job_config = bigquery.LoadJobConfig(
        schema=schema,
        source_format=bigquery.SourceFormat.CSV,
        skip_leading_rows=1,
        autodetect=False,
        write_disposition=getattr(bigquery.WriteDisposition, config.write_disposition),
        create_disposition=bigquery.CreateDisposition.CREATE_IF_NEEDED,
    )

    table_ref = config.table_ref

    # Step 6: Execute load job
    with open(path, mode="rb") as source_file:
        load_job = client.load_table_from_file(
            source_file,
            table_ref,
            job_config=job_config,
        )

    # Wait for job completion
    load_job.result()

    output_rows = getattr(load_job, "output_rows", val_result.total_rows)

    return {
        "status": "SUCCESS",
        "job_id": getattr(load_job, "job_id", "N/A"),
        "destination_table": table_ref,
        "write_disposition": config.write_disposition,
        "rows_validated": val_result.total_rows,
        "rows_loaded": output_rows,
        "unique_cases": val_result.unique_cases,
    }


def main(argv: Optional[List[str]] = None) -> int:
    """CLI entrypoint for CareFlow BigQuery loader and validator."""
    parser = argparse.ArgumentParser(
        description="CareFlow: BigQuery Raw Hospital Event Log Ingestion & Offline Validator"
    )
    parser.add_argument(
        "--mode",
        choices=["offline", "live"],
        default="offline",
        help="Validation/ingestion mode: 'offline' (local validation, no cloud/credentials needed) "
        "or 'live' (loads data into BigQuery). Default: 'offline'.",
    )
    parser.add_argument(
        "--csv",
        type=str,
        default=str(DEFAULT_RAW_CSV_PATH),
        help=f"Path to the raw CSV file to process. Default: {DEFAULT_RAW_CSV_PATH}",
    )
    parser.add_argument(
        "--project",
        type=str,
        default=None,
        help="Google Cloud project ID (or set GCP_PROJECT_ID environment variable).",
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default=None,
        help="BigQuery dataset name (or set BIGQUERY_DATASET environment variable, default: careflow_raw).",
    )
    parser.add_argument(
        "--table",
        type=str,
        default=None,
        help="BigQuery table name (or set BIGQUERY_TABLE_RAW environment variable, default: hospital_events_raw).",
    )
    parser.add_argument(
        "--write-disposition",
        choices=["WRITE_EMPTY", "WRITE_APPEND", "WRITE_TRUNCATE"],
        default=None,
        help="Write disposition for BigQuery load job. Default: WRITE_EMPTY (safe, refuses overwrite).",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        default=False,
        help="Suppress detailed console output.",
    )

    args = parser.parse_args(argv)
    csv_file = Path(args.csv)

    if not args.quiet:
        print("=" * 72)
        print("CareFlow: BigQuery Ingestion Foundation")
        print("=" * 72)
        print(f"Target CSV  : {csv_file}")
        print(f"Mode        : {args.mode.upper()}")
        print("-" * 72)

    # Offline Mode
    if args.mode == "offline":
        val_result = validate_csv_for_bigquery(csv_file)
        if not args.quiet:
            print(val_result.summary())
            print("-" * 72)
            if val_result.is_valid:
                print("[SUCCESS] Offline validation passed. Schema contract is 100% BigQuery compatible.")
            else:
                print("[FAILED] Offline validation detected schema or data issues.")
        return 0 if val_result.is_valid else 1

    # Live Ingestion Mode
    try:
        config = BigQueryConfig.from_env_or_args(
            project_id=args.project,
            dataset_id=args.dataset,
            table_id=args.table,
            write_disposition=args.write_disposition,
        )
    except ValueError as val_err:
        print(f"[CONFIGURATION ERROR] {val_err}", file=sys.stderr)
        return 1

    if not args.quiet:
        print(f"Target Table      : {config.table_ref}")
        print(f"Write Disposition : {config.write_disposition}")
        print("-" * 72)

    try:
        summary = load_to_bigquery(csv_file, config=config)
        if not args.quiet:
            print("[SUCCESS] Live BigQuery Load Completed:")
            print(f"  - Job ID            : {summary['job_id']}")
            print(f"  - Destination Table : {summary['destination_table']}")
            print(f"  - Rows Loaded       : {summary['rows_loaded']:,}")
            print(f"  - Unique Cases      : {summary['unique_cases']:,}")
        return 0
    except (ValueError, ImportError, RuntimeError) as err:
        print(f"[EXECUTION ERROR] {err}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

