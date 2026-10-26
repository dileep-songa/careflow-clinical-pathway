"""Unit test suite for CareFlow Bottleneck Analyzer module (src/bottleneck_analyzer.py).

Validates:
1. Defensive schema validation: missing files, empty files, missing columns, empty DataFrames.
2. Value integrity checks: null values, empty/whitespace activities, non-numeric values,
   negative durations, non-positive or fractional counts, min > median, median > max,
   and mean bounds within [min, max].
3. Correct ranking logic: descending sort by mean observed transition time, deterministic
   tie-breaking, 1-indexed rank column, and preservation of timing statistics.
4. Output schema compliance against EXPECTED_OUTPUT_COLUMNS contract.
5. End-to-end execution against canonical outputs/dfg_transitions_summary.csv.
6. Immutability of input files during pipeline execution.
7. Repository-root-based CLI defaults and argument parsing.
"""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path
import tempfile
import unittest

import pandas as pd

from src.bottleneck_analyzer import (
    DEFAULT_INPUT_PATH,
    DEFAULT_OUTPUT_PATH,
    DURATION_COLUMNS,
    EXPECTED_OUTPUT_COLUMNS,
    NUMERIC_COLUMNS,
    PROJECT_ROOT,
    REQUIRED_INPUT_COLUMNS,
    build_cli_parser,
    get_top_bottlenecks,
    load_transitions_summary,
    main,
    rank_transitions,
    run_bottleneck_analysis,
    validate_transitions_dataframe,
)

CANONICAL_TRANSITIONS_CSV = PROJECT_ROOT / "outputs" / "dfg_transitions_summary.csv"


