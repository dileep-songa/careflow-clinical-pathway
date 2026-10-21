"""Automated validation tests for CareFlow dbt configuration and staging models.

Validates:
1. dbt_project.yml structure and configurations (verifies clean dataset naming).
2. profiles.yml.example BigQuery connection configuration.
3. _sources.yml definition and column tests.
4. _staging_models.yml schema tests and accepted values.
5. stg_hospital_events.sql model syntax, Jinja source references, and defensive WHERE filter.
6. SQL filtering rules against dirty edge-case inputs:
   - Excludes NULL, empty, and whitespace-only Case_IDs.
   - Excludes NULL, empty, and whitespace-only Activity_Names.
   - Excludes NULL and empty Timestamps.
   - Preserves all valid records and legitimate re-triage loop-backs.
7. Logical staging transformation execution against canonical 3,140-row simulated dataset:
   - Verifies 100% preservation of all 500 cases and 3,140 events.
   - Verifies 1-indexed sequential event ordering per case.
   - Verifies inter-activity transition duration calculation.
   - Confirms zero legitimate re-triage loop-backs are dropped.
"""

import csv
from datetime import datetime
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any, Dict, List, Optional
import unittest
import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DBT_DIR = PROJECT_ROOT / "careflow_dbt"
CANONICAL_CSV = PROJECT_ROOT / "data" / "raw" / "hospital_events_simulated.csv"


from src.staging_transform import apply_stg_hospital_events_transformation


