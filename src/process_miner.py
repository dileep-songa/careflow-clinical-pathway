"""CareFlow Clinical Pathway Process Mining Module.

This module provides offline process-mining capabilities using PM4Py:
- Ingestion and schema validation of clinical event logs.
- Deterministic temporal sorting and conversion to PM4Py event logs.
- Computation of event log statistics: case counts, activity frequencies,
  observed case durations, and pathway variants.
- Directly-Follows Graph (DFG) discovery: transition frequencies and
  observed transition durations between consecutive activities.

Note on Terminology:
Observed transition time represents the elapsed duration between recorded timestamps
of consecutive events within a patient encounter. It should NOT be assumed to equal
actual patient clinical waiting time, as clinical encounters include active care,
patient transport, and administrative processing alongside queuing.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from datetime import datetime
import json
import logging
import os
from pathlib import Path
import shutil
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
import pm4py

# Configure logger
logger = logging.getLogger("careflow.process_miner")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# Canonical 6-column contract (Raw schema)
RAW_REQUIRED_COLUMNS: List[str] = [
    "Case_ID",
    "Activity_Name",
    "Timestamp",
    "Department",
    "Resource",
    "Data_Type",
]

# Backward compatibility alias
REQUIRED_COLUMNS: List[str] = RAW_REQUIRED_COLUMNS

# Normalized schema required base columns (dbt staging output)
NORMALIZED_REQUIRED_BASE_COLUMNS: List[str] = [
    "case_id",
    "event_timestamp",
    "department",
    "resource_id",
    "data_provenance",
]

# Mapping from normalized staging columns to CareFlow canonical schema
NORMALIZED_COLUMN_MAPPING: Dict[str, str] = {
    "case_id": "Case_ID",
    "event_timestamp": "Timestamp",
    "department": "Department",
    "resource_id": "Resource",
    "data_provenance": "Data_Type",
}


@dataclass(frozen=True)
class EventLogSummary:
    """Summary metrics of an analyzed clinical event log."""

    total_events: int
    total_cases: int
    distinct_activities: int
    start_activities: Dict[str, int]
    end_activities: Dict[str, int]
    activity_frequencies: Dict[str, int]
    min_duration_minutes: float
    max_duration_minutes: float
    mean_duration_minutes: float
    median_duration_minutes: float
    std_duration_minutes: float
    total_variants: int
    top_variants: List[Dict[str, Any]]


def load_event_log(
    file_path: Union[str, Path],
    schema: str = "raw",
) -> pd.DataFrame:
    """Load and validate a clinical event log CSV file without modifying it.

    Args:
        file_path: Path to the event log CSV.
        schema: Schema format of the input file ('raw' or 'normalized'). Default: 'raw'.

    Returns:
        A validated, cleaned pandas DataFrame with parsed UTC Timestamps,
        sorted chronologically within each patient encounter.

    Raises:
        FileNotFoundError: If the CSV file does not exist.
        ValueError: If the file is empty, missing required columns, contains
            empty/whitespace required values, contains unparseable timestamps,
            or an unsupported schema is specified.
    """
    if schema not in ("raw", "normalized"):
        raise ValueError(
            f"Unsupported schema '{schema}'. Expected 'raw' or 'normalized'."
        )

    path = Path(file_path).resolve()
    if not path.is_file():
        raise FileNotFoundError(f"Event log file not found at: {path}")

    if path.stat().st_size == 0:
        raise ValueError(f"Event log file is empty (0 bytes): {path}")

    # Read CSV strictly as strings to prevent loss of precision or silent type coercions
    try:
        df = pd.read_csv(path, dtype=str)
    except Exception as exc:
        raise ValueError(f"Failed to read CSV at {path}: {exc}") from exc

    if schema == "normalized":
        df = normalize_staging_dataframe(df)
    else:
        validate_event_log_dataframe(df)

    return parse_and_sort_event_log(df)


def load_normalized_event_log(file_path: Union[str, Path]) -> pd.DataFrame:
    """Load and validate a normalized staging event log CSV without modifying it.

    Args:
        file_path: Path to the normalized event log CSV.

    Returns:
        A validated, cleaned pandas DataFrame mapped to the canonical CareFlow schema
        with parsed UTC Timestamps, sorted chronologically within each patient encounter.

    Raises:
        FileNotFoundError: If the CSV file does not exist.
        ValueError: If the file is empty, missing required columns, contains
            empty/whitespace required values, or contains unparseable timestamps.
    """
    return load_event_log(file_path, schema="normalized")


def validate_event_log_dataframe(df: pd.DataFrame) -> None:
    """Validate DataFrame structure against the CareFlow raw schema contract.

    Args:
        df: Raw event log DataFrame.

    Raises:
        ValueError: If columns are missing, DataFrame is empty, or required fields
            contain null or blank values.
    """
    if df.empty:
        raise ValueError("Event log DataFrame contains zero records.")

    # 1. Column existence
    missing_columns = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_columns:
        raise ValueError(
            f"Event log is missing required columns: {missing_columns}. "
            f"Expected schema: {REQUIRED_COLUMNS}"
        )

    # 2. Check for null or blank values across required columns
    empty_report: Dict[str, int] = {}
    for col in REQUIRED_COLUMNS:
        empty_mask = df[col].isna() | (df[col].astype(str).str.strip() == "")
        empty_count = int(empty_mask.sum())
        if empty_count > 0:
            empty_report[col] = empty_count

    if empty_report:
        raise ValueError(
            f"Required columns contain empty or whitespace-only values: {empty_report}"
        )


def validate_normalized_event_log_dataframe(df: pd.DataFrame) -> None:
    """Validate DataFrame structure against the normalized CareFlow staging contract.

    Args:
        df: Normalized staging event log DataFrame.

    Raises:
        ValueError: If base columns are missing, neither activity column is present,
            the DataFrame is empty, or required columns contain null/whitespace values.
    """
    if df.empty:
        raise ValueError("Normalized event log DataFrame contains zero records.")

    # 1. Base column existence
    missing_columns = [
        col for col in NORMALIZED_REQUIRED_BASE_COLUMNS if col not in df.columns
    ]
    has_raw_activity = "raw_activity_name" in df.columns
    has_activity = "activity_name" in df.columns

    if not has_raw_activity and not has_activity:
        missing_columns.append("raw_activity_name' or 'activity_name")

    if missing_columns:
        raise ValueError(
            f"Normalized event log is missing required columns: {missing_columns}. "
            f"Expected base columns: {NORMALIZED_REQUIRED_BASE_COLUMNS} and at least one "
            f"of ['raw_activity_name', 'activity_name']."
        )

    # 2. Check for null or blank values across required columns
    active_act_col = "raw_activity_name" if has_raw_activity else "activity_name"
    cols_to_check = NORMALIZED_REQUIRED_BASE_COLUMNS + [active_act_col]

    empty_report: Dict[str, int] = {}
    for col in cols_to_check:
        empty_mask = df[col].isna() | (df[col].astype(str).str.strip() == "")
        empty_count = int(empty_mask.sum())
        if empty_count > 0:
            empty_report[col] = empty_count

    if empty_report:
        raise ValueError(
            f"Normalized required columns contain empty or whitespace-only values: {empty_report}"
        )


def normalize_staging_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Convert normalized staging DataFrame into the canonical CareFlow schema.

    Maps:
        - case_id -> Case_ID
        - raw_activity_name -> Activity_Name (when available; otherwise activity_name)
        - event_timestamp -> Timestamp
        - department -> Department
        - resource_id -> Resource
        - data_provenance -> Data_Type

    Args:
        df: Raw DataFrame matching the dbt staging schema.

    Returns:
        DataFrame conforming to CareFlow canonical schema (Case_ID, Activity_Name, Timestamp,
        Department, Resource, Data_Type) plus any auxiliary staging columns preserved.

    Raises:
        ValueError: If validation fails.
    """
    validate_normalized_event_log_dataframe(df)

    out_df = df.copy()

    # Map activity name: raw_activity_name preferred, fallback to activity_name
    if "raw_activity_name" in out_df.columns:
        out_df["Activity_Name"] = out_df["raw_activity_name"]
    else:
        out_df["Activity_Name"] = out_df["activity_name"]

    # Map base columns
    for norm_col, canon_col in NORMALIZED_COLUMN_MAPPING.items():
        out_df[canon_col] = out_df[norm_col]

    return out_df


