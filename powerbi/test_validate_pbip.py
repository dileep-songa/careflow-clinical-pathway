"""
Validation test for CareFlow_Dashboard.pbip (folder-based TMDL semantic model & PBIR report)
"""
import os
import json
from pathlib import Path

# Path to CareFlow Dashboard Project directory derived dynamically from __file__
PROJ_DIR = Path(__file__).resolve().parent / "CareFlow_Dashboard_Project"

def test_pbip_validation():
    proj = str(PROJ_DIR)

    # 1. Validate JSON files
    pbip_file = os.path.join(proj, "CareFlow_Dashboard.pbip")
    assert os.path.exists(pbip_file), f"Missing {pbip_file}"
    with open(pbip_file, "r", encoding="utf-8") as f:
        pbip_data = json.load(f)

    # Confirm enableAutoAuth is strictly absent from settings
    settings = pbip_data.get("settings", {})
    assert "enableAutoAuth" not in settings, "enableAutoAuth must not be present in settings"
    print("[VERIFIED] enableAutoAuth is absent from pbip settings.")

    # Validate required JSON manifest and report files
    json_files = [
        pbip_file,
        os.path.join(proj, "CareFlow_Dashboard.SemanticModel", "definition.pbism"),
        os.path.join(proj, "CareFlow_Dashboard.Report", "definition.pbir"),
        os.path.join(proj, "CareFlow_Dashboard.Report", "report.json")
    ]
    for jf in json_files:
        assert os.path.exists(jf), f"Missing required file: {jf}"
        with open(jf, "r", encoding="utf-8") as f:
            data = json.load(f)
        print(f"[VALID JSON] {os.path.basename(jf)}")

    # Verify definition.pbir links to the semantic model
    pbir_path = os.path.join(proj, "CareFlow_Dashboard.Report", "definition.pbir")
    with open(pbir_path, "r", encoding="utf-8") as f:
        pbir_data = json.load(f)
    sm_path = pbir_data.get("datasetReference", {}).get("byPath", {}).get("path")
    assert sm_path == "../CareFlow_Dashboard.SemanticModel", f"Unexpected datasetReference path: {sm_path}"
    print("[VERIFIED] definition.pbir references ../CareFlow_Dashboard.SemanticModel")

    # 2. Validate folder-based TMDL semantic model
    sm_def = os.path.join(proj, "CareFlow_Dashboard.SemanticModel", "definition")
    assert os.path.exists(sm_def), f"Missing TMDL definition directory: {sm_def}"

    # Verify model.tmdl exists and references primary tables
    model_tmdl_path = os.path.join(sm_def, "model.tmdl")
    assert os.path.exists(model_tmdl_path), f"Missing model.tmdl: {model_tmdl_path}"
    with open(model_tmdl_path, "r", encoding="utf-8") as f:
        model_tmdl = f.read()

    expected_table_refs = [
        "stg_hospital_events",
        "stg_hospital_events (2)",
        "pathway_variants_summary",
        "bottleneck_analysis_summary",
        "pathway_improvement_comparison"
    ]
    for tbl_ref in expected_table_refs:
        assert f"ref table '{tbl_ref}'" in model_tmdl or f"ref table {tbl_ref}" in model_tmdl, (
            f"Table reference for {tbl_ref} missing from model.tmdl"
        )
    print(f"[VERIFIED] model.tmdl references all {len(expected_table_refs)} primary tables.")

    # Verify supporting TMDL files exist
    for tmdl_file in ["database.tmdl", "relationships.tmdl", os.path.join("cultures", "en-US.tmdl")]:
        fpath = os.path.join(sm_def, tmdl_file)
        assert os.path.exists(fpath), f"Missing TMDL file: {fpath}"
        print(f"[VERIFIED TMDL] {tmdl_file}")

    # Check TMDL tables in tables/ folder
    tables_dir = os.path.join(sm_def, "tables")
    assert os.path.exists(tables_dir), f"Missing TMDL tables directory: {tables_dir}"

    # Verify stg_hospital_events.tmdl
    stg_path = os.path.join(tables_dir, "stg_hospital_events.tmdl")
    assert os.path.exists(stg_path), f"Missing {stg_path}"
    with open(stg_path, "r", encoding="utf-8") as f:
        stg_content = f.read()
    assert "Table.ReplaceValue" in stg_content, "Table.ReplaceValue missing from stg_hospital_events.tmdl"
    assert "Encoding=65001" in stg_content, "Encoding=65001 missing from stg_hospital_events.tmdl"

    expected_measures = [
        "Total Cases", "Total Events", "Avg Case Cycle Time (Mins)",
        "Median Case Cycle Time (Mins)", "Re-Triage Rate %",
        "Conformant Cases Count", "Repeat Triage Cases Count", "Conformance Rate %"
    ]
    for meas in expected_measures:
        assert f"measure '{meas}'" in stg_content or f"measure {meas}" in stg_content, (
            f"Measure '{meas}' missing from stg_hospital_events.tmdl"
        )
    print(f"[VERIFIED TMDL] stg_hospital_events.tmdl contains Table.ReplaceValue, Encoding=65001, and all {len(expected_measures)} measures.")

    # Verify stg_hospital_events (2).tmdl
    stg2_path = os.path.join(tables_dir, "stg_hospital_events (2).tmdl")
    assert os.path.exists(stg2_path), f"Missing {stg2_path}"
    with open(stg2_path, "r", encoding="utf-8") as f:
        stg2_content = f.read()
    assert "excludeFromModelRefresh" in stg2_content, "excludeFromModelRefresh missing from stg_hospital_events (2).tmdl"
    assert "GoogleBigQuery" not in stg2_content, "GoogleBigQuery must not be in stg_hospital_events (2).tmdl"
    print("[VERIFIED TMDL] stg_hospital_events (2).tmdl uses local-safe reference and excludeFromModelRefresh: true.")

    # Verify pathway_variants_summary.tmdl
    pvs_path = os.path.join(tables_dir, "pathway_variants_summary.tmdl")
    assert os.path.exists(pvs_path), f"Missing {pvs_path}"
    with open(pvs_path, "r", encoding="utf-8") as f:
        pvs_content = f.read()
    assert "Total Variant Cases" in pvs_content, "Total Variant Cases measure missing from pathway_variants_summary.tmdl"
    print("[VERIFIED TMDL] pathway_variants_summary.tmdl contains Total Variant Cases measure.")

    # Verify bottleneck_analysis_summary.tmdl
    bas_path = os.path.join(tables_dir, "bottleneck_analysis_summary.tmdl")
    assert os.path.exists(bas_path), f"Missing {bas_path}"
    with open(bas_path, "r", encoding="utf-8") as f:
        bas_content = f.read()
    assert "Avg Transition Duration" in bas_content, "Avg Transition Duration measure missing from bottleneck_analysis_summary.tmdl"
    print("[VERIFIED TMDL] bottleneck_analysis_summary.tmdl contains Avg Transition Duration measure.")

    # Verify pathway_improvement_comparison.tmdl
    pic_path = os.path.join(tables_dir, "pathway_improvement_comparison.tmdl")
    assert os.path.exists(pic_path), f"Missing {pic_path}"
    with open(pic_path, "r", encoding="utf-8") as f:
        pic_content = f.read()
    assert "Relative % Difference" in pic_content, "Relative % Difference measure missing from pathway_improvement_comparison.tmdl"
    assert "[proposed_value] - [baseline_value]" in pic_content, "Relative change formula missing from pathway_improvement_comparison.tmdl"
    print("[VERIFIED TMDL] pathway_improvement_comparison.tmdl contains Relative % Difference and relative change formula.")

    # Verify date tables exist
    date_template = [f for f in os.listdir(tables_dir) if f.startswith("DateTableTemplate")]
    assert len(date_template) > 0, "Missing DateTableTemplate in TMDL tables"
    local_date_tables = [f for f in os.listdir(tables_dir) if f.startswith("LocalDateTable")]
    assert len(local_date_tables) >= 4, f"Expected at least 4 LocalDateTable files, found {len(local_date_tables)}"
    print(f"[VERIFIED TMDL] Found {len(local_date_tables)} LocalDateTable files and DateTableTemplate.")

    # 3. Inspect report.json structure
    rep_path = os.path.join(proj, "CareFlow_Dashboard.Report", "report.json")
    with open(rep_path, "r", encoding="utf-8") as f:
        rep = json.load(f)

    sections = rep["sections"]
    assert len(sections) == 3, f"Expected 3 sections, found {len(sections)}"

    expected_pages = [
        "Hospital Overview",
        "Patient Flow",
        "Transition Analysis & Process Improvement"
    ]

    total_data_visuals = 0
    total_textboxes = 0

    for idx, expected_name in enumerate(expected_pages):
        sec = sections[idx]
        assert sec["displayName"] == expected_name, f"Expected {expected_name}, found {sec['displayName']}"
        vcs = sec["visualContainers"]
        print(f"\nPage {idx+1}: '{sec['displayName']}' - {len(vcs)} Visuals:")
        for vc in vcs:
            cfg = json.loads(vc["config"])
            vtype = cfg["singleVisual"]["visualType"]
            vname = cfg["name"]
            print(f"  - {vname} ({vtype})")
            if vtype == "textbox":
                total_textboxes += 1
            else:
                total_data_visuals += 1
                assert "query" in vc, f"Visual {vname} missing query definition"
                query_obj = json.loads(vc["query"])
                assert "Commands" in query_obj, f"Visual {vname} query missing Commands"
                assert "dataTransforms" in vc, f"Visual {vname} missing dataTransforms"
                dt = json.loads(vc["dataTransforms"])
                assert "selects" in dt and len(dt["selects"]) > 0, f"Visual {vname} missing dt.selects"
                assert "projectionOrdering" in dt, f"Visual {vname} missing dt.projectionOrdering"

    assert total_data_visuals == 15, f"Expected 15 data visuals, found {total_data_visuals}"
    assert total_textboxes == 3, f"Expected 3 textbox visuals, found {total_textboxes}"
    print(f"\n[VERIFIED visualContainers] All {total_data_visuals} data visuals have valid query and dataTransforms.")

    # Check Page 1 Total Events visual display units
    p1 = sections[0]
    total_events_vc = [vc for vc in p1["visualContainers"] if json.loads(vc["config"])["name"] == "card_total_events"][0]
    cfg_te = json.loads(total_events_vc["config"])
    callout_obj = cfg_te["singleVisual"]["objects"]["value"][0]["properties"]["displayUnits"]["expr"]["Literal"]["Value"]
    assert callout_obj == "1D", f"Expected displayUnits '1D' (None), found {callout_obj}"
    print("[VERIFIED] card_total_events is explicitly configured with displayUnits = 1D (None).")

    # 4. Check theme file
    theme_file = os.path.join(proj, "CareFlow_Dashboard.Report", "StaticResources", "SharedResources", "BaseThemes", "CY26SU05.json")
    if not os.path.exists(theme_file):
        theme_file = os.path.join(proj, "CareFlow_Dashboard.Report", "definition", "StaticResources", "SharedResources", "BaseThemes", "CY26SU05.json")
    assert os.path.exists(theme_file), f"Theme file missing: {theme_file}"
    print(f"[VERIFIED Theme] CY26SU05.json exists at {theme_file}")

    print("\n=== ALL PBIP VALIDATION CHECKS PASSED SUCCESSFULLY ===")


