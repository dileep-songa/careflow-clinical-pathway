# Upgraded CareFlow PBIP Builder with Premium Visual Redesign & Container Styling
import os
import json
import zipfile

def get_container_formatting(title=None, subtitle=None):
    obj = {
        "background": [
            {
                "properties": {
                    "show": {"expr": {"Literal": {"Value": "true"}}},
                    "color": {"solid": {"color": {"expr": {"Literal": {"Value": "'#FFFFFF'"}}}}},
                    "transparency": {"expr": {"Literal": {"Value": "0D"}}}
                }
            }
        ],
        "border": [
            {
                "properties": {
                    "show": {"expr": {"Literal": {"Value": "true"}}},
                    "color": {"solid": {"color": {"expr": {"Literal": {"Value": "'#E2E8F0'"}}}}},
                    "radius": {"expr": {"Literal": {"Value": "6D"}}}
                }
            }
        ]
    }
    if title:
        obj["title"] = [
            {
                "properties": {
                    "show": {"expr": {"Literal": {"Value": "true"}}},
                    "text": {"expr": {"Literal": {"Value": f"'{title}'"}}},
                    "fontFamily": {"expr": {"Literal": {"Value": "'Segoe UI Semibold'"}}},
                    "fontSize": {"expr": {"Literal": {"Value": "10.5D"}}},
                    "fontColor": {"solid": {"color": {"expr": {"Literal": {"Value": "'#102A43'"}}}}},
                    "titleWrap": {"expr": {"Literal": {"Value": "true"}}}
                }
            }
        ]
    if subtitle:
        obj["subTitle"] = [
            {
                "properties": {
                    "show": {"expr": {"Literal": {"Value": "true"}}},
                    "text": {"expr": {"Literal": {"Value": f"'{subtitle}'"}}},
                    "fontFamily": {"expr": {"Literal": {"Value": "'Segoe UI'"}}},
                    "fontSize": {"expr": {"Literal": {"Value": "8D"}}},
                    "fontColor": {"solid": {"color": {"expr": {"Literal": {"Value": "'#627D98'"}}}}}
                }
            }
        ]
    return obj

def get_header_banner(name, x, y, w, h, z, title_text, subtitle_text, metadata_text=None):
    dark_container = {
        "background": [
            {
                "properties": {
                    "show": {"expr": {"Literal": {"Value": "true"}}},
                    "color": {"solid": {"color": {"expr": {"Literal": {"Value": "'#102A43'"}}}}},
                    "transparency": {"expr": {"Literal": {"Value": "0D"}}}
                }
            }
        ],
        "border": [
            {
                "properties": {
                    "show": {"expr": {"Literal": {"Value": "true"}}},
                    "color": {"solid": {"color": {"expr": {"Literal": {"Value": "'#1E3A8A'"}}}}},
                    "radius": {"expr": {"Literal": {"Value": "6D"}}}
                }
            }
        ]
    }
    runs_p1 = [
        {
            "value": "CareFlow  ",
            "textStyle": {
                "fontFamily": "Segoe UI Semibold",
                "fontSize": "13pt",
                "fontWeight": "bold",
                "color": "#FFFFFF"
            }
        },
        {
            "value": "|  " + title_text + "  ",
            "textStyle": {
                "fontFamily": "Segoe UI",
                "fontSize": "10pt",
                "color": "#38BDF8"
            }
        }
    ]
    if subtitle_text:
        runs_p1.append({
            "value": "|  " + subtitle_text,
            "textStyle": {
                "fontFamily": "Segoe UI",
                "fontSize": "8.5pt",
                "color": "#94A3B8"
            }
        })
    paragraphs = [{"textRuns": runs_p1}]
    if metadata_text:
        paragraphs.append({
            "textRuns": [
                {
                    "value": metadata_text,
                    "textStyle": {
                        "fontFamily": "Segoe UI",
                        "fontSize": "8pt",
                        "color": "#CBD5E1"
                    }
                }
            ]
        })
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
                "background": dark_container["background"],
                "border": dark_container["border"],
                "general": [
                    {
                        "properties": {
                            "paragraphs": paragraphs
                        }
                    }
                ]
            },
            "visualContainerObjects": dark_container,
            "vcObjects": dark_container
        },
        "visualContainerObjects": dark_container,
        "vcObjects": dark_container
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

