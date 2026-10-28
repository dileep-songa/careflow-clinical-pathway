"""Automated test suite for CareFlow Bottleneck Findings Report (outputs/bottleneck_findings.md).

Validates:
1. Existence and non-emptiness of outputs/bottleneck_findings.md.
2. Structural compliance with all required analytical sections.
3. Numerical consistency between the report text and outputs/bottleneck_analysis_summary.csv.
4. Proper characterization of clinical explanations as interpretations rather than measured facts.
5. Retention of synthetic EHR data disclaimers and healthcare metrics interpretation boundaries.
6. Cloud pipeline described as intended/in-progress without assuming unverified warehouse execution.
7. Absence of unconfirmed Sandbox expiration dates.
8. Clean typography (e.g., proper en-dash in 'Levels 1–5' without garbled character artifacts).
9. Reference to the visual artifact outputs/bottleneck_analysis.png.
"""

from __future__ import annotations

from pathlib import Path
import unittest

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPORT_FILE = PROJECT_ROOT / "outputs" / "bottleneck_findings.md"
SUMMARY_CSV = PROJECT_ROOT / "outputs" / "bottleneck_analysis_summary.csv"
VISUAL_PNG = PROJECT_ROOT / "outputs" / "bottleneck_analysis.png"


class TestBottleneckFindingsReport(unittest.TestCase):
    """Test suite validating outputs/bottleneck_findings.md content, tone, and accuracy."""

    @classmethod
    def setUpClass(cls) -> None:
        """Load report text and source summary CSV once for testing."""
        if not REPORT_FILE.is_file():
            raise unittest.SkipTest(f"Report file missing at: {REPORT_FILE}")
        if not SUMMARY_CSV.is_file():
            raise unittest.SkipTest(f"Summary CSV missing at: {SUMMARY_CSV}")

        with open(REPORT_FILE, "r", encoding="utf-8") as f:
            cls.report_text = f.read()

        cls.summary_df = pd.read_csv(SUMMARY_CSV)

    def test_report_file_exists_and_non_empty(self) -> None:
        """Verify the report file exists and has substantive content."""
        self.assertTrue(REPORT_FILE.is_file(), "Report file does not exist")
        self.assertGreater(REPORT_FILE.stat().st_size, 1500, "Report file is unexpectedly small")

    def test_report_contains_required_sections(self) -> None:
        """Verify presence of all required analytical sections and headings."""
        required_headings = [
            "Executive Summary & Objective",
            "Data Provenance & Synthetic Disclaimer",
            "Top Five Observed Clinical Transitions",
            "Operational & Clinical Interpretation",
            "Visual Artifact Reference",
            "Analytical Limitations & Healthcare Terminology Clarification",
            "Recommended Next Checks & Next Steps",
        ]
        for heading in required_headings:
            self.assertIn(
                heading,
                self.report_text,
                f"Missing required section heading: '{heading}' in report",
            )

    def test_top_five_transitions_numerical_consistency(self) -> None:
        """Verify that top 5 transition metrics in report match source summary CSV exactly."""
        top5 = self.summary_df.head(5)
        for _, row in top5.iterrows():
            src = str(row["source_activity"])
            tgt = str(row["target_activity"])
            count = int(row["transition_count"])
            mean_dur = f"{float(row['mean_observed_transition_minutes']):.2f}"

            # Verify activities appear in the report
            self.assertIn(src, self.report_text, f"Source activity '{src}' missing from report")
            self.assertIn(tgt, self.report_text, f"Target activity '{tgt}' missing from report")

            # Verify transition count appears in the report
            self.assertIn(str(count), self.report_text, f"Transition count {count} for {src}->{tgt} missing from report")

            # Verify mean duration appears in the report
            self.assertIn(mean_dur, self.report_text, f"Mean duration {mean_dur} for {src}->{tgt} missing from report")

    def test_clinical_interpretation_topics(self) -> None:
        """Verify discussion of repeated triage, diagnostic reviews, and discharge."""
        self.assertIn("Triage -> Triage", self.report_text)
        self.assertIn("Laboratory -> Consultation", self.report_text)
        self.assertIn("X-Ray -> Consultation", self.report_text)
        self.assertIn("Treatment -> Discharge", self.report_text)

        # Check re-triage specific volume (60 encounters, 12.0%)
        self.assertIn("60", self.report_text)
        self.assertIn("12.0%", self.report_text)

    def test_clinical_explanations_labeled_as_interpretations(self) -> None:
        """Verify clinical explanations are explicitly framed as interpretations, not facts."""
        text_lower = self.report_text.lower()
        self.assertIn("possible interpretations", text_lower)
        self.assertIn("not facts directly measured by the event log", text_lower)
        self.assertIn("plausible", text_lower)

    def test_synthetic_data_and_healthcare_caveats(self) -> None:
        """Verify strict healthcare data disclaimers and observed transition distinctions."""
        text_lower = self.report_text.lower()

        # Synthetic data disclaimer
        self.assertTrue(
            "synthetic" in text_lower or "simulated" in text_lower,
            "Synthetic data disclaimer missing from report",
        )
        self.assertIn("no real patient data", text_lower)

        # Observed transition vs waiting time distinction
        self.assertIn("observed transition duration", text_lower)
        clean_text = text_lower.replace("*", "")
        self.assertIn("do not establish actual patient waiting times or confirmed clinical bottlenecks", clean_text)

        # Cloud pipeline described as intended architecture
        self.assertIn("intended", text_lower)

        # Ensure unverified Sandbox expiration dates are not asserted
        self.assertNotIn("december 23", text_lower)

    def test_typography_and_clean_characters(self) -> None:
        """Verify typography is clean with proper en-dashes and no encoding artifacts."""
        self.assertIn("Levels 1–5", self.report_text)
        self.assertNotIn("Levels 1â€“5", self.report_text)
        self.assertNotIn("â€”", self.report_text)
        self.assertNotIn("â€“", self.report_text)
        self.assertNotIn("Ã¢", self.report_text)
        self.assertNotIn("Ãƒ", self.report_text)

    def test_visual_artifact_reference(self) -> None:
        """Verify explicit reference to outputs/bottleneck_analysis.png."""
        self.assertIn("bottleneck_analysis.png", self.report_text)
        self.assertTrue(VISUAL_PNG.is_file(), "Referenced PNG visual artifact does not exist on disk")


if __name__ == "__main__":
    unittest.main()