def test_relative_percentage_difference_calculation():
    """
    Regression test for relative percentage difference calculations.
    Ensures:
      - (Proposed - Baseline) / Baseline is computed exactly once
      - Output is a fractional ratio formatted as percentage (+0.0%;-0.0%;0.0%)
      - No double-scaling (e.g. -1025.0% instead of -10.3%)
      - Safe handling of zero and blank baselines
      - PBIP report layout and visual field configurations are verified
    """
    def compute_relative_diff(baseline, proposed):
        if baseline is None or baseline == 0:
            if proposed == 0:
                return 0.0
            return None
        return (proposed - baseline) / baseline

    def format_dax_percentage(ratio):
        if ratio is None:
            return "BLANK"
        pct = ratio * 100.0
        # Power BI formatString: +0.0%;-0.0%;0.0%
        if round(pct, 1) > 0:
            return f"+{pct:.1f}%"
        elif round(pct, 1) < 0:
            return f"{pct:.1f}%"
        else:
            return "0.0%"

    # 1. Representative test cases
    test_cases = [
        # (baseline, proposed, expected_ratio, expected_display_pct, desc)
        (202.54, 181.77, -0.10254764490964747, "-10.3%", "Mean Encounter Duration"),
        (6, 4, -0.3333333333333333, "-33.3%", "Clinical Pathway Variants"),
        (500, 500, 0.0, "0.0%", "Total Evaluated Cases (Preserved)"),
        (65.63, 0.0, -1.0, "-100.0%", "Repeat Triage Loop Elimination"),
        (100.0, 125.0, 0.25, "+25.0%", "Operational Volume Growth Scenario"),
        (0.0, 0.0, 0.0, "0.0%", "Zero Baseline, Zero Proposed"),
        (0.0, 50.0, None, "BLANK", "Zero Baseline, Positive Proposed (Safe Blank)"),
        (None, 50.0, None, "BLANK", "Blank Baseline (Safe Blank)")
    ]

    for baseline, proposed, exp_ratio, exp_str, desc in test_cases:
        actual_ratio = compute_relative_diff(baseline, proposed)
        if exp_ratio is None:
            assert actual_ratio is None, f"Failed safe blank check for {desc}: got {actual_ratio}"
        else:
            assert abs(actual_ratio - exp_ratio) < 1e-6, f"Failed ratio for {desc}: expected {exp_ratio}, got {actual_ratio}"
        actual_str = format_dax_percentage(actual_ratio)
        assert actual_str == exp_str, f"Failed formatted string for {desc}: expected {exp_str}, got {actual_str}"

    print("[VERIFIED] All relative percentage difference edge cases and display strings passed.")

    # 2. Verify semantic model schema and M partition in TMDL
    proj = str(PROJ_DIR)
    pic_path = os.path.join(proj, "CareFlow_Dashboard.SemanticModel", "definition", "tables", "pathway_improvement_comparison.tmdl")
    assert os.path.exists(pic_path), f"Missing pathway_improvement_comparison.tmdl: {pic_path}"
    with open(pic_path, "r", encoding="utf-8") as f:
        pic_tmdl = f.read()

    # Verify column percentage_difference format in TMDL
    assert "column percentage_difference" in pic_tmdl, "percentage_difference column missing from TMDL"
    assert "formatString: +0.0%;-0.0%;0.0%" in pic_tmdl, "formatString +0.0%;-0.0%;0.0% missing from TMDL"

    # Verify DAX measure Relative % Difference
    assert "measure 'Relative % Difference'" in pic_tmdl or "measure Relative % Difference" in pic_tmdl, (
        "Relative % Difference measure missing from TMDL"
    )
    assert "DIVIDE(Proposed - Baseline, Baseline)" in pic_tmdl, (
        "DIVIDE missing from Relative % Difference DAX measure in TMDL"
    )

    # Verify Power Query removes precalculated column and re-computes relative difference
    assert 'Table.RemoveColumns(#"Promoted Headers",{"percentage_difference"})' in pic_tmdl, (
        "Power Query M expression must remove precalculated CSV percentage_difference in TMDL"
    )
    assert "([proposed_value] - [baseline_value]) / [baseline_value]" in pic_tmdl, (
        "Power Query M expression must calculate relative difference as decimal ratio in TMDL"
    )

    # 3. Verify Report Visual Layout & Display Names
    rep_path = os.path.join(proj, "CareFlow_Dashboard.Report", "report.json")
    with open(rep_path, "r", encoding="utf-8") as f:
        rep = json.load(f)

    # Check Page 3 tbl_improvement_comparison layout and display names
    p3 = [p for p in rep["sections"] if p["displayName"] == "Transition Analysis & Process Improvement"][0]
    p3_table_vc = [vc for vc in p3["visualContainers"] if "tbl_improvement_comparison" in vc.get("config", "")][0]
    p3_cfg = json.loads(p3_table_vc["config"])
    p3_width = p3_cfg["layouts"][0]["position"]["width"]
    assert p3_width >= 700, f"Page 3 table width should be >= 700 to prevent text clipping, got {p3_width}"

    p3_dt = json.loads(p3_table_vc["dataTransforms"])
    p3_display_names = {s["queryName"]: s.get("displayName") for s in p3_dt.get("selects", [])}
    assert p3_display_names.get("pathway_improvement_comparison.metric_name") == "Metric"
    assert p3_display_names.get("pathway_improvement_comparison.baseline_value") == "Baseline (As-Is)"
    assert p3_display_names.get("pathway_improvement_comparison.proposed_value") == "Proposed (To-Be)"
    assert p3_display_names.get("pathway_improvement_comparison.percentage_difference") == "% Difference (Relative)"
    assert p3_display_names.get("pathway_improvement_comparison.interpretation") == "Operational Interpretation"

    # Check Page 2 tbl_case_audit display names
    p2 = [p for p in rep["sections"] if p["displayName"] == "Patient Flow"][0]
    p2_table_vc = [vc for vc in p2["visualContainers"] if "tbl_case_audit" in vc.get("config", "")][0]
    p2_dt = json.loads(p2_table_vc["dataTransforms"])
    p2_display_names = {s["queryName"]: s.get("displayName") for s in p2_dt.get("selects", [])}
    assert p2_display_names.get("stg_hospital_events.case_id") == "Case ID"
    assert p2_display_names.get("stg_hospital_events.raw_activity_name") == "Activity"
    assert p2_display_names.get("stg_hospital_events.transition_minutes_from_previous") == "Elapsed (Mins)"

    print("[VERIFIED] Semantic model TMDL, Power Query transforms, DAX measures, and report visual configurations are validated.")

if __name__ == "__main__":
    test_pbip_validation()
    test_relative_percentage_difference_calculation()