def parse_and_sort_event_log(df: pd.DataFrame) -> pd.DataFrame:
    """Parse timestamps and deterministically order events by case and timestamp.

    Args:
        df: Validated event log DataFrame with string timestamps or datetime values.

    Returns:
        Sorted DataFrame with parsed UTC datetimes.

    Raises:
        ValueError: If any timestamp fails parsing.
    """
    cleaned_df = df.copy()

    # Parse timestamps using strict format with ISO8601 fallback
    if not pd.api.types.is_datetime64_any_dtype(cleaned_df["Timestamp"]):
        try:
            cleaned_df["Timestamp"] = pd.to_datetime(
                cleaned_df["Timestamp"],
                format="%Y-%m-%d %H:%M:%S",
                utc=True,
                errors="raise",
            )
        except Exception:
            try:
                cleaned_df["Timestamp"] = pd.to_datetime(
                    cleaned_df["Timestamp"],
                    format="ISO8601",
                    utc=True,
                    errors="raise",
                )
            except Exception as exc:
                raise ValueError(
                    f"Failed to parse Timestamp column with format '%Y-%m-%d %H:%M:%S': {exc}"
                ) from exc
    else:
        # Standardize existing datetime objects to UTC
        if cleaned_df["Timestamp"].dt.tz is None:
            cleaned_df["Timestamp"] = cleaned_df["Timestamp"].dt.tz_localize("UTC")
        else:
            cleaned_df["Timestamp"] = cleaned_df["Timestamp"].dt.tz_convert("UTC")

    # Deterministic multi-key sort: Case_ID ASC, Timestamp ASC, Activity_Name ASC, Resource ASC
    cleaned_df = cleaned_df.sort_values(
        by=["Case_ID", "Timestamp", "Activity_Name", "Resource"],
        ascending=[True, True, True, True],
    ).reset_index(drop=True)

    return cleaned_df


