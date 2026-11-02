"""
Complete generator for CareFlow_Dashboard.pbip with full SemanticQueryDataShapeCommand
queries, dataTransforms, theme resource packages, and local-safe partition settings.
"""

import os
import json
import shutil
import zipfile

import json

def get_card_visual(name, x, y, w, h, z, entity, measure_name, display_units_none=False, format_string="#,##0"):
    cfg = {
        "name": name,
        "layouts": [
            {
                "id": 0,
                "position": {"x": x, "y": y, "width": w, "height": h, "z": z, "tabOrder": z}
            }
        ],
        "singleVisual": {
            "visualType": "cardVisual",
            "projections": {
                "Data": [{"queryRef": f"{entity}.{measure_name}"}]
            },
            "prototypeQuery": {
                "Version": 2,
                "From": [{"Name": "s", "Entity": entity, "Type": 0}],
                "Select": [
                    {
                        "Measure": {
                            "Expression": {"SourceRef": {"Source": "s"}},
                            "Property": measure_name
                        },
                        "Name": f"{entity}.{measure_name}",
                        "NativeReferenceName": measure_name
                    }
                ],
                "OrderBy": [
                    {
                        "Direction": 2,
                        "Expression": {
                            "Measure": {
                                "Expression": {"SourceRef": {"Source": "s"}},
                                "Property": measure_name
                            }
                        }
                    }
                ]
            },
            "drillFilterOtherVisuals": True,
            "hasDefaultSort": True
        }
    }
    if display_units_none:
        cfg["singleVisual"]["objects"] = {
            "value": [
                {
                    "properties": {
                        "displayUnits": {
                            "expr": {"Literal": {"Value": "1D"}}
                        }
                    }
                }
            ]
        }

    query = {
        "Commands": [
            {
                "SemanticQueryDataShapeCommand": {
                    "Query": {
                        "Version": 2,
                        "From": [{"Name": "s", "Entity": entity, "Type": 0}],
                        "Select": [
                            {
                                "Measure": {
                                    "Expression": {"SourceRef": {"Source": "s"}},
                                    "Property": measure_name
                                },
                                "Name": f"{entity}.{measure_name}",
                                "NativeReferenceName": measure_name
                            }
                        ]
                    },
                    "Binding": {
                        "Primary": {
                            "Groupings": [{"Projections": [0]}]
                        },
                        "Version": 1
                    },
                    "ExecutionMetricsKind": 1
                }
            }
        ]
    }

    data_transforms = {
        "projectionOrdering": {"Data": [0]},
        "queryMetadata": {
            "Select": [
                {
                    "Restatement": measure_name,
                    "Name": f"{entity}.{measure_name}",
                    "Type": 3,
                    "Format": format_string
                }
            ],
            "Filters": [
                {
                    "type": 2,
                    "expression": {
                        "Measure": {
                            "Expression": {"SourceRef": {"Entity": entity}},
                            "Property": measure_name
                        }
                    }
                }
            ]
        },
        "visualElements": [
            {"DataRoles": [{"Name": "Data", "Projection": 0, "isActive": False}]}
        ],
        "selects": [
            {
                "displayName": measure_name,
                "format": format_string,
                "queryName": f"{entity}.{measure_name}",
                "roles": {"Data": True},
                "type": {"category": None, "underlyingType": 260},
                "expr": {
                    "Measure": {
                        "Expression": {"SourceRef": {"Entity": entity}},
                        "Property": measure_name
                    }
                }
            }
        ]
    }

    return {
        "x": x,
        "y": y,
        "z": z,
        "width": w,
        "height": h,
        "config": json.dumps(cfg),
        "filters": "[]",
        "query": json.dumps(query),
        "dataTransforms": json.dumps(data_transforms)
    }

def get_donut_chart(name, x, y, w, h, z, entity, category_col, val_measure):
    cfg = {
        "name": name,
        "layouts": [
            {
                "id": 0,
                "position": {"x": x, "y": y, "width": w, "height": h, "z": z, "tabOrder": z}
            }
        ],
        "singleVisual": {
            "visualType": "donutChart",
            "projections": {
                "Category": [{"queryRef": f"{entity}.{category_col}"}],
                "Y": [{"queryRef": f"{entity}.{val_measure}"}]
            },
            "prototypeQuery": {
                "Version": 2,
                "From": [{"Name": "s", "Entity": entity, "Type": 0}],
                "Select": [
                    {
                        "Column": {"Expression": {"SourceRef": {"Source": "s"}}, "Property": category_col},
                        "Name": f"{entity}.{category_col}",
                        "NativeReferenceName": category_col
                    },
                    {
                        "Measure": {"Expression": {"SourceRef": {"Source": "s"}}, "Property": val_measure},
                        "Name": f"{entity}.{val_measure}",
                        "NativeReferenceName": val_measure
                    }
                ]
            },
            "drillFilterOtherVisuals": True
        }
    }

    query = {
        "Commands": [
            {
                "SemanticQueryDataShapeCommand": {
                    "Query": {
                        "Version": 2,
                        "From": [{"Name": "s", "Entity": entity, "Type": 0}],
                        "Select": [
                            {
                                "Column": {"Expression": {"SourceRef": {"Source": "s"}}, "Property": category_col},
                                "Name": f"{entity}.{category_col}",
                                "NativeReferenceName": category_col
                            },
                            {
                                "Measure": {"Expression": {"SourceRef": {"Source": "s"}}, "Property": val_measure},
                                "Name": f"{entity}.{val_measure}",
                                "NativeReferenceName": val_measure
                            }
                        ]
                    },
                    "Binding": {
                        "Primary": {"Groupings": [{"Projections": [0, 1]}]},
                        "Version": 1
                    },
                    "ExecutionMetricsKind": 1
                }
            }
        ]
    }

    data_transforms = {
        "projectionOrdering": {"Category": [0], "Y": [1]},
        "queryMetadata": {
            "Select": [
                {"Restatement": category_col, "Name": f"{entity}.{category_col}", "Type": 1},
                {"Restatement": val_measure, "Name": f"{entity}.{val_measure}", "Type": 3}
            ]
        },
        "visualElements": [
            {"DataRoles": [{"Name": "Category", "Projection": 0, "isActive": False}, {"Name": "Y", "Projection": 1, "isActive": False}]}
        ],
        "selects": [
            {
                "displayName": category_col,
                "queryName": f"{entity}.{category_col}",
                "roles": {"Category": True},
                "type": {"category": None, "underlyingType": 1},
                "expr": {
                    "Column": {
                        "Expression": {"SourceRef": {"Entity": entity}},
                        "Property": category_col
                    }
                }
            },
            {
                "displayName": val_measure,
                "queryName": f"{entity}.{val_measure}",
                "roles": {"Y": True},
                "type": {"category": None, "underlyingType": 260},
                "expr": {
                    "Measure": {
                        "Expression": {"SourceRef": {"Entity": entity}},
                        "Property": val_measure
                    }
                }
            }
        ]
    }

    return {
        "x": x,
        "y": y,
        "z": z,
        "width": w,
        "height": h,
        "config": json.dumps(cfg),
        "filters": "[]",
        "query": json.dumps(query),
        "dataTransforms": json.dumps(data_transforms)
    }