def get_card_visual(name, x, y, w, h, z, entity, measure_name, display_units_none=False, format_string="#,##0", title=None, subtitle=None, callout_color="#102A43"):
    card_container = {
        "background": [
            {
                "properties": {
                    "show": {"expr": {"Literal": {"Value": "true"}}},
                    "color": {"solid": {"color": {"expr": {"Literal": {"Value": "'#FFFFFF'"}}}}},
                    "transparency": {"expr": {"Literal": {"Value": "0D"}}}
                }
            }
        ],
        "border": [
            {
                "properties": {
                    "show": {"expr": {"Literal": {"Value": "true"}}},
                    "color": {"solid": {"color": {"expr": {"Literal": {"Value": "'#E2E8F0'"}}}}},
                    "radius": {"expr": {"Literal": {"Value": "6D"}}}
                }
            }
        ]
    }
    display_title = title if title else measure_name
    query_ref = f"{entity}.{measure_name}"

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
                "Data": [{"queryRef": query_ref}]
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
                        "Name": query_ref,
                        "NativeReferenceName": display_title
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
            "hasDefaultSort": True,
            "visualContainerObjects": card_container,
            "vcObjects": card_container
        },
        "visualContainerObjects": card_container,
        "vcObjects": card_container
    }

    objects = {
        "background": card_container["background"],
        "border": card_container["border"],
        "shapeCustomRectangle": [
            {
                "properties": {
                    "tileShape": {"expr": {"Literal": {"Value": "'rectangleRoundedByPixel'"}}},
                    "rectangleRoundedCurve": {"expr": {"Literal": {"Value": "6D"}}}
                }
            }
        ],
        "outline": [
            {
                "properties": {
                    "show": {"expr": {"Literal": {"Value": "true"}}},
                    "lineColor": {"solid": {"color": {"expr": {"Literal": {"Value": "'#E2E8F0'"}}}}}
                }
            }
        ],
        "layout": [
            {
                "properties": {
                    "backgroundShow": {"expr": {"Literal": {"Value": "true"}}},
                    "verticalAlignment": {"expr": {"Literal": {"Value": "'Middle'"}}},
                    "paddingUniform": {"expr": {"Literal": {"Value": "4D"}}}
                }
            }
        ],
        "padding": [
            {
                "properties": {
                    "paddingUniform": {"expr": {"Literal": {"Value": "4D"}}}
                }
            }
        ],
        "spacing": [
            {
                "properties": {
                    "verticalSpacing": {"expr": {"Literal": {"Value": "4D"}}}
                }
            }
        ],
        "image": [
            {
                "properties": {
                    "show": {"expr": {"Literal": {"Value": "false"}}},
                    "imageAreaSize": {"expr": {"Literal": {"Value": "0D"}}}
                }
            }
        ]
    }

    value_props = {
        "fontFamily": {"expr": {"Literal": {"Value": "'Segoe UI Semibold'"}}},
        "fontSize": {"expr": {"Literal": {"Value": "14D"}}},
        "fontColor": {"solid": {"color": {"expr": {"Literal": {"Value": f"'{callout_color}'"}}}}},
        "alignment": {"expr": {"Literal": {"Value": "'Center'"}}}
    }
    if display_units_none:
        value_props["displayUnits"] = {"expr": {"Literal": {"Value": "1D"}}}
        value_props["valueDisplayUnits"] = {"expr": {"Literal": {"Value": "1D"}}}
        value_props["labelDisplayUnits"] = {"expr": {"Literal": {"Value": "1D"}}}
    objects["value"] = [{"properties": value_props}]
    objects["calloutValue"] = [{"properties": value_props}]
    objects["labels"] = [{"properties": value_props}]
    objects["callout"] = [{"properties": value_props}]

    label_props = {
        "show": {"expr": {"Literal": {"Value": "true"}}},
        "fontFamily": {"expr": {"Literal": {"Value": "'Segoe UI'"}}},
        "fontSize": {"expr": {"Literal": {"Value": "8D"}}},
        "fontColor": {"solid": {"color": {"expr": {"Literal": {"Value": "'#627D98'"}}}}},
        "position": {"expr": {"Literal": {"Value": "'belowValue'"}}},
        "textWrap": {"expr": {"Literal": {"Value": "true"}}},
        "alignment": {"expr": {"Literal": {"Value": "'Center'"}}}
    }
    objects["label"] = [{"properties": label_props}]
    objects["categoryLabels"] = [{"properties": label_props}]

    cfg["singleVisual"]["objects"] = objects

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
                                "Name": query_ref,
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
                    "Restatement": display_title,
                    "Name": query_ref,
                    "Type": 3,
                    "Format": format_string
                }
            ]
        },
        "visualElements": [
            {
                "DataRoles": [
                    {
                        "Name": "Data",
                        "Projection": 0,
                        "isActive": False
                    }
                ]
            }
        ],
        "selects": [
            {
                "displayName": display_title,
                "format": format_string,
                "queryName": query_ref,
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

def get_donut_chart(name, x, y, w, h, z, entity, category_col, val_measure, title=None, subtitle=None, order_by_measure=True, category_display_name=None, val_display_name=None):
    cat_disp = category_display_name if category_display_name else category_col
    val_disp = val_display_name if val_display_name else val_measure
    container_formatting = get_container_formatting(title=title, subtitle=subtitle)
    order_by = [
        {
            "Direction": 2,
            "Expression": {
                "Measure": {
                    "Expression": {"SourceRef": {"Source": "s"}},
                    "Property": val_measure
                }
            }
        }
    ] if order_by_measure else [
        {
            "Direction": 1,
            "Expression": {
                "Column": {
                    "Expression": {"SourceRef": {"Source": "s"}},
                    "Property": category_col
                }
            }
        }
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
                ],
                "OrderBy": order_by
            },
            "drillFilterOtherVisuals": True,
            "hasDefaultSort": True,
            "visualContainerObjects": container_formatting,
            "vcObjects": container_formatting
        },
        "visualContainerObjects": container_formatting,
        "vcObjects": container_formatting
    }

    objects = {
        "background": container_formatting["background"],
        "border": container_formatting["border"],
        "legend": [
            {
                "properties": {
                    "show": {"expr": {"Literal": {"Value": "true"}}},
                    "position": {"expr": {"Literal": {"Value": "'Top'"}}},
                    "showTitle": {"expr": {"Literal": {"Value": "false"}}},
                    "fontSize": {"expr": {"Literal": {"Value": "8.5D"}}},
                    "fontFamily": {"expr": {"Literal": {"Value": "'Segoe UI'"}}}
                }
            }
        ],
        "labels": [
            {
                "properties": {
                    "show": {"expr": {"Literal": {"Value": "true"}}},
                    "labelStyle": {"expr": {"Literal": {"Value": "'Both'"}}},
                    "fontSize": {"expr": {"Literal": {"Value": "8.5D"}}},
                    "fontFamily": {"expr": {"Literal": {"Value": "'Segoe UI'"}}},
                    "displayUnits": {"expr": {"Literal": {"Value": "1D"}}},
                    "labelDisplayUnits": {"expr": {"Literal": {"Value": "1D"}}},
                    "labelPrecision": {"expr": {"Literal": {"Value": "0D"}}}
                }
            }
        ],
        "slices": [
            {"properties": {"fill": {"solid": {"color": {"expr": {"Literal": {"Value": "'#0284C7'"}}}}}}, "selector": {"data": [{"scopeId": {"Comparison": {"ComparisonKind": 0, "Left": {"Column": {"Expression": {"SourceRef": {"Source": "s"}}, "Property": category_col}}, "Right": {"Literal": {"Value": "'ER'"}}}}}]}},
            {"properties": {"fill": {"solid": {"color": {"expr": {"Literal": {"Value": "'#102A43'"}}}}}}, "selector": {"data": [{"scopeId": {"Comparison": {"ComparisonKind": 0, "Left": {"Column": {"Expression": {"SourceRef": {"Source": "s"}}, "Property": category_col}}, "Right": {"Literal": {"Value": "'LAB'"}}}}}]}},
            {"properties": {"fill": {"solid": {"color": {"expr": {"Literal": {"Value": "'#D97706'"}}}}}}, "selector": {"data": [{"scopeId": {"Comparison": {"ComparisonKind": 0, "Left": {"Column": {"Expression": {"SourceRef": {"Source": "s"}}, "Property": category_col}}, "Right": {"Literal": {"Value": "'RADIOLOGY'"}}}}}]}}
        ]
    }
    if title:
        objects["title"] = container_formatting["title"]
    if subtitle:
        objects["subTitle"] = container_formatting.get("subTitle", [])
    cfg["singleVisual"]["objects"] = objects

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
                        ],
                        "OrderBy": order_by
                    },
                    "Binding": {
                        "Primary": {
                            "Groupings": [{"Projections": [0, 1]}]
                        },
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
                {"Restatement": cat_disp, "Name": f"{entity}.{category_col}", "Type": 2048},
                {"Restatement": val_disp, "Name": f"{entity}.{val_measure}", "Type": 3, "Format": "#,##0"}
            ]
        },
        "visualElements": [
            {"DataRoles": [{"Name": "Category", "Projection": 0, "isActive": False}, {"Name": "Y", "Projection": 1, "isActive": False}]}
        ],
        "selects": [
            {
                "displayName": cat_disp,
                "queryName": f"{entity}.{category_col}",
                "roles": {"Category": True},
                "type": {"category": None, "underlyingType": 1},
                "expr": {"Column": {"Expression": {"SourceRef": {"Entity": entity}}, "Property": category_col}}
            },
            {
                "displayName": val_disp,
                "format": "#,##0",
                "queryName": f"{entity}.{val_measure}",
                "roles": {"Y": True},
                "type": {"category": None, "underlyingType": 260},
                "expr": {"Measure": {"Expression": {"SourceRef": {"Entity": entity}}, "Property": val_measure}}
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

def get_bar_chart_measure(name, x, y, w, h, z, entity, category_col, val_measure, title=None, subtitle=None, max_margin=50, show_data_labels=True, category_display_name=None, val_display_name=None, bar_color=None, show_category_title=True):
    res = get_donut_chart(name, x, y, w, h, z, entity, category_col, val_measure, title=title, subtitle=subtitle, category_display_name=category_display_name, val_display_name=val_display_name)
    cfg = json.loads(res["config"])
    cfg["singleVisual"]["visualType"] = "clusteredBarChart"
    container_formatting = get_container_formatting(title=title, subtitle=subtitle)
    cfg["singleVisual"]["vcObjects"] = container_formatting
    cfg["singleVisual"]["visualContainerObjects"] = container_formatting
    cfg["vcObjects"] = container_formatting
    cfg["visualContainerObjects"] = container_formatting

    objects = cfg["singleVisual"].setdefault("objects", {})
    objects.pop("legend", None)
    objects.pop("slices", None)
    objects["background"] = container_formatting["background"]
    objects["border"] = container_formatting["border"]
    if title:
        objects["title"] = container_formatting["title"]
    if subtitle:
        objects["subTitle"] = container_formatting.get("subTitle", [])

    cat_props = {
        "showAxisTitle": {"expr": {"Literal": {"Value": "true" if show_category_title else "false"}}},
        "fontSize": {"expr": {"Literal": {"Value": "8D"}}},
        "fontFamily": {"expr": {"Literal": {"Value": "'Segoe UI'"}}}
    }
    if max_margin is not None:
        cat_props["maxMargin"] = {"expr": {"Literal": {"Value": f"{max_margin}D"}}}
    if category_display_name and show_category_title:
        cat_props["titleText"] = {"expr": {"Literal": {"Value": f"'{category_display_name}'"}}}
    objects["categoryAxis"] = [{"properties": cat_props}]

    val_props = {
        "showAxisTitle": {"expr": {"Literal": {"Value": "true"}}},
        "fontSize": {"expr": {"Literal": {"Value": "8.5D"}}},
        "fontFamily": {"expr": {"Literal": {"Value": "'Segoe UI'"}}}
    }
    if val_display_name:
        val_props["titleText"] = {"expr": {"Literal": {"Value": f"'{val_display_name}'"}}}
    objects["valueAxis"] = [{"properties": val_props}]

    if show_data_labels:
        objects["labels"] = [
            {
                "properties": {
                    "show": {"expr": {"Literal": {"Value": "true"}}},
                    "fontSize": {"expr": {"Literal": {"Value": "8.5D"}}},
                    "fontFamily": {"expr": {"Literal": {"Value": "'Segoe UI Semibold'"}}},
                    "displayUnits": {"expr": {"Literal": {"Value": "1D"}}}
                }
            }
        ]
    if bar_color:
        objects["dataPoint"] = [
            {
                "properties": {
                    "fill": {"solid": {"color": {"expr": {"Literal": {"Value": f"'{bar_color}'"}}}}}
                }
            }
        ]
    res["config"] = json.dumps(cfg)
    return res

def get_column_chart(name, x, y, w, h, z, entity, category_col, val_measure, title=None, subtitle=None, order_by_measure=False, col_color=None):
    res = get_donut_chart(name, x, y, w, h, z, entity, category_col, val_measure, title=title, subtitle=subtitle, order_by_measure=order_by_measure)
    cfg = json.loads(res["config"])
    cfg["singleVisual"]["visualType"] = "clusteredColumnChart"
    container_formatting = get_container_formatting(title=title, subtitle=subtitle)
    cfg["singleVisual"]["vcObjects"] = container_formatting
    cfg["singleVisual"]["visualContainerObjects"] = container_formatting
    cfg["vcObjects"] = container_formatting
    cfg["visualContainerObjects"] = container_formatting

    objects = cfg["singleVisual"].setdefault("objects", {})
    objects.pop("legend", None)
    objects.pop("slices", None)
    objects["background"] = container_formatting["background"]
    objects["border"] = container_formatting["border"]
    if title:
        objects["title"] = container_formatting["title"]
    if subtitle:
        objects["subTitle"] = container_formatting.get("subTitle", [])

    objects["categoryAxis"] = [
        {
            "properties": {
                "showAxisTitle": {"expr": {"Literal": {"Value": "true"}}},
                "titleText": {"expr": {"Literal": {"Value": "'Intake Date'"}}},
                "fontSize": {"expr": {"Literal": {"Value": "8.5D"}}},
                "fontFamily": {"expr": {"Literal": {"Value": "'Segoe UI'"}}}
            }
        }
    ]
    objects["valueAxis"] = [
        {
            "properties": {
                "showAxisTitle": {"expr": {"Literal": {"Value": "true"}}},
                "titleText": {"expr": {"Literal": {"Value": "'Daily Events'"}}},
                "fontSize": {"expr": {"Literal": {"Value": "8.5D"}}},
                "fontFamily": {"expr": {"Literal": {"Value": "'Segoe UI'"}}}
            }
        }
    ]
    objects["labels"] = [
        {
            "properties": {
                "show": {"expr": {"Literal": {"Value": "true"}}},
                "fontSize": {"expr": {"Literal": {"Value": "8.5D"}}},
                "fontFamily": {"expr": {"Literal": {"Value": "'Segoe UI Semibold'"}}},
                "displayUnits": {"expr": {"Literal": {"Value": "1D"}}}
            }
        }
    ]
    if col_color:
        objects["dataPoint"] = [
            {
                "properties": {
                    "fill": {"solid": {"color": {"expr": {"Literal": {"Value": f"'{col_color}'"}}}}}
                }
            }
        ]
    res["config"] = json.dumps(cfg)
    return res

def get_table_visual(name, x, y, w, h, z, entity, columns, display_names=None, title=None, subtitle=None, formats=None):
    if display_names is None:
        display_names = {}
    if formats is None:
        formats = {}
    container_formatting = get_container_formatting(title=title, subtitle=subtitle)
    projections = [{"queryRef": f"{entity}.{c}"} for c in columns]
    selects = [
        {
            "Column": {"Expression": {"SourceRef": {"Source": "s"}}, "Property": c},
            "Name": f"{entity}.{c}",
            "NativeReferenceName": display_names.get(c, c)
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
            "drillFilterOtherVisuals": True,
            "visualContainerObjects": container_formatting,
            "vcObjects": container_formatting
        },
        "visualContainerObjects": container_formatting,
        "vcObjects": container_formatting
    }
    tbl_objects = {
        "background": container_formatting["background"],
        "border": container_formatting["border"],
        "columnHeaders": [
            {
                "properties": {
                    "bold": {"expr": {"Literal": {"Value": "true"}}},
                    "fontSize": {"expr": {"Literal": {"Value": "8.5D"}}},
                    "fontFamily": {"expr": {"Literal": {"Value": "'Segoe UI Semibold'"}}},
                    "fontColor": {"solid": {"color": {"expr": {"Literal": {"Value": "'#102A43'"}}}}},
                    "backColor": {"solid": {"color": {"expr": {"Literal": {"Value": "'#F1F5F9'"}}}}},
                    "autoSizeColumnWidth": {"expr": {"Literal": {"Value": "true"}}}
                }
            }
        ],
        "values": [
            {
                "properties": {
                    "fontSize": {"expr": {"Literal": {"Value": "8.5D"}}},
                    "fontFamily": {"expr": {"Literal": {"Value": "'Segoe UI'"}}},
                    "fontColor": {"solid": {"color": {"expr": {"Literal": {"Value": "'#172B4D'"}}}}}
                }
            }
        ],
        "grid": [
            {
                "properties": {
                    "gridHorizontal": {"expr": {"Literal": {"Value": "true"}}},
                    "gridHorizontalColor": {"solid": {"color": {"expr": {"Literal": {"Value": "'#E2E8F0'"}}}}},
                    "gridVertical": {"expr": {"Literal": {"Value": "false"}}}
                }
            }
        ]
    }
    if title:
        tbl_objects["title"] = container_formatting["title"]
    if subtitle:
        tbl_objects["subTitle"] = container_formatting.get("subTitle", [])
    cfg["singleVisual"]["objects"] = tbl_objects

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
                        "Primary": {
                            "Groupings": [{"Projections": list(range(len(columns)))}]
                        },
                        "Version": 1
                    },
                    "ExecutionMetricsKind": 1
                }
            }
        ]
    }

    dt_selects = []
    qm_selects = []
    for idx, c in enumerate(columns):
        disp = display_names.get(c, c)
        fmt = formats.get(c, None)
        item_qm = {"Restatement": disp, "Name": f"{entity}.{c}", "Type": 2048}
        if fmt:
            item_qm["Format"] = fmt
        qm_selects.append(item_qm)

        item_sel = {
            "displayName": disp,
            "queryName": f"{entity}.{c}",
            "roles": {"Values": True},
            "type": {"category": None, "underlyingType": 1 if c in ["case_id", "raw_activity_name", "department", "metric_name", "unit", "interpretation", "event_timestamp"] else 260},
            "expr": {"Column": {"Expression": {"SourceRef": {"Entity": entity}}, "Property": c}}
        }
        if fmt:
            item_sel["format"] = fmt
        dt_selects.append(item_sel)

    data_transforms = {
        "projectionOrdering": {"Values": list(range(len(columns)))},
        "queryMetadata": {"Select": qm_selects},
        "visualElements": [
            {"DataRoles": [{"Name": "Values", "Projection": i, "isActive": False} for i in range(len(columns))]}
        ],
        "selects": dt_selects
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
    container_formatting = get_container_formatting()
    paragraphs = []
    lines = text_content.strip().split("\n")
    for idx, line in enumerate(lines):
        line_str = line.strip()
        if not line_str:
            continue
        is_bullet = any(line_str.startswith(p) for p in ['\u2022', '-', '*', '1.', '2.', '3.', '4.', '5.', '6.', '\ufffd'])
        is_heading = (idx == 0) and not is_bullet
        paragraphs.append({
            "textRuns": [
                {
                    "value": line_str,
                    "textStyle": {
                        "fontFamily": "Segoe UI Semibold" if is_heading else "Segoe UI",
                        "fontSize": "8pt" if is_heading else "7.5pt",
                        "fontWeight": "bold" if is_heading else "normal",
                        "color": "#102A43" if is_heading else "#334E68"
                    }
                }
            ]
        })
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
                "background": container_formatting["background"],
                "border": container_formatting["border"],
                "general": [
                    {
                        "properties": {
                            "paragraphs": paragraphs
                        }
                    }
                ]
            },
            "visualContainerObjects": container_formatting,
            "vcObjects": container_formatting
        },
        "visualContainerObjects": container_formatting,
        "vcObjects": container_formatting
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

