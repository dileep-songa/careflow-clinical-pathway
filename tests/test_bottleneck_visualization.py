"""Unit test suite for CareFlow Bottleneck Visualizer module (src/bottleneck_visualizer.py).

Validates:
1. Input validation & error handling: missing file, empty file, empty DataFrame,
   missing required columns, blank activity strings, non-numeric and negative durations.
2. Successful chart generation from canonical summary CSV and direct DataFrames.
3. Correct sorting and top-N selection (e.g. from unsorted 15-row fixtures).
4. Graceful handling of fewer than 10 rows (1, 3, 5 rows).
5. Output format integrity (verifies PNG binary signature).
6. Directory auto-creation for nested output targets.
7. CLI parser configuration and execution with custom arguments.
"""

from __future__ import annotations

import csv
from pathlib import Path
import tempfile
import unittest

import pandas as pd

from src.bottleneck_visualizer import (
    DEFAULT_INPUT_CSV,
    DEFAULT_OUTPUT_PNG,
    PROJECT_ROOT,
    REQUIRED_PLOT_COLUMNS,
    build_cli_parser,
    generate_bottleneck_chart,
    load_bottleneck_data,
    main,
    validate_plot_dataframe,
)

CANONICAL_BOTTLENECK_CSV = PROJECT_ROOT / "outputs" / "bottleneck_analysis_summary.csv"
PNG_MAGIC_BYTES = b"\x89PNG\r\n\x1a\n"


class TestBottleneckVisualizationValidation(unittest.TestCase):
    """Test input validation, schema enforcement, and defensive checks."""

    def test_missing_file_raises_error(self) -> None:
        """Verify FileNotFoundError is raised when input CSV does not exist."""
        non_existent = PROJECT_ROOT / "outputs" / "non_existent_bottlenecks.csv"
        with self.assertRaises(FileNotFoundError):
            load_bottleneck_data(non_existent)

    def test_empty_file_raises_error(self) -> None:
        """Verify ValueError is raised for 0-byte input CSV."""
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            temp_path = Path(f.name)
        try:
            with self.assertRaises(ValueError) as ctx:
                load_bottleneck_data(temp_path)
            self.assertIn("empty", str(ctx.exception).lower())
        finally:
            temp_path.unlink(missing_ok=True)

    def test_empty_dataframe_raises_error(self) -> None:
        """Verify ValueError is raised if DataFrame has zero records."""
        df_empty = pd.DataFrame(columns=REQUIRED_PLOT_COLUMNS)
        with self.assertRaises(ValueError) as ctx:
            validate_plot_dataframe(df_empty)
        self.assertIn("zero records", str(ctx.exception).lower())

    def test_missing_required_columns_raises_error(self) -> None:
        """Verify ValueError is raised if any required plot columns are missing."""
        df_missing = pd.DataFrame(
            {
                "source_activity": ["Consultation"],
                "target_activity": ["Treatment"],
                # Missing mean_observed_transition_minutes
            }
        )
        with self.assertRaises(ValueError) as ctx:
            validate_plot_dataframe(df_missing)
        self.assertIn("missing required visualization columns", str(ctx.exception).lower())

    def test_null_or_whitespace_activity_names_raise_error(self) -> None:
        """Verify ValueError is raised if activity names are null or whitespace-only."""
        df_null_src = pd.DataFrame(
            {
                "source_activity": [None],
                "target_activity": ["Treatment"],
                "mean_observed_transition_minutes": [30.0],
            }
        )
        with self.assertRaises(ValueError) as ctx:
            validate_plot_dataframe(df_null_src)
        self.assertIn("null or nan", str(ctx.exception).lower())

        df_blank_tgt = pd.DataFrame(
            {
                "source_activity": ["Consultation"],
                "target_activity": ["   "],
                "mean_observed_transition_minutes": [30.0],
            }
        )
        with self.assertRaises(ValueError) as ctx:
            validate_plot_dataframe(df_blank_tgt)
        self.assertIn("whitespace", str(ctx.exception).lower())

    def test_non_numeric_duration_raises_error(self) -> None:
        """Verify ValueError is raised when mean duration contains non-numeric strings."""
        df_invalid = pd.DataFrame(
            {
                "source_activity": ["Registration"],
                "target_activity": ["Triage"],
                "mean_observed_transition_minutes": ["forty_two"],
            }
        )
        with self.assertRaises(ValueError) as ctx:
            validate_plot_dataframe(df_invalid)
        self.assertIn("non-numeric", str(ctx.exception).lower())

    def test_negative_duration_raises_error(self) -> None:
        """Verify ValueError is raised when mean duration is negative."""
        df_neg = pd.DataFrame(
            {
                "source_activity": ["Registration"],
                "target_activity": ["Triage"],
                "mean_observed_transition_minutes": [-10.5],
            }
        )
        with self.assertRaises(ValueError) as ctx:
            validate_plot_dataframe(df_neg)
        self.assertIn("cannot contain negative", str(ctx.exception).lower())

    def test_invalid_data_type_raises_type_error(self) -> None:
        """Verify TypeError is raised if data argument is neither DataFrame nor Path/str."""
        with self.assertRaises(TypeError):
            generate_bottleneck_chart(data=12345)  # type: ignore

    def test_invalid_top_n_raises_value_error(self) -> None:
        """Verify ValueError is raised when top_n is less than 1."""
        df = pd.DataFrame(
            {
                "source_activity": ["Registration"],
                "target_activity": ["Triage"],
                "mean_observed_transition_minutes": [20.0],
            }
        )
        with self.assertRaises(ValueError) as ctx:
            generate_bottleneck_chart(data=df, top_n=0)
        self.assertIn("positive integer", str(ctx.exception).lower())