def get_bar_chart_measure(name, x, y, w, h, z, entity, category_col, val_measure):
    res = get_donut_chart(name, x, y, w, h, z, entity, category_col, val_measure)
    cfg = json.loads(res["config"])
    cfg["singleVisual"]["visualType"] = "clusteredBarChart"
    res["config"] = json.dumps(cfg)
    return res

def get_column_chart(name, x, y, w, h, z, entity, category_col, val_measure):
    res = get_donut_chart(name, x, y, w, h, z, entity, category_col, val_measure)
    cfg = json.loads(res["config"])
    cfg["singleVisual"]["visualType"] = "clusteredColumnChart"
    res["config"] = json.dumps(cfg)
    return res

def get_bar_chart_cols(name, x, y, w, h, z, entity, category_col, val_col):
    cfg = {
        "name": name,
        "layouts": [
            {
                "id": 0,
                "position": {"x": x, "y": y, "width": w, "height": h, "z": z, "tabOrder": z}
            }
        ],
        "singleVisual": {
            "visualType": "clusteredBarChart",
            "projections": {
                "Category": [{"queryRef": f"{entity}.{category_col}"}],
                "Y": [{"queryRef": f"{entity}.{val_col}"}]
            },
            "prototypeQuery": {
                "Version": 2,
                "From": [{"Name": "s", "Entity": entity, "Type": 0}],
                "Select": [
                    {
                        "Column": {"Expression": {"SourceRef": {"Source": "s"}}, "Property": category_col},
                        "Name": f"{entity}.{category_col}",
                        "NativeReferenceName": category_col
                    },
                    {
                        "Column": {"Expression": {"SourceRef": {"Source": "s"}}, "Property": val_col},
                        "Name": f"{entity}.{val_col}",
                        "NativeReferenceName": val_col
                    }
                ]
            },
            "drillFilterOtherVisuals": True
        }
    }

    query = {
        "Commands": [
            {
                "SemanticQueryDataShapeCommand": {
                    "Query": {
                        "Version": 2,
                        "From": [{"Name": "s", "Entity": entity, "Type": 0}],
                        "Select": [
                            {
                                "Column": {"Expression": {"SourceRef": {"Source": "s"}}, "Property": category_col},
                                "Name": f"{entity}.{category_col}",
                                "NativeReferenceName": category_col
                            },
                            {
                                "Column": {"Expression": {"SourceRef": {"Source": "s"}}, "Property": val_col},
                                "Name": f"{entity}.{val_col}",
                                "NativeReferenceName": val_col
                            }
                        ]
                    },
                    "Binding": {
                        "Primary": {"Groupings": [{"Projections": [0, 1]}]},
                        "Version": 1
                    },
                    "ExecutionMetricsKind": 1
                }
            }
        ]
    }

    data_transforms = {
        "projectionOrdering": {"Category": [0], "Y": [1]},
        "queryMetadata": {
            "Select": [
                {"Restatement": category_col, "Name": f"{entity}.{category_col}", "Type": 1},
                {"Restatement": val_col, "Name": f"{entity}.{val_col}", "Type": 2}
            ]
        },
        "visualElements": [
            {"DataRoles": [{"Name": "Category", "Projection": 0, "isActive": False}, {"Name": "Y", "Projection": 1, "isActive": False}]}
        ],
        "selects": [
            {
                "displayName": category_col,
                "queryName": f"{entity}.{category_col}",
                "roles": {"Category": True},
                "type": {"category": None, "underlyingType": 1},
                "expr": {
                    "Column": {
                        "Expression": {"SourceRef": {"Entity": entity}},
                        "Property": category_col
                    }
                }
            },
            {
                "displayName": val_col,
                "queryName": f"{entity}.{val_col}",
                "roles": {"Y": True},
                "type": {"category": None, "underlyingType": 260},
                "expr": {
                    "Column": {
                        "Expression": {"SourceRef": {"Entity": entity}},
                        "Property": val_col
                    }
                }
            }
        ]
    }

    return {
        "x": x,
        "y": y,
        "z": z,
        "width": w,
        "height": h,
        "config": json.dumps(cfg),
        "filters": "[]",
        "query": json.dumps(query),
        "dataTransforms": json.dumps(data_transforms)
    }

def get_table_visual(name, x, y, w, h, z, entity, columns, display_names=None):
    if display_names is None:
        display_names = {}
    projections = [{"queryRef": f"{entity}.{c}"} for c in columns]
    selects = [
        {
            "Column": {"Expression": {"SourceRef": {"Source": "s"}}, "Property": c},
            "Name": f"{entity}.{c}",
            "NativeReferenceName": c
        }
        for c in columns
    ]
    cfg = {
        "name": name,
        "layouts": [
            {
                "id": 0,
                "position": {"x": x, "y": y, "width": w, "height": h, "z": z, "tabOrder": z}
            }
        ],
        "singleVisual": {
            "visualType": "tableEx",
            "projections": {"Values": projections},
            "prototypeQuery": {
                "Version": 2,
                "From": [{"Name": "s", "Entity": entity, "Type": 0}],
                "Select": selects
            },
            "drillFilterOtherVisuals": True
        }
    }

    query = {
        "Commands": [
            {
                "SemanticQueryDataShapeCommand": {
                    "Query": {
                        "Version": 2,
                        "From": [{"Name": "s", "Entity": entity, "Type": 0}],
                        "Select": selects
                    },
                    "Binding": {
                        "Primary": {"Groupings": [{"Projections": list(range(len(columns)))}]},
                        "Version": 1
                    },
                    "ExecutionMetricsKind": 1
                }
            }
        ]
    }

    data_transforms = {
        "projectionOrdering": {"Values": list(range(len(columns)))},
        "queryMetadata": {
            "Select": [
                {"Restatement": display_names.get(c, c), "Name": f"{entity}.{c}", "Type": 1}
                for c in columns
            ]
        },
        "visualElements": [
            {"DataRoles": [{"Name": "Values", "Projection": i, "isActive": False} for i in range(len(columns))]}
        ],
        "selects": [
            {
                "displayName": display_names.get(c, c),
                "queryName": f"{entity}.{c}",
                "roles": {"Values": True},
                "type": {"category": None, "underlyingType": 1},
                "expr": {
                    "Column": {
                        "Expression": {"SourceRef": {"Entity": entity}},
                        "Property": c
                    }
                }
            }
            for c in columns
        ]
    }

    return {
        "x": x,
        "y": y,
        "z": z,
        "width": w,
        "height": h,
        "config": json.dumps(cfg),
        "filters": "[]",
        "query": json.dumps(query),
        "dataTransforms": json.dumps(data_transforms)
    }

def get_textbox_visual(name, x, y, w, h, z, text_content):
    cfg = {
        "name": name,
        "layouts": [
            {
                "id": 0,
                "position": {"x": x, "y": y, "width": w, "height": h, "z": z, "tabOrder": z}
            }
        ],
        "singleVisual": {
            "visualType": "textbox",
            "objects": {
                "general": [
                    {
                        "properties": {
                            "paragraphs": [
                                {
                                    "textRuns": [
                                        {
                                            "value": text_content,
                                            "textStyle": {
                                                "fontFamily": "Segoe UI",
                                                "fontSize": "10pt"
                                            }
                                        }
                                    ]
                                }
                            ]
                        }
                    }
                ]
            }
        }
    }
    return {
        "x": x,
        "y": y,
        "z": z,
        "width": w,
        "height": h,
        "config": json.dumps(cfg),
        "filters": "[]"
    }