class TestBottleneckAnalyzerValidation(unittest.TestCase):
    """Test defensive schema validation, missing data, and value boundaries."""

    def test_missing_file_raises_error(self) -> None:
        """Verify FileNotFoundError is raised when input file path does not exist."""
        non_existent = PROJECT_ROOT / "outputs" / "does_not_exist.csv"
        with self.assertRaises(FileNotFoundError):
            load_transitions_summary(non_existent)

    def test_empty_file_raises_error(self) -> None:
        """Verify ValueError is raised for 0-byte input file."""
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            temp_path = Path(f.name)
        try:
            with self.assertRaises(ValueError) as ctx:
                load_transitions_summary(temp_path)
            self.assertIn("empty", str(ctx.exception).lower())
        finally:
            temp_path.unlink(missing_ok=True)

    def test_empty_dataframe_raises_error(self) -> None:
        """Verify ValueError is raised if DataFrame contains zero rows."""
        df_empty = pd.DataFrame(columns=REQUIRED_INPUT_COLUMNS)
        with self.assertRaises(ValueError) as ctx:
            validate_transitions_dataframe(df_empty)
        self.assertIn("zero records", str(ctx.exception).lower())

    def test_missing_required_columns_raises_error(self) -> None:
        """Verify ValueError is raised if any required columns are omitted."""
        df_missing = pd.DataFrame(
            {
                "source_activity": ["Consultation"],
                "target_activity": ["Treatment"],
                "transition_count": [500],
                # Missing all duration columns
            }
        )
        with self.assertRaises(ValueError) as ctx:
            validate_transitions_dataframe(df_missing)
        self.assertIn("missing required columns", str(ctx.exception).lower())

    def test_null_or_whitespace_activity_names_raise_error(self) -> None:
        """Verify ValueError is raised if activity names are null, empty, or whitespace."""
        # Null activity
        df_null_act = pd.DataFrame(
            {
                "source_activity": [None],
                "target_activity": ["Treatment"],
                "transition_count": [10],
                "mean_observed_transition_minutes": [20.0],
                "median_observed_transition_minutes": [20.0],
                "min_observed_transition_minutes": [10.0],
                "max_observed_transition_minutes": [30.0],
            }
        )
        with self.assertRaises(ValueError) as ctx:
            validate_transitions_dataframe(df_null_act)
        self.assertIn("null or nan", str(ctx.exception).lower())

        # Whitespace-only activity
        df_blank_act = pd.DataFrame(
            {
                "source_activity": ["Consultation"],
                "target_activity": ["   "],
                "transition_count": [10],
                "mean_observed_transition_minutes": [20.0],
                "median_observed_transition_minutes": [20.0],
                "min_observed_transition_minutes": [10.0],
                "max_observed_transition_minutes": [30.0],
            }
        )
        with self.assertRaises(ValueError) as ctx:
            validate_transitions_dataframe(df_blank_act)
        self.assertIn("whitespace", str(ctx.exception).lower())

    def test_non_numeric_values_raise_error(self) -> None:
        """Verify ValueError is raised when numeric columns contain non-numeric strings."""
        df_bad_type = pd.DataFrame(
            {
                "source_activity": ["Registration"],
                "target_activity": ["Triage"],
                "transition_count": [100],
                "mean_observed_transition_minutes": ["not_a_number"],
                "median_observed_transition_minutes": [20.0],
                "min_observed_transition_minutes": [10.0],
                "max_observed_transition_minutes": [30.0],
            }
        )
        with self.assertRaises(ValueError) as ctx:
            validate_transitions_dataframe(df_bad_type)
        self.assertIn("non-numeric", str(ctx.exception).lower())

    def test_null_numeric_values_raise_error(self) -> None:
        """Verify ValueError is raised when numeric columns contain null/NaN values."""
        df_null_num = pd.DataFrame(
            {
                "source_activity": ["Registration"],
                "target_activity": ["Triage"],
                "transition_count": [100],
                "mean_observed_transition_minutes": [20.0],
                "median_observed_transition_minutes": [None],
                "min_observed_transition_minutes": [10.0],
                "max_observed_transition_minutes": [30.0],
            }
        )
        with self.assertRaises(ValueError) as ctx:
            validate_transitions_dataframe(df_null_num)
        self.assertIn("null or nan", str(ctx.exception).lower())

    def test_negative_durations_raise_error(self) -> None:
        """Verify ValueError is raised if any transition duration metric is negative."""
        df_neg = pd.DataFrame(
            {
                "source_activity": ["Registration"],
                "target_activity": ["Triage"],
                "transition_count": [100],
                "mean_observed_transition_minutes": [-5.0],
                "median_observed_transition_minutes": [20.0],
                "min_observed_transition_minutes": [10.0],
                "max_observed_transition_minutes": [30.0],
            }
        )
        with self.assertRaises(ValueError) as ctx:
            validate_transitions_dataframe(df_neg)
        self.assertIn("cannot contain negative", str(ctx.exception).lower())

    def test_non_positive_transition_count_raises_error(self) -> None:
        """Verify ValueError is raised if transition_count is zero or negative."""
        df_zero_count = pd.DataFrame(
            {
                "source_activity": ["Registration"],
                "target_activity": ["Triage"],
                "transition_count": [0],
                "mean_observed_transition_minutes": [20.0],
                "median_observed_transition_minutes": [20.0],
                "min_observed_transition_minutes": [10.0],
                "max_observed_transition_minutes": [30.0],
            }
        )
        with self.assertRaises(ValueError) as ctx:
            validate_transitions_dataframe(df_zero_count)
        self.assertIn("positive integers", str(ctx.exception).lower())

    def test_fractional_transition_count_raises_error(self) -> None:
        """Verify ValueError is raised if transition_count contains fractional values."""
        df_frac_count = pd.DataFrame(
            {
                "source_activity": ["Registration"],
                "target_activity": ["Triage"],
                "transition_count": [12.5],
                "mean_observed_transition_minutes": [20.0],
                "median_observed_transition_minutes": [20.0],
                "min_observed_transition_minutes": [10.0],
                "max_observed_transition_minutes": [30.0],
            }
        )
        with self.assertRaises(ValueError) as ctx:
            validate_transitions_dataframe(df_frac_count)
        self.assertIn("fractional", str(ctx.exception).lower())

    def test_min_exceeds_median_raises_error(self) -> None:
        """Verify ValueError is raised if minimum duration exceeds median duration."""
        df_inverted = pd.DataFrame(
            {
                "source_activity": ["Registration"],
                "target_activity": ["Triage"],
                "transition_count": [100],
                "mean_observed_transition_minutes": [22.0],
                "median_observed_transition_minutes": [20.0],
                "min_observed_transition_minutes": [25.0],  # min > median
                "max_observed_transition_minutes": [30.0],
            }
        )
        with self.assertRaises(ValueError) as ctx:
            validate_transitions_dataframe(df_inverted)
        self.assertIn("cannot exceed median", str(ctx.exception).lower())

    def test_median_exceeds_max_raises_error(self) -> None:
        """Verify ValueError is raised if median duration exceeds maximum duration."""
        df_inverted = pd.DataFrame(
            {
                "source_activity": ["Registration"],
                "target_activity": ["Triage"],
                "transition_count": [100],
                "mean_observed_transition_minutes": [20.0],
                "median_observed_transition_minutes": [35.0],  # median > max
                "min_observed_transition_minutes": [10.0],
                "max_observed_transition_minutes": [30.0],
            }
        )
        with self.assertRaises(ValueError) as ctx:
            validate_transitions_dataframe(df_inverted)
        self.assertIn("cannot exceed max", str(ctx.exception).lower())

    def test_mean_less_than_min_raises_error(self) -> None:
        """Verify ValueError is raised if mean duration is less than minimum duration."""
        df_invalid_mean = pd.DataFrame(
            {
                "source_activity": ["Registration"],
                "target_activity": ["Triage"],
                "transition_count": [100],
                "mean_observed_transition_minutes": [8.0],  # mean < min
                "median_observed_transition_minutes": [15.0],
                "min_observed_transition_minutes": [10.0],
                "max_observed_transition_minutes": [25.0],
            }
        )
        with self.assertRaises(ValueError) as ctx:
            validate_transitions_dataframe(df_invalid_mean)
        self.assertIn("cannot be less than min", str(ctx.exception).lower())

    def test_mean_exceeds_max_raises_error(self) -> None:
        """Verify ValueError is raised if mean duration exceeds maximum duration."""
        df_invalid_mean = pd.DataFrame(
            {
                "source_activity": ["Registration"],
                "target_activity": ["Triage"],
                "transition_count": [100],
                "mean_observed_transition_minutes": [35.0],  # mean > max
                "median_observed_transition_minutes": [20.0],
                "min_observed_transition_minutes": [10.0],
                "max_observed_transition_minutes": [30.0],
            }
        )
        with self.assertRaises(ValueError) as ctx:
            validate_transitions_dataframe(df_invalid_mean)
        self.assertIn("cannot exceed max", str(ctx.exception).lower())