def apply_premium_healthcare_theme(theme_path):
    if not os.path.exists(theme_path):
        return
    with open(theme_path, "r", encoding="utf-8") as f:
        theme = json.load(f)

    healthcare_colors = [
        "#0D9488",  # Healthcare Teal Primary
        "#102A43",  # Deep Navy
        "#243B53",  # Secondary Navy
        "#3B82F6",  # Accent Blue
        "#16A34A",  # Success Green
        "#D97706",  # Warning Amber
        "#DC6B6B",  # Critical Coral
        "#627D98",  # Secondary Slate
        "#059669",  # Emerald
        "#7C3AED",  # Violet
        "#CCFBF1",  # Light Teal
        "#F1F5F9"   # Light Slate
    ]
    theme["dataColors"] = healthcare_colors + [c for c in theme.get("dataColors", []) if c not in healthcare_colors]
    theme["foreground"] = "#172B4D"
    theme["foregroundNeutralSecondary"] = "#627D98"
    theme["foregroundNeutralTertiary"] = "#CBD5E1"
    theme["background"] = "#FFFFFF"
    theme["backgroundLight"] = "#F4F7FA"
    theme["backgroundNeutral"] = "#E2E8F0"
    theme["tableAccent"] = "#0D9488"
    theme["good"] = "#16A34A"
    theme["neutral"] = "#D97706"
    theme["bad"] = "#DC6B6B"
    theme["maximum"] = "#0D9488"
    theme["center"] = "#D97706"
    theme["minimum"] = "#CCFBF1"

    theme["textClasses"] = {
        "callout": {"fontSize": 14, "fontFace": "Segoe UI Semibold", "color": "#102A43"},
        "title": {"fontSize": 11, "fontFace": "Segoe UI Semibold", "color": "#102A43"},
        "header": {"fontSize": 10, "fontFace": "Segoe UI Semibold", "color": "#102A43"},
        "label": {"fontSize": 8, "fontFace": "Segoe UI", "color": "#627D98"}
    }

    all_styles = theme.setdefault("visualStyles", {}).setdefault("*", {}).setdefault("*", {})
    all_styles["background"] = [{"show": True, "color": {"solid": {"color": "#FFFFFF"}}, "transparency": 0}]
    all_styles["border"] = [{"show": True, "color": {"solid": {"color": "#E2E8F0"}}, "radius": 6}]
    all_styles["title"] = [{"show": True, "fontFamily": "'Segoe UI Semibold'", "fontColor": {"solid": {"color": "#102A43"}}}]

    page_styles = theme.setdefault("visualStyles", {}).setdefault("page", {}).setdefault("*", {})
    page_styles["background"] = [{"color": {"solid": {"color": "#F4F7FA"}}, "transparency": 0}]
    page_styles["outspace"] = [{"color": {"solid": {"color": "#F4F7FA"}}}]

    cv_styles = theme.setdefault("visualStyles", {}).setdefault("cardVisual", {}).setdefault("*", {})
    cv_styles["shapeCustomRectangle"] = [{"$id": "default", "tileShape": "rectangleRoundedByPixel", "rectangleRoundedCurve": 6}]
    cv_styles["outline"] = [{"$id": "default", "lineColor": {"solid": {"color": "#E2E8F0"}}}]
    cv_styles["layout"] = [{"$id": "default", "backgroundShow": True, "paddingUniform": 4}]
    cv_styles["padding"] = [{"$id": "default", "paddingUniform": 4, "paddingIndividual": False}]
    cv_styles["spacing"] = [{"$id": "default", "verticalSpacing": 4}]
    cv_styles["image"] = [{"$id": "default", "show": False, "imageAreaSize": 0, "padding": 0}]
    cv_styles["value"] = [{"$id": "default", "fontFamily": "'Segoe UI Semibold', wf_segoe-ui_semibold, helvetica, arial, sans-serif", "fontSize": 14, "fontColor": {"solid": {"color": "#102A43"}}, "displayUnits": 1, "valueDisplayUnits": 1, "alignment": "Center"}]
    cv_styles["label"] = [{"$id": "default", "position": "belowValue", "fontSize": 8, "fontColor": {"solid": {"color": "#627D98"}}, "textWrap": True, "alignment": "Center"}]

    tbl_styles = theme.setdefault("visualStyles", {}).setdefault("tableEx", {}).setdefault("*", {})
    tbl_styles["columnHeaders"] = [{
        "bold": True,
        "fontSize": 8.5,
        "fontColor": {"solid": {"color": "#102A43"}},
        "backColor": {"solid": {"color": "#F1F5F9"}},
        "autoSizeColumnWidth": True
    }]

    dc_styles = theme.setdefault("visualStyles", {}).setdefault("donutChart", {}).setdefault("*", {})
    dc_styles["labels"] = [{
        "show": True,
        "labelStyle": "Both",
        "labelDisplayUnits": 1,
        "displayUnits": 1,
        "labelPrecision": 0
    }]

    with open(theme_path, "w", encoding="utf-8") as f:
        json.dump(theme, f, indent=2)

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
                        "AVERAGEX(",
                        "    VALUES('stg_hospital_events'[case_id]),",
                        "    CALCULATE(SUM('stg_hospital_events'[transition_minutes_from_previous]))",
                        ")"
                    ]
                    m['formatString'] = '0.0 "mins"'
            meas = {m['name']: m for m in t.get('measures', [])}
            clean_measures = [
                ('Average Cycle Time', '[Avg Case Cycle Time (Mins)]', '0.0 "mins"'),
                ('Median Cycle Time', '[Median Case Cycle Time (Mins)]', '0.0 "mins"'),
                ('Repeat-Triage Rate', '[Re-Triage Rate %]', '0.0%'),
                ('Conformant Cases', '[Conformant Cases Count]', '#,##0'),
                ('Repeat-Triage Cases', '[Repeat Triage Cases Count]', '#,##0'),
                ('Conformance Rate', '[Conformance Rate %]', '0.0%')
            ]
            for m_name, m_expr, m_fmt in clean_measures:
                if m_name not in meas:
                    t.setdefault('measures', []).append({
                        'name': m_name,
                        'expression': m_expr,
                        'formatString': m_fmt
                    })
                elif m['name'] == 'Median Case Cycle Time (Mins)':
                    m['expression'] = [
                        "MEDIANX(",
                        "    VALUES('stg_hospital_events'[case_id]),",
                        "    CALCULATE(SUM('stg_hospital_events'[transition_minutes_from_previous]))",
                        ")"
                    ]
                    m['formatString'] = '0.0 "mins"'
            meas = {m['name']: m for m in t.get('measures', [])}
            clean_measures = [
                ('Average Cycle Time', '[Avg Case Cycle Time (Mins)]', '0.0 "mins"'),
                ('Median Cycle Time', '[Median Case Cycle Time (Mins)]', '0.0 "mins"'),
                ('Repeat-Triage Rate', '[Re-Triage Rate %]', '0.0%'),
                ('Conformant Cases', '[Conformant Cases Count]', '#,##0'),
                ('Repeat-Triage Cases', '[Repeat Triage Cases Count]', '#,##0'),
                ('Conformance Rate', '[Conformance Rate %]', '0.0%')
            ]
            for m_name, m_expr, m_fmt in clean_measures:
                if m_name not in meas:
                    t.setdefault('measures', []).append({
                        'name': m_name,
                        'expression': m_expr,
                        'formatString': m_fmt
                    })

        elif t['name'] == 'stg_hospital_events (2)':
            t['excludeFromModelRefresh'] = True
            t['partitions'][0]['source']['expression'] = [
                'let',
                f'    Source = Csv.Document(File.Contents("{csv_events}"),[Delimiter=",", Columns=11, Encoding=65001, QuoteStyle=QuoteStyle.None]),',
                '    #"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),',
                '    #"Replaced Empty Strings" = Table.ReplaceValue(#"Promoted Headers", "", null, Replacer.ReplaceValue, {"previous_activity", "transition_minutes_from_previous"}),',
                '    #"Changed Type" = Table.TransformColumnTypes(#"Replaced Empty Strings",{{"case_id", type text}, {"event_sequence", Int64.Type}, {"raw_activity_name", type text}, {"activity_name", type text}, {"event_timestamp", type datetime}, {"event_date", type date}, {"department", type text}, {"resource_id", type text}, {"data_provenance", type text}, {"previous_activity", type text}, {"transition_minutes_from_previous", Int64.Type}})',
                'in',
                '    #"Changed Type"'
            ]

        elif t['name'] == 'pathway_variants_summary':
            t['partitions'][0]['source']['expression'] = [
                'let',
                f'    Source = Csv.Document(File.Contents("{csv_variants}"),[Delimiter=",", Columns=4, Encoding=65001, QuoteStyle=QuoteStyle.None]),',
                '    #"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),',
                '    #"Changed Type" = Table.TransformColumnTypes(#"Promoted Headers",{{"variant_rank", Int64.Type}, {"case_count", Int64.Type}, {"percentage", type number}, {"pathway", type text}}),',
                '    #"Added Variant Label" = Table.AddColumn(#"Changed Type", "variant_label", each (if [variant_rank] = 1 then "Standard Flow (40%)" else if [variant_rank] = 2 then "Lab Diagnostic (22%)" else if [variant_rank] = 3 then "X-Ray Diagnostic (16%)" else if [variant_rank] = 4 then "Lab + X-Ray (10%)" else if [variant_rank] = 5 then "Re-Triage Loop (7%)" else "Re-Triage + Lab (5%)"), type text)',
                'in',
                '    #"Added Variant Label"'
            ]
            cols = {c['name']: c for c in t.get('columns', [])}
            if 'variant_label' not in cols:
                t['columns'].append({
                    'name': 'variant_label',
                    'dataType': 'string',
                    'sourceColumn': 'variant_label'
                })
            meas = {m['name']: m for m in t.get('measures', [])}
            if 'Total Variant Cases' not in meas:
                if 'measures' not in t:
                    t['measures'] = []
                t['measures'].append({
                    'name': 'Total Variant Cases',
                    'expression': "SUM('pathway_variants_summary'[case_count])",
                    'formatString': '#,##0'
                })
            if 'Total Pathway Variants' not in meas:
                if 'measures' not in t:
                    t['measures'] = []
                t['measures'].append({
                    'name': 'Total Pathway Variants',
                    'expression': "COUNTROWS('pathway_variants_summary')",
                    'formatString': '0'
                })
            if 'Pathway Variants' not in meas:
                if 'measures' not in t:
                    t['measures'] = []
                t['measures'].append({
                    'name': 'Pathway Variants',
                    'expression': "COUNTROWS('pathway_variants_summary')",
                    'formatString': '0'
                })

        elif t['name'] == 'bottleneck_analysis_summary':
            t['partitions'][0]['source']['expression'] = [
                'let',
                f'    Source = Csv.Document(File.Contents("{csv_bottlenecks}"),[Delimiter=",", Columns=8, Encoding=65001, QuoteStyle=QuoteStyle.None]),',
                '    #"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),',
                '    #"Changed Type" = Table.TransformColumnTypes(#"Promoted Headers",{{"rank", Int64.Type}, {"source_activity", type text}, {"target_activity", type text}, {"transition_count", Int64.Type}, {"mean_observed_transition_minutes", type number}, {"median_observed_transition_minutes", type number}, {"min_observed_transition_minutes", type number}, {"max_observed_transition_minutes", type number}}),',
                '    #"Added Transition" = Table.AddColumn(#"Changed Type", "transition", each [source_activity] & " -> " & [target_activity], type text),',
                '    #"Added Transition Label" = Table.AddColumn(#"Added Transition", "transition_label", each [source_activity] & " -> " & [target_activity], type text),',
                '    #"Added Avg Duration Mins" = Table.AddColumn(#"Added Transition Label", "avg_duration_mins", each [mean_observed_transition_minutes], type number),',
                '    #"Added Transition Display" = Table.AddColumn(#"Added Avg Duration Mins", "transition_display", each (if [source_activity] = "Triage" and [target_activity] = "Triage" then "Triage →#(lf)Re-Triage" else [source_activity] & " →#(lf)" & [target_activity]), type text)',
                'in',
                '    #"Added Transition Display"'
            ]
            cols = {c['name']: c for c in t.get('columns', [])}
            needed_cols = [
                ('transition_count', 'int64'),
                ('median_observed_transition_minutes', 'double'),
                ('min_observed_transition_minutes', 'double'),
                ('max_observed_transition_minutes', 'double'),
                ('transition_display', 'string')
            ]
            for col_name, d_type in needed_cols:
                if col_name not in cols:
                    t['columns'].append({
                        'name': col_name,
                        'dataType': d_type,
                        'sourceColumn': col_name
                    })
            meas = {m['name']: m for m in t.get('measures', [])}
            if 'Avg Transition Duration' not in meas:
                if 'measures' not in t:
                    t['measures'] = []
                t['measures'].append({
                    'name': 'Avg Transition Duration',
                    'expression': "AVERAGE('bottleneck_analysis_summary'[mean_observed_transition_minutes])",
                    'formatString': '0.0 "mins"'
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
                    'expression': "DIVIDE(MAX('pathway_improvement_comparison'[proposed_value]) - MAX('pathway_improvement_comparison'[baseline_value]), MAX('pathway_improvement_comparison'[baseline_value]), 0)",
                    'formatString': '+0.0%;-0.0%;0.0%'
                })

    with open(bim_path, 'w', encoding='utf-8') as f:
        json.dump(bim, f, indent=2)
    print(f"[UPDATED] {bim_path}")

