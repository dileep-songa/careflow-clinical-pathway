"""Automated test suite for CareFlow offline process mining module (src/process_miner.py).

Validates:
1. Column schema and non-null validation.
2. Handling of missing files, empty files, and malformed timestamps.
3. Event and case counts against canonical baseline dataset.
4. Activity frequencies against canonical baseline dataset.
5. Exact hand-calculated transition counts and observed transition durations on tiny fixture.
6. Case duration statistics and pathway variant extraction.
7. PM4Py event log conversion and Directly-Follows Graph (DFG) discovery.
8. Preservation and immutability of the baseline CSV file.
9. Export of summary tables to CSV/JSON and graceful Graphviz fallback.
"""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path
import tempfile
from typing import Dict, List
import unittest

import pandas as pd
import pm4py

from src.process_miner import (
    REQUIRED_COLUMNS,
    build_transition_summary_table,
    calculate_activity_frequencies,
    calculate_case_duration_statistics,
    convert_to_pm4py_event_log,
    discover_directly_follows_graph,
    extract_pathway_variants,
    load_event_log,
    render_dfg_visualization,
    run_process_mining_pipeline,
    validate_event_log_dataframe,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CANONICAL_CSV = PROJECT_ROOT / "data" / "raw" / "hospital_events_simulated.csv"
CANONICAL_MD5 = "d8de55d0fccd116b3482c4c05a681d9e"
CANONICAL_SIZE = 197844
CANONICAL_ROWS = 3140
CANONICAL_CASES = 500


class TestProcessMinerValidationAndErrors(unittest.TestCase):
    """Test defensive validation, error handling, and schema checking."""

    def test_missing_file_raises_error(self) -> None:
        """Verify FileNotFoundError is raised for non-existent CSV path."""
        non_existent = PROJECT_ROOT / "data" / "raw" / "non_existent_file.csv"
        with self.assertRaises(FileNotFoundError):
            load_event_log(non_existent)

    def test_empty_file_raises_error(self) -> None:
        """Verify ValueError is raised for empty 0-byte file."""
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            temp_path = Path(f.name)
        try:
            with self.assertRaises(ValueError) as ctx:
                load_event_log(temp_path)
            self.assertIn("empty", str(ctx.exception).lower())
        finally:
            temp_path.unlink(missing_ok=True)

    def test_missing_required_columns_raises_error(self) -> None:
        """Verify ValueError is raised if any required columns are missing."""
        df_invalid = pd.DataFrame(
            {
                "Case_ID": ["CASE_0001"],
                "Activity_Name": ["Registration"],
                "Timestamp": ["2024-10-01 10:00:00"],
                # Missing Department, Resource, Data_Type
            }
        )
        with self.assertRaises(ValueError) as ctx:
            validate_event_log_dataframe(df_invalid)
        self.assertIn("missing required columns", str(ctx.exception).lower())

    def test_empty_dataframe_raises_error(self) -> None:
        """Verify ValueError is raised if DataFrame has 0 rows."""
        df_empty = pd.DataFrame(columns=REQUIRED_COLUMNS)
        with self.assertRaises(ValueError) as ctx:
            validate_event_log_dataframe(df_empty)
        self.assertIn("zero records", str(ctx.exception).lower())

    def test_empty_or_whitespace_values_raise_error(self) -> None:
        """Verify ValueError is raised when required columns contain blanks or spaces."""
        df_blank = pd.DataFrame(
            {
                "Case_ID": ["CASE_0001", "   "],
                "Activity_Name": ["Registration", "Triage"],
                "Timestamp": ["2024-10-01 10:00:00", "2024-10-01 10:15:00"],
                "Department": ["Emergency", "Emergency"],
                "Resource": ["NURSE_01", "NURSE_02"],
                "Data_Type": ["SIMULATED", "SIMULATED"],
            }
        )
        with self.assertRaises(ValueError) as ctx:
            validate_event_log_dataframe(df_blank)
        self.assertIn("empty or whitespace", str(ctx.exception).lower())

    def test_invalid_timestamp_format_raises_error(self) -> None:
        """Verify ValueError is raised if timestamp string does not conform to format."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="") as f:
            writer = csv.writer(f)
            writer.writerow(REQUIRED_COLUMNS)
            writer.writerow(["C1", "Registration", "invalid-date-format", "ER", "R1", "SIMULATED"])
            temp_path = Path(f.name)
        try:
            with self.assertRaises(ValueError) as ctx:
                load_event_log(temp_path)
            self.assertIn("failed to parse timestamp", str(ctx.exception).lower())
        finally:
            temp_path.unlink(missing_ok=True)


class TestProcessMinerHandcraftedDataset(unittest.TestCase):
    """Test process-mining metrics and DFG calculations against hand-calculated fixture."""

    @classmethod
    def setUpClass(cls) -> None:
        """Create a handcrafted 2-case, 11-event synthetic dataset with known answers."""
        cls.temp_file = tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="")
        writer = csv.writer(cls.temp_file)
        writer.writerow(REQUIRED_COLUMNS)

        # Case C1 (5 events, duration = 120 mins):
        # Registration (10:00) -> Triage (10:20, +20m) -> Consultation (10:50, +30m)
        # -> Treatment (11:30, +40m) -> Discharge (12:00, +30m)
        writer.writerow(["C1", "Registration", "2024-10-01 10:00:00", "ER", "R1", "SIMULATED"])
        writer.writerow(["C1", "Triage", "2024-10-01 10:20:00", "ER", "R2", "SIMULATED"])
        writer.writerow(["C1", "Consultation", "2024-10-01 10:50:00", "ER", "R3", "SIMULATED"])
        writer.writerow(["C1", "Treatment", "2024-10-01 11:30:00", "ER", "R4", "SIMULATED"])
        writer.writerow(["C1", "Discharge", "2024-10-01 12:00:00", "ER", "R5", "SIMULATED"])

        # Case C2 (6 events, includes re-triage loop, duration = 180 mins):
        # Registration (10:05) -> Triage (10:35, +30m) -> Triage (10:55, +20m)
        # -> Consultation (11:25, +30m) -> Treatment (12:05, +40m) -> Discharge (13:05, +60m)
        writer.writerow(["C2", "Registration", "2024-10-01 10:05:00", "ER", "R1", "SIMULATED"])
        writer.writerow(["C2", "Triage", "2024-10-01 10:35:00", "ER", "R2", "SIMULATED"])
        writer.writerow(["C2", "Triage", "2024-10-01 10:55:00", "ER", "R2", "SIMULATED"])
        writer.writerow(["C2", "Consultation", "2024-10-01 11:25:00", "ER", "R3", "SIMULATED"])
        writer.writerow(["C2", "Treatment", "2024-10-01 12:05:00", "ER", "R4", "SIMULATED"])
        writer.writerow(["C2", "Discharge", "2024-10-01 13:05:00", "ER", "R5", "SIMULATED"])

        cls.temp_file.close()
        cls.fixture_path = Path(cls.temp_file.name)

    @classmethod
    def tearDownClass(cls) -> None:
        """Clean up temporary test file."""
        cls.fixture_path.unlink(missing_ok=True)

    def test_handcrafted_load_and_sorting(self) -> None:
        """Verify handcrafted dataset loads exactly 11 events across 2 cases."""
        df = load_event_log(self.fixture_path)
        self.assertEqual(len(df), 11)
        self.assertEqual(df["Case_ID"].nunique(), 2)

    def test_handcrafted_activity_frequencies(self) -> None:
        """Verify activity frequencies match known counts."""
        df = load_event_log(self.fixture_path)
        freqs = calculate_activity_frequencies(df)
        expected = {
            "Triage": 3,
            "Registration": 2,
            "Consultation": 2,
            "Treatment": 2,
            "Discharge": 2,
        }
        self.assertEqual(freqs, expected)

    def test_handcrafted_case_duration_statistics(self) -> None:
        """Verify case duration statistics: C1=120m, C2=180m -> Mean=150m, Median=150m."""
        df = load_event_log(self.fixture_path)
        stats = calculate_case_duration_statistics(df)
        self.assertEqual(stats["min_minutes"], 120.0)
        self.assertEqual(stats["max_minutes"], 180.0)
        self.assertEqual(stats["mean_minutes"], 150.0)
        self.assertEqual(stats["median_minutes"], 150.0)
        self.assertEqual(stats["std_minutes"], 42.43)

    def test_handcrafted_pathway_variants(self) -> None:
        """Verify exactly 2 variants are discovered (1 per case = 50% each)."""
        df = load_event_log(self.fixture_path)
        log = convert_to_pm4py_event_log(df)
        variants = extract_pathway_variants(log)
        self.assertEqual(len(variants), 2)
        v1, v2 = variants[0], variants[1]
        self.assertEqual(v1["case_count"], 1)
        self.assertEqual(v1["percentage"], 50.0)
        self.assertEqual(v2["case_count"], 1)
        self.assertEqual(v2["percentage"], 50.0)

    def test_handcrafted_dfg_transitions_and_observed_times(self) -> None:
        """Verify DFG transition frequencies and mean/median observed transition durations."""
        df = load_event_log(self.fixture_path)
        log = convert_to_pm4py_event_log(df)
        dfg_freq, dfg_perf, start_acts, end_acts = discover_directly_follows_graph(log)

        # Start and end
        self.assertEqual(start_acts, {"Registration": 2})
        self.assertEqual(end_acts, {"Discharge": 2})

        # Transition frequencies
        self.assertEqual(dfg_freq[("Registration", "Triage")], 2)
        self.assertEqual(dfg_freq[("Triage", "Triage")], 1)
        self.assertEqual(dfg_freq[("Triage", "Consultation")], 2)
        self.assertEqual(dfg_freq[("Consultation", "Treatment")], 2)
        self.assertEqual(dfg_freq[("Treatment", "Discharge")], 2)

        # Tabular summary inspection
        df_table = build_transition_summary_table(dfg_freq, dfg_perf)
        self.assertEqual(len(df_table), 5)

        # Registration -> Triage: C1=20m, C2=30m -> Mean = 25.0m, Median = 25.0m
        reg_triage = df_table[
            (df_table["source_activity"] == "Registration")
            & (df_table["target_activity"] == "Triage")
        ].iloc[0]
        self.assertEqual(reg_triage["transition_count"], 2)
        self.assertEqual(reg_triage["mean_observed_transition_minutes"], 25.0)
        self.assertEqual(reg_triage["median_observed_transition_minutes"], 25.0)
        self.assertEqual(reg_triage["min_observed_transition_minutes"], 20.0)
        self.assertEqual(reg_triage["max_observed_transition_minutes"], 30.0)

        # Triage -> Triage (re-triage loop): C2=20m
        retriage = df_table[
            (df_table["source_activity"] == "Triage")
            & (df_table["target_activity"] == "Triage")
        ].iloc[0]
        self.assertEqual(retriage["transition_count"], 1)
        self.assertEqual(retriage["mean_observed_transition_minutes"], 20.0)


class TestProcessMinerCanonicalDataset(unittest.TestCase):
    """Test process-mining execution against the full canonical baseline dataset."""

    @classmethod
    def setUpClass(cls) -> None:
        """Verify canonical dataset exists before testing."""
        if not CANONICAL_CSV.is_file():
            raise unittest.SkipTest(f"Canonical dataset missing at {CANONICAL_CSV}")

    def test_canonical_event_and_case_counts(self) -> None:
        """Verify canonical baseline contains exactly 3,140 events across 500 cases."""
        df = load_event_log(CANONICAL_CSV)
        self.assertEqual(len(df), CANONICAL_ROWS)
        self.assertEqual(df["Case_ID"].nunique(), CANONICAL_CASES)

    def test_canonical_activity_frequencies(self) -> None:
        """Verify activity frequencies match known distributions."""
        df = load_event_log(CANONICAL_CSV)
        freqs = calculate_activity_frequencies(df)
        expected = {
            "Consultation": 765,
            "Triage": 560,
            "Registration": 500,
            "Treatment": 500,
            "Discharge": 500,
            "Laboratory": 185,
            "X-Ray": 130,
        }
        self.assertEqual(freqs, expected)

    def test_canonical_start_and_end_activities(self) -> None:
        """Verify all 500 cases start with Registration and end with Discharge."""
        df = load_event_log(CANONICAL_CSV)
        log = convert_to_pm4py_event_log(df)
        _, _, start_acts, end_acts = discover_directly_follows_graph(log)
        self.assertEqual(start_acts, {"Registration": 500})
        self.assertEqual(end_acts, {"Discharge": 500})

    def test_canonical_pathway_variants(self) -> None:
        """Verify discovery of exactly 6 unique pathway variants summing to 500 cases."""
        df = load_event_log(CANONICAL_CSV)
        log = convert_to_pm4py_event_log(df)
        variants = extract_pathway_variants(log)
        self.assertEqual(len(variants), 6)

        total_cases = sum(v["case_count"] for v in variants)
        self.assertEqual(total_cases, 500)

        # Standard straight-through pathway is top variant (200 cases / 40.0%)
        top_v = variants[0]
        self.assertEqual(
            top_v["pathway_str"],
            "Registration -> Triage -> Consultation -> Treatment -> Discharge",
        )
        self.assertEqual(top_v["case_count"], 200)
        self.assertEqual(top_v["percentage"], 40.0)

    def test_canonical_observed_duration_statistics(self) -> None:
        """Verify observed duration bounds and mean values."""
        df = load_event_log(CANONICAL_CSV)
        stats = calculate_case_duration_statistics(df)
        self.assertEqual(stats["min_minutes"], 95.0)
        self.assertEqual(stats["max_minutes"], 354.0)
        self.assertEqual(stats["mean_minutes"], 202.54)
        self.assertEqual(stats["median_minutes"], 211.0)
        self.assertEqual(stats["std_minutes"], 62.44)

    def test_canonical_baseline_csv_remains_unmodified(self) -> None:
        """Verify canonical dataset byte size and MD5 hash remain completely identical."""
        self.assertTrue(CANONICAL_CSV.is_file())
        current_size = CANONICAL_CSV.stat().st_size
        with open(CANONICAL_CSV, "rb") as f:
            current_md5 = hashlib.md5(f.read()).hexdigest()

        self.assertEqual(current_size, CANONICAL_SIZE)
        self.assertEqual(current_md5, CANONICAL_MD5)


class TestProcessMinerOutputsAndRendering(unittest.TestCase):
    """Test output file generation and graceful degradation."""

    def test_pipeline_export_to_output_directory(self) -> None:
        """Verify pipeline exports transition CSV, variants CSV, and summary JSON."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            results = run_process_mining_pipeline(CANONICAL_CSV, output_dir=tmp_dir)
            out_files = results["exported_files"]

            self.assertIn("transitions_csv", out_files)
            self.assertIn("variants_csv", out_files)
            self.assertIn("summary_json", out_files)

            self.assertTrue(Path(out_files["transitions_csv"]).is_file())
            self.assertTrue(Path(out_files["variants_csv"]).is_file())
            self.assertTrue(Path(out_files["summary_json"]).is_file())

            # Read back transitions CSV to ensure validity
            df_trans = pd.read_csv(out_files["transitions_csv"])
            self.assertGreater(len(df_trans), 0)
            self.assertIn("mean_observed_transition_minutes", df_trans.columns)

    def test_graceful_graphviz_missing_handling(self) -> None:
        """Verify render_dfg_visualization handles missing Graphviz binary gracefully without raising."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_img = Path(tmp_dir) / "test_dfg.png"
            result = render_dfg_visualization(
                dfg_frequency={("A", "B"): 1},
                start_activities={"A": 1},
                end_activities={"B": 1},
                output_path=out_img,
            )
            # If dot is not in PATH, result is None; if dot is installed, it returns Path
            self.assertTrue(result is None or isinstance(result, Path))


if __name__ == "__main__":
    unittest.main()