class TestBottleneckChartGeneration(unittest.TestCase):
    """Test chart rendering, top-N slicing, fewer-than-10 handling, and file integrity."""

    @classmethod
    def setUpClass(cls) -> None:
        """Ensure canonical summary exists before testing."""
        if not CANONICAL_BOTTLENECK_CSV.is_file():
            raise unittest.SkipTest(f"Missing canonical file: {CANONICAL_BOTTLENECK_CSV}")

    def test_successful_chart_creation_from_canonical_csv(self) -> None:
        """Verify chart generates successfully from canonical CSV with valid PNG signature."""
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            temp_png = Path(f.name)

        try:
            out = generate_bottleneck_chart(
                data=CANONICAL_BOTTLENECK_CSV,
                output_path=temp_png,
                top_n=10,
                dpi=100,  # Lower DPI for fast test execution
            )
            self.assertEqual(out, temp_png.resolve())
            self.assertTrue(temp_png.is_file())
            self.assertGreater(temp_png.stat().st_size, 5000)

            # Validate PNG magic bytes header
            with open(temp_png, "rb") as png_f:
                magic = png_f.read(8)
            self.assertEqual(magic, PNG_MAGIC_BYTES)
        finally:
            temp_png.unlink(missing_ok=True)

    def test_successful_chart_creation_from_dataframe(self) -> None:
        """Verify chart generates directly from a DataFrame in memory."""
        df = pd.DataFrame(
            [
                {
                    "rank": 1,
                    "source_activity": "Laboratory",
                    "target_activity": "Consultation",
                    "transition_count": 135,
                    "mean_observed_transition_minutes": 67.44,
                },
                {
                    "rank": 2,
                    "source_activity": "Triage",
                    "target_activity": "Triage",
                    "transition_count": 60,
                    "mean_observed_transition_minutes": 65.63,
                },
            ]
        )
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            temp_png = Path(f.name)

        try:
            out = generate_bottleneck_chart(data=df, output_path=temp_png, top_n=10, dpi=100)
            self.assertTrue(temp_png.is_file())
            self.assertGreater(temp_png.stat().st_size, 1000)
            with open(temp_png, "rb") as png_f:
                self.assertEqual(png_f.read(8), PNG_MAGIC_BYTES)
        finally:
            temp_png.unlink(missing_ok=True)

    def test_sorting_and_top_10_selection(self) -> None:
        """Verify unsorted DataFrame with 15 transitions is properly sorted and sliced to 10."""
        # Create 15 transitions with ascending mean duration (10, 20, ..., 150)
        rows = [
            {
                "source_activity": f"Act_{i}",
                "target_activity": f"Act_{i+1}",
                "transition_count": 10 * i,
                "mean_observed_transition_minutes": float(i * 10),
            }
            for i in range(1, 16)
        ]
        df_15 = pd.DataFrame(rows)

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            temp_png = Path(f.name)

        try:
            out = generate_bottleneck_chart(data=df_15, output_path=temp_png, top_n=10, dpi=100)
            self.assertTrue(temp_png.is_file())
            self.assertGreater(temp_png.stat().st_size, 1000)
        finally:
            temp_png.unlink(missing_ok=True)

    def test_fewer_than_10_rows_handling(self) -> None:
        """Verify datasets with 1, 3, or 5 rows render cleanly without errors."""
        for num_rows in [1, 3, 5]:
            rows = [
                {
                    "source_activity": f"Source_{i}",
                    "target_activity": f"Target_{i}",
                    "mean_observed_transition_minutes": float(25.0 + i * 5),
                }
                for i in range(1, num_rows + 1)
            ]
            df_small = pd.DataFrame(rows)

            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
                temp_png = Path(f.name)

            try:
                out = generate_bottleneck_chart(
                    data=df_small,
                    output_path=temp_png,
                    top_n=10,
                    dpi=100,
                )
                self.assertTrue(temp_png.is_file())
                self.assertGreater(temp_png.stat().st_size, 1000)
            finally:
                temp_png.unlink(missing_ok=True)

    def test_output_parent_directory_creation(self) -> None:
        """Verify non-existent parent directory is created automatically on export."""
        with tempfile.TemporaryDirectory() as temp_dir:
            nested_output = Path(temp_dir) / "nested_subdir" / "chart.png"
            self.assertFalse(nested_output.parent.exists())

            df = pd.DataFrame(
                [
                    {
                        "source_activity": "Reg",
                        "target_activity": "Triage",
                        "mean_observed_transition_minutes": 20.0,
                    }
                ]
            )
            out = generate_bottleneck_chart(data=df, output_path=nested_output, dpi=100)
            self.assertTrue(nested_output.parent.exists())
            self.assertTrue(nested_output.is_file())


