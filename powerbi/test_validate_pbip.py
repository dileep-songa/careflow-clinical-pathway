"""
Validation test for CareFlow_Dashboard.pbip (folder-based TMDL semantic model & PBIR report)
"""
import os
import json
import csv
from collections import defaultdict
import statistics
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

    # 2. Validate semantic model (supporting both folder-based TMDL and model.bim)
    sm_dir = os.path.join(proj, "CareFlow_Dashboard.SemanticModel")
    sm_def = os.path.join(sm_dir, "definition")
    bim_path = os.path.join(sm_dir, "model.bim")
    assert os.path.exists(sm_def) or os.path.exists(bim_path), f"Missing semantic model: neither {sm_def} nor {bim_path} exists."

    expected_table_refs = [
        "stg_hospital_events",
        "stg_hospital_events (2)",
        "pathway_variants_summary",
        "bottleneck_analysis_summary",
        "pathway_improvement_comparison"
    ]
    expected_measures = [
        "Total Cases", "Total Events", "Avg Case Cycle Time (Mins)",
        "Median Case Cycle Time (Mins)", "Re-Triage Rate %",
        "Conformant Cases Count", "Repeat Triage Cases Count", "Conformance Rate %"
    ]

    if os.path.exists(sm_def):
        model_tmdl_path = os.path.join(sm_def, "model.tmdl")
        assert os.path.exists(model_tmdl_path), f"Missing model.tmdl: {model_tmdl_path}"
        with open(model_tmdl_path, "r", encoding="utf-8") as f:
            model_tmdl = f.read()

        for tbl_ref in expected_table_refs:
            assert f"ref table '{tbl_ref}'" in model_tmdl or f"ref table {tbl_ref}" in model_tmdl, (
                f"Table reference for {tbl_ref} missing from model.tmdl"
            )
        print(f"[VERIFIED TMDL] model.tmdl references all {len(expected_table_refs)} primary tables.")

        for tmdl_file in ["database.tmdl", "relationships.tmdl", os.path.join("cultures", "en-US.tmdl")]:
            fpath = os.path.join(sm_def, tmdl_file)
            assert os.path.exists(fpath), f"Missing TMDL file: {fpath}"
            print(f"[VERIFIED TMDL] {tmdl_file}")

        tables_dir = os.path.join(sm_def, "tables")
        assert os.path.exists(tables_dir), f"Missing TMDL tables directory: {tables_dir}"

        stg_path = os.path.join(tables_dir, "stg_hospital_events.tmdl")
        assert os.path.exists(stg_path), f"Missing {stg_path}"
        with open(stg_path, "r", encoding="utf-8") as f:
            stg_content = f.read()
        assert "Table.ReplaceValue" in stg_content, "Table.ReplaceValue missing from stg_hospital_events.tmdl"
        assert "Encoding=65001" in stg_content, "Encoding=65001 missing from stg_hospital_events.tmdl"
        for meas in expected_measures:
            assert f"measure '{meas}'" in stg_content or f"measure {meas}" in stg_content, (
                f"Measure '{meas}' missing from stg_hospital_events.tmdl"
            )
        print(f"[VERIFIED TMDL] stg_hospital_events.tmdl contains Table.ReplaceValue, Encoding=65001, and all {len(expected_measures)} measures.")

        stg2_path = os.path.join(tables_dir, "stg_hospital_events (2).tmdl")
        assert os.path.exists(stg2_path), f"Missing {stg2_path}"
        with open(stg2_path, "r", encoding="utf-8") as f:
            stg2_content = f.read()
        assert "excludeFromModelRefresh" in stg2_content, "excludeFromModelRefresh missing from stg_hospital_events (2).tmdl"
        assert "GoogleBigQuery" not in stg2_content, "GoogleBigQuery must not be in stg_hospital_events (2).tmdl"
        assert "Source = stg_hospital_events" not in stg2_content, "Chained/circular query reference must not be in stg_hospital_events (2).tmdl"
        assert "Csv.Document(File.Contents(" in stg2_content, "Direct CSV source missing from stg_hospital_events (2).tmdl"
        print("[VERIFIED TMDL] stg_hospital_events (2).tmdl uses independent CSV source (no circular reference) and excludeFromModelRefresh: true.")

        pvs_path = os.path.join(tables_dir, "pathway_variants_summary.tmdl")
        assert os.path.exists(pvs_path), f"Missing {pvs_path}"
        with open(pvs_path, "r", encoding="utf-8") as f:
            pvs_content = f.read()
        assert "Total Variant Cases" in pvs_content, "Total Variant Cases measure missing from pathway_variants_summary.tmdl"
        print("[VERIFIED TMDL] pathway_variants_summary.tmdl contains Total Variant Cases measure.")

        bas_path = os.path.join(tables_dir, "bottleneck_analysis_summary.tmdl")
        assert os.path.exists(bas_path), f"Missing {bas_path}"
        with open(bas_path, "r", encoding="utf-8") as f:
            bas_content = f.read()
        assert "Avg Transition Duration" in bas_content, "Avg Transition Duration measure missing from bottleneck_analysis_summary.tmdl"
        print("[VERIFIED TMDL] bottleneck_analysis_summary.tmdl contains Avg Transition Duration measure.")

        pic_path = os.path.join(tables_dir, "pathway_improvement_comparison.tmdl")
        assert os.path.exists(pic_path), f"Missing {pic_path}"
        with open(pic_path, "r", encoding="utf-8") as f:
            pic_content = f.read()
        assert "Relative % Difference" in pic_content, "Relative % Difference measure missing from pathway_improvement_comparison.tmdl"
        assert "[proposed_value] - [baseline_value]" in pic_content, "Relative change formula missing from pathway_improvement_comparison.tmdl"
        print("[VERIFIED TMDL] pathway_improvement_comparison.tmdl contains Relative % Difference and relative change formula.")

        date_template = [f for f in os.listdir(tables_dir) if f.startswith("DateTableTemplate")]
        assert len(date_template) > 0, "Missing DateTableTemplate in TMDL tables"
        local_date_tables = [f for f in os.listdir(tables_dir) if f.startswith("LocalDateTable")]
        assert len(local_date_tables) >= 4, f"Expected at least 4 LocalDateTable files, found {len(local_date_tables)}"
        print(f"[VERIFIED TMDL] Found {len(local_date_tables)} LocalDateTable files and DateTableTemplate.")

    if os.path.exists(bim_path):
        with open(bim_path, "r", encoding="utf-8") as f:
            bim = json.load(f)
        bim_tables_list = bim["model"]["tables"]
        assert len(bim_tables_list) == 10, f"Expected 10 total tables in model.bim, found {len(bim_tables_list)}"
        bim_tables = {t["name"]: t for t in bim_tables_list}
        for tbl_ref in expected_table_refs:
            assert tbl_ref in bim_tables, f"Table {tbl_ref} missing from model.bim"

        # Verify date tables in model.bim (1 template + 4 local date tables)
        date_template_bim = [t for t in bim_tables_list if t["name"].startswith("DateTableTemplate")]
        assert len(date_template_bim) > 0, "Missing DateTableTemplate in model.bim"
        local_date_tables_bim = [t for t in bim_tables_list if t["name"].startswith("LocalDateTable")]
        assert len(local_date_tables_bim) >= 4, f"Expected at least 4 LocalDateTable in model.bim, found {len(local_date_tables_bim)}"

        # Verify 19 DAX measures and their exact distribution across tables
        total_bim_measures = sum(len(t.get("measures", [])) for t in bim_tables_list)
        assert total_bim_measures == 19, f"Expected 19 DAX measures in model.bim, found {total_bim_measures}"
        assert len(bim_tables["stg_hospital_events"].get("measures", [])) == 14, "Expected 14 measures in stg_hospital_events"
        assert len(bim_tables["pathway_variants_summary"].get("measures", [])) == 3, "Expected 3 measures in pathway_variants_summary"
        assert len(bim_tables["bottleneck_analysis_summary"].get("measures", [])) == 1, "Expected 1 measure in bottleneck_analysis_summary"
        assert len(bim_tables["pathway_improvement_comparison"].get("measures", [])) == 1, "Expected 1 measure in pathway_improvement_comparison"

        stg_meas = {m["name"] for m in bim_tables["stg_hospital_events"].get("measures", [])}
        for meas in expected_measures:
            assert meas in stg_meas, f"Measure {meas} missing from model.bim stg_hospital_events"
        stg2_bim = bim_tables["stg_hospital_events (2)"]
        assert stg2_bim.get("excludeFromModelRefresh") is True, "excludeFromModelRefresh missing in model.bim"
        stg2_expr = "".join(stg2_bim["partitions"][0]["source"]["expression"])
        assert "Source = stg_hospital_events" not in stg2_expr, "Chained/circular query reference must not be in model.bim stg_hospital_events (2)"
        assert "Csv.Document(File.Contents(" in stg2_expr, "Direct CSV source missing from model.bim stg_hospital_events (2)"
        print(f"[VERIFIED BIM] model.bim verified with all {len(bim_tables_list)} tables (5 data + {len(date_template_bim) + len(local_date_tables_bim)} date) and {total_bim_measures} DAX measures (no circular reference).")

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
                has_query = ("query" in vc) or ("prototypeQuery" in cfg.get("singleVisual", {}))
                assert has_query, f"Visual {vname} missing query definition"
                if "query" in vc:
                    query_obj = json.loads(vc["query"])
                    assert "Commands" in query_obj, f"Visual {vname} query missing Commands"
                elif "prototypeQuery" in cfg.get("singleVisual", {}):
                    pq = cfg["singleVisual"]["prototypeQuery"]
                    assert "Select" in pq or "From" in pq, f"Visual {vname} prototypeQuery missing Select/From"

                has_transforms = ("dataTransforms" in vc) or ("projections" in cfg.get("singleVisual", {}))
                assert has_transforms, f"Visual {vname} missing dataTransforms or projections"
                if "dataTransforms" in vc:
                    dt = json.loads(vc["dataTransforms"])
                    assert "selects" in dt and len(dt["selects"]) > 0, f"Visual {vname} missing dt.selects"
                    assert "projectionOrdering" in dt, f"Visual {vname} missing dt.projectionOrdering"
                elif "projections" in cfg.get("singleVisual", {}):
                    assert len(cfg["singleVisual"]["projections"]) > 0, f"Visual {vname} missing projections"

    assert total_data_visuals in [15, 16], f"Expected 15 or 16 data visuals, found {total_data_visuals}"
    assert total_textboxes in [3, 6], f"Expected 3 or 6 textbox visuals, found {total_textboxes}"
    print(f"\n[VERIFIED visualContainers] All {total_data_visuals} data visuals have valid query and dataTransforms.")

    # Check Page 1 Total Events visual display units
    p1 = sections[0]
    total_events_vc = [vc for vc in p1["visualContainers"] if json.loads(vc["config"])["name"] == "card_total_events"][0]
    cfg_te = json.loads(total_events_vc["config"])
    val_props = cfg_te["singleVisual"]["objects"]["value"][0]["properties"]
    display_unit_setting = val_props.get("labelDisplayUnits") or val_props.get("displayUnits") or val_props.get("valueDisplayUnits")
    assert display_unit_setting is not None, "card_total_events value properties must explicitly define a display-unit setting (labelDisplayUnits, displayUnits, or valueDisplayUnits)"
    callout_obj = display_unit_setting["expr"]["Literal"]["Value"]
    assert callout_obj == "1D", f"Expected display-unit setting '1D' (None), found {callout_obj}"
    print(f"[VERIFIED] card_total_events is explicitly configured with display-unit setting = {callout_obj} (None).")

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

    # 2. Verify semantic model schema and M partition in TMDL and/or model.bim
    proj = str(PROJ_DIR)
    sm_dir = os.path.join(proj, "CareFlow_Dashboard.SemanticModel")
    pic_path = os.path.join(sm_dir, "definition", "tables", "pathway_improvement_comparison.tmdl")
    bim_path = os.path.join(sm_dir, "model.bim")
    assert os.path.exists(pic_path) or os.path.exists(bim_path), "Missing semantic model definitions"

    if os.path.exists(pic_path):
        with open(pic_path, "r", encoding="utf-8") as f:
            pic_tmdl = f.read()
        assert "column percentage_difference" in pic_tmdl, "percentage_difference column missing from TMDL"
        assert "formatString: +0.0%;-0.0%;0.0%" in pic_tmdl, "formatString +0.0%;-0.0%;0.0% missing from TMDL"
        assert "measure 'Relative % Difference'" in pic_tmdl or "measure Relative % Difference" in pic_tmdl, (
            "Relative % Difference measure missing from TMDL"
        )
        assert "DIVIDE(Proposed - Baseline, Baseline)" in pic_tmdl, (
            "DIVIDE missing from Relative % Difference DAX measure in TMDL"
        )
        assert 'Table.RemoveColumns(#"Promoted Headers",{"percentage_difference"})' in pic_tmdl, (
            "Power Query M expression must remove precalculated CSV percentage_difference in TMDL"
        )
        assert "([proposed_value] - [baseline_value]) / [baseline_value]" in pic_tmdl, (
            "Power Query M expression must calculate relative difference as decimal ratio in TMDL"
        )

    if os.path.exists(bim_path):
        with open(bim_path, "r", encoding="utf-8") as f:
            bim_data = json.load(f)
        bim_tables = {t["name"]: t for t in bim_data["model"]["tables"]}
        assert "pathway_improvement_comparison" in bim_tables
        pic_tbl = bim_tables["pathway_improvement_comparison"]
        cols = {c["name"]: c for c in pic_tbl["columns"]}
        assert "percentage_difference" in cols
        assert cols["percentage_difference"].get("formatString") == "+0.0%;-0.0%;0.0%"
        measures = {m["name"]: m for m in pic_tbl.get("measures", [])}
        assert "Relative % Difference" in measures
        m_expr = pic_tbl["partitions"][0]["source"]["expression"]
        m_str = "\n".join(m_expr) if isinstance(m_expr, list) else m_expr
        assert 'Table.RemoveColumns(#"Promoted Headers",{"percentage_difference"})' in m_str
        assert "([proposed_value] - [baseline_value]) / [baseline_value]" in m_str

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

    if "dataTransforms" in p3_table_vc:
        p3_dt = json.loads(p3_table_vc["dataTransforms"])
        p3_display_names = {s["queryName"]: s.get("displayName") for s in p3_dt.get("selects", [])}
        assert p3_display_names.get("pathway_improvement_comparison.metric_name") in ["Metric", "Clinical Metric"]
        assert p3_display_names.get("pathway_improvement_comparison.baseline_value") in ["Baseline", "Baseline (As-Is)"]
        assert p3_display_names.get("pathway_improvement_comparison.proposed_value") in ["Proposed", "Proposed (To-Be)"]
        assert p3_display_names.get("pathway_improvement_comparison.percentage_difference") in ["Change %", "Change (%)", "% Difference (Relative)", "% Difference"]
        if "pathway_improvement_comparison.interpretation" in p3_display_names:
            assert p3_display_names.get("pathway_improvement_comparison.interpretation") == "Operational Interpretation"

    # Check Page 2 tbl_case_audit display names
    p2 = [p for p in rep["sections"] if p["displayName"] == "Patient Flow"][0]
    p2_table_vc = [vc for vc in p2["visualContainers"] if "tbl_case_audit" in vc.get("config", "")][0]
    if "dataTransforms" in p2_table_vc:
        p2_dt = json.loads(p2_table_vc["dataTransforms"])
        p2_display_names = {s["queryName"]: s.get("displayName") for s in p2_dt.get("selects", [])}
        assert p2_display_names.get("stg_hospital_events.case_id") == "Case ID"
        assert p2_display_names.get("stg_hospital_events.raw_activity_name") in ["Activity", "Activity Name"]
        if "stg_hospital_events.transition_minutes_from_previous" in p2_display_names:
            assert p2_display_names.get("stg_hospital_events.transition_minutes_from_previous") == "Elapsed (Mins)"

    print("[VERIFIED] Semantic model TMDL, Power Query transforms, DAX measures, and report visual configurations are validated.")



