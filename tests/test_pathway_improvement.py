"""Automated unit and integration tests for CareFlow Pathway Improvement Engine.

Tests cover:
- Data validation, missing columns, invalid timestamps, and empty datasets
- Descriptive duration statistics, percentiles, and zero-division safe percentages
- To-Be scenario simulation, re-triage resolution, and transition reductions
- As-Is vs. To-Be comparative evaluation on isolated test data
- Exact canonical dataset cohort validation (500 cases, 3,140 events)
- Machine-readable artifact generation (CSV, JSON, MD, PNG)
- CLI argument parsing and execution
- Reproducibility and determinism of generated metrics
- Preservation of existing repository data and outputs
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np
import pandas as pd

from src.pathway_improvement import (
    DEFAULT_INPUT_CSV,
    PROJECT_ROOT,
    ComparisonMetric,
    MetricProvenance,
    PathwayImprovementResult,
    ToBeScenarioConfig,
    TransitionReductionConfig,
    calculate_duration_percentiles,
    compare_as_is_vs_to_be,
    export_comparison_csv,
    export_improvement_report,
    export_summary_json,
    generate_comparison_chart,
    generate_improvement_report,
    load_and_validate_event_log,
    parse_args,
    run_pathway_improvement_pipeline,
    safe_percentage_change,
    simulate_to_be_event_log,
)


class TestPathwayImprovementValidation(unittest.TestCase):
    """Test suite for event log input validation and column normalization."""

    def test_missing_file_raises_error(self) -> None:
        """Verify non-existent file path raises FileNotFoundError."""
        with self.assertRaises(FileNotFoundError):
            load_and_validate_event_log(Path("data/non_existent_events.csv"))

    def test_empty_file_raises_error(self) -> None:
        """Verify 0-byte file raises ValueError."""
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            temp_path = Path(f.name)
        try:
            with self.assertRaises(ValueError) as ctx:
                load_and_validate_event_log(temp_path)
            self.assertIn("empty", str(ctx.exception).lower())
        finally:
            if temp_path.exists():
                temp_path.unlink()

    def test_empty_dataframe_raises_error(self) -> None:
        """Verify empty DataFrame raises ValueError."""
        empty_df = pd.DataFrame()
        with self.assertRaises(ValueError) as ctx:
            load_and_validate_event_log(empty_df)
        self.assertIn("zero records", str(ctx.exception).lower())

    def test_missing_required_columns_raises_error(self) -> None:
        """Verify missing case_id, activity, or timestamp raises ValueError."""
        df_no_case = pd.DataFrame(
            {
                "activity_name": ["Registration"],
                "event_timestamp": ["2024-10-01 08:00:00"],
            }
        )
        with self.assertRaises(ValueError) as ctx:
            load_and_validate_event_log(df_no_case)
        self.assertIn("missing required columns", str(ctx.exception).lower())

    def test_null_or_empty_case_id_raises_error(self) -> None:
        """Verify null or blank case_id raises ValueError."""
        df_null_case = pd.DataFrame(
            {
                "case_id": [None, "CASE_001"],
                "activity_name": ["Registration", "Triage"],
                "event_timestamp": ["2024-10-01 08:00:00", "2024-10-01 08:15:00"],
            }
        )
        with self.assertRaises(ValueError):
            load_and_validate_event_log(df_null_case)

    def test_null_or_empty_activity_raises_error(self) -> None:
        """Verify null or blank activity_name raises ValueError."""
        df_empty_act = pd.DataFrame(
            {
                "case_id": ["CASE_001", "CASE_001"],
                "activity_name": ["Registration", "   "],
                "event_timestamp": ["2024-10-01 08:00:00", "2024-10-01 08:15:00"],
            }
        )
        with self.assertRaises(ValueError):
            load_and_validate_event_log(df_empty_act)

    def test_invalid_timestamp_raises_error(self) -> None:
        """Verify unparseable timestamp string raises ValueError."""
        df_bad_ts = pd.DataFrame(
            {
                "case_id": ["CASE_001"],
                "activity_name": ["Registration"],
                "event_timestamp": ["NOT_A_TIMESTAMP"],
            }
        )
        with self.assertRaises(ValueError) as ctx:
            load_and_validate_event_log(df_bad_ts)
        self.assertIn("parse event timestamps", str(ctx.exception).lower())


class TestDurationAndPercentileCalculations(unittest.TestCase):
    """Test suite for duration statistics, percentiles, and percentage change arithmetic."""

    def test_calculate_duration_percentiles_empty(self) -> None:
        """Verify empty sequence produces clean zeroes."""
        stats = calculate_duration_percentiles([])
        self.assertEqual(stats["mean"], 0.0)
        self.assertEqual(stats["median"], 0.0)
        self.assertEqual(stats["std"], 0.0)
        self.assertEqual(stats["p25"], 0.0)
        self.assertEqual(stats["p75"], 0.0)
        self.assertEqual(stats["p90"], 0.0)

    def test_calculate_duration_percentiles_single_element(self) -> None:
        """Verify single element sequence produces identical mean/median and zero std."""
        stats = calculate_duration_percentiles([45.0])
        self.assertEqual(stats["mean"], 45.0)
        self.assertEqual(stats["median"], 45.0)
        self.assertEqual(stats["min"], 45.0)
        self.assertEqual(stats["max"], 45.0)
        self.assertEqual(stats["std"], 0.0)

    def test_calculate_duration_percentiles_known_values(self) -> None:
        """Verify statistical accuracy on known distribution."""
        values = [10.0, 20.0, 30.0, 40.0, 50.0]
        stats = calculate_duration_percentiles(values)
        self.assertEqual(stats["mean"], 30.0)
        self.assertEqual(stats["median"], 30.0)
        self.assertEqual(stats["min"], 10.0)
        self.assertEqual(stats["max"], 50.0)
        self.assertEqual(stats["p25"], 20.0)
        self.assertEqual(stats["p75"], 40.0)

    def test_safe_percentage_change_standard_cases(self) -> None:
        """Verify percentage calculation on normal numeric inputs."""
        # 20% increase
        self.assertEqual(safe_percentage_change(100.0, 120.0), 20.0)
        # 15% decrease
        self.assertEqual(safe_percentage_change(100.0, 85.0), -15.0)

    def test_safe_percentage_change_zero_division_guard(self) -> None:
        """Verify division-by-zero protection when baseline is zero."""
        # Zero baseline and zero proposed -> 0.0%
        self.assertEqual(safe_percentage_change(0.0, 0.0), 0.0)
        # Zero baseline and non-zero proposed -> None (undefined)
        self.assertIsNone(safe_percentage_change(0.0, 50.0))


class TestToBeScenarioSimulation(unittest.TestCase):
    """Test suite for To-Be scenario event simulation and transformation rules."""

    def setUp(self) -> None:
        """Set up standard test configuration."""
        self.config = ToBeScenarioConfig.default_conservative()

    def test_simulation_single_event_case(self) -> None:
        """Verify single-event encounter passes through gracefully."""
        df = pd.DataFrame(
            {
                "case_id": ["CASE_SOLO"],
                "activity_name": ["Registration"],
                "event_timestamp": [pd.Timestamp("2024-10-01 08:00:00")],
                "event_sequence": [1],
            }
        )
        sim_df = simulate_to_be_event_log(df, self.config)
        self.assertEqual(len(sim_df), 1)
        self.assertEqual(sim_df.iloc[0]["case_id"], "CASE_SOLO")
        self.assertEqual(sim_df.iloc[0]["activity_name"], "Registration")

    def test_simulation_re_triage_resolution(self) -> None:
        """Verify consecutive triage (Triage -> Triage) is collapsed and delay removed."""
        # Case with re-triage: Reg (08:00) -> Triage1 (08:20) -> Triage2 (09:20) -> Consult (09:45) -> Disch (10:30)
        # Total As-Is duration: 150 minutes
        # Re-triage wait (Triage1 -> Triage2): 60 minutes
        # Triage2 -> Consult: 25 minutes
        df = pd.DataFrame(
            {
                "case_id": ["CASE_RETRIAGE"] * 5,
                "activity_name": ["Registration", "Triage", "Triage", "Consultation", "Discharge"],
                "event_timestamp": pd.to_datetime(
                    [
                        "2024-10-01 08:00:00",
                        "2024-10-01 08:20:00",
                        "2024-10-01 09:20:00",
                        "2024-10-01 09:45:00",
                        "2024-10-01 10:30:00",
                    ]
                ),
                "event_sequence": [1, 2, 3, 4, 5],
            }
        )

        sim_df = simulate_to_be_event_log(df, self.config)

        # In To-Be: 4 events (one Triage removed)
        self.assertEqual(len(sim_df), 4)
        acts = sim_df["activity_name"].tolist()
        self.assertEqual(acts, ["Registration", "Triage", "Consultation", "Discharge"])

        # Triage -> Consultation elapsed time in To-Be should equal the 25-minute post-triage interval
        triage_ts = sim_df.loc[sim_df["activity_name"] == "Triage", "event_timestamp"].iloc[0]
        consult_ts = sim_df.loc[sim_df["activity_name"] == "Consultation", "event_timestamp"].iloc[0]
        self.assertEqual((consult_ts - triage_ts).total_seconds() / 60.0, 25.0)

    def test_simulation_keep_repeated_triage(self) -> None:
        """Verify re-triage is retained when resolve_repeated_triage is False."""
        cfg = ToBeScenarioConfig.default_conservative()
        cfg.resolve_repeated_triage = False

        df = pd.DataFrame(
            {
                "case_id": ["CASE_KEEP"] * 4,
                "activity_name": ["Registration", "Triage", "Triage", "Discharge"],
                "event_timestamp": pd.to_datetime(
                    [
                        "2024-10-01 08:00:00",
                        "2024-10-01 08:20:00",
                        "2024-10-01 09:20:00",
                        "2024-10-01 10:00:00",
                    ]
                ),
                "event_sequence": [1, 2, 3, 4],
            }
        )

        sim_df = simulate_to_be_event_log(df, cfg)
        self.assertEqual(len(sim_df), 4)
        self.assertEqual(sim_df["activity_name"].tolist().count("Triage"), 2)

    def test_simulation_transition_reduction_with_floor(self) -> None:
        """Verify percentage reduction applies to targeted transition with floor limit."""
        cfg = ToBeScenarioConfig()
        cfg.resolve_repeated_triage = False
        cfg.transition_reductions[("Laboratory", "Consultation")] = TransitionReductionConfig(
            source_activity="Laboratory",
            target_activity="Consultation",
            percentage_reduction=50.0,
            min_floor_minutes=20.0,
            rationale="Test 50% reduction with 20m floor",
        )

        # Baseline: Laboratory (08:00) -> Consultation (08:30) = 30 minutes
        # 50% of 30m = 15m, but floor is 20m -> result should be 20m
        df = pd.DataFrame(
            {
                "case_id": ["CASE_LAB"] * 2,
                "activity_name": ["Laboratory", "Consultation"],
                "event_timestamp": pd.to_datetime(["2024-10-01 08:00:00", "2024-10-01 08:30:00"]),
                "event_sequence": [1, 2],
            }
        )

        sim_df = simulate_to_be_event_log(df, cfg)
        t_lab = sim_df.loc[sim_df["activity_name"] == "Laboratory", "event_timestamp"].iloc[0]
        t_consult = sim_df.loc[sim_df["activity_name"] == "Consultation", "event_timestamp"].iloc[0]
        elapsed = (t_consult - t_lab).total_seconds() / 60.0
        self.assertEqual(elapsed, 20.0)


class TestAsIsVsToBeComparison(unittest.TestCase):
    """Test suite for full comparative analysis on isolated test data."""

    def test_isolated_cohort_comparison(self) -> None:
        """Verify As-Is vs To-Be comparison calculations on multi-case test dataset."""
        data = {
            "case_id": [
                "C1", "C1", "C1",
                "C2", "C2", "C2", "C2",
            ],
            "activity_name": [
                "Registration", "Triage", "Discharge",
                "Registration", "Triage", "Triage", "Discharge",
            ],
            "event_timestamp": [
                "2024-10-01 08:00:00", "2024-10-01 08:20:00", "2024-10-01 09:00:00",
                "2024-10-01 08:00:00", "2024-10-01 08:20:00", "2024-10-01 09:20:00", "2024-10-01 10:00:00",
            ],
            "event_sequence": [1, 2, 3, 1, 2, 3, 4],
        }
        df = pd.DataFrame(data)
        validated = load_and_validate_event_log(df)

        result = compare_as_is_vs_to_be(validated)

        # Baseline: 2 cases, 7 events, 2 variants
        self.assertEqual(result.as_is_summary["total_cases"], 2)
        self.assertEqual(result.as_is_summary["total_events"], 7)
        self.assertEqual(len(result.as_is_variants), 2)

        # To-Be: 2 cases, 6 events (re-triage resolved in C2), 1 standardized variant
        self.assertEqual(result.to_be_summary["total_cases"], 2)
        self.assertEqual(result.to_be_summary["total_events"], 6)
        self.assertEqual(len(result.to_be_variants), 1)

    def test_explicit_labeling_of_assumptions_and_provenance(self) -> None:
        """Verify all metrics carry explicit analytical provenance labels."""
        df = load_and_validate_event_log(DEFAULT_INPUT_CSV)
        result = compare_as_is_vs_to_be(df)

        valid_provenances = {
            MetricProvenance.OBSERVED_BASELINE.value,
            MetricProvenance.SIMULATED_ESTIMATE.value,
            MetricProvenance.CALCULATED_DELTA.value,
            MetricProvenance.ASSUMED_HYPOTHETICAL.value,
        }

        for metric in result.comparison_table:
            self.assertIn(
                metric.provenance,
                valid_provenances,
                f"Metric {metric.metric_name} missing valid provenance label.",
            )
            self.assertTrue(len(metric.interpretation.strip()) > 0)

        variant_metric = next(m for m in result.comparison_table if m.metric_name == "Clinical Pathway Variants")
        self.assertEqual(
            variant_metric.interpretation,
            "Hypothetical pathway consolidation: repeated triage events are removed in the proposed scenario, subject to clinical validation.",
        )


class TestCanonicalDatasetImprovement(unittest.TestCase):
    """Test suite evaluating the official canonical CareFlow simulated dataset."""

    @classmethod
    def setUpClass(cls) -> None:
        """Load and evaluate canonical dataset once for suite."""
        cls.df = load_and_validate_event_log(DEFAULT_INPUT_CSV)
        cls.result = compare_as_is_vs_to_be(cls.df)

    def test_canonical_cohort_totals(self) -> None:
        """Verify canonical cohort counts: 500 cases, 3,140 -> 3,080 events, 6 -> 4 variants."""
        self.assertEqual(self.result.as_is_summary["total_cases"], 500)
        self.assertEqual(self.result.to_be_summary["total_cases"], 500)

        # 60 repeated triage events removed
        self.assertEqual(self.result.as_is_summary["total_events"], 3140)
        self.assertEqual(self.result.to_be_summary["total_events"], 3080)

        # Variants consolidate from 6 to 4
        self.assertEqual(len(self.result.as_is_variants), 6)
        self.assertEqual(len(self.result.to_be_variants), 4)

    def test_canonical_case_durations(self) -> None:
        """Verify baseline vs proposed encounter duration metrics."""
        as_is = self.result.as_is_summary["case_durations"]
        to_be = self.result.to_be_summary["case_durations"]

        self.assertEqual(as_is["mean"], 202.54)
        self.assertEqual(as_is["median"], 211.0)
        self.assertEqual(as_is["p90"], 284.0)

        self.assertEqual(to_be["mean"], 181.77)
        self.assertEqual(to_be["median"], 191.18)
        self.assertEqual(to_be["p90"], 255.18)

        # Mean duration reduced by ~20.77 minutes (-10.25%)
        delta_mean = round(to_be["mean"] - as_is["mean"], 2)
        self.assertEqual(delta_mean, -20.77)
        pct_change = safe_percentage_change(as_is["mean"], to_be["mean"])
        self.assertEqual(pct_change, -10.25)

    def test_canonical_targeted_transitions(self) -> None:
        """Verify targeted bottleneck transitions reflect modeled reductions."""
        # Find metrics in comparison table
        metric_map = {
            m.metric_name.split(" (N=")[0]: m for m in self.result.comparison_table
            if m.category == "Transition Duration (Minutes)"
        }

        # Laboratory -> Consultation
        lab_m = metric_map.get("Laboratory -> Consultation")
        self.assertIsNotNone(lab_m)
        self.assertEqual(float(lab_m.baseline_value), 67.44)
        self.assertEqual(float(lab_m.proposed_value), 57.32)
        self.assertEqual(float(lab_m.absolute_difference), -10.12)
        self.assertEqual(lab_m.percentage_difference, -15.01)

        # Triage -> Triage eliminated
        triage_m = metric_map.get("Triage -> Triage")
        self.assertIsNotNone(triage_m)
        self.assertEqual(float(triage_m.baseline_value), 65.63)
        self.assertEqual(float(triage_m.proposed_value), 0.0)
        self.assertEqual(float(triage_m.absolute_difference), -65.63)
        self.assertEqual(triage_m.percentage_difference, -100.0)

        # Treatment -> Discharge
        treat_m = metric_map.get("Treatment -> Discharge")
        self.assertIsNotNone(treat_m)
        self.assertEqual(float(treat_m.baseline_value), 52.01)
        self.assertEqual(float(treat_m.proposed_value), 44.21)
        self.assertEqual(float(treat_m.absolute_difference), -7.80)
        self.assertEqual(treat_m.percentage_difference, -15.0)

        # X-Ray -> Consultation
        xray_m = metric_map.get("X-Ray -> Consultation")
        self.assertIsNotNone(xray_m)
        self.assertEqual(float(xray_m.baseline_value), 60.36)
        self.assertEqual(float(xray_m.proposed_value), 51.31)
        self.assertEqual(float(xray_m.absolute_difference), -9.05)
        self.assertEqual(xray_m.percentage_difference, -14.99)

    def test_canonical_variant_shift(self) -> None:
        """Verify pathway variants shift deterministically."""
        as_is_map = {v["pathway"]: v["case_count"] for v in self.result.as_is_variants}
        to_be_map = {v["pathway"]: v["case_count"] for v in self.result.to_be_variants}

        # Variant 1 expands: 200 -> 235 (+35 from Variant 5)
        pwy1 = "Registration -> Triage -> Consultation -> Treatment -> Discharge"
        self.assertEqual(as_is_map[pwy1], 200)
        self.assertEqual(to_be_map[pwy1], 235)

        # Variant 2 expands: 110 -> 135 (+25 from Variant 6)
        pwy2 = "Registration -> Triage -> Consultation -> Laboratory -> Consultation -> Treatment -> Discharge"
        self.assertEqual(as_is_map[pwy2], 110)
        self.assertEqual(to_be_map[pwy2], 135)

        # Re-triage variants absent in To-Be
        pwy5 = "Registration -> Triage -> Triage -> Consultation -> Treatment -> Discharge"
        self.assertEqual(as_is_map[pwy5], 35)
        self.assertNotIn(pwy5, to_be_map)


class TestArtifactExportAndCLI(unittest.TestCase):
    """Test suite for file exports, report generation, and CLI parsing."""

    def test_export_all_artifacts_to_temporary_directory(self) -> None:
        """Verify pipeline creates non-empty CSV, JSON, MD, and PNG files."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            result = run_pathway_improvement_pipeline(
                input_source=DEFAULT_INPUT_CSV,
                output_dir=tmp_path,
                generate_chart=True,
            )
            self.assertIsInstance(result, PathwayImprovementResult)

            csv_file = tmp_path / "pathway_improvement_comparison.csv"
            json_file = tmp_path / "pathway_improvement_summary.json"
            report_file = tmp_path / "pathway_improvement_report.md"
            png_file = tmp_path / "pathway_improvement_comparison.png"

            self.assertTrue(csv_file.exists())
            self.assertTrue(json_file.exists())
            self.assertTrue(report_file.exists())
            self.assertTrue(png_file.exists())

            self.assertGreater(csv_file.stat().st_size, 100)
            self.assertGreater(json_file.stat().st_size, 500)
            self.assertGreater(report_file.stat().st_size, 500)
            self.assertGreater(png_file.stat().st_size, 5000)

    def test_report_contains_required_sections_and_disclaimers(self) -> None:
        """Verify Markdown report contains mandatory disclaimers, tables, and clean encoding."""
        df = load_and_validate_event_log(DEFAULT_INPUT_CSV)
        result = compare_as_is_vs_to_be(df)
        report_text = generate_improvement_report(result)

        self.assertIn("# CareFlow Clinical Pathway: As-Is vs. To-Be Improvement Report", report_text)
        self.assertIn("Synthetic Event Data", report_text)
        self.assertIn("100% Synthetic", report_text)
        self.assertIn("Analytical & Clinical Boundaries", report_text)
        self.assertIn("Cohort & Process Overview", report_text)
        self.assertIn("Pathway Variant Distribution Shift", report_text)
        self.assertIn("Analytical Limitations", report_text)
        self.assertIn("Recommended Next Steps", report_text)
        self.assertIn("Clinical Safety Assumption:", report_text)
        self.assertIn(
            "The To-Be scenario removes repeated triage events as a hypothetical operational improvement.",
            report_text,
        )
        self.assertIn(
            "Simulated event data alone cannot determine whether reassessment is clinically necessary.",
            report_text,
        )
        self.assertIn(
            "Qualified hospital staff must validate this assumption before any real-world workflow change.",
            report_text,
        )
        self.assertIn(
            "Consultations, diagnostic activities, treatment, and discharge remain represented in the simulated pathways.",
            report_text,
        )
        self.assertNotIn("Zero Clinical Activity Omission", report_text)
        self.assertNotIn("redundant re-assessment", report_text)
        self.assertNotIn("non-conformant re-triage pathways", report_text)
        self.assertTrue(report_text.endswith("\n"))

        # Verify no garbled character encodings
        for bad_char in ["â€”", "â€“", "Ã¢", "Ãƒ"]:
            self.assertNotIn(bad_char, report_text)

    def test_reproducibility_of_pipeline_outputs(self) -> None:
        """Verify executing pipeline twice yields identical numerical outputs."""
        df = load_and_validate_event_log(DEFAULT_INPUT_CSV)
        res1 = compare_as_is_vs_to_be(df)
        res2 = compare_as_is_vs_to_be(df)

        self.assertEqual(
            res1.as_is_summary["case_durations"],
            res2.as_is_summary["case_durations"],
        )
        self.assertEqual(
            res1.to_be_summary["case_durations"],
            res2.to_be_summary["case_durations"],
        )
        self.assertEqual(
            [m.to_dict() for m in res1.comparison_table],
            [m.to_dict() for m in res2.comparison_table],
        )

    def test_cli_parsing(self) -> None:
        """Verify command-line argument parsing with default and custom values."""
        args = parse_args(
            [
                "--input", "data/test.csv",
                "--output-dir", "custom_outputs",
                "--scenario-name", "Custom Scenario",
                "--lab-reduction-pct", "20.0",
                "--keep-repeated-triage",
                "--no-plot",
            ]
        )
        self.assertEqual(args.input, "data/test.csv")
        self.assertEqual(args.output_dir, "custom_outputs")
        self.assertEqual(args.scenario_name, "Custom Scenario")
        self.assertEqual(args.lab_reduction_pct, 20.0)
        self.assertTrue(args.keep_repeated_triage)
        self.assertTrue(args.no_plot)


class TestPreservationOfExistingBehavior(unittest.TestCase):
    """Test suite ensuring existing project outputs and data remain unmodified."""

    def test_existing_source_dataset_integrity(self) -> None:
        """Verify baseline staging event log has not been modified or truncated."""
        df = pd.read_csv(DEFAULT_INPUT_CSV)
        self.assertEqual(len(df), 3140)
        self.assertEqual(df["case_id"].nunique(), 500)

    def test_existing_bottleneck_outputs_preserved(self) -> None:
        """Verify Phase 3 bottleneck summary CSV is intact and untouched."""
        bottleneck_csv = PROJECT_ROOT / "outputs" / "bottleneck_analysis_summary.csv"
        self.assertTrue(bottleneck_csv.exists())
        df_bn = pd.read_csv(bottleneck_csv)
        self.assertEqual(len(df_bn), 10)
        self.assertIn("mean_observed_transition_minutes", df_bn.columns)


if __name__ == "__main__":
    unittest.main()
