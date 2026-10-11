"""Unit tests for CareFlow simulated hospital dataset generation.

Verifies:
1. File creation and path resolution
2. CSV header schema compliance
3. 500 distinct Case_IDs
4. Every record marked SIMULATED
5. Every case has multiple activities
6. Chronological ordering within every case
7. No missing/null values or duplicate records
8. Deterministic reproducibility
9. Valid pathway variations (e.g., repeated Triage visits)
"""

import csv
from datetime import datetime
from pathlib import Path
import sys
import unittest

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import data_generator


class TestSimulatedDatasetGeneration(unittest.TestCase):
    """Test suite for CareFlow Step 2 dataset generator."""

    @classmethod
    def setUpClass(cls):
        """Generate test dataset once for the test suite."""
        cls.test_csv_path = PROJECT_ROOT / "data" / "raw" / "hospital_events_simulated.csv"
        cls.events = data_generator.generate_event_log(num_cases=500, seed=42)
        data_generator.save_event_log_to_csv(cls.events, cls.test_csv_path)

    def test_file_exists_and_non_empty(self):
        """Test that the CSV file exists at the canonical path and has non-zero size."""
        self.assertTrue(self.test_csv_path.is_file(), f"File does not exist: {self.test_csv_path}")
        self.assertGreater(self.test_csv_path.stat().st_size, 0, "File is empty")

    def test_csv_headers(self):
        """Test that the CSV contains the exact required columns in order."""
        expected_columns = [
            "Case_ID",
            "Activity_Name",
            "Timestamp",
            "Department",
            "Resource",
            "Data_Type",
        ]
        with open(self.test_csv_path, mode="r", newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            headers = next(reader)
        self.assertEqual(headers, expected_columns)

    def test_exact_500_distinct_case_ids(self):
        """Test that exactly 500 unique Case_IDs are present."""
        with open(self.test_csv_path, mode="r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            case_ids = {row["Case_ID"] for row in reader}
        self.assertEqual(len(case_ids), 500)

    def test_all_records_marked_simulated(self):
        """Test that every row has Data_Type == 'SIMULATED'."""
        with open(self.test_csv_path, mode="r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row_idx, row in enumerate(reader, start=2):
                self.assertEqual(
                    row["Data_Type"],
                    "SIMULATED",
                    f"Row {row_idx} has non-simulated Data_Type: {row['Data_Type']}",
                )

    def test_multiple_activities_per_case(self):
        """Test that every case has at least 2 activities."""
        case_activity_counts = {}
        with open(self.test_csv_path, mode="r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                case_id = row["Case_ID"]
                case_activity_counts[case_id] = case_activity_counts.get(case_id, 0) + 1

        for case_id, count in case_activity_counts.items():
            self.assertGreaterEqual(
                count,
                2,
                f"Case {case_id} has only {count} activities (expected >= 2)",
            )

    def test_chronological_ordering_within_cases(self):
        """Test that timestamps are valid and strictly increasing within each case."""
        case_timestamps = {}
        with open(self.test_csv_path, mode="r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                case_id = row["Case_ID"]
                ts = datetime.strptime(row["Timestamp"], "%Y-%m-%d %H:%M:%S")
                case_timestamps.setdefault(case_id, []).append(ts)

        for case_id, timestamps in case_timestamps.items():
            for i in range(len(timestamps) - 1):
                self.assertLess(
                    timestamps[i],
                    timestamps[i + 1],
                    f"Case {case_id} timestamps not strictly increasing: "
                    f"{timestamps[i]} >= {timestamps[i+1]}",
                )

    def test_no_missing_or_empty_values(self):
        """Test that no rows contain None, blank, or null values."""
        with open(self.test_csv_path, mode="r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row_idx, row in enumerate(reader, start=2):
                for col, val in row.items():
                    self.assertIsNotNone(val, f"Null value in {col} at row {row_idx}")
                    self.assertTrue(val.strip() != "", f"Empty string in {col} at row {row_idx}")

    def test_no_duplicate_event_records(self):
        """Test that no duplicate event records exist."""
        seen = set()
        with open(self.test_csv_path, mode="r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row_idx, row in enumerate(reader, start=2):
                key = (row["Case_ID"], row["Activity_Name"], row["Timestamp"])
                self.assertNotIn(key, seen, f"Duplicate event at row {row_idx}: {key}")
                seen.add(key)

    def test_reproducibility(self):
        """Test that generating with the same seed produces the identical dataset."""
        reproducible = data_generator.check_reproducibility(
            self.test_csv_path, num_cases=500, seed=42
        )
        self.assertTrue(reproducible, "Dataset is not reproducible with seed=42")

    def test_pathway_variations_and_retriage(self):
        """Test that controlled pathway variations exist, including repeated Triage."""
        case_activities = {}
        with open(self.test_csv_path, mode="r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                case_activities.setdefault(row["Case_ID"], []).append(row["Activity_Name"])

        retriage_cases = 0
        lab_cases = 0
        xray_cases = 0

        for case_id, acts in case_activities.items():
            triage_count = acts.count("Triage")
            if triage_count > 1:
                retriage_cases += 1
            if "Laboratory" in acts:
                lab_cases += 1
            if "X-Ray" in acts:
                xray_cases += 1

        self.assertGreater(retriage_cases, 0, "No repeated Triage visits found")
        self.assertEqual(retriage_cases, 60, "Expected exactly 60 repeated Triage cases")
        self.assertEqual(lab_cases, 185, "Expected exactly 185 cases with Laboratory")
        self.assertEqual(xray_cases, 130, "Expected exactly 130 cases with X-Ray")

    def test_validate_event_log_function(self):
        """Test that the built-in validator returns valid=True with zero issues."""
        res = data_generator.validate_event_log(self.test_csv_path, expected_cases=500)
        self.assertTrue(res["is_valid"], f"Validation failed with issues: {res['issues']}")
        self.assertEqual(len(res["issues"]), 0)


if __name__ == "__main__":
    unittest.main()