class TestBottleneckAnalyzerRanking(unittest.TestCase):
    """Test ranking logic, expected columns, tie breaking, and preservation of metrics."""

    def setUp(self) -> None:
        """Set up synthetic transitions fixture."""
        self.fixture_df = pd.DataFrame(
            [
                {
                    "source_activity": "Triage",
                    "target_activity": "Consultation",
                    "transition_count": 100,
                    "mean_observed_transition_minutes": 25.0,
                    "median_observed_transition_minutes": 24.0,
                    "min_observed_transition_minutes": 10.0,
                    "max_observed_transition_minutes": 40.0,
                },
                {
                    "source_activity": "Laboratory",
                    "target_activity": "Consultation",
                    "transition_count": 50,
                    "mean_observed_transition_minutes": 70.0,
                    "median_observed_transition_minutes": 68.0,
                    "min_observed_transition_minutes": 45.0,
                    "max_observed_transition_minutes": 95.0,
                },
                {
                    "source_activity": "Treatment",
                    "target_activity": "Discharge",
                    "transition_count": 100,
                    "mean_observed_transition_minutes": 50.0,
                    "median_observed_transition_minutes": 48.0,
                    "min_observed_transition_minutes": 25.0,
                    "max_observed_transition_minutes": 75.0,
                },
            ]
        )

    def test_expected_output_columns(self) -> None:
        """Verify ranked output contains exactly the expected columns in correct sequence."""
        ranked = rank_transitions(self.fixture_df)
        self.assertEqual(list(ranked.columns), EXPECTED_OUTPUT_COLUMNS)

    def test_correct_ranking_order(self) -> None:
        """Verify transitions are ordered descending by mean observed transition time."""
        ranked = rank_transitions(self.fixture_df)
        self.assertEqual(ranked["rank"].tolist(), [1, 2, 3])
        self.assertEqual(
            ranked["source_activity"].tolist(),
            ["Laboratory", "Treatment", "Triage"],
        )
        self.assertEqual(
            ranked["mean_observed_transition_minutes"].tolist(),
            [70.0, 50.0, 25.0],
        )

    def test_preserves_counts_and_timing_statistics(self) -> None:
        """Verify transition counts and duration statistics match original values exactly."""
        ranked = rank_transitions(self.fixture_df)
        lab_row = ranked[ranked["source_activity"] == "Laboratory"].iloc[0]
        self.assertEqual(lab_row["transition_count"], 50)
        self.assertEqual(lab_row["mean_observed_transition_minutes"], 70.0)
        self.assertEqual(lab_row["median_observed_transition_minutes"], 68.0)
        self.assertEqual(lab_row["min_observed_transition_minutes"], 45.0)
        self.assertEqual(lab_row["max_observed_transition_minutes"], 95.0)

    def test_deterministic_tie_breaking(self) -> None:
        """Verify deterministic tie-breaking when mean durations are equal."""
        df_ties = pd.DataFrame(
            [
                {
                    "source_activity": "Beta",
                    "target_activity": "Target",
                    "transition_count": 30,
                    "mean_observed_transition_minutes": 40.0,
                    "median_observed_transition_minutes": 38.0,
                    "min_observed_transition_minutes": 20.0,
                    "max_observed_transition_minutes": 60.0,
                },
                {
                    "source_activity": "Alpha",
                    "target_activity": "Target",
                    "transition_count": 30,
                    "mean_observed_transition_minutes": 40.0,
                    "median_observed_transition_minutes": 38.0,
                    "min_observed_transition_minutes": 20.0,
                    "max_observed_transition_minutes": 60.0,
                },
                {
                    "source_activity": "Gamma",
                    "target_activity": "Target",
                    "transition_count": 50,  # higher count breaks tie
                    "mean_observed_transition_minutes": 40.0,
                    "median_observed_transition_minutes": 38.0,
                    "min_observed_transition_minutes": 20.0,
                    "max_observed_transition_minutes": 60.0,
                },
            ]
        )
        ranked = rank_transitions(df_ties)
        # Gamma has higher transition_count (50 > 30), so ranks 1st
        # Alpha and Beta tie on mean, median, count -> tie broken by source_activity alphabetically
        self.assertEqual(ranked["source_activity"].tolist(), ["Gamma", "Alpha", "Beta"])
        self.assertEqual(ranked["rank"].tolist(), [1, 2, 3])

    def test_single_row_input(self) -> None:
        """Verify single transition row yields rank 1 with identical metrics."""
        df_single = pd.DataFrame(
            [
                {
                    "source_activity": "Registration",
                    "target_activity": "Triage",
                    "transition_count": 10,
                    "mean_observed_transition_minutes": 15.5,
                    "median_observed_transition_minutes": 15.0,
                    "min_observed_transition_minutes": 10.0,
                    "max_observed_transition_minutes": 20.0,
                }
            ]
        )
        ranked = rank_transitions(df_single)
        self.assertEqual(len(ranked), 1)
        self.assertEqual(ranked.iloc[0]["rank"], 1)
        self.assertEqual(ranked.iloc[0]["mean_observed_transition_minutes"], 15.5)

    def test_get_top_bottlenecks(self) -> None:
        """Verify get_top_bottlenecks returns expected number of top records."""
        top2 = get_top_bottlenecks(self.fixture_df, n=2)
        self.assertEqual(len(top2), 2)
        self.assertEqual(top2["rank"].tolist(), [1, 2])
        self.assertEqual(top2["source_activity"].tolist(), ["Laboratory", "Treatment"])