import json
import os

def update_model_bim(bim_path, repo_root=None):
    if repo_root is None:
        repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    csv_events = os.path.join(repo_root, "data", "cleaned", "stg_hospital_events.csv")
    csv_variants = os.path.join(repo_root, "outputs", "pathway_variants_summary.csv")
    csv_bottlenecks = os.path.join(repo_root, "outputs", "bottleneck_analysis_summary.csv")
    csv_improvement = os.path.join(repo_root, "outputs", "pathway_improvement_comparison.csv")
    with open(bim_path, 'r', encoding='utf-8') as f:
        bim = json.load(f)

    # 1. Update stg_hospital_events
    for t in bim['model']['tables']:
        if t['name'] == 'stg_hospital_events':
            t['partitions'][0]['source']['expression'] = [
                'let',
                f'    Source = Csv.Document(File.Contents("{csv_events}"),[Delimiter=",", Columns=11, Encoding=65001, QuoteStyle=QuoteStyle.None]),',
                '    #"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),',
                '    #"Replaced Empty Strings" = Table.ReplaceValue(#"Promoted Headers", "", null, Replacer.ReplaceValue, {"previous_activity", "transition_minutes_from_previous"}),',
                '    #"Changed Type" = Table.TransformColumnTypes(#"Replaced Empty Strings",{{"case_id", type text}, {"event_sequence", Int64.Type}, {"raw_activity_name", type text}, {"activity_name", type text}, {"event_timestamp", type datetime}, {"event_date", type date}, {"department", type text}, {"resource_id", type text}, {"data_provenance", type text}, {"previous_activity", type text}, {"transition_minutes_from_previous", Int64.Type}})',
                'in',
                '    #"Changed Type"'
            ]
            for m in t.get('measures', []):
                if m['name'] == 'Conformant Cases Count':
                    m['expression'] = '[Total Cases] - [Repeat Triage Cases Count]'
                elif m['name'] == 'Avg Case Cycle Time (Mins)':
                    m['expression'] = [
                        'VAR CaseDurations =',
                        '    ADDCOLUMNS(',
                        "        VALUES('stg_hospital_events'[case_id]),",
                        '        "CaseTotalMinutes",',
                        "        CALCULATE(SUM('stg_hospital_events'[transition_minutes_from_previous]))",
                        '    )',
                        'RETURN',
                        'AVERAGEX(CaseDurations, [CaseTotalMinutes])'
                    ]
                elif m['name'] == 'Median Case Cycle Time (Mins)':
                    m['expression'] = [
                        'VAR CaseDurations =',
                        '    ADDCOLUMNS(',
                        "        VALUES('stg_hospital_events'[case_id]),",
                        '        "CaseTotalMinutes",',
                        "        CALCULATE(SUM('stg_hospital_events'[transition_minutes_from_previous]))",
                        '    )',
                        'RETURN',
                        'MEDIANX(CaseDurations, [CaseTotalMinutes])'
                    ]

        elif t['name'] == 'stg_hospital_events (2)':
            t['excludeFromModelRefresh'] = True
            t['partitions'][0]['source']['expression'] = [
                'let',
                '    Source = stg_hospital_events',
                'in',
                '    Source'
            ]

        elif t['name'] == 'pathway_variants_summary':
            t['partitions'][0]['source']['expression'] = [
                'let',
                f'    Source = Csv.Document(File.Contents("{csv_variants}"),[Delimiter=",", Columns=4, Encoding=65001, QuoteStyle=QuoteStyle.None]),',
                '    #"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),',
                '    #"Changed Type" = Table.TransformColumnTypes(#"Promoted Headers",{{"variant_rank", Int64.Type}, {"case_count", Int64.Type}, {"percentage", type number}, {"pathway", type text}})',
                'in',
                '    #"Changed Type"'
            ]
            # Ensure Total Variant Cases measure exists
            meas = {m['name']: m for m in t.get('measures', [])}
            if 'Total Variant Cases' not in meas:
                if 'measures' not in t:
                    t['measures'] = []
                t['measures'].append({
                    'name': 'Total Variant Cases',
                    'expression': "SUM('pathway_variants_summary'[case_count])",
                    'formatString': '#,##0'
                })

        elif t['name'] == 'bottleneck_analysis_summary':
            t['partitions'][0]['source']['expression'] = [
                'let',
                f'    Source = Csv.Document(File.Contents("{csv_bottlenecks}"),[Delimiter=",", Columns=8, Encoding=65001, QuoteStyle=QuoteStyle.None]),',
                '    #"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),',
                '    #"Changed Type" = Table.TransformColumnTypes(#"Promoted Headers",{{"rank", Int64.Type}, {"source_activity", type text}, {"target_activity", type text}, {"transition_count", Int64.Type}, {"mean_observed_transition_minutes", type number}, {"median_observed_transition_minutes", type number}, {"min_observed_transition_minutes", type number}, {"max_observed_transition_minutes", type number}}),',
                '    #"Added Transition Label" = Table.AddColumn(#"Changed Type", "transition_label", each [source_activity] & " -> " & [target_activity], type text)',
                'in',
                '    #"Added Transition Label"'
            ]
            # Ensure transition_label is a physical column
            for col in t.get('columns', []):
                if col['name'] == 'transition_label':
                    col.pop('type', None)
                    col.pop('expression', None)
                    col['sourceColumn'] = 'transition_label'
            # Ensure Avg Transition Duration measure exists
            meas = {m['name']: m for m in t.get('measures', [])}
            if 'Avg Transition Duration' not in meas:
                if 'measures' not in t:
                    t['measures'] = []
                t['measures'].append({
                    'name': 'Avg Transition Duration',
                    'expression': "AVERAGE('bottleneck_analysis_summary'[mean_observed_transition_minutes])",
                    'formatString': '0.0 "Mins"'
                })

        elif t['name'] == 'pathway_improvement_comparison':
            t['partitions'][0]['source']['expression'] = [
                'let',
                f'    Source = Csv.Document(File.Contents("{csv_improvement}"),[Delimiter=",", Columns=9, Encoding=65001, QuoteStyle=QuoteStyle.None]),',
                '    #"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),',
                '    #"Removed Precalculated Pct" = Table.RemoveColumns(#"Promoted Headers",{"percentage_difference"}),',
                '    #"Changed Type" = Table.TransformColumnTypes(#"Removed Precalculated Pct",{{"category", type text}, {"metric_name", type text}, {"baseline_value", type number}, {"proposed_value", type number}, {"absolute_difference", type number}, {"unit", type text}, {"provenance", type text}, {"interpretation", type text}}),',
                '    #"Calculated Relative Difference" = Table.AddColumn(#"Changed Type", "percentage_difference", each if [baseline_value] = null or [baseline_value] = 0 then (if [proposed_value] = 0 then 0.0 else null) else ([proposed_value] - [baseline_value]) / [baseline_value], type number),',
                '    #"Reordered Columns" = Table.SelectColumns(#"Calculated Relative Difference", {"category", "metric_name", "baseline_value", "proposed_value", "absolute_difference", "percentage_difference", "unit", "provenance", "interpretation"})',
                'in',
                '    #"Reordered Columns"'
            ]
            meas = {m['name']: m for m in t.get('measures', [])}
            if 'Relative % Difference' not in meas:
                if 'measures' not in t:
                    t['measures'] = []
                t['measures'].append({
                    'name': 'Relative % Difference',
                    'expression': [
                        "VAR Baseline = SELECTEDVALUE('pathway_improvement_comparison'[baseline_value])",
                        "VAR Proposed = SELECTEDVALUE('pathway_improvement_comparison'[proposed_value])",
                        "RETURN",
                        "    IF(",
                        "        ISBLANK(Baseline) || Baseline = 0,",
                        "        IF(Proposed = 0, 0, BLANK()),",
                        "        DIVIDE(Proposed - Baseline, Baseline)",
                        "    )"
                    ],
                    'formatString': '+0.0%;-0.0%;0.0%'
                })

    with open(bim_path, 'w', encoding='utf-8') as f:
        json.dump(bim, f, indent=2)
    print(f"Updated {bim_path} successfully!")


