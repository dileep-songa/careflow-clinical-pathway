"""CareFlow Bottleneck Visualizer Module.

This module generates reproducible visual reports for clinical pathway transition bottlenecks
using simulated process-mining metrics. It reads ranked bottleneck summaries and produces
publication-quality horizontal bar charts illustrating observed transition durations.

Clinical & Healthcare Analytics Terminology:
Observed transition time represents the elapsed duration between recorded timestamps
of consecutive events within a patient encounter. It should NOT be assumed to equal
actual patient clinical waiting time, as clinical encounters include active care,
patient transport, and administrative processing alongside queuing. All visualized data
is synthetic (simulated EHR encounters).
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Union

import matplotlib
# Use headless backend for non-interactive and CI execution
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

# Configure logger
logger = logging.getLogger("careflow.bottleneck_visualizer")
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
DEFAULT_INPUT_CSV = PROJECT_ROOT / "outputs" / "bottleneck_analysis_summary.csv"
DEFAULT_OUTPUT_PNG = PROJECT_ROOT / "outputs" / "bottleneck_analysis.png"

# Schema contract required for visualization
REQUIRED_PLOT_COLUMNS: List[str] = [
    "source_activity",
    "target_activity",
    "mean_observed_transition_minutes",
]


def validate_plot_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Validate completeness and numeric bounds of a DataFrame intended for plotting.

    Args:
        df: Input DataFrame containing transition metrics.

    Returns:
        Cleaned DataFrame with verified numeric durations and non-empty activity labels.

    Raises:
        ValueError: If df is empty, missing required columns, or contains invalid data.
    """
    if df is None or df.empty:
        raise ValueError("Input DataFrame contains zero records to visualize")

    missing = [c for c in REQUIRED_PLOT_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Input DataFrame missing required visualization columns: {missing}")

    # Validate activity names
    for col in ["source_activity", "target_activity"]:
        if df[col].isna().any():
            raise ValueError(f"Column '{col}' contains null or NaN values")
        if (df[col].astype(str).str.strip() == "").any():
            raise ValueError(f"Column '{col}' contains empty or whitespace-only activity names")

    # Validate numeric mean duration
    durations = pd.to_numeric(df["mean_observed_transition_minutes"], errors="coerce")
    if durations.isna().any():
        raise ValueError("Column 'mean_observed_transition_minutes' contains non-numeric values")
    if (durations < 0).any():
        raise ValueError("Column 'mean_observed_transition_minutes' cannot contain negative values")

    cleaned = df.copy()
    cleaned["source_activity"] = cleaned["source_activity"].astype(str).str.strip()
    cleaned["target_activity"] = cleaned["target_activity"].astype(str).str.strip()
    cleaned["mean_observed_transition_minutes"] = durations.astype(float)
    return cleaned


def load_bottleneck_data(file_path: Union[str, Path] = DEFAULT_INPUT_CSV) -> pd.DataFrame:
    """Load and validate bottleneck summary data from a CSV file.

    Args:
        file_path: Path to the bottleneck CSV. Defaults to DEFAULT_INPUT_CSV.

    Returns:
        Validated DataFrame.

    Raises:
        FileNotFoundError: If the CSV file does not exist.
        ValueError: If the file is empty or fails validation.
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
        raise FileNotFoundError(f"Bottleneck summary file not found: {path}")

    if path.stat().st_size == 0:
        raise ValueError(f"Input bottleneck summary file is empty (0 bytes): {path}")

    try:
        df = pd.read_csv(path)
    except pd.errors.EmptyDataError:
        raise ValueError(f"Input bottleneck summary file contains no data: {path}")

    return validate_plot_dataframe(df)


def generate_bottleneck_chart(
    data: Union[pd.DataFrame, str, Path] = DEFAULT_INPUT_CSV,
    output_path: Optional[Union[str, Path]] = DEFAULT_OUTPUT_PNG,
    top_n: int = 10,
    dpi: int = 300,
) -> Path:
    """Generate a publication-quality horizontal bar chart of top clinical bottlenecks.

    Transitions are ordered with the longest mean observed transition time at the top.
    Handles datasets with fewer than top_n rows gracefully.

    Args:
        data: DataFrame or file path to bottleneck summary CSV.
        output_path: Destination path for the rendered PNG image.
        top_n: Maximum number of top transitions to visualize (default: 10).
        dpi: Resolution of the output image (default: 300).

    Returns:
        Path to the saved image file.

    Raises:
        ValueError: If data is invalid, empty, or top_n < 1.
    """
    if top_n < 1:
        raise ValueError("top_n must be a positive integer (>= 1)")

    if isinstance(data, (str, Path)):
        df = load_bottleneck_data(data)
    elif isinstance(data, pd.DataFrame):
        df = validate_plot_dataframe(data)
    else:
        raise TypeError(f"Expected DataFrame or Path/str for data, got {type(data)}")

    # Ensure data is sorted descending by mean observed transition duration
    sort_cols = ["mean_observed_transition_minutes"]
    ascending = [False]
    if "median_observed_transition_minutes" in df.columns:
        sort_cols.append("median_observed_transition_minutes")
        ascending.append(False)
    if "transition_count" in df.columns:
        sort_cols.append("transition_count")
        ascending.append(False)

    df_sorted = df.sort_values(by=sort_cols, ascending=ascending).reset_index(drop=True)

    # Subset to top_n (handles fewer than top_n rows gracefully)
    num_to_plot = min(len(df_sorted), top_n)
    plot_df = df_sorted.head(num_to_plot).copy()

    # Build transition label: "Source -> Target" or "Rank. Source -> Target"
    labels: List[str] = []
    for idx, row in plot_df.iterrows():
        src = row["source_activity"]
        tgt = row["target_activity"]
        rank_val = row.get("rank", idx + 1)
        count_val = row.get("transition_count")
        if pd.notna(count_val):
            labels.append(f"#{int(rank_val)}: {src} -> {tgt}  (N={int(count_val):,})")
        else:
            labels.append(f"#{int(rank_val)}: {src} -> {tgt}")

    durations = plot_df["mean_observed_transition_minutes"].tolist()

    # Invert ordering so the longest transition (#1) appears at the top of the chart
    labels_rev = labels[::-1]
    durations_rev = durations[::-1]
    y_positions = list(range(len(labels_rev)))

    # Figure dimensions scaled to row count
    fig_height = max(5.0, 1.2 + 0.55 * num_to_plot)
    fig, ax = plt.subplots(figsize=(11.5, fig_height), dpi=dpi)

    # Color gradient: highest duration has darker/prominent shade
    # Normalized against max duration
    max_dur = max(durations) if durations else 1.0
    colors = [
        plt.cm.Blues(0.45 + 0.5 * (d / max_dur))
        for d in durations_rev
    ]

    bars = ax.barh(
        y_positions,
        durations_rev,
        height=0.62,
        color=colors,
        edgecolor="#1f4e78",
        linewidth=1.0,
        alpha=0.92,
    )

    # Add numeric value labels on bars
    for bar, val in zip(bars, durations_rev):
        width = bar.get_width()
        ax.text(
            width + (max_dur * 0.015),
            bar.get_y() + bar.get_height() / 2.0,
            f"{val:.2f} min",
            va="center",
            ha="left",
            fontsize=9.5,
            fontweight="bold",
            color="#1a2530",
        )

    # Format Axes
    ax.set_yticks(y_positions)
    ax.set_yticklabels(labels_rev, fontsize=10)
    ax.set_xlabel("Mean Observed Transition Duration (Minutes)", fontsize=11, fontweight="bold", labelpad=10)

    # Upper limit margin for value labels
    ax.set_xlim(0, max_dur * 1.18)

    # Styling: subtle vertical gridlines, remove top/right spines
    ax.xaxis.grid(True, linestyle="--", alpha=0.5, color="#cbd5e1", zorder=0)
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#64748b")
    ax.spines["bottom"].set_color("#64748b")

    # Chart Title and Subtitle
    title_text = f"CareFlow Clinical Pathway: Top {num_to_plot} Activity Transitions"
    subtitle_text = (
        "Ranked by Mean Observed Transition Duration | Simulated EHR Data (500 Cases, 3,140 Events)\n"
        "Note: Observed transition duration conflates active care, inter-department transit, and idle queuing."
    )
    fig.suptitle(title_text, fontsize=13, fontweight="bold", x=0.5, y=0.98 if fig_height > 6 else 1.01)
    ax.set_title(subtitle_text, fontsize=8.5, color="#475569", pad=12, style="italic")

    plt.tight_layout()

    # Destination path resolution and export
    if output_path is None:
        target_path = DEFAULT_OUTPUT_PNG
    else:
        target_path = Path(output_path)
        if not target_path.is_absolute():
            target_path = (PROJECT_ROOT / target_path).resolve()
        else:
            target_path = target_path.resolve()

    target_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(target_path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)

    logger.info("Successfully exported bottleneck visualization to: %s", target_path)
    return target_path


def build_cli_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser with repository-root-based defaults."""
    parser = argparse.ArgumentParser(
        description="CareFlow Bottleneck Visualizer: Generate horizontal bar chart of top clinical bottlenecks."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT_CSV,
        help=f"Path to input bottleneck summary CSV (default: {DEFAULT_INPUT_CSV})",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PNG,
        help=f"Path to output PNG image file (default: {DEFAULT_OUTPUT_PNG})",
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=10,
        help="Maximum number of top transitions to plot (default: 10)",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=300,
        help="Image resolution in DPI (default: 300)",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> None:
    """CLI entrypoint for running the CareFlow bottleneck visualizer."""
    parser = build_cli_parser()
    args = parser.parse_args(argv)

    generate_bottleneck_chart(
        data=args.input,
        output_path=args.output,
        top_n=args.top_n,
        dpi=args.dpi,
    )


if __name__ == "__main__":
    main()
