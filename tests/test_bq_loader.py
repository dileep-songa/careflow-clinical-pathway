"""Unit tests for CareFlow BigQuery raw event log loader and validator.

Tests cover:
1. Valid event-log schema validation on canonical dataset.
2. Missing required columns detection.
3. Invalid timestamps and empty/null value detection.
4. Non-existent and 0-byte input handling.
5. Non-simulated Data_Type detection.
6. Offline mode execution without cloud credentials or network access.
7. Confirmation that offline validation does not modify the CSV file.
8. Deterministic/repeatable validation results.
9. BigQueryConfig validation and error handling for missing/placeholder projects.
10. Mocked live-mode BigQuery load execution and load job configuration.
11. Confirmation that offline mode never invokes BigQuery client or API calls.
"""

from datetime import datetime
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

# Ensure src is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import bq_loader


class TestBigQueryLoader(unittest.TestCase):
    """Test suite for CareFlow BigQuery loader and validator."""

    @classmethod
    def setUpClass(cls):
        """Locate canonical simulated dataset."""
        cls.canonical_csv = PROJECT_ROOT / "data" / "raw" / "hospital_events_simulated.csv"

    def test_valid_event_log_schema_on_canonical_file(self):
        """Test that canonical simulated dataset passes all BigQuery schema validation checks."""
        self.assertTrue(self.canonical_csv.is_file(), f"File missing: {self.canonical_csv}")
        result = bq_loader.validate_csv_for_bigquery(self.canonical_csv)

        self.assertTrue(result.is_valid, f"Validation failed with issues: {result.issues}")
        self.assertEqual(result.total_rows, 3140)
        self.assertEqual(result.unique_cases, 500)
        self.assertEqual(len(result.issues), 0)
        self.assertIsNotNone(result.earliest_timestamp)
        self.assertIsNotNone(result.latest_timestamp)
        self.assertIn("Registration", result.activity_distribution)
        self.assertIn("ER", result.department_distribution)

    def test_missing_required_columns(self):
        """Test that missing required columns are caught during validation."""
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".csv", newline="") as tf:
            # Header missing 'Timestamp' and 'Resource'
            tf.write("Case_ID,Activity_Name,Department,Data_Type\n")
            tf.write("CASE_0001,Registration,ER,SIMULATED\n")
            temp_path = Path(tf.name)

        try:
            result = bq_loader.validate_csv_for_bigquery(temp_path)
            self.assertFalse(result.is_valid)
            self.assertTrue(any("Header mismatch" in issue for issue in result.issues))
        finally:
            temp_path.unlink(missing_ok=True)

    def test_invalid_timestamp_format(self):
        """Test that unparseable or corrupted timestamp values fail validation."""
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".csv", newline="") as tf:
            tf.write("Case_ID,Activity_Name,Timestamp,Department,Resource,Data_Type\n")
            tf.write("CASE_0001,Registration,2024-13-45 99:99:99,ER,REG_CLERK_01,SIMULATED\n")
            temp_path = Path(tf.name)

        try:
            result = bq_loader.validate_csv_for_bigquery(temp_path)
            self.assertFalse(result.is_valid)
            self.assertTrue(any("Invalid timestamp" in issue for issue in result.issues))
        finally:
            temp_path.unlink(missing_ok=True)

    def test_empty_values_in_required_columns(self):
        """Test that empty string or blank values fail validation."""
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".csv", newline="") as tf:
            tf.write("Case_ID,Activity_Name,Timestamp,Department,Resource,Data_Type\n")
            tf.write("CASE_0001,,2024-10-01 08:00:00,ER,REG_CLERK_01,SIMULATED\n")
            temp_path = Path(tf.name)

        try:
            result = bq_loader.validate_csv_for_bigquery(temp_path)
            self.assertFalse(result.is_valid)
            self.assertTrue(any("missing or blank" in issue for issue in result.issues))
        finally:
            temp_path.unlink(missing_ok=True)

    def test_non_simulated_data_type(self):
        """Test that records not tagged as SIMULATED are flagged."""
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".csv", newline="") as tf:
            tf.write("Case_ID,Activity_Name,Timestamp,Department,Resource,Data_Type\n")
            tf.write("CASE_0001,Registration,2024-10-01 08:00:00,ER,REG_CLERK_01,UNVERIFIED\n")
            temp_path = Path(tf.name)

        try:
            result = bq_loader.validate_csv_for_bigquery(temp_path)
            self.assertFalse(result.is_valid)
            self.assertTrue(any("Data_Type is 'UNVERIFIED'" in issue for issue in result.issues))
        finally:
            temp_path.unlink(missing_ok=True)

    def test_empty_and_missing_file_handling(self):
        """Test proper handling of missing file and 0-byte file."""
        non_existent = PROJECT_ROOT / "data" / "raw" / "non_existent_file.csv"
        res_missing = bq_loader.validate_csv_for_bigquery(non_existent)
        self.assertFalse(res_missing.is_valid)
        self.assertTrue(any("does not exist" in issue for issue in res_missing.issues))

        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".csv") as tf:
            temp_empty = Path(tf.name)

        try:
            res_empty = bq_loader.validate_csv_for_bigquery(temp_empty)
            self.assertFalse(res_empty.is_valid)
            self.assertTrue(any("empty" in issue for issue in res_empty.issues))
        finally:
            temp_empty.unlink(missing_ok=True)

    def test_offline_mode_does_not_modify_csv(self):
        """Confirm that offline validation is strictly read-only and does not alter the target file."""
        with open(self.canonical_csv, "rb") as f:
            hash_before = hashlib.sha256(f.read()).hexdigest()

        # Run validation multiple times
        result = bq_loader.validate_csv_for_bigquery(self.canonical_csv)
        self.assertTrue(result.is_valid)

        with open(self.canonical_csv, "rb") as f:
            hash_after = hashlib.sha256(f.read()).hexdigest()

        self.assertEqual(hash_before, hash_after, "CSV content was modified during validation")

    def test_repeatable_validation_results(self):
        """Confirm that validation runs produce identical deterministic output."""
        res1 = bq_loader.validate_csv_for_bigquery(self.canonical_csv)
        res2 = bq_loader.validate_csv_for_bigquery(self.canonical_csv)

        self.assertEqual(res1.is_valid, res2.is_valid)
        self.assertEqual(res1.total_rows, res2.total_rows)
        self.assertEqual(res1.unique_cases, res2.unique_cases)
        self.assertEqual(res1.issues, res2.issues)
        self.assertEqual(res1.activity_distribution, res2.activity_distribution)
        self.assertEqual(res1.department_distribution, res2.department_distribution)

    def test_bigquery_config_validation(self):
        """Test BigQueryConfig error handling for missing and invalid parameters."""
        # Empty project
        with self.assertRaises(ValueError) as ctx:
            bq_loader.BigQueryConfig(project_id="").validate()
        self.assertIn("Missing Google Cloud project_id", str(ctx.exception))

        # Placeholder project
        with self.assertRaises(ValueError) as ctx:
            bq_loader.BigQueryConfig(project_id="your-gcp-project-id").validate()
        self.assertIn("Invalid project_id", str(ctx.exception))

        # Empty dataset
        with self.assertRaises(ValueError) as ctx:
            bq_loader.BigQueryConfig(project_id="valid-project", dataset_id="").validate()
        self.assertIn("dataset_id cannot be empty", str(ctx.exception))

        # Invalid write disposition
        with self.assertRaises(ValueError) as ctx:
            bq_loader.BigQueryConfig(
                project_id="valid-project", write_disposition="INVALID_DISPOSITION"
            ).validate()
        self.assertIn("Invalid write_disposition", str(ctx.exception))

    def test_cli_offline_mode_does_not_call_bigquery(self):
        """Test that CLI offline mode runs cleanly and never calls BigQuery."""
        with patch("bq_loader.load_to_bigquery") as mock_load:
            exit_code = bq_loader.main(["--mode", "offline", "--csv", str(self.canonical_csv), "--quiet"])
            self.assertEqual(exit_code, 0)
            mock_load.assert_not_called()

    def test_cli_live_mode_fails_cleanly_without_config(self):
        """Test that CLI live mode without config fails safely with non-zero exit code."""
        with patch.dict("os.environ", {}, clear=True):
            exit_code = bq_loader.main(["--mode", "live", "--csv", str(self.canonical_csv), "--quiet"])
            self.assertEqual(exit_code, 1)

    def test_load_to_bigquery_with_mocked_client(self):
        """Test load_to_bigquery logic, parameters, and return value using a mocked BigQuery client."""
        mock_client = MagicMock()
        mock_job = MagicMock()
        mock_job.job_id = "test-job-id-12345"
        mock_job.output_rows = 3140
        mock_job.result.return_value = None
        mock_client.load_table_from_file.return_value = mock_job

        config = bq_loader.BigQueryConfig(
            project_id="test-healthcare-project",
            dataset_id="careflow_raw",
            table_id="hospital_events_raw",
            write_disposition="WRITE_EMPTY",
        )

        # Mock get_bigquery_schema to avoid needing real google-cloud-bigquery library
        with patch("bq_loader.get_bigquery_schema", return_value=[]):
            with patch.dict(sys.modules, {"google.cloud": MagicMock(), "google.cloud.bigquery": MagicMock()}):
                import google.cloud.bigquery as mock_bq

                mock_bq.SourceFormat.CSV = "CSV"
                mock_bq.WriteDisposition.WRITE_EMPTY = "WRITE_EMPTY"
                mock_bq.CreateDisposition.CREATE_IF_NEEDED = "CREATE_IF_NEEDED"
                mock_bq.LoadJobConfig.return_value = MagicMock()

                summary = bq_loader.load_to_bigquery(
                    csv_path=self.canonical_csv,
                    config=config,
                    client=mock_client,
                )

                self.assertEqual(summary["status"], "SUCCESS")
                self.assertEqual(summary["job_id"], "test-job-id-12345")
                self.assertEqual(summary["destination_table"], "test-healthcare-project.careflow_raw.hospital_events_raw")
                self.assertEqual(summary["rows_validated"], 3140)
                self.assertEqual(summary["unique_cases"], 500)
                mock_client.load_table_from_file.assert_called_once()
                mock_job.result.assert_called_once()


if __name__ == "__main__":
    unittest.main()