def build():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(script_dir)
    project_root = os.path.join(script_dir, "CareFlow_Dashboard_Project")
    sm_dir = os.path.join(project_root, "CareFlow_Dashboard.SemanticModel")
    sm_def = os.path.join(sm_dir, "definition")
    tables_dir = os.path.join(sm_def, "tables")
    cultures_dir = os.path.join(sm_def, "cultures")

    rep_dir = os.path.join(project_root, "CareFlow_Dashboard.Report")
    rep_def = os.path.join(rep_dir, "definition")

    os.makedirs(tables_dir, exist_ok=True)
    os.makedirs(cultures_dir, exist_ok=True)
    os.makedirs(rep_def, exist_ok=True)

    # 1. CareFlow_Dashboard.pbip
    pbip_content = {
        "version": "1.0",
        "artifacts": [
            {
                "report": {
                    "path": "CareFlow_Dashboard.Report"
                }
            }
        ],
        "settings": {}
    }
    with open(os.path.join(project_root, "CareFlow_Dashboard.pbip"), "w", encoding="utf-8") as f:
        json.dump(pbip_content, f, indent=2)

    # 2. definition.pbism
    with open(os.path.join(sm_dir, "definition.pbism"), "w", encoding="utf-8") as f:
        json.dump({"version": "1.0"}, f, indent=2)

    # 3. definition.pbir
    pbir_content = {
        "version": "1.0",
        "datasetReference": {
            "byPath": {
                "path": "../CareFlow_Dashboard.SemanticModel"
            },
            "byConnection": None
        }
    }
    with open(os.path.join(rep_dir, "definition.pbir"), "w", encoding="utf-8") as f:
        json.dump(pbir_content, f, indent=2)

    # 4. Copy TMDL files from careflow_semantic_model
    src_tmdl = os.path.join(os.path.dirname(os.path.abspath(__file__)), "careflow_semantic_model")
    shutil.copy(os.path.join(src_tmdl, "database.tmdl"), sm_def)
    shutil.copy(os.path.join(src_tmdl, "relationships.tmdl"), sm_def)
    shutil.copy(os.path.join(src_tmdl, "cultures", "en-US.tmdl"), cultures_dir)

    for f in os.listdir(os.path.join(src_tmdl, "tables")):
        if f.startswith("DateTableTemplate") or f.startswith("LocalDateTable"):
            shutil.copy(os.path.join(src_tmdl, "tables", f), tables_dir)

    # 4a. stg_hospital_events (2) with excludeFromModelRefresh
    stg2_content = """table 'stg_hospital_events (2)'
\tlineageTag: 27a25c1c-4740-4992-9301-d14ce0ac8fc7
\texcludeFromModelRefresh

\tcolumn case_id
\t\tdataType: string
\t\tlineageTag: 38d6e019-3d53-466b-b56f-c40442dfbdb6
\t\tsummarizeBy: none
\t\tsourceColumn: case_id

\t\tannotation SummarizationSetBy = Automatic

\tcolumn event_sequence
\t\tdataType: int64
\t\tformatString: 0
\t\tlineageTag: cb2536fb-f1a5-48b4-9c07-fc085a6a66a1
\t\tsummarizeBy: sum
\t\tsourceColumn: event_sequence

\t\tannotation SummarizationSetBy = Automatic

\tcolumn raw_activity_name
\t\tdataType: string
\t\tlineageTag: a0958b10-096b-4ca0-b26a-9f5da0cb59f7
\t\tsummarizeBy: none
\t\tsourceColumn: raw_activity_name

\t\tannotation SummarizationSetBy = Automatic

\tcolumn activity_name
\t\tdataType: string
\t\tlineageTag: 61ff7920-56ae-4357-9f7a-fa2d60fb41f1
\t\tsummarizeBy: none
\t\tsourceColumn: activity_name

\t\tannotation SummarizationSetBy = Automatic

\tcolumn event_timestamp
\t\tdataType: dateTime
\t\tformatString: General Date
\t\tlineageTag: 359c276e-39cc-48a7-811c-7d2c495aa085
\t\tsummarizeBy: none
\t\tsourceColumn: event_timestamp

\t\tvariation Variation
\t\t\tisDefault
\t\t\trelationship: 0bef2581-4d0c-4bc5-8378-e1e0791fccd9
\t\t\tdefaultHierarchy: LocalDateTable_49c443fd-4f20-4c85-89a4-93bf72969d08.'Date Hierarchy'

\t\tannotation SummarizationSetBy = Automatic

\tcolumn event_date
\t\tdataType: dateTime
\t\tformatString: Long Date
\t\tlineageTag: e78034dd-87b6-43b8-b419-b9eb221d269e
\t\tsummarizeBy: none
\t\tsourceColumn: event_date

\t\tvariation Variation
\t\t\tisDefault
\t\t\trelationship: 7156ce9b-4d7e-4b77-8cd0-a942e984ca31
\t\t\tdefaultHierarchy: LocalDateTable_e9b76cac-079d-4de9-acda-a06cd19308e8.'Date Hierarchy'

\t\tannotation SummarizationSetBy = Automatic

\t\tannotation UnderlyingDateTimeDataType = Date

\tcolumn department
\t\tdataType: string
\t\tlineageTag: f26da655-4e2e-44c0-b6d3-4474c69023d8
\t\tsummarizeBy: none
\t\tsourceColumn: department

\t\tannotation SummarizationSetBy = Automatic

\tcolumn resource_id
\t\tdataType: string
\t\tlineageTag: cff4915d-85fa-44fc-a0dc-5d1dbbe65db5
\t\tsummarizeBy: none
\t\tsourceColumn: resource_id

\t\tannotation SummarizationSetBy = Automatic

\tcolumn data_provenance
\t\tdataType: string
\t\tlineageTag: 2cae61d6-0f86-4acb-836a-9c347229f824
\t\tsummarizeBy: none
\t\tsourceColumn: data_provenance

\t\tannotation SummarizationSetBy = Automatic

\tcolumn previous_activity
\t\tdataType: string
\t\tlineageTag: 0223f275-fb3b-4a36-9f7a-157c89fd5aba
\t\tsummarizeBy: none
\t\tsourceColumn: previous_activity

\t\tannotation SummarizationSetBy = Automatic

\tcolumn transition_minutes_from_previous
\t\tdataType: int64
\t\tformatString: 0
\t\tlineageTag: a1fff7aa-5c4f-4877-bc03-816089e74d60
\t\tsummarizeBy: sum
\t\tsourceColumn: transition_minutes_from_previous

\t\tannotation SummarizationSetBy = Automatic

\tpartition 'stg_hospital_events (2)' = m
\t\tmode: import
\t\tsource =
\t\t\t\tlet
\t\t\t\t    Source = stg_hospital_events
\t\t\t\tin
\t\t\t\t    Source

\tannotation PBI_ResultType = Table
"""
    with open(os.path.join(tables_dir, "stg_hospital_events (2).tmdl"), "w", encoding="utf-8") as f:
        f.write(stg2_content)

    # 4b. stg_hospital_events with measures and date variations
    stg_tmdl = """table stg_hospital_events
\tlineageTag: 16005fff-e9ff-454a-9d9b-826c68590aeb

\tmeasure 'Total Cases' = DISTINCTCOUNT('stg_hospital_events'[case_id])
\t\tformatString: #,##0
\t\tlineageTag: 268e0df6-b01e-4525-b852-f217108b0841

\tmeasure 'Total Events' = COUNTROWS('stg_hospital_events')
\t\tformatString: #,##0
\t\tlineageTag: c6b88a5b-b73d-459c-85bc-a50867f9cd39

\tmeasure 'Avg Case Cycle Time (Mins)' =
\t\t\tVAR CaseDurations =
\t\t\t    ADDCOLUMNS(
\t\t\t        VALUES('stg_hospital_events'[case_id]),
\t\t\t        "CaseTotalMinutes",
\t\t\t        CALCULATE(SUM('stg_hospital_events'[transition_minutes_from_previous]))
\t\t\t    )
\t\t\tRETURN
\t\t\tAVERAGEX(CaseDurations, [CaseTotalMinutes])
\t\tformatString: 0.0 "Mins"
\t\tlineageTag: 1138ea12-042b-4c0d-a572-4c546277a8c3

\tmeasure 'Median Case Cycle Time (Mins)' =
\t\t\tVAR CaseDurations =
\t\t\t    ADDCOLUMNS(
\t\t\t        VALUES('stg_hospital_events'[case_id]),
\t\t\t        "CaseTotalMinutes",
\t\t\t        CALCULATE(SUM('stg_hospital_events'[transition_minutes_from_previous]))
\t\t\t    )
\t\t\tRETURN
\t\t\tMEDIANX(CaseDurations, [CaseTotalMinutes])
\t\tformatString: 0.0 "Mins"
\t\tlineageTag: d4cfb71f-b7e6-4dba-a4d8-85abd6c80396

\tmeasure 'Re-Triage Rate %' =
\t\t\tVAR ReTriageCases =
\t\t\t    CALCULATE(
\t\t\t        DISTINCTCOUNT('stg_hospital_events'[case_id]),
\t\t\t        'stg_hospital_events'[raw_activity_name] = "Triage",
\t\t\t        'stg_hospital_events'[previous_activity] = "Triage"
\t\t\t    )
\t\t\tRETURN
\t\t\tDIVIDE(ReTriageCases, [Total Cases], 0)
\t\tformatString: 0.0%
\t\tlineageTag: 345f49c1-6dcd-4120-b092-0a7484ca557d

\tmeasure 'Conformant Cases Count' = [Total Cases] - [Repeat Triage Cases Count]
\t\tformatString: #,##0
\t\tlineageTag: 7a8b9c0d-1e2f-3a4b-5c6d-7e8f9a0b1c2d

\tmeasure 'Repeat Triage Cases Count' =
\t\t\tCALCULATE(
\t\t\t    DISTINCTCOUNT('stg_hospital_events'[case_id]),
\t\t\t    'stg_hospital_events'[raw_activity_name] = "Triage",
\t\t\t    'stg_hospital_events'[previous_activity] = "Triage"
\t\t\t)
\t\tformatString: #,##0
\t\tlineageTag: 8b9c0d1e-2f3a-4b5c-6d7e-8f9a0b1c2d3e

\tmeasure 'Conformance Rate %' =
\t\t\tDIVIDE([Conformant Cases Count], [Total Cases], 0)
\t\tformatString: 0.0%
\t\tlineageTag: 9c0d1e2f-3a4b-5c6d-7e8f-9a0b1c2d3e4f

\tcolumn case_id
\t\tdataType: string
\t\tlineageTag: 5fc73f6b-6446-40e1-82ca-4d62a6bb976b
\t\tsummarizeBy: none
\t\tsourceColumn: case_id

\tcolumn event_sequence
\t\tdataType: int64
\t\tformatString: 0
\t\tlineageTag: a98ce6da-eec7-4078-a9e9-8ba9b5c9c0c7
\t\tsummarizeBy: sum
\t\tsourceColumn: event_sequence

\tcolumn raw_activity_name
\t\tdataType: string
\t\tlineageTag: 00699417-93a7-4f31-8715-c6542db98daf
\t\tsummarizeBy: none
\t\tsourceColumn: raw_activity_name

\tcolumn activity_name
\t\tdataType: string
\t\tlineageTag: fa5edfef-fade-4f4c-81ae-aa74be0a6480
\t\tsummarizeBy: none
\t\tsourceColumn: activity_name

\tcolumn event_timestamp
\t\tdataType: dateTime
\t\tformatString: yyyy-mm-dd hh:nn:ss
\t\tlineageTag: ac4e4b62-3f53-48be-a508-33c432c697ac
\t\tsummarizeBy: none
\t\tsourceColumn: event_timestamp

\t\tvariation Variation
\t\t\tisDefault
\t\t\trelationship: c9df3b01-cbdd-4034-81de-32c5ade92f52
\t\t\tdefaultHierarchy: LocalDateTable_b02213a0-917d-4fce-9237-50aa9100f0ee.'Date Hierarchy'

\t\tannotation SummarizationSetBy = Automatic

\tcolumn event_date
\t\tdataType: dateTime
\t\tformatString: yyyy-mm-dd
\t\tlineageTag: b0624bf3-018f-4318-ae25-274f88e1a179
\t\tsummarizeBy: none
\t\tsourceColumn: event_date

\t\tvariation Variation
\t\t\tisDefault
\t\t\trelationship: 3cb3b656-e3b2-41e5-a4c5-3cf909fce244
\t\t\tdefaultHierarchy: LocalDateTable_b77ddfa2-054a-4d91-af85-e6383c65e7b3.'Date Hierarchy'

\t\tannotation SummarizationSetBy = Automatic
\t\tannotation UnderlyingDateTimeDataType = Date

\tcolumn department
\t\tdataType: string
\t\tlineageTag: 033d8cff-9001-4c2a-941f-7191cba91fe8
\t\tsummarizeBy: none
\t\tsourceColumn: department

\tcolumn resource_id
\t\tdataType: string
\t\tlineageTag: ab01f686-c089-46d8-81ce-9e4579c09602
\t\tsummarizeBy: none
\t\tsourceColumn: resource_id

\tcolumn data_provenance
\t\tdataType: string
\t\tlineageTag: c4102fe4-f430-4426-98d6-90a98c204561
\t\tsummarizeBy: none
\t\tsourceColumn: data_provenance

\tcolumn previous_activity
\t\tdataType: string
\t\tlineageTag: 1e6b40bd-3513-4b11-a01c-eca169bafe53
\t\tsummarizeBy: none
\t\tsourceColumn: previous_activity

\tcolumn transition_minutes_from_previous
\t\tdataType: int64
\t\tformatString: #,##0
\t\tlineageTag: 95f45a92-2f4c-4fda-9a91-adb891070be8
\t\tsummarizeBy: sum
\t\tsourceColumn: transition_minutes_from_previous

\tpartition stg_hospital_events = m
\t\tmode: import
\t\tsource =
\t\t\t\tlet
\t\t\t\t    Source = Csv.Document(File.Contents("__CSV_EVENTS__"),[Delimiter=",", Columns=11, Encoding=65001, QuoteStyle=QuoteStyle.None]),
\t\t\t\t    #"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
\t\t\t\t    #"Replaced Empty Strings" = Table.ReplaceValue(#"Promoted Headers", "", null, Replacer.ReplaceValue, {"previous_activity", "transition_minutes_from_previous"}),
\t\t\t\t    #"Changed Type" = Table.TransformColumnTypes(#"Replaced Empty Strings",{{"case_id", type text}, {"event_sequence", Int64.Type}, {"raw_activity_name", type text}, {"activity_name", type text}, {"event_timestamp", type datetime}, {"event_date", type date}, {"department", type text}, {"resource_id", type text}, {"data_provenance", type text}, {"previous_activity", type text}, {"transition_minutes_from_previous", Int64.Type}})
\t\t\t\tin
\t\t\t\t    #"Changed Type"

\tannotation PBI_ResultType = Table
"""
    stg_tmdl = stg_tmdl.replace("__CSV_EVENTS__", os.path.join(repo_root, "data", "cleaned", "stg_hospital_events.csv"))
    with open(os.path.join(tables_dir, "stg_hospital_events.tmdl"), "w", encoding="utf-8") as f:
        f.write(stg_tmdl)

    # 4c. pathway_variants_summary.tmdl
    pathway_tmdl = """table pathway_variants_summary
\tlineageTag: a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d

\tmeasure 'Total Variant Cases' = SUM('pathway_variants_summary'[case_count])
\t\tformatString: #,##0
\t\tlineageTag: a2b3c4d5-e6f7-8a9b-0c1d-2e3f4a5b6c7d

\tcolumn variant_rank
\t\tdataType: int64
\t\tformatString: 0
\t\tsummarizeBy: none
\t\tsourceColumn: variant_rank

\tcolumn case_count
\t\tdataType: int64
\t\tformatString: #,##0
\t\tsummarizeBy: sum
\t\tsourceColumn: case_count

\tcolumn percentage
\t\tdataType: double
\t\tformatString: 0.0"%"
\t\tsummarizeBy: none
\t\tsourceColumn: percentage

\tcolumn pathway
\t\tdataType: string
\t\tsummarizeBy: none
\t\tsourceColumn: pathway

\tpartition pathway_variants_summary = m
\t\tmode: import
\t\tsource =
\t\t\t\tlet
\t\t\t\t    Source = Csv.Document(File.Contents("__CSV_VARIANTS__"),[Delimiter=",", Columns=4, Encoding=65001, QuoteStyle=QuoteStyle.None]),
\t\t\t\t    #"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
\t\t\t\t    #"Changed Type" = Table.TransformColumnTypes(#"Promoted Headers",{{"variant_rank", Int64.Type}, {"case_count", Int64.Type}, {"percentage", type number}, {"pathway", type text}})
\t\t\t\tin
\t\t\t\t    #"Changed Type"

\tannotation PBI_ResultType = Table
"""
    pathway_tmdl = pathway_tmdl.replace("__CSV_VARIANTS__", os.path.join(repo_root, "outputs", "pathway_variants_summary.csv"))
    with open(os.path.join(tables_dir, "pathway_variants_summary.tmdl"), "w", encoding="utf-8") as f:
        f.write(pathway_tmdl)

    # 4d. bottleneck_analysis_summary.tmdl
    bottleneck_tmdl = """table bottleneck_analysis_summary
\tlineageTag: b2c3d4e5-f6a7-8b9c-0d1e-2f3a4b5c6d7e

\tmeasure 'Avg Transition Duration' = AVERAGE('bottleneck_analysis_summary'[mean_observed_transition_minutes])
\t\tformatString: 0.0 "Mins"
\t\tlineageTag: b3c4d5e6-f7a8-9b0c-1d2e-3f4a5b6c7d8e

\tcolumn rank
\t\tdataType: int64
\t\tformatString: 0
\t\tsummarizeBy: none
\t\tsourceColumn: rank

\tcolumn source_activity
\t\tdataType: string
\t\tsummarizeBy: none
\t\tsourceColumn: source_activity

\tcolumn target_activity
\t\tdataType: string
\t\tsummarizeBy: none
\t\tsourceColumn: target_activity

\tcolumn transition_label
\t\tdataType: string
\t\tsummarizeBy: none
\t\tsourceColumn: transition_label

\tcolumn transition_count
\t\tdataType: int64
\t\tformatString: #,##0
\t\tsummarizeBy: sum
\t\tsourceColumn: transition_count

\tcolumn mean_observed_transition_minutes
\t\tdataType: double
\t\tformatString: 0.0 "Mins"
\t\tsummarizeBy: average
\t\tsourceColumn: mean_observed_transition_minutes

\tcolumn median_observed_transition_minutes
\t\tdataType: double
\t\tformatString: 0.0 "Mins"
\t\tsummarizeBy: average
\t\tsourceColumn: median_observed_transition_minutes

\tcolumn min_observed_transition_minutes
\t\tdataType: double
\t\tformatString: 0.0
\t\tsummarizeBy: none
\t\tsourceColumn: min_observed_transition_minutes

\tcolumn max_observed_transition_minutes
\t\tdataType: double
\t\tformatString: 0.0
\t\tsummarizeBy: none
\t\tsourceColumn: max_observed_transition_minutes

\tpartition bottleneck_analysis_summary = m
\t\tmode: import
\t\tsource =
\t\t\t\tlet
\t\t\t\t    Source = Csv.Document(File.Contents("__CSV_BOTTLENECK__"),[Delimiter=",", Columns=8, Encoding=65001, QuoteStyle=QuoteStyle.None]),
\t\t\t\t    #"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
\t\t\t\t    #"Changed Type" = Table.TransformColumnTypes(#"Promoted Headers",{{"rank", Int64.Type}, {"source_activity", type text}, {"target_activity", type text}, {"transition_count", Int64.Type}, {"mean_observed_transition_minutes", type number}, {"median_observed_transition_minutes", type number}, {"min_observed_transition_minutes", type number}, {"max_observed_transition_minutes", type number}}),
\t\t\t\t    #"Added Transition Label" = Table.AddColumn(#"Changed Type", "transition_label", each [source_activity] & " -> " & [target_activity], type text)
\t\t\t\tin
\t\t\t\t    #"Added Transition Label"

\tannotation PBI_ResultType = Table
"""
    bottleneck_tmdl = bottleneck_tmdl.replace("__CSV_BOTTLENECK__", os.path.join(repo_root, "outputs", "bottleneck_analysis_summary.csv"))
    with open(os.path.join(tables_dir, "bottleneck_analysis_summary.tmdl"), "w", encoding="utf-8") as f:
        f.write(bottleneck_tmdl)

    # 4e. pathway_improvement_comparison.tmdl
    improvement_tmdl = """table pathway_improvement_comparison
\tlineageTag: c3d4e5f6-a7b8-9c0d-1e2f-3a4b5c6d7e8f

\tcolumn category
\t\tdataType: string
\t\tsummarizeBy: none
\t\tsourceColumn: category

\tcolumn metric_name
\t\tdataType: string
\t\tsummarizeBy: none
\t\tsourceColumn: metric_name

\tcolumn baseline_value
\t\tdataType: double
\t\tformatString: #,##0.0
\t\tsummarizeBy: none
\t\tsourceColumn: baseline_value

\tcolumn proposed_value
\t\tdataType: double
\t\tformatString: #,##0.0
\t\tsummarizeBy: none
\t\tsourceColumn: proposed_value

\tcolumn absolute_difference
\t\tdataType: double
\t\tformatString: #,##0.0
\t\tsummarizeBy: none
\t\tsourceColumn: absolute_difference

\tcolumn percentage_difference
\t\tdataType: double
\t\tformatString: +0.0%;-0.0%;0.0%
\t\tsummarizeBy: none
\t\tsourceColumn: percentage_difference

\tcolumn unit
\t\tdataType: string
\t\tsummarizeBy: none
\t\tsourceColumn: unit

\tcolumn provenance
\t\tdataType: string
\t\tsummarizeBy: none
\t\tsourceColumn: provenance

\tcolumn interpretation
\t\tdataType: string
\t\tsummarizeBy: none
\t\tsourceColumn: interpretation

\tmeasure 'Relative % Difference' =
\t\t\tVAR Baseline = SELECTEDVALUE('pathway_improvement_comparison'[baseline_value])
\t\t\tVAR Proposed = SELECTEDVALUE('pathway_improvement_comparison'[proposed_value])
\t\t\tRETURN
\t\t\t\tIF(
\t\t\t\t\tISBLANK(Baseline) || Baseline = 0,
\t\t\t\t\tIF(Proposed = 0, 0, BLANK()),
\t\t\t\t\tDIVIDE(Proposed - Baseline, Baseline)
\t\t\t\t)
\t\tformatString: +0.0%;-0.0%;0.0%
\t\tlineageTag: c4d5e6f7-a8b9-0c1d-2e3f-4a5b6c7d8e9f

\tpartition pathway_improvement_comparison = m
\t\tmode: import
\t\tsource =
\t\t\t\tlet
\t\t\t\t    Source = Csv.Document(File.Contents("__CSV_IMPROVEMENT__"),[Delimiter=",", Columns=9, Encoding=65001, QuoteStyle=QuoteStyle.None]),
\t\t\t\t    #"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
\t\t\t\t    #"Removed Precalculated Pct" = Table.RemoveColumns(#"Promoted Headers",{"percentage_difference"}),
\t\t\t\t    #"Changed Type" = Table.TransformColumnTypes(#"Removed Precalculated Pct",{{"category", type text}, {"metric_name", type text}, {"baseline_value", type number}, {"proposed_value", type number}, {"absolute_difference", type number}, {"unit", type text}, {"provenance", type text}, {"interpretation", type text}}),
\t\t\t\t    #"Calculated Relative Difference" = Table.AddColumn(#"Changed Type", "percentage_difference", each if [baseline_value] = null or [baseline_value] = 0 then (if [proposed_value] = 0 then 0.0 else null) else ([proposed_value] - [baseline_value]) / [baseline_value], type number),
\t\t\t\t    #"Reordered Columns" = Table.SelectColumns(#"Calculated Relative Difference", {"category", "metric_name", "baseline_value", "proposed_value", "absolute_difference", "percentage_difference", "unit", "provenance", "interpretation"})
\t\t\t\tin
\t\t\t\t    #"Reordered Columns"

\tannotation PBI_ResultType = Table
"""
    improvement_tmdl = improvement_tmdl.replace("__CSV_IMPROVEMENT__", os.path.join(repo_root, "outputs", "pathway_improvement_comparison.csv"))
    with open(os.path.join(tables_dir, "pathway_improvement_comparison.tmdl"), "w", encoding="utf-8") as f:
        f.write(improvement_tmdl)

    # 4f. model.tmdl
    model_tmdl = """model Model
\tculture: en-US
\tdefaultPowerBIDataSourceVersion: powerBI_V3
\tsourceQueryCulture: en-IN
\tdataAccessOptions
\t\tlegacyRedirects
\t\treturnErrorValuesAsNull

annotation __PBI_TimeIntelligenceEnabled = 1

annotation PBI_QueryOrder = ["stg_hospital_events","stg_hospital_events (2)","pathway_variants_summary","bottleneck_analysis_summary","pathway_improvement_comparison"]

ref table stg_hospital_events
ref table DateTableTemplate_07490a40-7037-4685-a350-043d68764b27
ref table LocalDateTable_b02213a0-917d-4fce-9237-50aa9100f0ee
ref table LocalDateTable_b77ddfa2-054a-4d91-af85-e6383c65e7b3
ref table 'stg_hospital_events (2)'
ref table LocalDateTable_49c443fd-4f20-4c85-89a4-93bf72969d08
ref table LocalDateTable_e9b76cac-079d-4de9-acda-a06cd19308e8
ref table pathway_variants_summary
ref table bottleneck_analysis_summary
ref table pathway_improvement_comparison

ref cultureInfo en-US
"""
    with open(os.path.join(sm_def, "model.tmdl"), "w", encoding="utf-8") as f:
        f.write(model_tmdl)

    # 4g. Copy verified model.bim
    bim_template = os.path.join(src_tmdl, "model.bim")
    if os.path.exists(bim_template):
        with open(bim_template, "r", encoding="utf-8") as f:
            bim = json.load(f)
        # Ensure excludeFromModelRefresh on stg_hospital_events (2)
        for t in bim["model"]["tables"]:
            if t["name"] == "stg_hospital_events (2)":
                t["excludeFromModelRefresh"] = True
        with open(os.path.join(sm_dir, "model.bim"), "w", encoding="utf-8") as f:
            json.dump(bim, f, indent=2)
        update_model_bim(os.path.join(sm_dir, "model.bim"), repo_root=repo_root)

    # 5. Extract StaticResources from backup PBIX
    backup_pbix = os.path.join(script_dir, "backup", "CareFlow_AutoRecovery_Backup.pbix")
    if os.path.exists(backup_pbix):
        with zipfile.ZipFile(backup_pbix, "r") as z:
            for name in z.namelist():
                if name.startswith("Report/StaticResources"):
                    rel = name[len("Report/"):]
                    for base in [rep_dir, rep_def]:
                        dest = os.path.join(base, rel)
                        os.makedirs(os.path.dirname(dest), exist_ok=True)
                        with open(dest, "wb") as out_f:
                            out_f.write(z.read(name))

    # 6. Build Report Visual Containers with full query and dataTransforms

    page1_visuals = [
        get_card_visual("card_total_cases", 20, 20, 235, 130, 0, "stg_hospital_events", "Total Cases"),
        get_card_visual("card_total_events", 270, 20, 235, 130, 1, "stg_hospital_events", "Total Events", display_units_none=True),
        get_card_visual("card_avg_duration", 520, 20, 235, 130, 2, "stg_hospital_events", "Avg Case Cycle Time (Mins)", format_string="0.0 \"Mins\""),
        get_card_visual("card_med_duration", 770, 20, 235, 130, 3, "stg_hospital_events", "Median Case Cycle Time (Mins)", format_string="0.0 \"Mins\""),
        get_card_visual("card_retriage_rate", 1020, 20, 235, 130, 4, "stg_hospital_events", "Re-Triage Rate %", format_string="0.0%"),
        get_donut_chart("donut_dept_breakdown", 20, 170, 380, 450, 5, "stg_hospital_events", "department", "Total Events"),
        get_bar_chart_measure("bar_activity_breakdown", 415, 170, 430, 450, 6, "stg_hospital_events", "raw_activity_name", "Total Events"),
        get_column_chart("col_daily_trend", 860, 170, 400, 450, 7, "stg_hospital_events", "event_date", "Total Events"),
        get_textbox_visual(
            "txt_disclaimer_page1", 20, 635, 1240, 65, 8,
            "Data Source Note: CareFlow emergency clinical pathway event log (500 cases, 3,140 events across 7 activities). All data is simulated for process-mining education and does not contain real patient health records. Observed elapsed durations capture active clinical execution, transit, and reviews rather than pure waiting time."
        )
    ]

    page2_visuals = [
        get_card_visual("card_conformant_cases", 20, 20, 385, 130, 0, "stg_hospital_events", "Conformant Cases Count"),
        get_card_visual("card_retriage_cases", 430, 20, 385, 130, 1, "stg_hospital_events", "Repeat Triage Cases Count"),
        get_card_visual("card_conformance_rate", 840, 20, 415, 130, 2, "stg_hospital_events", "Conformance Rate %", format_string="0.0%"),
        get_bar_chart_measure("bar_pathway_variants", 20, 170, 680, 450, 3, "pathway_variants_summary", "pathway", "Total Variant Cases"),
        get_table_visual("tbl_case_audit", 720, 170, 535, 450, 4, "stg_hospital_events", ["case_id", "event_sequence", "raw_activity_name", "department", "transition_minutes_from_previous"], display_names={"case_id": "Case ID", "event_sequence": "Seq #", "raw_activity_name": "Activity", "department": "Department", "transition_minutes_from_previous": "Elapsed (Mins)"}),
        get_textbox_visual(
            "txt_guidance_page2", 20, 635, 1235, 65, 5,
            "Workflow Audit Note: 440 patient encounters (88.0%) adhered to standard forward clinical pathways. 60 encounters (12.0%) experienced an operational re-triage loop prior to physician consultation. This distinction represents sequential workflow pattern classification, not a judgment on clinical necessity."
        )
    ]

    page3_visuals = [
        get_bar_chart_measure("bar_bottlenecks", 20, 20, 480, 510, 0, "bottleneck_analysis_summary", "transition_label", "Avg Transition Duration"),
        get_table_visual("tbl_improvement_comparison", 515, 20, 745, 510, 1, "pathway_improvement_comparison", ["metric_name", "baseline_value", "proposed_value", "percentage_difference", "unit", "interpretation"], display_names={"metric_name": "Metric", "baseline_value": "Baseline (As-Is)", "proposed_value": "Proposed (To-Be)", "percentage_difference": "% Difference (Relative)", "unit": "Unit", "interpretation": "Operational Interpretation"}),
        get_textbox_visual(
            "txt_safety_banner_page3", 20, 545, 1240, 155, 2,
            "Analytical Caution: Observed transition duration reflects the total elapsed clock time between sequential milestone timestamps. It captures specimen processing in laboratories, diagnostic radiology image review, medication administration, and intra-departmental transport, not pure waiting time.\\n\\n" +
            "Hypothetical Scenario Disclaimer: The To-Be pathway model projects queue streamlining and 15% coordination reductions, treating repeat-triage elimination as a simulated operational alternative. Simulated logs cannot establish whether clinical reassessment was medically necessary. Qualified hospital clinical staff must validate these operational assumptions before real-world adoption.\\n\\n" +
            "Sign Convention Note: Relative percentage difference is calculated as (Proposed - Baseline) / Baseline. Negative values indicate operational reductions (e.g., lower encounter cycle times, eliminated repeat triage steps, or reduced variant complexity)."
        )
    ]

    sections = [
        {
            "id": 0,
            "name": "section_hospital_overview",
            "displayName": "Hospital Overview",
            "filters": "[]",
            "ordinal": 0,
            "visualContainers": page1_visuals,
            "config": "{}",
            "displayOption": 1,
            "width": 1280,
            "height": 720
        },
        {
            "id": 1,
            "name": "section_patient_flow",
            "displayName": "Patient Flow",
            "filters": "[]",
            "ordinal": 1,
            "visualContainers": page2_visuals,
            "config": "{}",
            "displayOption": 1,
            "width": 1280,
            "height": 720
        },
        {
            "id": 2,
            "name": "section_process_improvement",
            "displayName": "Transition Analysis & Process Improvement",
            "filters": "[]",
            "ordinal": 2,
            "visualContainers": page3_visuals,
            "config": "{}",
            "displayOption": 1,
            "width": 1280,
            "height": 720
        }
    ]

    report_json = {
        "id": 0,
        "resourcePackages": [
            {
                "resourcePackage": {
                    "name": "SharedResources",
                    "type": 2,
                    "items": [
                        {
                            "type": 202,
                            "path": "BaseThemes/CY26SU05.json",
                            "name": "CY26SU05"
                        }
                    ],
                    "disabled": False
                }
            }
        ],
        "sections": sections,
        "config": json.dumps({
            "version": "5.73",
            "themeCollection": {
                "baseTheme": {
                    "name": "CY26SU05",
                    "version": {"visual": "2.9.0", "report": "3.3.0", "page": "2.3.1"},
                    "type": 2
                }
            },
            "activeSectionIndex": 0,
            "defaultDrillFilterOtherVisuals": True,
            "settings": {
                "useNewFilterPaneExperience": True,
                "allowChangeFilterTypes": True,
                "useStylableVisualContainerHeader": True,
                "queryLimitOption": 6,
                "useEnhancedTooltips": True,
                "exportDataMode": 1,
                "useDefaultAggregateDisplayName": True
            },
            "objects": {
                "section": [
                    {
                        "properties": {
                            "verticalAlignment": {
                                "expr": {
                                    "Literal": {"Value": "'Top'"}
                                }
                            }
                        }
                    }
                ]
            }
        }),
        "layoutOptimization": 0
    }

    # Save to BOTH definition/report.json and report.json at root
    with open(os.path.join(rep_def, "report.json"), "w", encoding="utf-8") as f:
        json.dump(report_json, f, indent=2)

    with open(os.path.join(rep_dir, "report.json"), "w", encoding="utf-8") as f:
        json.dump(report_json, f, indent=2)

    print("Successfully built CareFlow_Dashboard.pbip with complete queries and transforms at:")
    print(project_root)

if __name__ == "__main__":
    build()