def convert_to_pm4py_event_log(df: pd.DataFrame) -> pd.DataFrame:
    """Convert CareFlow DataFrame into a standardized PM4Py event log.

    Args:
        df: Validated, sorted event log DataFrame.

    Returns:
        Standardized PM4Py DataFrame with internal keys (case_id, activity_key, timestamp_key).
    """
    event_log = pm4py.format_dataframe(
        df,
        case_id="Case_ID",
        activity_key="Activity_Name",
        timestamp_key="Timestamp",
        timest_format="%Y-%m-%d %H:%M:%S",
    )
    return event_log


def calculate_activity_frequencies(df: pd.DataFrame) -> Dict[str, int]:
    """Calculate frequency count of each clinical activity.

    Args:
        df: Event log DataFrame.

    Returns:
        Dictionary mapping activity name to event count, sorted descending.
    """
    counts = df["Activity_Name"].value_counts().to_dict()
    return {str(k): int(v) for k, v in counts.items()}


def calculate_case_duration_statistics(df: pd.DataFrame) -> Dict[str, float]:
    """Calculate case-duration statistics in observed minutes across all encounters.

    Case duration is defined as the elapsed time between the first and last recorded
    event timestamps in that case encounter.

    Args:
        df: Event log DataFrame with datetime Timestamps.

    Returns:
        Dictionary containing min, max, mean, median, and sample standard deviation in minutes.
    """
    if df.empty:
        return {
            "min_minutes": 0.0,
            "max_minutes": 0.0,
            "mean_minutes": 0.0,
            "median_minutes": 0.0,
            "std_minutes": 0.0,
        }

    grouped = df.groupby("Case_ID")["Timestamp"]
    durations_minutes = grouped.agg(
        lambda ts: (ts.max() - ts.min()).total_seconds() / 60.0
    )

    std_val = float(durations_minutes.std()) if len(durations_minutes) > 1 else 0.0
    # Guard against NaN std when variance is 0 or 1 element
    if pd.isna(std_val):
        std_val = 0.0

    return {
        "min_minutes": round(float(durations_minutes.min()), 2),
        "max_minutes": round(float(durations_minutes.max()), 2),
        "mean_minutes": round(float(durations_minutes.mean()), 2),
        "median_minutes": round(float(durations_minutes.median()), 2),
        "std_minutes": round(std_val, 2),
    }


