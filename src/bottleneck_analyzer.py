"""CareFlow Bottleneck Analyzer Module.

This module provides reproducible bottleneck analysis based on simulated process-mining
transition summaries. It ingests directly-follows graph (DFG) transition metrics,
validates schema contracts and numeric integrity, and ranks clinical activity transitions
by observed transition duration.

Clinical & Process Mining Terminology:
Observed transition time represents the elapsed duration between recorded timestamps
of consecutive events within a patient encounter. It should NOT be assumed to equal
actual patient clinical waiting time, as clinical encounters include active care,
patient transport, and administrative processing alongside queuing.
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Union

import pandas as pd

# Configure logger
logger = logging.getLogger("careflow.bottleneck_analyzer")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# Repository root and default paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INPUT_PATH = PROJECT_ROOT / "outputs" / "dfg_transitions_summary.csv"
DEFAULT_OUTPUT_PATH = PROJECT_ROOT / "outputs" / "bottleneck_analysis_summary.csv"

# Canonical schema contracts
REQUIRED_INPUT_COLUMNS: List[str] = [
    "source_activity",
    "target_activity",
    "transition_count",
    "mean_observed_transition_minutes",
    "median_observed_transition_minutes",
    "min_observed_transition_minutes",
    "max_observed_transition_minutes",
]

EXPECTED_OUTPUT_COLUMNS: List[str] = [
    "rank",
    "source_activity",
    "target_activity",
    "transition_count",
    "mean_observed_transition_minutes",
    "median_observed_transition_minutes",
    "min_observed_transition_minutes",
    "max_observed_transition_minutes",
]

NUMERIC_COLUMNS: List[str] = [
    "transition_count",
    "mean_observed_transition_minutes",
    "median_observed_transition_minutes",
    "min_observed_transition_minutes",
    "max_observed_transition_minutes",
]

DURATION_COLUMNS: List[str] = [
    "mean_observed_transition_minutes",
    "median_observed_transition_minutes",
    "min_observed_transition_minutes",
    "max_observed_transition_minutes",
]


def validate_transitions_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Validate schema, completeness, and numeric bounds of a transitions DataFrame.

    Enforces:
    1. Presence of all REQUIRED_INPUT_COLUMNS.
    2. Non-empty, non-whitespace activity strings.
    3. Proper numeric types for transition_count and duration metrics.
    4. Positive integer values (>= 1) for transition_count.
    5. Non-negative durations (>= 0.0).
    6. Logical consistency of timing statistics:
       - minimum <= median <= maximum
       - mean within minimum/maximum (minimum <= mean <= maximum)

    Args:
        df: Input DataFrame containing transition metrics.

    Returns:
        Cleaned and properly typed DataFrame.

    Raises:
        ValueError: If required columns are missing, DataFrame is empty,
            contains invalid non-numeric/null values, negative durations,
            non-positive counts, or logically inconsistent statistics.
    """
    if df is None or df.empty:
        raise ValueError("Input transition data contains zero records")

    missing_cols = [col for col in REQUIRED_INPUT_COLUMNS if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Input data missing required columns: {missing_cols}")

    # Validate activity names (must be non-null and non-empty strings)
    for col in ["source_activity", "target_activity"]:
        if df[col].isna().any():
            raise ValueError(f"Column '{col}' contains null or NaN values")
        if (df[col].astype(str).str.strip() == "").any():
            raise ValueError(f"Column '{col}' contains empty or whitespace-only values")

    # Validate numeric columns
    for col in NUMERIC_COLUMNS:
        if df[col].isna().any():
            raise ValueError(f"Column '{col}' contains null or NaN values")

        coerced = pd.to_numeric(df[col], errors="coerce")
        if coerced.isna().any():
            raise ValueError(f"Column '{col}' contains non-numeric or unparseable values")

    # Validate transition_count bounds and integrity (must be integer >= 1)
    counts = pd.to_numeric(df["transition_count"], errors="coerce")
    if (counts <= 0).any():
        raise ValueError("Column 'transition_count' must contain positive integers (>= 1)")
    if (counts % 1 != 0).any():
        raise ValueError("Column 'transition_count' cannot contain fractional values")

    # Validate duration bounds (non-negative)
    for col in DURATION_COLUMNS:
        durations = pd.to_numeric(df[col], errors="coerce")
        if (durations < 0).any():
            raise ValueError(f"Column '{col}' cannot contain negative values")

    # Validate logical range and ordering of timing statistics:
    # 1. minimum <= median <= maximum
    # 2. mean within [minimum, maximum] (minimum <= mean <= maximum)
    mins = pd.to_numeric(df["min_observed_transition_minutes"], errors="coerce")
    maxs = pd.to_numeric(df["max_observed_transition_minutes"], errors="coerce")
    medians = pd.to_numeric(df["median_observed_transition_minutes"], errors="coerce")
    means = pd.to_numeric(df["mean_observed_transition_minutes"], errors="coerce")

    if (mins > medians).any():
        raise ValueError("min_observed_transition_minutes cannot exceed median_observed_transition_minutes")
    if (medians > maxs).any():
        raise ValueError("median_observed_transition_minutes cannot exceed max_observed_transition_minutes")
    if (means < mins).any():
        raise ValueError("mean_observed_transition_minutes cannot be less than min_observed_transition_minutes")
    if (means > maxs).any():
        raise ValueError("mean_observed_transition_minutes cannot exceed max_observed_transition_minutes")

    # Construct clean typed copy
    cleaned = df.copy()
    cleaned["source_activity"] = cleaned["source_activity"].astype(str).str.strip()
    cleaned["target_activity"] = cleaned["target_activity"].astype(str).str.strip()
    cleaned["transition_count"] = cleaned["transition_count"].astype(int)
    for col in DURATION_COLUMNS:
        cleaned[col] = cleaned[col].astype(float)

    return cleaned


def load_transitions_summary(file_path: Union[str, Path] = DEFAULT_INPUT_PATH) -> pd.DataFrame:
    """Load and validate a transition summary CSV file.

    Args:
        file_path: Path to the transition summary CSV. Defaults to
            PROJECT_ROOT / 'outputs' / 'dfg_transitions_summary.csv'.

    Returns:
        Validated DataFrame.

    Raises:
        FileNotFoundError: If the specified file path does not exist.
        ValueError: If the file is 0 bytes, empty, or fails validation.
    """
    path = Path(file_path)
    if not path.is_absolute():
        resolved_path = (PROJECT_ROOT / path).resolve()
        if resolved_path.is_file():
            path = resolved_path
        else:
            path = path.resolve()
    else:
        path = path.resolve()

    if not path.is_file():
        raise FileNotFoundError(f"Transition summary file not found: {path}")

    if path.stat().st_size == 0:
        raise ValueError(f"Input transition file is empty (0 bytes): {path}")

    try:
        df = pd.read_csv(path)
    except pd.errors.EmptyDataError:
        raise ValueError(f"Input transition file contains no data: {path}")

    return validate_transitions_dataframe(df)


def rank_transitions(df: pd.DataFrame) -> pd.DataFrame:
    """Rank clinical transitions by mean observed transition time in descending order.

    Deterministic tie-breaking:
    1. mean_observed_transition_minutes (DESC)
    2. median_observed_transition_minutes (DESC)
    3. transition_count (DESC)
    4. source_activity (ASC)
    5. target_activity (ASC)

    Args:
        df: Validated DataFrame containing transition metrics.

    Returns:
        DataFrame sorted by mean duration with a 1-indexed 'rank' column.
    """
    validated = validate_transitions_dataframe(df)

    sorted_df = validated.sort_values(
        by=[
            "mean_observed_transition_minutes",
            "median_observed_transition_minutes",
            "transition_count",
            "source_activity",
            "target_activity",
        ],
        ascending=[False, False, False, True, True],
    ).reset_index(drop=True)

    sorted_df.insert(0, "rank", range(1, len(sorted_df) + 1))
    return sorted_df[EXPECTED_OUTPUT_COLUMNS]


def get_top_bottlenecks(df_ranked: pd.DataFrame, n: int = 3) -> pd.DataFrame:
    """Return the top N longest observed transitions from a ranked DataFrame.

    Args:
        df_ranked: Ranked transitions DataFrame.
        n: Number of top transitions to return.

    Returns:
        Subset DataFrame containing top N transitions.
    """
    if "rank" not in df_ranked.columns:
        df_ranked = rank_transitions(df_ranked)
    return df_ranked.head(n).copy().reset_index(drop=True)


def run_bottleneck_analysis(
    input_path: Union[str, Path] = DEFAULT_INPUT_PATH,
    output_path: Optional[Union[str, Path]] = DEFAULT_OUTPUT_PATH,
) -> pd.DataFrame:
    """Execute end-to-end bottleneck analysis on transitions summary.

    Args:
        input_path: Path to the input DFG transitions summary CSV.
            Defaults to DEFAULT_INPUT_PATH.
        output_path: Optional destination path to write ranked summary CSV.
            Defaults to DEFAULT_OUTPUT_PATH.

    Returns:
        Ranked transitions DataFrame.
    """
    logger.info("Loading transition summary from: %s", input_path)
    df_raw = load_transitions_summary(input_path)
    logger.info("Loaded %d transition records. Ranking transitions...", len(df_raw))

    ranked_df = rank_transitions(df_raw)

    if output_path is not None:
        out_file = Path(output_path).resolve()
        out_file.parent.mkdir(parents=True, exist_ok=True)
        ranked_df.to_csv(out_file, index=False)
        logger.info("Successfully exported bottleneck analysis summary to: %s", out_file)

    return ranked_df


def build_cli_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser with repository-root-based defaults."""
    parser = argparse.ArgumentParser(
        description="CareFlow Bottleneck Analyzer: Rank clinical transitions by observed duration."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT_PATH,
        help=f"Path to input DFG transitions summary CSV (default: {DEFAULT_INPUT_PATH})",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
        help=f"Path to output bottleneck analysis summary CSV (default: {DEFAULT_OUTPUT_PATH})",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> None:
    """CLI entrypoint for running the CareFlow bottleneck analyzer."""
    parser = build_cli_parser()
    args = parser.parse_args(argv)

    run_bottleneck_analysis(args.input, args.output)


if __name__ == "__main__":
    main()