class TestCanonicalBottleneckExecution(unittest.TestCase):
    """Test bottleneck analyzer against canonical outputs/dfg_transitions_summary.csv."""

    @classmethod
    def setUpClass(cls) -> None:
        """Verify canonical DFG transitions summary exists before running tests."""
        if not CANONICAL_TRANSITIONS_CSV.is_file():
            raise unittest.SkipTest(f"Missing canonical file: {CANONICAL_TRANSITIONS_CSV}")

    def test_canonical_ranking_results(self) -> None:
        """Verify ranking on canonical transitions reproduces expected order and metrics."""
        ranked = run_bottleneck_analysis(CANONICAL_TRANSITIONS_CSV)

        # Canonical file has exactly 10 distinct transitions
        self.assertEqual(len(ranked), 10)
        self.assertEqual(list(ranked.columns), EXPECTED_OUTPUT_COLUMNS)

        # Rank 1: Laboratory -> Consultation (longest mean duration: 67.44 min)
        r1 = ranked.iloc[0]
        self.assertEqual(r1["rank"], 1)
        self.assertEqual(r1["source_activity"], "Laboratory")
        self.assertEqual(r1["target_activity"], "Consultation")
        self.assertEqual(r1["transition_count"], 135)
        self.assertEqual(r1["mean_observed_transition_minutes"], 67.44)
        self.assertEqual(r1["median_observed_transition_minutes"], 67.0)

        # Rank 2: Triage -> Triage (re-triage loop: 65.63 min)
        r2 = ranked.iloc[1]
        self.assertEqual(r2["rank"], 2)
        self.assertEqual(r2["source_activity"], "Triage")
        self.assertEqual(r2["target_activity"], "Triage")
        self.assertEqual(r2["transition_count"], 60)
        self.assertEqual(r2["mean_observed_transition_minutes"], 65.63)

        # Rank 3: X-Ray -> Consultation (60.36 min)
        r3 = ranked.iloc[2]
        self.assertEqual(r3["rank"], 3)
        self.assertEqual(r3["source_activity"], "X-Ray")
        self.assertEqual(r3["target_activity"], "Consultation")
        self.assertEqual(r3["transition_count"], 130)
        self.assertEqual(r3["mean_observed_transition_minutes"], 60.36)

        # Rank 10: Registration -> Triage (shortest mean duration: 20.58 min)
        r10 = ranked.iloc[9]
        self.assertEqual(r10["rank"], 10)
        self.assertEqual(r10["source_activity"], "Registration")
        self.assertEqual(r10["target_activity"], "Triage")
        self.assertEqual(r10["transition_count"], 500)
        self.assertEqual(r10["mean_observed_transition_minutes"], 20.58)

    def test_export_to_csv_output(self) -> None:
        """Verify run_bottleneck_analysis writes valid CSV to disk with correct headers."""
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            temp_output = Path(f.name)

        try:
            ranked = run_bottleneck_analysis(CANONICAL_TRANSITIONS_CSV, output_path=temp_output)
            self.assertTrue(temp_output.is_file())
            self.assertGreater(temp_output.stat().st_size, 0)

            # Read back and inspect
            df_read = pd.read_csv(temp_output)
            self.assertEqual(list(df_read.columns), EXPECTED_OUTPUT_COLUMNS)
            self.assertEqual(len(df_read), 10)
            self.assertEqual(df_read.iloc[0]["source_activity"], "Laboratory")
            self.assertEqual(df_read.iloc[0]["target_activity"], "Consultation")
        finally:
            temp_output.unlink(missing_ok=True)

    def test_canonical_input_file_immutability(self) -> None:
        """Verify input DFG transitions summary CSV is unchanged after running analysis."""
        with open(CANONICAL_TRANSITIONS_CSV, "rb") as f:
            initial_hash = hashlib.md5(f.read()).hexdigest()

        # Execute analysis
        _ = run_bottleneck_analysis(CANONICAL_TRANSITIONS_CSV)

        with open(CANONICAL_TRANSITIONS_CSV, "rb") as f:
            final_hash = hashlib.md5(f.read()).hexdigest()

        self.assertEqual(
            initial_hash,
            final_hash,
            "Input transition summary file was modified during analysis execution",
        )