def extract_pathway_variants(event_log: pd.DataFrame) -> List[Dict[str, Any]]:
    """Extract and rank unique clinical pathway variants from the event log.

    Args:
        event_log: Standardized PM4Py event log.

    Returns:
        List of variant dictionaries containing rank, pathway tuple, formatted string,
        case count, and percentage of the total case cohort.
    """
    variants = pm4py.get_variants_as_tuples(event_log)
    total_cases = sum(variants.values()) if variants else 1

    ranked = sorted(variants.items(), key=lambda item: item[1], reverse=True)
    results = []
    for rank, (pathway, count) in enumerate(ranked, start=1):
        pct = round((count / total_cases) * 100.0, 2)
        results.append(
            {
                "variant_rank": rank,
                "pathway": pathway,
                "pathway_str": " -> ".join(pathway),
                "case_count": int(count),
                "percentage": pct,
            }
        )
    return results


def discover_directly_follows_graph(
    event_log: pd.DataFrame,
) -> Tuple[
    Dict[Tuple[str, str], int],
    Dict[Tuple[str, str], Dict[str, float]],
    Dict[str, int],
    Dict[str, int],
]:
    """Discover Directly-Follows Graph (DFG) frequencies and observed transition durations.

    Args:
        event_log: Standardized PM4Py event log.

    Returns:
        Tuple of:
        - dfg_frequency: mapping of (source, target) -> count
        - dfg_performance: mapping of (source, target) -> performance dict (seconds)
        - start_activities: mapping of activity -> start count
        - end_activities: mapping of activity -> end count
    """
    dfg_frequency, start_activities, end_activities = pm4py.discover_dfg(event_log)
    dfg_performance, _, _ = pm4py.discover_performance_dfg(event_log)
    return dfg_frequency, dfg_performance, start_activities, end_activities


def build_transition_summary_table(
    dfg_frequency: Dict[Tuple[str, str], int],
    dfg_performance: Dict[Tuple[str, str], Dict[str, float]],
) -> pd.DataFrame:
    """Build a structured tabular summary of observed activity transitions.

    Args:
        dfg_frequency: Frequency dictionary of activity transitions.
        dfg_performance: Performance dictionary of transition durations (in seconds).

    Returns:
        DataFrame containing transition counts and observed transition times in minutes.
    """
    rows = []
    for (src, tgt), count in dfg_frequency.items():
        perf = dfg_performance.get((src, tgt), {})
        mean_sec = perf.get("mean", 0.0)
        med_sec = perf.get("median", 0.0)
        min_sec = perf.get("min", 0.0)
        max_sec = perf.get("max", 0.0)

        rows.append(
            {
                "source_activity": src,
                "target_activity": tgt,
                "transition_count": count,
                "mean_observed_transition_minutes": round(mean_sec / 60.0, 2),
                "median_observed_transition_minutes": round(med_sec / 60.0, 2),
                "min_observed_transition_minutes": round(min_sec / 60.0, 2),
                "max_observed_transition_minutes": round(max_sec / 60.0, 2),
            }
        )

    df_table = pd.DataFrame(rows)
    if not df_table.empty:
        df_table = df_table.sort_values(
            by=["transition_count", "source_activity", "target_activity"],
            ascending=[False, True, True],
        ).reset_index(drop=True)
    return df_table