def test_case_cycle_time_measures_and_activity_volume():
    """
    Validates DAX expressions and report bindings for:
      - Avg Case Cycle Time (Mins) and Median Case Cycle Time (Mins)
      - Clinical Activity Volume chart (bar_activity_breakdown)
      - Exact dataset baselines from data/cleaned/stg_hospital_events.csv
    """
    proj = str(PROJ_DIR)
    sm_dir = os.path.join(proj, "CareFlow_Dashboard.SemanticModel")
    tmdl_path = os.path.join(sm_dir, "definition", "tables", "stg_hospital_events.tmdl")
    bim_path = os.path.join(sm_dir, "model.bim")

    # 1. Verify DAX pattern in TMDL
    if os.path.exists(tmdl_path):
        with open(tmdl_path, "r", encoding="utf-8") as f:
            tmdl = f.read()
        assert "measure 'Avg Case Cycle Time (Mins)' =" in tmdl
        assert "AVERAGEX(" in tmdl
        assert "VALUES('stg_hospital_events'[case_id])" in tmdl
        assert "CALCULATE(SUM('stg_hospital_events'[transition_minutes_from_previous]))" in tmdl
        assert ('formatString: 0.0 "mins"' in tmdl) or ('formatString: 0.0 "min"' in tmdl)

        assert "measure 'Median Case Cycle Time (Mins)' =" in tmdl
        assert "MEDIANX(" in tmdl
        print("[VERIFIED TMDL] Duration measures use canonical AVERAGEX/MEDIANX without virtual column lineage issues.")

    # 2. Verify DAX pattern in model.bim
    if os.path.exists(bim_path):
        with open(bim_path, "r", encoding="utf-8") as f:
            bim = json.load(f)
        stg_tbl = [t for t in bim["model"]["tables"] if t["name"] == "stg_hospital_events"][0]
        meas_dict = {m["name"]: m for m in stg_tbl.get("measures", [])}
        assert "Avg Case Cycle Time (Mins)" in meas_dict
        assert "Median Case Cycle Time (Mins)" in meas_dict
        avg_expr = meas_dict["Avg Case Cycle Time (Mins)"]["expression"]
        avg_str = "\n".join(avg_expr) if isinstance(avg_expr, list) else avg_expr
        assert "AVERAGEX" in avg_str
        assert "VALUES('stg_hospital_events'[case_id])" in avg_str
        assert meas_dict["Avg Case Cycle Time (Mins)"].get("formatString") in ['0.0 "mins"', '0.0 "min"']
        assert meas_dict["Median Case Cycle Time (Mins)"].get("formatString") in ['0.0 "mins"', '0.0 "min"']
        print('[VERIFIED BIM] Duration measures verified in model.bim with canonical DAX and formatString 0.0 "mins".')

    # 3. Verify report visuals: cards and bar chart
    rep_path = os.path.join(proj, "CareFlow_Dashboard.Report", "report.json")
    with open(rep_path, "r", encoding="utf-8") as f:
        rep = json.load(f)

    p1 = [p for p in rep["sections"] if p["displayName"] == "Hospital Overview"][0]
    p1_vcs = {json.loads(vc["config"])["name"]: vc for vc in p1["visualContainers"]}

    # Duration cards
    if "dataTransforms" in p1_vcs["card_avg_duration"]:
        card_avg_dt = json.loads(p1_vcs["card_avg_duration"]["dataTransforms"])
        assert card_avg_dt["selects"][0]["format"] in ['0.0 "mins"', '0.0 "min"']
    if "dataTransforms" in p1_vcs["card_med_duration"]:
        card_med_dt = json.loads(p1_vcs["card_med_duration"]["dataTransforms"])
        assert card_med_dt["selects"][0]["format"] in ['0.0 "mins"', '0.0 "min"']
    print('[VERIFIED Visual] Duration card visuals configured with formatString 0.0 "mins".')

    # Clinical Activity Volume chart
    bar_vc = p1_vcs["bar_activity_breakdown"]
    bar_cfg = json.loads(bar_vc["config"])
    assert bar_cfg["singleVisual"]["visualType"] == "clusteredBarChart", "bar_activity_breakdown must be a clusteredBarChart"

    cat_axis = bar_cfg["singleVisual"]["objects"]["categoryAxis"][0]["properties"]
    val_axis = bar_cfg["singleVisual"]["objects"]["valueAxis"][0]["properties"]
    assert cat_axis["showAxisTitle"]["expr"]["Literal"]["Value"] == "true", "Category axis title should be shown"
    assert cat_axis["titleText"]["expr"]["Literal"]["Value"] == "'Clinical Activity'", f"Expected category title 'Clinical Activity', got {cat_axis['titleText']['expr']['Literal']['Value']}"
    assert val_axis["showAxisTitle"]["expr"]["Literal"]["Value"] == "true", "Value axis title should be shown"
    assert val_axis["titleText"]["expr"]["Literal"]["Value"] == "'Event Count'", f"Expected value title 'Event Count', got {val_axis['titleText']['expr']['Literal']['Value']}"

    show_labels = bar_cfg["singleVisual"]["objects"]["labels"][0]["properties"]["show"]["expr"]["Literal"]["Value"]
    assert show_labels == "true", f"Expected show_labels 'true', got {show_labels}"
    data_point_color = bar_cfg["singleVisual"]["objects"]["dataPoint"][0]["properties"]["fill"]["solid"]["color"]["expr"]["Literal"]["Value"]
    assert data_point_color == "'#0D9488'", f"Expected bar color '#0D9488', got {data_point_color}"

    # If title is present in visualContainerObjects, vcObjects, or objects, validate text
    title_obj = (
        bar_cfg.get("singleVisual", {}).get("vcObjects", {}).get("title")
        or bar_cfg.get("singleVisual", {}).get("visualContainerObjects", {}).get("title")
        or bar_cfg.get("singleVisual", {}).get("objects", {}).get("title")
    )
    if title_obj:
        bar_title = title_obj[0]["properties"]["text"]["expr"]["Literal"]["Value"]
        assert bar_title == "'Clinical Activity Volume'", f"Expected 'Clinical Activity Volume', got {bar_title}"

    if "maxMargin" in cat_axis:
        max_margin = cat_axis["maxMargin"]["expr"]["Literal"]["Value"]
        assert max_margin in ["35D", "50D"], f"Expected maxMargin '35D' or '50D', got {max_margin}"

    if "dataTransforms" in bar_vc:
        bar_dt = json.loads(bar_vc["dataTransforms"])
        disp_names = {s["queryName"]: s.get("displayName") for s in bar_dt["selects"]}
        assert disp_names.get("stg_hospital_events.raw_activity_name") in ["Clinical Activity", "Activity", "raw_activity_name"]
        assert disp_names.get("stg_hospital_events.Total Events") in ["Event Count", "Total Events", None]
    print("[VERIFIED Visual] bar_activity_breakdown configured with category axis 'Clinical Activity', value axis 'Event Count', and data labels.")

    # Donut chart formatting on Page 1
    donut_vc = p1_vcs["donut_dept_breakdown"]
    donut_cfg = json.loads(donut_vc["config"])
    donut_labels = donut_cfg["singleVisual"]["objects"]["labels"][0]["properties"]
    assert donut_labels["labelStyle"]["expr"]["Literal"]["Value"] == "'Both'"
    donut_disp_unit = (donut_labels.get("labelDisplayUnits") or donut_labels.get("displayUnits"))["expr"]["Literal"]["Value"]
    assert donut_disp_unit == "1D"
    assert donut_labels["labelPrecision"]["expr"]["Literal"]["Value"] == "0D"
    print("[VERIFIED Visual] donut_dept_breakdown configured with labelStyle='Both', displayUnits=1D (exact counts), and labelPrecision=0D.")

    # Bottlenecks chart on Page 3
    p3 = [p for p in rep["sections"] if p["displayName"] == "Transition Analysis & Process Improvement"][0]
    p3_vcs = {json.loads(vc["config"])["name"]: vc for vc in p3["visualContainers"]}
    bot_cfg = json.loads(p3_vcs["bar_bottlenecks"]["config"])
    bot_title_obj = (
        bot_cfg.get("singleVisual", {}).get("vcObjects", {}).get("title")
        or bot_cfg.get("singleVisual", {}).get("visualContainerObjects", {}).get("title")
        or bot_cfg.get("singleVisual", {}).get("objects", {}).get("title")
    )
    assert bot_title_obj is not None, "Missing title object for bar_bottlenecks"
    bot_title = bot_title_obj[0]["properties"]["text"]["expr"]["Literal"]["Value"]
    assert bot_title == "'Highest Observed Transition Durations'", f"Expected 'Highest Observed Transition Durations', got {bot_title}"
    print("[VERIFIED Visual] bar_bottlenecks configured with title 'Highest Observed Transition Durations'.")

    # 4. Verify exact dataset metrics from stg_hospital_events.csv
    repo_root = Path(proj).parent.parent
    csv_file = repo_root / "data" / "cleaned" / "stg_hospital_events.csv"
    assert csv_file.exists(), f"Missing dataset: {csv_file}"

    case_durations = defaultdict(float)
    activity_counts = defaultdict(int)
    total_events = 0
    cases_seen = set()
    retriage_cases = set()

    with open(csv_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cid = row["case_id"]
            cases_seen.add(cid)
            total_events += 1
            act = row["raw_activity_name"]
            activity_counts[act] += 1
            trans_min = row["transition_minutes_from_previous"]
            if trans_min and trans_min.strip():
                case_durations[cid] += float(trans_min)
            if act == "Triage" and row["previous_activity"] == "Triage":
                retriage_cases.add(cid)

    total_cases = len(cases_seen)
    assert total_cases == 500, f"Expected 500 cases, got {total_cases}"
    assert total_events == 3140, f"Expected 3140 events, got {total_events}"

    durations_list = [case_durations[cid] for cid in cases_seen]
    mean_dur = statistics.mean(durations_list)
    med_dur = statistics.median(durations_list)

    assert round(mean_dur, 1) == 202.5, f"Expected mean duration 202.5, got {mean_dur:.3f}"
    assert round(med_dur, 1) == 211.0, f"Expected median duration 211.0, got {med_dur:.3f}"

    conformant_count = total_cases - len(retriage_cases)
    assert conformant_count == 440, f"Expected 440 conformant cases, got {conformant_count}"
    assert len(retriage_cases) == 60, f"Expected 60 re-triage cases, got {len(retriage_cases)}"

    # Confirm equal activity volume for Registration, Treatment, and Discharge (500 each)
    assert activity_counts["Registration"] == 500, f"Expected 500 Registration events, got {activity_counts['Registration']}"
    assert activity_counts["Treatment"] == 500, f"Expected 500 Treatment events, got {activity_counts['Treatment']}"
    assert activity_counts["Discharge"] == 500, f"Expected 500 Discharge events, got {activity_counts['Discharge']}"
    assert activity_counts["Registration"] == activity_counts["Treatment"] == activity_counts["Discharge"], (
        "Registration, Treatment, and Discharge must have exactly identical volume (equal bar lengths)"
    )
    print(f"[VERIFIED Baseline Data] 500 cases, 3,140 events, {mean_dur:.1f}m mean, {med_dur:.1f}m median, Registration=Treatment=Discharge=500.")


def test_report_json_synchronization():
    """
    Verifies that CareFlow_Dashboard.Report/report.json exists and is valid JSON.
    If CareFlow_Dashboard.Report/definition/report.json is also present, verifies
    they are SHA-256 byte-identical.
    """
    import hashlib
    proj = str(PROJ_DIR)
    rep_root = os.path.join(proj, "CareFlow_Dashboard.Report", "report.json")
    rep_def = os.path.join(proj, "CareFlow_Dashboard.Report", "definition", "report.json")

    assert os.path.exists(rep_root), f"Missing root report file: {rep_root}"
    with open(rep_root, "r", encoding="utf-8") as f:
        rep_data = json.load(f)
    assert "sections" in rep_data, "Root report.json missing 'sections'"
    assert len(rep_data["sections"]) >= 3, f"Expected at least 3 report sections, found {len(rep_data['sections'])}"
    print("[VERIFIED Report JSON] Root report.json exists, is valid JSON, and contains all required sections.")

    if os.path.exists(rep_def):
        with open(rep_root, "rb") as f1, open(rep_def, "rb") as f2:
            h1 = hashlib.sha256(f1.read()).hexdigest()
            h2 = hashlib.sha256(f2.read()).hexdigest()
        assert h1 == h2, f"SHA-256 mismatch between root and definition report.json: {h1} vs {h2}"
        print(f"[VERIFIED Synchronization] report.json files are byte-identical (SHA-256: {h1[:16]}...).")

if __name__ == "__main__":
    test_pbip_validation()
    test_relative_percentage_difference_calculation()
    test_case_cycle_time_measures_and_activity_volume()
    test_report_json_synchronization()