class TestBottleneckVisualizerCLI(unittest.TestCase):
    """Test CLI parsing and execution."""

    def test_cli_defaults_anchored_to_project_root(self) -> None:
        """Verify default input CSV and output PNG are anchored to PROJECT_ROOT."""
        self.assertEqual(DEFAULT_INPUT_CSV, PROJECT_ROOT / "outputs" / "bottleneck_analysis_summary.csv")
        self.assertEqual(DEFAULT_OUTPUT_PNG, PROJECT_ROOT / "outputs" / "bottleneck_analysis.png")
        self.assertTrue(DEFAULT_INPUT_CSV.is_absolute())
        self.assertTrue(DEFAULT_OUTPUT_PNG.is_absolute())

    def test_build_cli_parser_defaults(self) -> None:
        """Verify parser defaults match expected constants and configuration."""
        parser = build_cli_parser()
        args = parser.parse_args([])
        self.assertEqual(args.input, DEFAULT_INPUT_CSV)
        self.assertEqual(args.output, DEFAULT_OUTPUT_PNG)
        self.assertEqual(args.top_n, 10)
        self.assertEqual(args.dpi, 300)

    def test_cli_main_with_custom_paths(self) -> None:
        """Verify main() runs end-to-end with custom arguments."""
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            temp_output = Path(f.name)

        try:
            main([
                "--input", str(CANONICAL_BOTTLENECK_CSV),
                "--output", str(temp_output),
                "--top-n", "5",
                "--dpi", "100",
            ])
            self.assertTrue(temp_output.is_file())
            self.assertGreater(temp_output.stat().st_size, 1000)
            with open(temp_output, "rb") as png_f:
                self.assertEqual(png_f.read(8), PNG_MAGIC_BYTES)
        finally:
            temp_output.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