def render_dfg_visualization(
    dfg_frequency: Dict[Tuple[str, str], int],
    start_activities: Dict[str, int],
    end_activities: Dict[str, int],
    output_path: Union[str, Path],
) -> Optional[Path]:
    """Render and save a DFG visualization diagram if Graphviz binary is present.

    Args:
        dfg_frequency: Frequency dictionary of transitions.
        start_activities: Start activity counts.
        end_activities: End activity counts.
        output_path: Target image file path (e.g., .png).

    Returns:
        Path to rendered diagram if successful, or None if Graphviz 'dot' binary is missing.
    """
    dot_binary = shutil.which("dot")
    if not dot_binary:
        logger.warning(
            "Graphviz executable ('dot') is not installed or not in system PATH. "
            "Skipping graphical DFG diagram generation. Transition metrics are preserved in CSV."
        )
        return None

    out_file = Path(output_path).resolve()
    out_file.parent.mkdir(parents=True, exist_ok=True)

    try:
        pm4py.save_vis_dfg(
            dfg_frequency,
            start_activities,
            end_activities,
            str(out_file),
        )
        logger.info(f"DFG diagram rendered successfully at: {out_file}")
        return out_file
    except Exception as exc:
        logger.warning(f"Failed to render DFG visualization: {exc}")
        return None


def compute_event_log_summary(
    df: pd.DataFrame,
    event_log: pd.DataFrame,
) -> EventLogSummary:
    """Compute comprehensive clinical event log statistics.

    Args:
        df: Validated, sorted event log DataFrame.
        event_log: Standardized PM4Py event log.

    Returns:
        EventLogSummary dataclass populated with summary metrics.
    """
    dfg_freq, _, start_acts, end_acts = discover_directly_follows_graph(event_log)
    act_frequencies = calculate_activity_frequencies(df)
    duration_stats = calculate_case_duration_statistics(df)
    variants = extract_pathway_variants(event_log)

    return EventLogSummary(
        total_events=len(df),
        total_cases=int(df["Case_ID"].nunique()),
        distinct_activities=int(df["Activity_Name"].nunique()),
        start_activities={str(k): int(v) for k, v in start_acts.items()},
        end_activities={str(k): int(v) for k, v in end_acts.items()},
        activity_frequencies=act_frequencies,
        min_duration_minutes=duration_stats["min_minutes"],
        max_duration_minutes=duration_stats["max_minutes"],
        mean_duration_minutes=duration_stats["mean_minutes"],
        median_duration_minutes=duration_stats["median_minutes"],
        std_duration_minutes=duration_stats["std_minutes"],
        total_variants=len(variants),
        top_variants=variants[:5],
    )