class TestBottleneckAnalyzerCLI(unittest.TestCase):
    """Test repository-root-based CLI defaults and execution."""

    def test_cli_defaults_anchored_to_project_root(self) -> None:
        """Verify default input and output paths are anchored to PROJECT_ROOT."""
        self.assertEqual(DEFAULT_INPUT_PATH, PROJECT_ROOT / "outputs" / "dfg_transitions_summary.csv")
        self.assertEqual(DEFAULT_OUTPUT_PATH, PROJECT_ROOT / "outputs" / "bottleneck_analysis_summary.csv")
        self.assertTrue(DEFAULT_INPUT_PATH.is_absolute())
        self.assertTrue(DEFAULT_OUTPUT_PATH.is_absolute())

    def test_build_cli_parser_defaults(self) -> None:
        """Verify parser uses repository-root-based default paths when no flags are supplied."""
        parser = build_cli_parser()
        args = parser.parse_args([])
        self.assertEqual(args.input, DEFAULT_INPUT_PATH)
        self.assertEqual(args.output, DEFAULT_OUTPUT_PATH)

    def test_load_transitions_summary_default_path(self) -> None:
        """Verify load_transitions_summary loads canonical dataset when called without arguments."""
        df = load_transitions_summary()
        self.assertEqual(len(df), 10)
        self.assertIn("source_activity", df.columns)

    def test_cli_main_with_custom_paths(self) -> None:
        """Verify main() executes end-to-end with custom CLI arguments."""
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            temp_output = Path(f.name)

        try:
            main(["--input", str(CANONICAL_TRANSITIONS_CSV), "--output", str(temp_output)])
            self.assertTrue(temp_output.is_file())
            self.assertGreater(temp_output.stat().st_size, 0)
            df = pd.read_csv(temp_output)
            self.assertEqual(len(df), 10)
            self.assertEqual(df.iloc[0]["rank"], 1)
        finally:
            temp_output.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
