"""CareFlow Staging Transformation Module.

Provides the reference Python implementation of the SQL staging transformation
defined in careflow_dbt/models/staging/stg_hospital_events.sql.

Replicates:
1. WHERE clause: filters null/blank Case_IDs, Activity_Names, and Timestamps.
2. QUALIFY deduplication: deduplicates exact (case_id, activity_name, timestamp) records
   with deterministic tie-breaking (ordered by raw_resource ASC, raw_department ASC).
3. Window functions:
   - 1-indexed chronological event_sequence per patient journey.
   - previous_activity via LAG(raw_activity_name).
   - transition_minutes_from_previous via TIMESTAMP_DIFF in minutes.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

__all__ = ["apply_stg_hospital_events_transformation"]


def apply_stg_hospital_events_transformation(
    raw_records: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Simulate the exact SQL transformation logic defined in stg_hospital_events.sql.

    Replicates:
    1. WHERE clause:
       Case_ID IS NOT NULL AND TRIM(Case_ID) != ''
       AND Activity_Name IS NOT NULL AND TRIM(Activity_Name) != ''
       AND Timestamp IS NOT NULL
    2. QUALIFY deduplication:
       QUALIFY ROW_NUMBER() OVER (PARTITION BY raw_case_id, raw_activity_name, raw_timestamp
                                  ORDER BY raw_timestamp ASC) = 1
    3. Window functions:
       ROW_NUMBER() OVER (PARTITION BY raw_case_id ORDER BY raw_timestamp ASC) AS event_sequence
       LAG(raw_activity_name) OVER (PARTITION BY raw_case_id ORDER BY raw_timestamp ASC) AS previous_activity
       TIMESTAMP_DIFF(...) AS transition_minutes_from_previous
    """
    filtered_events = []
    for r in raw_records:
        cid = r.get("Case_ID")
        act = r.get("Activity_Name")
        ts = r.get("Timestamp")

        # Replicate WHERE clause: Case_ID IS NOT NULL AND TRIM(Case_ID) != ''
        if cid is None or not str(cid).strip():
            continue

        # Replicate WHERE clause: Activity_Name IS NOT NULL AND TRIM(Activity_Name) != ''
        if act is None or not str(act).strip():
            continue

        # Replicate WHERE clause: Timestamp IS NOT NULL
        if ts is None or not str(ts).strip():
            continue

        parsed_ts = (
            ts
            if isinstance(ts, datetime)
            else datetime.strptime(str(ts).strip(), "%Y-%m-%d %H:%M:%S")
        )

        filtered_events.append({
            "raw_case_id": str(cid).strip(),
            "raw_activity_name": str(act).strip(),
            "raw_timestamp": parsed_ts,
            "raw_department": str(r.get("Department", "")).strip().upper(),
            "raw_resource": str(r.get("Resource", "")).strip(),
            "raw_data_type": str(r.get("Data_Type", "")).strip(),
        })

    # Replicate QUALIFY physical record deduplication:
    # QUALIFY ROW_NUMBER() OVER (PARTITION BY raw_case_id, raw_activity_name, raw_timestamp
    #                            ORDER BY raw_resource ASC, raw_department ASC) = 1
    grouped_for_dedup: Dict[Tuple[str, str, Any], List[Dict[str, Any]]] = {}
    for r in filtered_events:
        key = (r["raw_case_id"], r["raw_activity_name"], r["raw_timestamp"])
        grouped_for_dedup.setdefault(key, []).append(r)

    deduped_events = []
    for key, group in grouped_for_dedup.items():
        # Order candidates by raw_resource ASC, raw_department ASC and select row 1
        best_row = min(group, key=lambda x: (x["raw_resource"], x["raw_department"]))
        deduped_events.append(best_row)

    # Replicate window functions grouped by raw_case_id with deterministic tie-breaking
    cases: Dict[str, List[Dict[str, Any]]] = {}
    for r in deduped_events:
        cases.setdefault(r["raw_case_id"], []).append(r)

    transformed: List[Dict[str, Any]] = []
    for cid, case_rows in cases.items():
        # ORDER BY raw_timestamp ASC, raw_activity_name ASC, raw_resource ASC
        case_rows.sort(key=lambda x: (x["raw_timestamp"], x["raw_activity_name"], x["raw_resource"]))
        for idx, row in enumerate(case_rows, start=1):
            prev_act = case_rows[idx - 2]["raw_activity_name"] if idx > 1 else None
            prev_ts = case_rows[idx - 2]["raw_timestamp"] if idx > 1 else None
            diff_min = (
                int((row["raw_timestamp"] - prev_ts).total_seconds() / 60)
                if prev_ts
                else None
            )

            transformed.append({
                "case_id": row["raw_case_id"],
                "event_sequence": idx,
                "raw_activity_name": row["raw_activity_name"],
                "activity_name": row["raw_activity_name"].lower().replace("-", "_"),
                "event_timestamp": row["raw_timestamp"],
                "event_date": row["raw_timestamp"].date(),
                "department": row["raw_department"],
                "resource_id": row["raw_resource"],
                "data_provenance": row["raw_data_type"],
                "previous_activity": prev_act,
                "transition_minutes_from_previous": diff_min,
            })

    return transformed