def _json_serial_default(obj: Any) -> Any:
    """JSON serialization fallback for NumPy scalars and arrays."""
    if isinstance(obj, np.generic):
        return obj.item()
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def run_process_mining_pipeline(
    csv_path: Union[str, Path],
    output_dir: Optional[Union[str, Path]] = None,
    schema: str = "raw",
) -> Dict[str, Any]:
    """Execute end-to-end offline process-mining pipeline on an event log CSV.

    Args:
        csv_path: Path to input event log CSV.
        output_dir: Optional directory to store summary CSVs and diagram.
        schema: Input schema format ('raw' or 'normalized'). Default: 'raw'.

    Returns:
        Dictionary containing summary dataclass, transition summary table,
        and paths to exported files.
    """
    logger.info(
        f"Starting CareFlow offline process mining on: {csv_path} (schema: {schema})"
    )

    # 1. Load and validate
    df = load_event_log(csv_path, schema=schema)
    logger.info(
        f"Loaded and validated {len(df)} events across {df['Case_ID'].nunique()} cases."
    )

    # 2. Convert to PM4Py event log
    event_log = convert_to_pm4py_event_log(df)

    # 3. Discover DFG and performance
    dfg_freq, dfg_perf, start_acts, end_acts = discover_directly_follows_graph(event_log)
    df_transitions = build_transition_summary_table(dfg_freq, dfg_perf)

    # 4. Compute comprehensive summary
    summary = compute_event_log_summary(df, event_log)
    variants = extract_pathway_variants(event_log)

    exported_files: Dict[str, str] = {}

    # 5. Export outputs if directory is specified
    if output_dir:
        out_path = Path(output_dir).resolve()
        out_path.mkdir(parents=True, exist_ok=True)

        # A. Transitions CSV
        trans_file = out_path / "dfg_transitions_summary.csv"
        df_transitions.to_csv(trans_file, index=False)
        exported_files["transitions_csv"] = str(trans_file)

        # B. Pathway Variants CSV
        df_variants = pd.DataFrame(
            [
                {
                    "variant_rank": v["variant_rank"],
                    "case_count": v["case_count"],
                    "percentage": v["percentage"],
                    "pathway": v["pathway_str"],
                }
                for v in variants
            ]
        )
        variants_file = out_path / "pathway_variants_summary.csv"
        df_variants.to_csv(variants_file, index=False)
        exported_files["variants_csv"] = str(variants_file)

        # C. Summary JSON
        summary_dict = asdict(summary)
        summary_dict["top_variants"] = [
            {
                "variant_rank": v["variant_rank"],
                "case_count": v["case_count"],
                "percentage": v["percentage"],
                "pathway": v["pathway_str"],
            }
            for v in summary.top_variants
        ]
        summary_file = out_path / "process_mining_summary.json"
        with open(summary_file, "w", encoding="utf-8") as f:
            json.dump(summary_dict, f, indent=2, default=_json_serial_default)
        exported_files["summary_json"] = str(summary_file)

        # D. Optional DFG diagram
        diag_file = out_path / "dfg_visualization.png"
        rendered = render_dfg_visualization(dfg_freq, start_acts, end_acts, diag_file)
        if rendered:
            exported_files["dfg_png"] = str(rendered)

    logger.info("Process mining pipeline completed successfully.")
    return {
        "summary": summary,
        "transitions_table": df_transitions,
        "variants": variants,
        "exported_files": exported_files,
    }


def main() -> None:
    """CLI interface for running CareFlow process mining."""
    parser = argparse.ArgumentParser(
        description="CareFlow Clinical Pathway Offline Process Miner"
    )
    parser.add_argument(
        "--input",
        type=str,
        default="data/raw/hospital_events_simulated.csv",
        help="Path to input event log CSV",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="outputs",
        help="Directory to save analysis summaries and diagrams (default: 'outputs')",
    )
    parser.add_argument(
        "--schema",
        type=str,
        choices=["raw", "normalized"],
        default="raw",
        help="Schema type of the input event log ('raw' or 'normalized'). Default: 'raw'.",
    )
    args = parser.parse_args()

    results = run_process_mining_pipeline(
        args.input, args.output_dir, schema=args.schema
    )
    summary: EventLogSummary = results["summary"]

    print("\n" + "=" * 60)
    print("CareFlow Clinical Pathway — Process Mining Summary")
    print("=" * 60)
    print(f"Total Events:        {summary.total_events:,}")
    print(f"Total Patient Cases: {summary.total_cases:,}")
    print(f"Distinct Activities: {summary.distinct_activities}")
    print(f"Unique Variants:     {summary.total_variants}")
    print("\nCase Observed Duration (Minutes):")
    print(f"  Min:    {summary.min_duration_minutes:.1f}")
    print(f"  Median: {summary.median_duration_minutes:.1f}")
    print(f"  Mean:   {summary.mean_duration_minutes:.1f}")
    print(f"  Max:    {summary.max_duration_minutes:.1f}")
    print(f"  Std:    {summary.std_duration_minutes:.1f}")

    print("\nTop Pathway Variants:")
    for v in summary.top_variants:
        print(
            f"  Variant #{v['variant_rank']}: {v['case_count']} cases ({v['percentage']}%) -> {v['pathway_str']}"
        )

    print("\nTop 5 Direct Transitions by Frequency:")
    df_trans: pd.DataFrame = results["transitions_table"]
    for _, row in df_trans.head(5).iterrows():
        print(
            f"  {row['source_activity']:15} -> {row['target_activity']:15} | "
            f"Count: {int(row['transition_count']):4} | "
            f"Median Observed: {row['median_observed_transition_minutes']:5.1f} min | "
            f"Mean: {row['mean_observed_transition_minutes']:5.1f} min"
        )
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