def build():
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    proj_dir = os.path.join(repo_root, "powerbi", "CareFlow_Dashboard_Project")
    sm_dir = os.path.join(proj_dir, "CareFlow_Dashboard.SemanticModel")
    sm_def = os.path.join(sm_dir, "definition")
    tables_dir = os.path.join(sm_def, "tables")
    rep_dir = os.path.join(proj_dir, "CareFlow_Dashboard.Report")
    rep_def = os.path.join(rep_dir, "definition")

    os.makedirs(tables_dir, exist_ok=True)
    os.makedirs(rep_dir, exist_ok=True)
    os.makedirs(rep_def, exist_ok=True)

    csv_events = os.path.join(repo_root, "data", "cleaned", "stg_hospital_events.csv")
    csv_variants = os.path.join(repo_root, "outputs", "pathway_variants_summary.csv")
    csv_bottlenecks = os.path.join(repo_root, "outputs", "bottleneck_analysis_summary.csv")
    csv_improvement = os.path.join(repo_root, "outputs", "pathway_improvement_comparison.csv")

    # 1. Update model.bim
    bim_path = os.path.join(sm_dir, "model.bim")
    if os.path.exists(bim_path):
        update_model_bim(bim_path, repo_root)

    # 2. Synchronize careflow_semantic_model
    template_bim = os.path.join(repo_root, "powerbi", "careflow_semantic_model", "model.bim")
    if os.path.exists(template_bim):
        update_model_bim(template_bim, repo_root)

    # 3. Update TMDL tables
    # 3a. stg_hospital_events.tmdl
    stg_tmdl = """table stg_hospital_events
	lineageTag: e8f1a2b3-c4d5-6e7f-8a9b-0c1d2e3f4a5b

	measure 'Total Cases' = DISTINCTCOUNT('stg_hospital_events'[case_id])
		formatString: #,##0
		lineageTag: f1a2b3c4-d5e6-7f8a-9b0c-1d2e3f4a5b6c

	measure 'Total Events' = COUNTROWS('stg_hospital_events')
		formatString: #,##0
		lineageTag: f2a3b4c5-e6f7-8a9b-0c1d-2e3f4a5b6c7d

	measure 'Avg Case Cycle Time (Mins)' =
			AVERAGEX(
			    VALUES('stg_hospital_events'[case_id]),
			    CALCULATE(SUM('stg_hospital_events'[transition_minutes_from_previous]))
			)
		formatString: 0.0 "mins"
		lineageTag: f3a4b5c6-f7a8-9b0c-1d2e-3f4a5b6c7d8e

	measure 'Median Case Cycle Time (Mins)' =
			MEDIANX(
			    VALUES('stg_hospital_events'[case_id]),
			    CALCULATE(SUM('stg_hospital_events'[transition_minutes_from_previous]))
			)
		formatString: 0.0 "mins"
		lineageTag: f4a5b6c7-a8b9-0c1d-2e3f-4a5b6c7d8e9f

	measure 'Re-Triage Rate %' = DIVIDE([Repeat Triage Cases Count], [Total Cases], 0)
		formatString: 0.0%
		lineageTag: f5a6b7c8-b9c0-1d2e-3f4a-5b6c7d8e9f0a

	measure 'Repeat Triage Cases Count' =
			CALCULATE(
			    DISTINCTCOUNT('stg_hospital_events'[case_id]),
			    'stg_hospital_events'[activity_name] = "Triage",
			    'stg_hospital_events'[previous_activity] = "Triage"
			)
		formatString: #,##0
		lineageTag: f6a7b8c9-c0d1-2e3f-4a5b-6c7d8e9f0a1b

	measure 'Conformant Cases Count' = [Total Cases] - [Repeat Triage Cases Count]
		formatString: #,##0
		lineageTag: f7a8b9c0-d1e2-3f4a-5b6c-7d8e9f0a1b2c

	measure 'Conformance Rate %' = DIVIDE([Conformant Cases Count], [Total Cases], 0)
		formatString: 0.0%
		lineageTag: f8a9b0c1-e2f3-4a5b-6c7d-8e9f0a1b2c3d

	measure 'Average Cycle Time' = [Avg Case Cycle Time (Mins)]
		formatString: 0.0 "mins"
		lineageTag: c1d2e3f4-a5b6-7c8d-9e0f-1a2b3c4d5e6f

	measure 'Median Cycle Time' = [Median Case Cycle Time (Mins)]
		formatString: 0.0 "mins"
		lineageTag: c2d3e4f5-b6c7-8d9e-0f1a-2b3c4d5e6f7a

	measure 'Repeat-Triage Rate' = [Re-Triage Rate %]
		formatString: 0.0%
		lineageTag: c3d4e5f6-c7d8-9e0f-1a2b-3c4d5e6f7a8b

	measure 'Conformant Cases' = [Conformant Cases Count]
		formatString: #,##0
		lineageTag: c4d5e6f7-d8e9-0f1a-2b3c-4d5e6f7a8b9c

	measure 'Repeat-Triage Cases' = [Repeat Triage Cases Count]
		formatString: #,##0
		lineageTag: c5d6e7f8-e9f0-1a2b-3c4d-5e6f7a8b9c0d

	measure 'Conformance Rate' = [Conformance Rate %]
		formatString: 0.0%
		lineageTag: c6d7e8f9-f0a1-2b3c-4d5e-6f7a8b9c0d1e

	column case_id
		dataType: string
		summarizeBy: none
		sourceColumn: case_id

	column event_sequence
		dataType: int64
		formatString: 0
		summarizeBy: none
		sourceColumn: event_sequence

	column raw_activity_name
		dataType: string
		summarizeBy: none
		sourceColumn: raw_activity_name

	column activity_name
		dataType: string
		summarizeBy: none
		sourceColumn: activity_name

	column event_timestamp
		dataType: dateTime
		formatString: yyyy-mm-dd hh:nn
		summarizeBy: none
		sourceColumn: event_timestamp

	column event_date
		dataType: dateTime
		formatString: yyyy-mm-dd
		summarizeBy: none
		sourceColumn: event_date

	column department
		dataType: string
		summarizeBy: none
		sourceColumn: department

	column resource_id
		dataType: string
		summarizeBy: none
		sourceColumn: resource_id

	column data_provenance
		dataType: string
		summarizeBy: none
		sourceColumn: data_provenance

	column previous_activity
		dataType: string
		summarizeBy: none
		sourceColumn: previous_activity

	column transition_minutes_from_previous
		dataType: int64
		formatString: #,##0
		summarizeBy: sum
		sourceColumn: transition_minutes_from_previous

	partition stg_hospital_events = m
		mode: import
		source =
				let
				    Source = Csv.Document(File.Contents("__CSV_EVENTS__"),[Delimiter=",", Columns=11, Encoding=65001, QuoteStyle=QuoteStyle.None]),
				    #"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
				    #"Replaced Empty Strings" = Table.ReplaceValue(#"Promoted Headers", "", null, Replacer.ReplaceValue, {"previous_activity", "transition_minutes_from_previous"}),
				    #"Changed Type" = Table.TransformColumnTypes(#"Replaced Empty Strings",{{"case_id", type text}, {"event_sequence", Int64.Type}, {"raw_activity_name", type text}, {"activity_name", type text}, {"event_timestamp", type datetime}, {"event_date", type date}, {"department", type text}, {"resource_id", type text}, {"data_provenance", type text}, {"previous_activity", type text}, {"transition_minutes_from_previous", Int64.Type}})
				in
				    #"Changed Type"

	annotation PBI_ResultType = Table
""".replace("__CSV_EVENTS__", csv_events)
    with open(os.path.join(tables_dir, "stg_hospital_events.tmdl"), "w", encoding="utf-8") as f:
        f.write(stg_tmdl)

    # 3b. stg_hospital_events (2).tmdl
    stg2_tmdl = """table 'stg_hospital_events (2)'
	lineageTag: e9f2a3b4-c5d6-7e8f-9a0b-1c2d3e4f5a6c
	excludeFromModelRefresh

	column case_id
		dataType: string
		summarizeBy: none
		sourceColumn: case_id

	column event_sequence
		dataType: int64
		formatString: 0
		summarizeBy: none
		sourceColumn: event_sequence

	column raw_activity_name
		dataType: string
		summarizeBy: none
		sourceColumn: raw_activity_name

	column activity_name
		dataType: string
		summarizeBy: none
		sourceColumn: activity_name

	column event_timestamp
		dataType: dateTime
		formatString: yyyy-mm-dd hh:nn
		summarizeBy: none
		sourceColumn: event_timestamp

	column event_date
		dataType: dateTime
		formatString: yyyy-mm-dd
		summarizeBy: none
		sourceColumn: event_date

	column department
		dataType: string
		summarizeBy: none
		sourceColumn: department

	column resource_id
		dataType: string
		summarizeBy: none
		sourceColumn: resource_id

	column data_provenance
		dataType: string
		summarizeBy: none
		sourceColumn: data_provenance

	column previous_activity
		dataType: string
		summarizeBy: none
		sourceColumn: previous_activity

	column transition_minutes_from_previous
		dataType: int64
		formatString: #,##0
		summarizeBy: sum
		sourceColumn: transition_minutes_from_previous

	partition 'stg_hospital_events (2)' = m
		mode: import
		source =
				let
				    Source = Csv.Document(File.Contents("__CSV_EVENTS__"),[Delimiter=",", Columns=11, Encoding=65001, QuoteStyle=QuoteStyle.None]),
				    #"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
				    #"Replaced Empty Strings" = Table.ReplaceValue(#"Promoted Headers", "", null, Replacer.ReplaceValue, {"previous_activity", "transition_minutes_from_previous"}),
				    #"Changed Type" = Table.TransformColumnTypes(#"Replaced Empty Strings",{{"case_id", type text}, {"event_sequence", Int64.Type}, {"raw_activity_name", type text}, {"activity_name", type text}, {"event_timestamp", type datetime}, {"event_date", type date}, {"department", type text}, {"resource_id", type text}, {"data_provenance", type text}, {"previous_activity", type text}, {"transition_minutes_from_previous", Int64.Type}})
				in
				    #"Changed Type"

	annotation PBI_ResultType = Table
""".replace("__CSV_EVENTS__", csv_events)
    with open(os.path.join(tables_dir, "stg_hospital_events (2).tmdl"), "w", encoding="utf-8") as f:
        f.write(stg2_tmdl)

    # 3c. pathway_variants_summary.tmdl
    pathway_tmdl = """table pathway_variants_summary
	lineageTag: a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d

	measure 'Total Variant Cases' = SUM('pathway_variants_summary'[case_count])
		formatString: #,##0
		lineageTag: a2b3c4d5-e6f7-8a9b-0c1d-2e3f4a5b6c7d

	measure 'Total Pathway Variants' = COUNTROWS('pathway_variants_summary')
		formatString: 0
		lineageTag: a3b4c5d6-e7f8-9a0b-1c2d-3e4f5a6b7c8d

	measure 'Pathway Variants' = [Total Pathway Variants]
		formatString: 0
		lineageTag: d1e2f3a4-b5c6-7d8e-9f0a-1b2c3d4e5f6a

	column variant_rank
		dataType: int64
		formatString: 0
		summarizeBy: none
		sourceColumn: variant_rank

	column case_count
		dataType: int64
		formatString: #,##0
		summarizeBy: sum
		sourceColumn: case_count

	column percentage
		dataType: double
		formatString: 0.0"%"
		summarizeBy: none
		sourceColumn: percentage

	column pathway
		dataType: string
		summarizeBy: none
		sourceColumn: pathway

	column variant_label
		dataType: string
		summarizeBy: none
		sourceColumn: variant_label

	partition pathway_variants_summary = m
		mode: import
		source =
				let
				    Source = Csv.Document(File.Contents("__CSV_VARIANTS__"),[Delimiter=",", Columns=4, Encoding=65001, QuoteStyle=QuoteStyle.None]),
				    #"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
				    #"Changed Type" = Table.TransformColumnTypes(#"Promoted Headers",{{"variant_rank", Int64.Type}, {"case_count", Int64.Type}, {"percentage", type number}, {"pathway", type text}}),
				    #"Added Variant Label" = Table.AddColumn(#"Changed Type", "variant_label", each (if [variant_rank] = 1 then "Standard Flow (40%)" else if [variant_rank] = 2 then "Lab Diagnostic (22%)" else if [variant_rank] = 3 then "X-Ray Diagnostic (16%)" else if [variant_rank] = 4 then "Lab + X-Ray (10%)" else if [variant_rank] = 5 then "Re-Triage Loop (7%)" else "Re-Triage + Lab (5%)"), type text)
				in
				    #"Added Variant Label"

	annotation PBI_ResultType = Table
""".replace("__CSV_VARIANTS__", csv_variants)
    with open(os.path.join(tables_dir, "pathway_variants_summary.tmdl"), "w", encoding="utf-8") as f:
        f.write(pathway_tmdl)

    # 3d. bottleneck_analysis_summary.tmdl
    bottleneck_tmdl = """table bottleneck_analysis_summary
	lineageTag: b2c3d4e5-f6a7-8b9c-0d1e-2f3a4b5c6d7e

	measure 'Avg Transition Duration' = AVERAGE('bottleneck_analysis_summary'[mean_observed_transition_minutes])
		formatString: 0.0 "mins"
		lineageTag: b3c4d5e6-f7a8-9b0c-1d2e-3f4a5b6c7d8e

	column rank
		dataType: int64
		formatString: 0
		summarizeBy: none
		sourceColumn: rank

	column source_activity
		dataType: string
		summarizeBy: none
		sourceColumn: source_activity

	column target_activity
		dataType: string
		summarizeBy: none
		sourceColumn: target_activity

	column mean_observed_transition_minutes
		dataType: double
		formatString: 0.0
		summarizeBy: none
		sourceColumn: mean_observed_transition_minutes

	column transition
		dataType: string
		summarizeBy: none
		sourceColumn: transition

	column transition_label
		dataType: string
		summarizeBy: none
		sourceColumn: transition_label

	column avg_duration_mins
		dataType: double
		formatString: 0.0
		summarizeBy: none
		sourceColumn: avg_duration_mins

	column transition_display
		dataType: string
		summarizeBy: none
		sourceColumn: transition_display

	column transition_count
		dataType: int64
		formatString: 0
		summarizeBy: sum
		sourceColumn: transition_count

	column median_observed_transition_minutes
		dataType: double
		formatString: 0.0
		summarizeBy: none
		sourceColumn: median_observed_transition_minutes

	column min_observed_transition_minutes
		dataType: double
		formatString: 0.0
		summarizeBy: none
		sourceColumn: min_observed_transition_minutes

	column max_observed_transition_minutes
		dataType: double
		formatString: 0.0
		summarizeBy: none
		sourceColumn: max_observed_transition_minutes

	partition bottleneck_analysis_summary = m
		mode: import
		source =
				let
				    Source = Csv.Document(File.Contents("__CSV_BOTTLENECKS__"),[Delimiter=",", Columns=8, Encoding=65001, QuoteStyle=QuoteStyle.None]),
				    #"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
				    #"Changed Type" = Table.TransformColumnTypes(#"Promoted Headers",{{"rank", Int64.Type}, {"source_activity", type text}, {"target_activity", type text}, {"transition_count", Int64.Type}, {"mean_observed_transition_minutes", type number}, {"median_observed_transition_minutes", type number}, {"min_observed_transition_minutes", type number}, {"max_observed_transition_minutes", type number}}),
				    #"Added Transition" = Table.AddColumn(#"Changed Type", "transition", each [source_activity] & " -> " & [target_activity], type text),
				    #"Added Transition Label" = Table.AddColumn(#"Added Transition", "transition_label", each [source_activity] & " -> " & [target_activity], type text),
				    #"Added Avg Duration Mins" = Table.AddColumn(#"Added Transition Label", "avg_duration_mins", each [mean_observed_transition_minutes], type number),
				    #"Added Transition Display" = Table.AddColumn(#"Added Avg Duration Mins", "transition_display", each (if [source_activity] = "Triage" and [target_activity] = "Triage" then "Triage →#(lf)Re-Triage" else [source_activity] & " →#(lf)" & [target_activity]), type text)
				in
				    #"Added Transition Display"

	annotation PBI_ResultType = Table
""".replace("__CSV_BOTTLENECKS__", csv_bottlenecks)
    with open(os.path.join(tables_dir, "bottleneck_analysis_summary.tmdl"), "w", encoding="utf-8") as f:
        f.write(bottleneck_tmdl)

    # 3e. pathway_improvement_comparison.tmdl
    improvement_tmdl = """table pathway_improvement_comparison
	lineageTag: c3d4e5f6-a7b8-9c0d-1e2f-3a4b5c6d7e8f

	column category
		dataType: string
		summarizeBy: none
		sourceColumn: category

	column metric_name
		dataType: string
		summarizeBy: none
		sourceColumn: metric_name

	column baseline_value
		dataType: double
		formatString: #,##0.0
		summarizeBy: none
		sourceColumn: baseline_value

	column proposed_value
		dataType: double
		formatString: #,##0.0
		summarizeBy: none
		sourceColumn: proposed_value

	column absolute_difference
		dataType: double
		formatString: #,##0.0
		summarizeBy: none
		sourceColumn: absolute_difference

	column percentage_difference
		dataType: double
		formatString: +0.0%;-0.0%;0.0%
		summarizeBy: none
		sourceColumn: percentage_difference

	column unit
		dataType: string
		summarizeBy: none
		sourceColumn: unit

	column provenance
		dataType: string
		summarizeBy: none
		sourceColumn: provenance

	column interpretation
		dataType: string
		summarizeBy: none
		sourceColumn: interpretation

	measure 'Relative % Difference' =
			VAR Baseline = SELECTEDVALUE('pathway_improvement_comparison'[baseline_value])
			VAR Proposed = SELECTEDVALUE('pathway_improvement_comparison'[proposed_value])
			RETURN
				IF(
					ISBLANK(Baseline) || Baseline = 0,
					IF(Proposed = 0, 0, BLANK()),
					DIVIDE(Proposed - Baseline, Baseline)
				)
		formatString: +0.0%;-0.0%;0.0%
		lineageTag: c4d5e6f7-a8b9-0c1d-2e3f-4a5b6c7d8e9f

	partition pathway_improvement_comparison = m
		mode: import
		source =
				let
				    Source = Csv.Document(File.Contents("__CSV_IMPROVEMENT__"),[Delimiter=",", Columns=9, Encoding=65001, QuoteStyle=QuoteStyle.None]),
				    #"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
				    #"Removed Precalculated Pct" = Table.RemoveColumns(#"Promoted Headers",{"percentage_difference"}),
				    #"Changed Type" = Table.TransformColumnTypes(#"Removed Precalculated Pct",{{"category", type text}, {"metric_name", type text}, {"baseline_value", type number}, {"proposed_value", type number}, {"absolute_difference", type number}, {"unit", type text}, {"provenance", type text}, {"interpretation", type text}}),
				    #"Calculated Relative Difference" = Table.AddColumn(#"Changed Type", "percentage_difference", each if [baseline_value] = null or [baseline_value] = 0 then (if [proposed_value] = 0 then 0.0 else null) else ([proposed_value] - [baseline_value]) / [baseline_value], type number),
				    #"Reordered Columns" = Table.SelectColumns(#"Calculated Relative Difference", {"category", "metric_name", "baseline_value", "proposed_value", "absolute_difference", "percentage_difference", "unit", "provenance", "interpretation"})
				in
				    #"Reordered Columns"

	annotation PBI_ResultType = Table
""".replace("__CSV_IMPROVEMENT__", csv_improvement)
    with open(os.path.join(tables_dir, "pathway_improvement_comparison.tmdl"), "w", encoding="utf-8") as f:
        f.write(improvement_tmdl)

    # 4. Synchronize template TMDL
    stg_template = os.path.join(repo_root, "powerbi", "careflow_semantic_model", "tables", "stg_hospital_events.tmdl")
    if os.path.exists(stg_template):
        with open(stg_template, "w", encoding="utf-8") as f:
            f.write(stg_tmdl)

    stg2_template = os.path.join(repo_root, "powerbi", "careflow_semantic_model", "tables", "stg_hospital_events (2).tmdl")
    if os.path.exists(stg2_template):
        with open(stg2_template, "w", encoding="utf-8") as f:
            f.write(stg2_tmdl)

    # 5. Extract Theme from AutoRecovery pbix
    pbix_backup = os.path.join(repo_root, "powerbi", "backup", "CareFlow_AutoRecovery_Backup.pbix")
    if os.path.exists(pbix_backup):
        with zipfile.ZipFile(pbix_backup, "r") as z:
            for name in z.namelist():
                if name.startswith("Report/StaticResources"):
                    rel = name[len("Report/"):]
                    for base in [rep_dir, rep_def]:
                        dest = os.path.join(base, rel)
                        os.makedirs(os.path.dirname(dest), exist_ok=True)
                        with open(dest, "wb") as out_f:
                            out_f.write(z.read(name))
            for base in [rep_dir, rep_def]:
                for tname in ["BaseThemes/CY26SU05.json", "BuiltInThemes/AccessibleCityPark.json"]:
                    theme_f = os.path.join(base, "StaticResources", "SharedResources", tname.replace("/", os.sep))
                    if os.path.exists(theme_f):
                        apply_premium_healthcare_theme(theme_f)

    # 6. Build Report Visual Containers with full query and dataTransforms

    p1_disclaimer = (
        "Executive Operations Insights & Clinical Governance:\n"
        "\u2022 Clinical Volumes: Consultation leads recorded activity (765 events; 24.4%), followed by Treatment (500) and Initial Triage (500).\n"
        "\u2022 Department Workload: Emergency handles 89.97% (2,825 events); Laboratory (185) and Radiology (130) deliver diagnostic evaluation.\n"
        "\u2022 Acuity Signal & Cohort: Repeat triage occurs in 12.0% of cases (60 encounters, +65.6 min latency). Simulated CareFlow ED cohort (500 cases, Oct 2024)."
    )
    page1_visuals = [
        get_header_banner("hdr_page1", 20, 12, 1240, 48, 0, "Hospital Operations Overview", "CareFlow Clinical Pathway Intelligence • 500 Patient Encounters • 3,140 Process Events"),
        get_card_visual("card_total_cases", 20, 68, 236, 110, 1, "stg_hospital_events", "Total Cases", display_units_none=True, title="Total Cases", subtitle="Discrete Cohort Encounters"),
        get_card_visual("card_total_events", 271, 68, 236, 110, 2, "stg_hospital_events", "Total Events", display_units_none=True, title="Total Events", subtitle="Recorded Milestone Steps"),
        get_card_visual("card_avg_duration", 522, 68, 236, 110, 3, "stg_hospital_events", "Average Cycle Time", format_string='0.0 "mins"', title="Average Cycle Time", subtitle="Mean Total Turnaround Time"),
        get_card_visual("card_med_duration", 773, 68, 236, 110, 4, "stg_hospital_events", "Median Cycle Time", format_string='0.0 "mins"', title="Median Cycle Time", subtitle="50th Percentile Turnaround Time"),
        get_card_visual("card_retriage_rate", 1024, 68, 236, 110, 5, "stg_hospital_events", "Repeat-Triage Rate", format_string="0.0%", title="Repeat-Triage Rate", subtitle="Secondary Assessment Rate", callout_color="#D97706"),
        get_donut_chart("donut_dept_breakdown", 20, 188, 380, 390, 6, "stg_hospital_events", "department", "Total Events", title="Event Distribution by Clinical Department", subtitle="Milestone activity volume by clinical service unit", category_display_name="Department", val_display_name="Event Volume"),
        get_bar_chart_measure(
            "bar_activity_breakdown", 415, 188, 430, 390, 7,
            "stg_hospital_events", "raw_activity_name", "Total Events",
            title="Clinical Activity Volume",
            subtitle="Encounter volume across standard and diagnostic pathway milestones",
            category_display_name="Clinical Activity",
            val_display_name="Event Count",
            max_margin=35,
            show_data_labels=True,
            bar_color="#0D9488"
        ),
        get_column_chart("col_daily_trend", 860, 188, 400, 390, 8, "stg_hospital_events", "event_date", "Total Events", title="Daily Patient Intake & Activity Trend", subtitle="Chronological daily event volume across observation window", col_color="#3B82F6"),
        get_textbox_visual("txt_disclaimer_page1", 20, 588, 1240, 122, 9, p1_disclaimer)
    ]

    p2_guidance = (
        "Workflow Conformance & Pathway Variant Analysis:\n"
        "\u2022 Standard Forward Flow: 440 patient encounters (88.0%) adhere to forward non-loop clinical pathways (dominant Standard Flow = 40.0%).\n"
        "\u2022 Repeat-Triage Loops: 60 encounters (12.0%) exhibit loop-back reassessments (Variants 5 & 6) prior to consultation, adding 65.6 min delay.\n"
        "\u2022 Clinical Governance: Re-triage reflects clinical monitoring of evolving acuity; protocol standardization offers an opportunity to streamline care."
    )
    page2_visuals = [
        get_header_banner("hdr_page2", 20, 12, 1240, 48, 0, "Patient Journey & Pathway Conformance", "Clinical Pathway Process Mining • Conformance Benchmarks & Operational Re-Triage Tracking"),
        get_card_visual("card_conformant_cases", 20, 68, 295, 110, 1, "stg_hospital_events", "Conformant Cases", display_units_none=True, title="Conformant Cases", subtitle="Standard Forward Pathways (88.0%)", callout_color="#0D9488"),
        get_card_visual("card_retriage_cases", 335, 68, 295, 110, 2, "stg_hospital_events", "Repeat-Triage Cases", display_units_none=True, title="Repeat-Triage Cases", subtitle="Loop-Back Reassessments (12.0%)", callout_color="#D97706"),
        get_card_visual("card_conformance_rate", 650, 68, 295, 110, 3, "stg_hospital_events", "Conformance Rate", format_string="0.0%", title="Conformance Rate", subtitle="Standard Care Adherence Benchmark", callout_color="#0D9488"),
        get_card_visual("card_pathway_variants", 965, 68, 295, 110, 4, "pathway_variants_summary", "Total Pathway Variants", display_units_none=True, title="Total Pathway Variants", subtitle="Distinct Observed Routing Sequences", callout_color="#102A43"),
        get_bar_chart_measure(
            "bar_pathway_variants", 20, 188, 580, 390, 5,
            "pathway_variants_summary", "variant_label", "Total Variant Cases",
            title="Clinical Pathway Variants by Case Volume",
            subtitle="Variant 1 (40%) leads; Variants 5 & 6 (12%) exhibit repeat-triage loops",
            category_display_name="Clinical Pathway Variant",
            val_display_name="Case Volume",
            max_margin=50,
            show_data_labels=True,
            bar_color="#0D9488"
        ),
        get_table_visual(
            "tbl_case_audit", 615, 188, 645, 390, 6,
            "stg_hospital_events",
            ["case_id", "event_sequence", "raw_activity_name", "department", "event_timestamp"],
            display_names={"case_id": "Case ID", "event_sequence": "Event Sequence", "raw_activity_name": "Activity Name", "department": "Department", "event_timestamp": "Event Timestamp"},
            title="Sequential Patient Encounter Audit Trail",
            subtitle="Chronological event sequence with department and elapsed interval",
            formats={"event_sequence": "#,##0"}
        ),
        get_textbox_visual("txt_guidance_page2", 20, 588, 1240, 122, 7, p2_guidance)
    ]

    p3_safety = (
        "Operational Bottlenecks & Hypothetical Process Improvement (Simulated Scenarios):\n"
        "1. Lab-to-Consultation Handoff (Signal: 67.4 min mean elapsed time across 135 encounters): Opportunity for automated critical result alerts.\n"
        "2. Diagnostic Radiology Coordination (Signal: 60.4 min mean elapsed time across 130 encounters): Opportunity to streamline PACS archiving notifications.\n"
        "3. Repeat-Triage Reassessment (Signal: 60 encounters / 12.0% volume, 65.6 min delay): Standardize secondary triage criteria and intake acuity stratification.\n"
        "\u2022 Clinical Safety Disclaimer: Observed transition durations reflect total clock elapsed time (specimen processing, imaging, medication, transport), not pure waiting time. Proposed To-Be improvements are hypothetical simulation scenarios requiring clinical validation."
    )
    page3_visuals = [
        get_header_banner("hdr_page3", 20, 12, 1240, 48, 0, "Operational Bottlenecks & Process Improvement", "Transition Latency Diagnostics • As-Is Baseline vs. Proposed Streamlining"),
        get_bar_chart_measure(
            "bar_bottlenecks", 20, 68, 520, 434, 1,
            "bottleneck_analysis_summary", "transition_display", "Avg Transition Duration",
            title="Highest Observed Transition Durations",
            subtitle="Mean elapsed duration between sequential milestone activities (mins)",
            category_display_name="Workflow Transition",
            val_display_name="Mean Elapsed Minutes",
            max_margin=50,
            show_data_labels=True,
            bar_color="#DC6B6B",
            show_category_title=False
        ),
        get_table_visual(
            "tbl_improvement_comparison", 555, 68, 705, 434, 2,
            "pathway_improvement_comparison",
            ["metric_name", "baseline_value", "proposed_value", "percentage_difference"],
            display_names={
                "metric_name": "Metric",
                "baseline_value": "Baseline",
                "proposed_value": "Proposed",
                "percentage_difference": "Change %"
            },
            title="Operational Impact Comparison (Baseline vs. Proposed Streamlining)",
            subtitle="Hypothetical process optimization modeling (Simulated To-Be Scenario)",
            formats={
                "baseline_value": "#,##0.0",
                "proposed_value": "#,##0.0",
                "percentage_difference": "+0.0%;-0.0%;0.0%"
            }
        ),
        get_textbox_visual("txt_safety_banner_page3", 20, 512, 1240, 198, 3, p3_safety)
    ]

    sec_config = json.dumps({
        "objects": {
            "background": [
                {
                    "properties": {
                        "color": {"solid": {"color": {"expr": {"Literal": {"Value": "'#F4F7FA'"}}}}},
                        "transparency": {"expr": {"Literal": {"Value": "0D"}}}
                    }
                }
            ],
            "outspace": [
                {
                    "properties": {
                        "color": {"solid": {"color": {"expr": {"Literal": {"Value": "'#F4F7FA'"}}}}}
                    }
                }
            ]
        }
    })

    sections = [
        {
            "id": 0,
            "name": "ReportSection_HospitalOverview",
            "displayName": "Hospital Overview",
            "filters": "[]",
            "ordinal": 0,
            "visualContainers": page1_visuals,
            "config": sec_config,
            "width": 1280.0,
            "height": 720.0
        },
        {
            "id": 1,
            "name": "ReportSection_PatientFlow",
            "displayName": "Patient Flow",
            "filters": "[]",
            "ordinal": 1,
            "visualContainers": page2_visuals,
            "config": sec_config,
            "width": 1280.0,
            "height": 720.0
        },
        {
            "id": 2,
            "name": "ReportSection_ProcessImprovement",
            "displayName": "Transition Analysis & Process Improvement",
            "filters": "[]",
            "ordinal": 2,
            "visualContainers": page3_visuals,
            "config": sec_config,
            "width": 1280.0,
            "height": 720.0
        }
    ]

    report = {
        "id": 0,
        "resourcePackages": [
            {
                "resourcePackage": {
                    "disabled": False,
                    "items": [
                        {
                            "name": "CY26SU05",
                            "path": "BaseThemes/CY26SU05.json",
                            "type": 202
                        }
                    ],
                    "name": "SharedResources",
                    "type": 2
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
                            "verticalAlignment": {"expr": {"Literal": {"Value": "'Top'"}}}
                        }
                    }
                ]
            }
        }),
        "layoutOptimization": 0
    }

    rep_json_str = json.dumps(report, indent=2)
    rep_path = os.path.join(rep_dir, "report.json")
    with open(rep_path, "w", encoding="utf-8") as f:
        f.write(rep_json_str)

    rep_def_path = os.path.join(rep_def, "report.json")
    with open(rep_def_path, "w", encoding="utf-8") as f:
        f.write(rep_json_str)

    print("[SUCCESS] PBIP project generated and synchronized successfully.")

if __name__ == "__main__":
    build()