class TestDbtConfiguration(unittest.TestCase):
    """Test suite verifying dbt project configuration, schemas, and staging SQL logic."""

    def test_dbt_project_yml_structure(self):
        """Test that dbt_project.yml exists and has clean dataset naming without redundant schema suffix."""
        project_file = DBT_DIR / "dbt_project.yml"
        self.assertTrue(project_file.is_file(), f"Missing {project_file}")

        with open(project_file, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)

        self.assertEqual(cfg.get("name"), "careflow_dbt")
        self.assertEqual(cfg.get("profile"), "careflow_bigquery")
        self.assertEqual(cfg.get("config-version"), 2)
        self.assertIn("models", cfg)
        self.assertIn("careflow_dbt", cfg["models"])
        staging_cfg = cfg["models"]["careflow_dbt"]["staging"]
        self.assertEqual(staging_cfg.get("+materialized"), "view")

        # Confirm +schema: staging was removed so dbt writes directly to target dataset (careflow_staging)
        self.assertNotIn(
            "+schema",
            staging_cfg,
            "Redundant +schema found in staging config. Omit +schema so views write directly to BIGQUERY_DATASET_STAGING.",
        )

    def test_profiles_yml_example(self):
        """Test that profiles.yml.example contains valid BigQuery connection configuration."""
        profile_file = DBT_DIR / "profiles.yml.example"
        self.assertTrue(profile_file.is_file(), f"Missing {profile_file}")

        with open(profile_file, "r", encoding="utf-8") as f:
            profiles = yaml.safe_load(f)

        self.assertIn("careflow_bigquery", profiles)
        bq_prof = profiles["careflow_bigquery"]
        self.assertEqual(bq_prof.get("target"), "dev")
        self.assertIn("dev", bq_prof.get("outputs", {}))
        dev_out = bq_prof["outputs"]["dev"]
        self.assertEqual(dev_out.get("type"), "bigquery")
        self.assertEqual(dev_out.get("method"), "oauth")

    def test_sources_yml_structure(self):
        """Test that _sources.yml declares raw_hospital_data with hospital_events_raw."""
        sources_file = DBT_DIR / "models" / "staging" / "_sources.yml"
        self.assertTrue(sources_file.is_file(), f"Missing {sources_file}")

        with open(sources_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        self.assertIn("sources", data)
        source = data["sources"][0]
        self.assertEqual(source.get("name"), "raw_hospital_data")

        tables = {t["name"]: t for t in source.get("tables", [])}
        self.assertIn("hospital_events_raw", tables)

        raw_tbl = tables["hospital_events_raw"]
        cols = {c["name"]: c for c in raw_tbl.get("columns", [])}
        expected_cols = ["Case_ID", "Activity_Name", "Timestamp", "Department", "Resource", "Data_Type"]

        for col in expected_cols:
            self.assertIn(col, cols, f"Column '{col}' missing from _sources.yml")
            col_tests = [t if isinstance(t, str) else list(t.keys())[0] for t in cols[col].get("tests", [])]
            self.assertIn("not_null", col_tests, f"Column '{col}' must have not_null test")

    def test_staging_models_yml_structure(self):
        """Test that _staging_models.yml defines stg_hospital_events with required tests."""
        models_file = DBT_DIR / "models" / "staging" / "_staging_models.yml"
        self.assertTrue(models_file.is_file(), f"Missing {models_file}")

        with open(models_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        self.assertIn("models", data)
        model = data["models"][0]
        self.assertEqual(model.get("name"), "stg_hospital_events")

        cols = {c["name"]: c for c in model.get("columns", [])}
        required_cols = [
            "case_id",
            "event_sequence",
            "raw_activity_name",
            "activity_name",
            "event_timestamp",
            "event_date",
            "department",
            "resource_id",
            "data_provenance",
        ]

        for col in required_cols:
            self.assertIn(col, cols, f"Column '{col}' missing from stg_hospital_events schema")
            tests = [t if isinstance(t, str) else list(t.keys())[0] for t in cols[col].get("tests", [])]
            self.assertIn("not_null", tests, f"Column '{col}' must have not_null test")

    def test_stg_hospital_events_sql_content_and_defensive_filter(self):
        """Test that stg_hospital_events.sql contains valid Jinja syntax and defensive WHERE filters."""
        sql_file = DBT_DIR / "models" / "staging" / "stg_hospital_events.sql"
        self.assertTrue(sql_file.is_file(), f"Missing {sql_file}")

        sql_content = sql_file.read_text(encoding="utf-8")

        # Source reference
        self.assertIn("{{ source('raw_hospital_data', 'hospital_events_raw') }}", sql_content)

        # Defensive WHERE clause rejecting NULLs, blanks, and whitespace-only strings
        self.assertIn("Case_ID IS NOT NULL", sql_content)
        self.assertIn("TRIM(Case_ID) != ''", sql_content)
        self.assertIn("Activity_Name IS NOT NULL", sql_content)
        self.assertIn("TRIM(Activity_Name) != ''", sql_content)
        self.assertIn("Timestamp IS NOT NULL", sql_content)

        # Confirm redundant schema = 'staging' is not present in model config
        self.assertNotIn("schema = 'staging'", sql_content)

        # Core columns and normalization
        self.assertIn("raw_case_id AS case_id", sql_content)
        self.assertIn("raw_activity_name", sql_content)
        self.assertIn("activity_name", sql_content)
        self.assertIn("event_timestamp", sql_content)
        self.assertIn("DATE(raw_timestamp) AS event_date", sql_content)

        # Window functions
        self.assertIn("ROW_NUMBER() OVER", sql_content)
        self.assertIn("PARTITION BY raw_case_id", sql_content)
        self.assertIn("LAG(raw_activity_name) OVER", sql_content)
        self.assertIn("TIMESTAMP_DIFF", sql_content)

        # Deterministic secondary ordering in window functions and deduplication
        self.assertIn(
            "ORDER BY raw_timestamp ASC, raw_activity_name ASC, raw_resource ASC",
            sql_content,
        )
        self.assertIn(
            "ORDER BY raw_resource ASC, raw_department ASC",
            sql_content,
        )

        # Deduplication guard clause
        self.assertIn("QUALIFY ROW_NUMBER() OVER", sql_content)

    def test_staging_filter_excludes_nulls_blanks_and_whitespace(self):
        """Test that NULL, empty, and whitespace-only records are excluded while preserving valid re-triages."""
        test_records = [
            # Valid case records (including legitimate repeated Triage with different timestamps)
            {
                "Case_ID": "CASE_VALID",
                "Activity_Name": "Registration",
                "Timestamp": "2024-10-01 08:00:00",
                "Department": "ER",
                "Resource": "REG_01",
                "Data_Type": "SIMULATED",
            },
            {
                "Case_ID": "CASE_VALID",
                "Activity_Name": "Triage",
                "Timestamp": "2024-10-01 08:15:00",
                "Department": "ER",
                "Resource": "NURSE_01",
                "Data_Type": "SIMULATED",
            },
            {
                "Case_ID": "CASE_VALID",
                "Activity_Name": "Triage",  # Legitimate re-triage loop-back
                "Timestamp": "2024-10-01 09:15:00",
                "Department": "ER",
                "Resource": "NURSE_02",
                "Data_Type": "SIMULATED",
            },
            # Invalid records that MUST be excluded:
            {"Case_ID": None, "Activity_Name": "Triage", "Timestamp": "2024-10-01 08:00:00"},  # NULL Case_ID
            {"Case_ID": "", "Activity_Name": "Triage", "Timestamp": "2024-10-01 08:00:00"},    # Empty Case_ID
            {"Case_ID": "   ", "Activity_Name": "Triage", "Timestamp": "2024-10-01 08:00:00"}, # Whitespace Case_ID
            {"Case_ID": "CASE_0001", "Activity_Name": None, "Timestamp": "2024-10-01 08:00:00"}, # NULL Activity
            {"Case_ID": "CASE_0001", "Activity_Name": "", "Timestamp": "2024-10-01 08:00:00"},   # Empty Activity
            {"Case_ID": "CASE_0001", "Activity_Name": "  \t  ", "Timestamp": "2024-10-01 08:00:00"}, # Whitespace Activity
            {"Case_ID": "CASE_0001", "Activity_Name": "Triage", "Timestamp": None},             # NULL Timestamp
            {"Case_ID": "CASE_0001", "Activity_Name": "Triage", "Timestamp": ""},               # Empty Timestamp
        ]

        result = apply_stg_hospital_events_transformation(test_records)

        # All 8 invalid records must be excluded
        self.assertEqual(len(result), 3, f"Expected exactly 3 valid records, got {len(result)}")

        # Verify legitimate re-triage loop-back is preserved
        self.assertEqual(result[0]["raw_activity_name"], "Registration")
        self.assertEqual(result[0]["event_sequence"], 1)

        self.assertEqual(result[1]["raw_activity_name"], "Triage")
        self.assertEqual(result[1]["event_sequence"], 2)

        self.assertEqual(result[2]["raw_activity_name"], "Triage")
        self.assertEqual(result[2]["event_sequence"], 3)
        self.assertEqual(result[2]["previous_activity"], "Triage")
        self.assertEqual(result[2]["transition_minutes_from_previous"], 60)

    def test_staging_transformation_logic_against_canonical_dataset(self):
        """Simulate the staging SQL transformation against the canonical CSV and verify results."""
        self.assertTrue(CANONICAL_CSV.is_file(), f"Missing dataset: {CANONICAL_CSV}")

        # Read source events
        raw_events = []
        with open(CANONICAL_CSV, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                raw_events.append(row)

        self.assertEqual(len(raw_events), 3140)

        transformed_rows = apply_stg_hospital_events_transformation(raw_events)

        # Confirm 100% data preservation
        self.assertEqual(len(transformed_rows), 3140)
        unique_cases = {r["case_id"] for r in transformed_rows}
        self.assertEqual(len(unique_cases), 500)

        # Count re-triage loop-backs (all 60 preserved)
        retriage_transitions = [
            r["transition_minutes_from_previous"]
            for r in transformed_rows
            if r["raw_activity_name"] == "Triage" and r["previous_activity"] == "Triage"
        ]

        self.assertEqual(len(retriage_transitions), 60)
        for wait in retriage_transitions:
            self.assertGreaterEqual(wait, 35, "Re-triage bottleneck wait should be >= 35 mins")

        # Count diagnostic review follow-up consultation loop-backs (all 265 preserved)
        consult_after_diagnostic = [
            r["transition_minutes_from_previous"]
            for r in transformed_rows
            if r["raw_activity_name"] == "Consultation"
            and r["previous_activity"] in ("Laboratory", "X-Ray")
        ]
        self.assertEqual(len(consult_after_diagnostic), 265)

        # Confirm 1st events have NULL transition and subsequent have valid transitions
        for r in transformed_rows:
            if r["event_sequence"] == 1:
                self.assertIsNone(r["previous_activity"])
                self.assertIsNone(r["transition_minutes_from_previous"])
            else:
                self.assertIsNotNone(r["previous_activity"])
                self.assertGreaterEqual(r["transition_minutes_from_previous"], 0)

    def test_staging_tie_breaking_determinism_for_simultaneous_timestamps(self):
        """Test that simultaneous events in the same case are ordered deterministically by activity and resource.

        Verifies that regardless of input arrival order, secondary ordering:
        ORDER BY raw_timestamp ASC, raw_activity_name ASC, raw_resource ASC
        produces identical, reproducible event sequences and 0-minute transition durations.
        """
        # Case with Registration at 08:00, then Consultation and Laboratory at identical timestamp 08:30
        order_a = [
            {"Case_ID": "CASE_TIE", "Activity_Name": "Registration", "Timestamp": "2024-10-01 08:00:00", "Department": "ER", "Resource": "REG_01", "Data_Type": "SIMULATED"},
            {"Case_ID": "CASE_TIE", "Activity_Name": "Laboratory", "Timestamp": "2024-10-01 08:30:00", "Department": "Lab", "Resource": "LAB_01", "Data_Type": "SIMULATED"},
            {"Case_ID": "CASE_TIE", "Activity_Name": "Consultation", "Timestamp": "2024-10-01 08:30:00", "Department": "ER", "Resource": "DOC_01", "Data_Type": "SIMULATED"},
        ]
        # Same records in reverse arrival order
        order_b = [
            {"Case_ID": "CASE_TIE", "Activity_Name": "Registration", "Timestamp": "2024-10-01 08:00:00", "Department": "ER", "Resource": "REG_01", "Data_Type": "SIMULATED"},
            {"Case_ID": "CASE_TIE", "Activity_Name": "Consultation", "Timestamp": "2024-10-01 08:30:00", "Department": "ER", "Resource": "DOC_01", "Data_Type": "SIMULATED"},
            {"Case_ID": "CASE_TIE", "Activity_Name": "Laboratory", "Timestamp": "2024-10-01 08:30:00", "Department": "Lab", "Resource": "LAB_01", "Data_Type": "SIMULATED"},
        ]

        res_a = apply_stg_hospital_events_transformation(order_a)
        res_b = apply_stg_hospital_events_transformation(order_b)

        # Output must be identical regardless of input order
        self.assertEqual(res_a, res_b)
        self.assertEqual(len(res_a), 3)

        # Registration is 1st (08:00)
        self.assertEqual(res_a[0]["raw_activity_name"], "Registration")
        self.assertEqual(res_a[0]["event_sequence"], 1)

        # Consultation alphabetically precedes Laboratory ('Consultation' < 'Laboratory')
        self.assertEqual(res_a[1]["raw_activity_name"], "Consultation")
        self.assertEqual(res_a[1]["event_sequence"], 2)
        self.assertEqual(res_a[1]["previous_activity"], "Registration")
        self.assertEqual(res_a[1]["transition_minutes_from_previous"], 30)

        # Laboratory is 3rd with 0-minute duration from simultaneous Consultation
        self.assertEqual(res_a[2]["raw_activity_name"], "Laboratory")
        self.assertEqual(res_a[2]["event_sequence"], 3)
        self.assertEqual(res_a[2]["previous_activity"], "Consultation")
        self.assertEqual(res_a[2]["transition_minutes_from_previous"], 0)

    def test_staging_deduplication_deterministic_row_selection(self):
        """Test that duplicate (Case_ID, Activity_Name, Timestamp) records deterministically pick lowest resource."""
        records = [
            {"Case_ID": "CASE_DEDUP", "Activity_Name": "Triage", "Timestamp": "2024-10-01 08:15:00", "Department": "ER", "Resource": "NURSE_02", "Data_Type": "SIMULATED"},
            {"Case_ID": "CASE_DEDUP", "Activity_Name": "Triage", "Timestamp": "2024-10-01 08:15:00", "Department": "ER", "Resource": "NURSE_01", "Data_Type": "SIMULATED"},
        ]
        result = apply_stg_hospital_events_transformation(records)
        self.assertEqual(len(result), 1)
        # Deterministically selects NURSE_01 because of ORDER BY raw_resource ASC
        self.assertEqual(result[0]["resource_id"], "NURSE_01")

    def test_gitignore_protects_dbt_profiles_and_artifacts(self):
        """Test that .gitignore protects local dbt profile files, build targets, and telemetry artifacts."""
        gitignore_path = PROJECT_ROOT / ".gitignore"
        self.assertTrue(gitignore_path.is_file(), "Missing .gitignore")
        with open(gitignore_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("profiles.yml", content)
        self.assertIn("target/", content)
        self.assertIn("dbt_packages/", content)
        self.assertIn(".user.yml", content)

    def test_dbt_parse_offline_execution(self):
        """Test that dbt parse runs successfully and builds the project manifest offline when dbt is installed."""
        dbt_bin = shutil.which("dbt")
        if not dbt_bin:
            candidate = Path(sys.executable).parent / ("dbt.exe" if sys.platform == "win32" else "dbt")
            if candidate.is_file():
                dbt_bin = str(candidate)

        if not dbt_bin:
            self.skipTest("dbt executable not available in current environment")

        cmd = [
            dbt_bin,
            "parse",
            "--project-dir",
            str(DBT_DIR),
            "--profiles-dir",
            str(DBT_DIR),
        ]
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
        )
        self.assertEqual(
            proc.returncode,
            0,
            f"dbt parse failed with returncode {proc.returncode}.\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}",
        )


if __name__ == "__main__":
    unittest.main()
