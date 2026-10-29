"""Automated test suite for CareFlow Patient Pathway Conformance Checking module.

Validates:
1. Input validation & error handling: missing file, empty file, empty DataFrame,
   missing required columns, null keys, and invalid timestamps.
2. Rule evaluation on standard and alternative valid clinical pathways (Variants 1-4).
3. Repeated triage audit flagging (Variants 5-6) as review candidates (not errors).
4. Detection of missing expected activities (e.g., missing Treatment, missing Registration).
5. Detection of unexpected activity ordering (e.g., Treatment before Consultation).
6. Diagnostic follow-up rules (unreviewed tests, unprompted diagnostic orders).
7. Duplicate event detection (repeated single-milestone events, identical timestamps).
8. Distinction between cases evaluated, cases flagged, total deviations, and individual rule counts.
9. Configurable rule parameters (e.g., toggling repeated triage audit).
10. Deterministic execution and verification against canonical dataset.
11. Proper output generation (case results CSV, findings summary JSON, and findings Markdown).
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
import tempfile
import unittest

import pandas as pd

from src.conformance_checker import (
    DEFAULT_CASE_RESULTS_CSV,
    DEFAULT_FINDINGS_MD,
    DEFAULT_INPUT_PATH,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_SUMMARY_JSON,
    PROJECT_ROOT,
    CaseConformanceResult,
    ConformanceRuleConfig,
    ConformanceSummary,
    RuleDeviation,
    RuleIdentifier,
    build_cli_parser,
    evaluate_case_conformance,
    export_conformance_outputs,
    load_and_validate_event_log,
    main,
    run_conformance_checking,
)


class TestConformanceCheckerValidation(unittest.TestCase):
    """Test input defensive validation, schema enforcement, and error handling."""

    def test_missing_file_raises_error(self) -> None:
        """Verify FileNotFoundError is raised when input file does not exist."""
        non_existent = PROJECT_ROOT / "data" / "cleaned" / "does_not_exist.csv"
        with self.assertRaises(FileNotFoundError):
            load_and_validate_event_log(non_existent)

    def test_empty_file_raises_error(self) -> None:
        """Verify ValueError is raised for 0-byte input file."""
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            temp_path = Path(f.name)
        try:
            with self.assertRaises(ValueError) as ctx:
                load_and_validate_event_log(temp_path)
            self.assertIn("empty", str(ctx.exception).lower())
        finally:
            temp_path.unlink(missing_ok=True)

    def test_empty_dataframe_raises_error(self) -> None:
        """Verify ValueError is raised if DataFrame contains zero records."""
        df_empty = pd.DataFrame(columns=["case_id", "activity_name", "event_timestamp"])
        with self.assertRaises(ValueError) as ctx:
            load_and_validate_event_log(df_empty)
        self.assertIn("zero records", str(ctx.exception).lower())

    def test_missing_required_columns_raises_error(self) -> None:
        """Verify ValueError is raised when required columns are absent."""
        df_missing = pd.DataFrame(
            {
                "case_id": ["CASE_0001"],
                "activity_name": ["Registration"],
                # Missing event_timestamp
            }
        )
        with self.assertRaises(ValueError) as ctx:
            load_and_validate_event_log(df_missing)
        self.assertIn("missing required columns", str(ctx.exception).lower())

    def test_null_or_empty_case_id_raises_error(self) -> None:
        """Verify ValueError is raised if case_id contains nulls or empty whitespace."""
        df_null = pd.DataFrame(
            {
                "case_id": [None, "CASE_0002"],
                "activity_name": ["Registration", "Registration"],
                "event_timestamp": ["2024-10-01 10:00:00", "2024-10-01 10:15:00"],
            }
        )
        with self.assertRaises(ValueError) as ctx:
            load_and_validate_event_log(df_null)
        self.assertIn("null or nan case_id", str(ctx.exception).lower())

        df_blank = pd.DataFrame(
            {
                "case_id": ["   ", "CASE_0002"],
                "activity_name": ["Registration", "Registration"],
                "event_timestamp": ["2024-10-01 10:00:00", "2024-10-01 10:15:00"],
            }
        )
        with self.assertRaises(ValueError) as ctx:
            load_and_validate_event_log(df_blank)
        self.assertIn("empty or whitespace case_id", str(ctx.exception).lower())

    def test_null_or_empty_activity_raises_error(self) -> None:
        """Verify ValueError is raised if activity contains nulls or empty whitespace."""
        df_null = pd.DataFrame(
            {
                "case_id": ["CASE_0001"],
                "activity_name": [None],
                "event_timestamp": ["2024-10-01 10:00:00"],
            }
        )
        with self.assertRaises(ValueError) as ctx:
            load_and_validate_event_log(df_null)
        self.assertIn("null or nan activity", str(ctx.exception).lower())

    def test_invalid_timestamp_raises_error(self) -> None:
        """Verify ValueError is raised when timestamp string fails parsing."""
        df_bad_ts = pd.DataFrame(
            {
                "case_id": ["CASE_0001"],
                "activity_name": ["Registration"],
                "event_timestamp": ["not_a_valid_timestamp_string"],
            }
        )
        with self.assertRaises(ValueError) as ctx:
            load_and_validate_event_log(df_bad_ts)
        self.assertIn("invalid timestamp", str(ctx.exception).lower())


class TestConformanceRuleEvaluation(unittest.TestCase):
    """Test case-level evaluation across valid pathways, re-triages, and synthetic anomalies."""

    def setUp(self) -> None:
        self.default_config = ConformanceRuleConfig()

    def _make_events(self, activities: list[str]) -> list[dict]:
        """Helper to create dummy event records with incrementing timestamps."""
        base_time = pd.Timestamp("2024-10-01 08:00:00")
        return [
            {
                "case_id": "TEST_CASE",
                "activity_name": act,
                "event_timestamp": base_time + pd.Timedelta(minutes=i * 15),
                "event_sequence": i + 1,
            }
            for i, act in enumerate(activities)
        ]

    def test_normal_pathway_variant_1_conformant(self) -> None:
        """Verify Variant 1 (standard pathway) is 100% conformant with 0 deviations."""
        events = self._make_events(
            ["Registration", "Triage", "Consultation", "Treatment", "Discharge"]
        )
        res = evaluate_case_conformance("C1", events, self.default_config)
        self.assertTrue(res.is_conformant)
        self.assertEqual(res.status, "CONFORMANT")
        self.assertEqual(res.total_deviations, 0)
        self.assertEqual(res.rule_ids, "NONE")
        self.assertIn("Conformant", res.review_reasons)

    def test_alternative_valid_pathways_variants_2_3_4_conformant(self) -> None:
        """Verify diagnostic pathways (Variants 2, 3, 4) are recognized as fully conformant."""
        # Variant 2: Laboratory
        v2_events = self._make_events(
            ["Registration", "Triage", "Consultation", "Laboratory", "Consultation", "Treatment", "Discharge"]
        )
        v2_res = evaluate_case_conformance("C2", v2_events, self.default_config)
        self.assertTrue(v2_res.is_conformant, "Variant 2 should be conformant")
        self.assertEqual(v2_res.status, "CONFORMANT")

        # Variant 3: X-Ray
        v3_events = self._make_events(
            ["Registration", "Triage", "Consultation", "X-Ray", "Consultation", "Treatment", "Discharge"]
        )
        v3_res = evaluate_case_conformance("C3", v3_events, self.default_config)
        self.assertTrue(v3_res.is_conformant, "Variant 3 should be conformant")
        self.assertEqual(v3_res.status, "CONFORMANT")

        # Variant 4: Laboratory + X-Ray multi-diagnostic
        v4_events = self._make_events(
            ["Registration", "Triage", "Consultation", "Laboratory", "X-Ray", "Consultation", "Treatment", "Discharge"]
        )
        v4_res = evaluate_case_conformance("C4", v4_events, self.default_config)
        self.assertTrue(v4_res.is_conformant, "Variant 4 should be conformant")
        self.assertEqual(v4_res.status, "CONFORMANT")

    def test_repeated_triage_flagged_as_review_candidate(self) -> None:
        """Verify Variant 5 (re-triage) triggers RULE_REPEATED_TRIAGE as review candidate."""
        v5_events = self._make_events(
            ["Registration", "Triage", "Triage", "Consultation", "Treatment", "Discharge"]
        )
        res = evaluate_case_conformance("C5", v5_events, self.default_config)
        self.assertFalse(res.is_conformant)
        self.assertEqual(res.status, "REVIEW_CANDIDATE")
        self.assertEqual(res.total_deviations, 1)
        self.assertEqual(res.rule_ids, RuleIdentifier.REPEATED_TRIAGE)
        self.assertIn("repeated triage", res.review_reasons.lower())
        self.assertIn("review candidate", res.review_reasons.lower())
        # Confirm it is NOT called an error
        self.assertNotIn("error", res.review_reasons.lower())

    def test_missing_expected_activities(self) -> None:
        """Verify missing mandatory activities trigger RULE_MANDATORY_ACTIVITIES."""
        # Missing Treatment
        no_treatment = self._make_events(["Registration", "Triage", "Consultation", "Discharge"])
        res1 = evaluate_case_conformance("C_NO_TX", no_treatment, self.default_config)
        self.assertFalse(res1.is_conformant)
        self.assertIn(RuleIdentifier.MANDATORY_ACTIVITIES, res1.rule_ids)
        self.assertIn("Treatment", res1.review_reasons)

        # Missing Registration (also violates expected start)
        no_reg = self._make_events(["Triage", "Consultation", "Treatment", "Discharge"])
        res2 = evaluate_case_conformance("C_NO_REG", no_reg, self.default_config)
        self.assertFalse(res2.is_conformant)
        self.assertIn(RuleIdentifier.MANDATORY_ACTIVITIES, res2.rule_ids)
        self.assertIn(RuleIdentifier.START_ACTIVITY, res2.rule_ids)

    def test_unexpected_activity_ordering(self) -> None:
        """Verify inverted activity temporal sequences trigger RULE_ACTIVITY_ORDER."""
        # Treatment before Consultation
        tx_first = self._make_events(
            ["Registration", "Triage", "Treatment", "Consultation", "Discharge"]
        )
        res = evaluate_case_conformance("C_ORDER", tx_first, self.default_config)
        self.assertFalse(res.is_conformant)
        self.assertIn(RuleIdentifier.ACTIVITY_ORDER, res.rule_ids)
        self.assertIn("after Treatment", res.review_reasons)

    def test_diagnostic_without_subsequent_consultation_review(self) -> None:
        """Verify diagnostic performed without follow-up Consultation triggers RULE_DIAGNOSTIC_FOLLOWUP."""
        # Laboratory directly followed by Treatment without follow-up Consultation
        no_review = self._make_events(
            ["Registration", "Triage", "Consultation", "Laboratory", "Treatment", "Discharge"]
        )
        res = evaluate_case_conformance("C_NO_REV", no_review, self.default_config)
        self.assertFalse(res.is_conformant)
        self.assertIn(RuleIdentifier.DIAGNOSTIC_FOLLOWUP, res.rule_ids)
        self.assertIn("not followed by physician Consultation review", res.review_reasons)

        # Treatment performed after diagnostic before follow-up Consultation
        treatment_before_review = self._make_events(
            ["Registration", "Triage", "Consultation", "Laboratory", "Treatment", "Consultation", "Discharge"]
        )
        res2 = evaluate_case_conformance("C_TREAT_BEFORE_REV", treatment_before_review, self.default_config)
        self.assertFalse(res2.is_conformant)
        self.assertIn(RuleIdentifier.DIAGNOSTIC_FOLLOWUP, res2.rule_ids)
        self.assertIn("prior to follow-up Consultation review", res2.review_reasons)

    def test_diagnostic_without_initial_physician_consultation(self) -> None:
        """Verify diagnostic performed before initial physician Consultation triggers RULE_DIAGNOSTIC_FOLLOWUP."""
        # Laboratory performed before Consultation
        no_initial_consult = self._make_events(
            ["Registration", "Triage", "Laboratory", "Consultation", "Treatment", "Discharge"]
        )
        res = evaluate_case_conformance("C_NO_INIT", no_initial_consult, self.default_config)
        self.assertFalse(res.is_conformant)
        self.assertIn(RuleIdentifier.DIAGNOSTIC_FOLLOWUP, res.rule_ids)
        self.assertIn("without prior physician Consultation", res.review_reasons)

    def test_duplicate_events_detection(self) -> None:
        """Verify duplicate single-milestone activities and identical timestamps trigger RULE_DUPLICATE_EVENTS."""
        # Multiple Registrations
        multi_reg = self._make_events(
            ["Registration", "Registration", "Triage", "Consultation", "Treatment", "Discharge"]
        )
        res1 = evaluate_case_conformance("C_DUP_REG", multi_reg, self.default_config)
        self.assertFalse(res1.is_conformant)
        self.assertIn(RuleIdentifier.DUPLICATE_EVENTS, res1.rule_ids)
        self.assertIn("Registration", res1.review_reasons)

        # Identical timestamp duplicate
        ts = pd.Timestamp("2024-10-01 10:00:00")
        same_ts_events = [
            {"activity_name": "Registration", "event_timestamp": ts},
            {"activity_name": "Triage", "event_timestamp": ts + pd.Timedelta(minutes=15)},
            {"activity_name": "Consultation", "event_timestamp": ts + pd.Timedelta(minutes=30)},
            {"activity_name": "Treatment", "event_timestamp": ts + pd.Timedelta(minutes=45)},
            {"activity_name": "Treatment", "event_timestamp": ts + pd.Timedelta(minutes=45)},  # duplicate
            {"activity_name": "Discharge", "event_timestamp": ts + pd.Timedelta(minutes=60)},
        ]
        res2 = evaluate_case_conformance("C_SAME_TS", same_ts_events, self.default_config)
        self.assertFalse(res2.is_conformant)
        self.assertIn(RuleIdentifier.DUPLICATE_EVENTS, res2.rule_ids)
        self.assertIn("Exact duplicate event", res2.review_reasons)


class TestConformanceConfigurabilityAndCounts(unittest.TestCase):
    """Test rule configurability and distinct counting of cases vs violations."""

    def test_configurable_disable_repeated_triage(self) -> None:
        """Verify disabling flag_repeated_triage allows re-triage encounters to pass as conformant."""
        config_no_retriage_flag = ConformanceRuleConfig(flag_repeated_triage=False)
        events = [
            {"activity_name": "Registration", "event_timestamp": pd.Timestamp("2024-10-01 08:00:00")},
            {"activity_name": "Triage", "event_timestamp": pd.Timestamp("2024-10-01 08:15:00")},
            {"activity_name": "Triage", "event_timestamp": pd.Timestamp("2024-10-01 08:30:00")},
            {"activity_name": "Consultation", "event_timestamp": pd.Timestamp("2024-10-01 09:00:00")},
            {"activity_name": "Treatment", "event_timestamp": pd.Timestamp("2024-10-01 09:30:00")},
            {"activity_name": "Discharge", "event_timestamp": pd.Timestamp("2024-10-01 10:00:00")},
        ]
        res = evaluate_case_conformance("C_CONFIG", events, config_no_retriage_flag)
        self.assertTrue(res.is_conformant)
        self.assertEqual(res.status, "CONFORMANT")
        self.assertEqual(res.total_deviations, 0)

    def test_distinction_cases_flagged_vs_total_deviations(self) -> None:
        """Verify that cases flagged count and total rule violations count are clearly distinguished."""
        # Construct small fixture: 3 cases
        # Case 1: 0 deviations (Conformant)
        # Case 2: 1 deviation (Repeat Triage)
        # Case 3: 3 deviations (Missing Treatment, Out-of-order, Duplicate Registration)
        rows = [
            # Case 1 (Conformant)
            {"case_id": "C1", "activity_name": "Registration", "event_timestamp": "2024-10-01 08:00:00"},
            {"case_id": "C1", "activity_name": "Triage", "event_timestamp": "2024-10-01 08:15:00"},
            {"case_id": "C1", "activity_name": "Consultation", "event_timestamp": "2024-10-01 08:30:00"},
            {"case_id": "C1", "activity_name": "Treatment", "event_timestamp": "2024-10-01 09:00:00"},
            {"case_id": "C1", "activity_name": "Discharge", "event_timestamp": "2024-10-01 09:30:00"},
            # Case 2 (1 deviation)
            {"case_id": "C2", "activity_name": "Registration", "event_timestamp": "2024-10-01 08:00:00"},
            {"case_id": "C2", "activity_name": "Triage", "event_timestamp": "2024-10-01 08:15:00"},
            {"case_id": "C2", "activity_name": "Triage", "event_timestamp": "2024-10-01 08:30:00"},
            {"case_id": "C2", "activity_name": "Consultation", "event_timestamp": "2024-10-01 09:00:00"},
            {"case_id": "C2", "activity_name": "Treatment", "event_timestamp": "2024-10-01 09:30:00"},
            {"case_id": "C2", "activity_name": "Discharge", "event_timestamp": "2024-10-01 10:00:00"},
            # Case 3 (Multiple deviations)
            {"case_id": "C3", "activity_name": "Registration", "event_timestamp": "2024-10-01 08:00:00"},
            {"case_id": "C3", "activity_name": "Registration", "event_timestamp": "2024-10-01 08:05:00"},  # duplicate
            {"case_id": "C3", "activity_name": "Consultation", "event_timestamp": "2024-10-01 08:15:00"},  # consult before triage
            {"case_id": "C3", "activity_name": "Triage", "event_timestamp": "2024-10-01 08:30:00"},
            {"case_id": "C3", "activity_name": "Discharge", "event_timestamp": "2024-10-01 09:00:00"},  # missing Treatment
        ]
        df_fixture = pd.DataFrame(rows)
        summary = run_conformance_checking(df_fixture)

        # Exact distinction assertions:
        self.assertEqual(summary.total_cases_evaluated, 3)
        self.assertEqual(summary.conformant_cases, 1)
        self.assertEqual(summary.flagged_cases, 2)  # C2 and C3 flagged
        self.assertGreater(summary.total_rule_deviations, summary.flagged_cases)  # 1 + >=3 = >=4 deviations
        self.assertEqual(summary.deviations_by_rule[RuleIdentifier.REPEATED_TRIAGE], 1)
        self.assertEqual(summary.deviations_by_rule[RuleIdentifier.MANDATORY_ACTIVITIES], 1)
        self.assertEqual(summary.deviations_by_rule[RuleIdentifier.DUPLICATE_EVENTS], 1)
        self.assertEqual(summary.deviations_by_rule[RuleIdentifier.ACTIVITY_ORDER], 1)

    def test_deterministic_output(self) -> None:
        """Verify running conformance checking twice on identical input yields identical metrics."""
        summary1 = run_conformance_checking(DEFAULT_INPUT_PATH)
        summary2 = run_conformance_checking(DEFAULT_INPUT_PATH)

        self.assertEqual(summary1.total_cases_evaluated, summary2.total_cases_evaluated)
        self.assertEqual(summary1.flagged_cases, summary2.flagged_cases)
        self.assertEqual(summary1.conformant_cases, summary2.conformant_cases)
        self.assertEqual(summary1.total_rule_deviations, summary2.total_rule_deviations)
        self.assertEqual(summary1.deviations_by_rule, summary2.deviations_by_rule)


class TestCanonicalDatasetConformance(unittest.TestCase):
    """Test conformance checker execution against canonical data/cleaned/stg_hospital_events.csv."""

    @classmethod
    def setUpClass(cls) -> None:
        if not DEFAULT_INPUT_PATH.is_file():
            raise unittest.SkipTest(f"Missing canonical staging file: {DEFAULT_INPUT_PATH}")
        cls.summary = run_conformance_checking(DEFAULT_INPUT_PATH)

    def test_canonical_cohort_counts(self) -> None:
        """Verify canonical dataset evaluates exactly 500 cases with 440 conformant and 60 flagged."""
        self.assertEqual(self.summary.total_cases_evaluated, 500)
        self.assertEqual(self.summary.conformant_cases, 440)
        self.assertEqual(self.summary.flagged_cases, 60)
        self.assertEqual(self.summary.deviation_rate_percent, 12.0)
        self.assertEqual(self.summary.total_rule_deviations, 60)

    def test_canonical_deviations_by_rule(self) -> None:
        """Verify repeated triage is the sole rule triggered on canonical data."""
        self.assertEqual(self.summary.deviations_by_rule[RuleIdentifier.REPEATED_TRIAGE], 60)
        self.assertEqual(self.summary.deviations_by_rule[RuleIdentifier.MANDATORY_ACTIVITIES], 0)
        self.assertEqual(self.summary.deviations_by_rule[RuleIdentifier.START_ACTIVITY], 0)
        self.assertEqual(self.summary.deviations_by_rule[RuleIdentifier.END_ACTIVITY], 0)
        self.assertEqual(self.summary.deviations_by_rule[RuleIdentifier.ACTIVITY_ORDER], 0)
        self.assertEqual(self.summary.deviations_by_rule[RuleIdentifier.DIAGNOSTIC_FOLLOWUP], 0)
        self.assertEqual(self.summary.deviations_by_rule[RuleIdentifier.DUPLICATE_EVENTS], 0)

    def test_canonical_variant_breakdown(self) -> None:
        """Verify compliance rates across all 6 discovered variants."""
        vb = self.summary.variant_breakdown

        v1_key = "Registration -> Triage -> Consultation -> Treatment -> Discharge"
        self.assertEqual(vb[v1_key]["total_cases"], 200)
        self.assertEqual(vb[v1_key]["flagged_cases"], 0)
        self.assertEqual(vb[v1_key]["compliance_rate_percent"], 100.0)

        v2_key = "Registration -> Triage -> Consultation -> Laboratory -> Consultation -> Treatment -> Discharge"
        self.assertEqual(vb[v2_key]["total_cases"], 110)
        self.assertEqual(vb[v2_key]["flagged_cases"], 0)
        self.assertEqual(vb[v2_key]["compliance_rate_percent"], 100.0)

        v3_key = "Registration -> Triage -> Consultation -> X-Ray -> Consultation -> Treatment -> Discharge"
        self.assertEqual(vb[v3_key]["total_cases"], 80)
        self.assertEqual(vb[v3_key]["flagged_cases"], 0)
        self.assertEqual(vb[v3_key]["compliance_rate_percent"], 100.0)

        v4_key = "Registration -> Triage -> Consultation -> Laboratory -> X-Ray -> Consultation -> Treatment -> Discharge"
        self.assertEqual(vb[v4_key]["total_cases"], 50)
        self.assertEqual(vb[v4_key]["flagged_cases"], 0)
        self.assertEqual(vb[v4_key]["compliance_rate_percent"], 100.0)

        v5_key = "Registration -> Triage -> Triage -> Consultation -> Treatment -> Discharge"
        self.assertEqual(vb[v5_key]["total_cases"], 35)
        self.assertEqual(vb[v5_key]["flagged_cases"], 35)

        v6_key = "Registration -> Triage -> Triage -> Consultation -> Laboratory -> Consultation -> Treatment -> Discharge"
        self.assertEqual(vb[v6_key]["total_cases"], 25)
        self.assertEqual(vb[v6_key]["flagged_cases"], 25)


class TestArtifactExportAndCLI(unittest.TestCase):
    """Test artifact generation, structure, and CLI invocation."""

    def test_export_conformance_outputs(self) -> None:
        """Verify export_conformance_outputs writes valid CSV, JSON, and MD files to disk."""
        summary = run_conformance_checking(DEFAULT_INPUT_PATH)

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            p_csv = tmp_path / "test_cases.csv"
            p_json = tmp_path / "test_summary.json"
            p_md = tmp_path / "test_findings.md"

            export_conformance_outputs(summary, p_csv, p_json, p_md)

            # Check CSV
            self.assertTrue(p_csv.is_file())
            df_cases = pd.read_csv(p_csv)
            self.assertEqual(len(df_cases), 500)
            self.assertEqual(
                list(df_cases.columns),
                [
                    "case_id",
                    "observed_pathway",
                    "is_conformant",
                    "status",
                    "rule_ids",
                    "review_reasons",
                    "total_deviations",
                ],
            )

            # Check JSON
            self.assertTrue(p_json.is_file())
            with open(p_json, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.assertEqual(data["total_cases_evaluated"], 500)
            self.assertEqual(data["flagged_cases"], 60)
            self.assertEqual(data["total_rule_deviations"], 60)

            # Check Markdown
            self.assertTrue(p_md.is_file())
            with open(p_md, "r", encoding="utf-8") as f:
                md_text = f.read()
            self.assertIn("# CareFlow Clinical Pathway: Patient Pathway Conformance Findings", md_text)
            self.assertIn("100% Synthetic Event Data", md_text)
            self.assertIn("Levels 1–5", md_text)

    def test_cli_execution_with_custom_output_dir(self) -> None:
        """Verify main() runs cleanly from CLI with custom flags."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            main(["--input", str(DEFAULT_INPUT_PATH), "--output-dir", str(tmp_dir)])
            self.assertTrue((Path(tmp_dir) / "conformance_case_results.csv").is_file())
            self.assertTrue((Path(tmp_dir) / "conformance_findings_summary.json").is_file())
            self.assertTrue((Path(tmp_dir) / "conformance_findings.md").is_file())


if __name__ == "__main__":
    unittest.main()
