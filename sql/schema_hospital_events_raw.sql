-- ==============================================================================
-- CareFlow: Clinical Pathway Process Mining
-- Target Warehouse: Google Cloud BigQuery
-- Layer: Raw Event Log Ingestion (Bronze / Source Layer)
-- Target Table: {project_id}.{dataset_id}.hospital_events_raw
-- ==============================================================================
-- Description:
-- DDL definition for raw simulated hospital event logs loaded from CSV exports.
-- Preserves the exact input contract produced by src/data_generator.py:
-- (Case_ID, Activity_Name, Timestamp, Department, Resource, Data_Type).
--
-- Optimization:
-- - Partitioned by DATE(Timestamp) for efficient date-range filtering.
-- - Clustered by Case_ID, Activity_Name for fast process-mining trace assembly.
-- ==============================================================================

CREATE TABLE IF NOT EXISTS `{project_id}.{dataset_id}.hospital_events_raw` (
    Case_ID STRING NOT NULL OPTIONS(description = "Unique patient encounter identifier (e.g., CASE_0001)"),
    Activity_Name STRING NOT NULL OPTIONS(description = "Clinical activity name in the patient pathway"),
    Timestamp TIMESTAMP NOT NULL OPTIONS(description = "Exact timestamp of event occurrence (UTC)"),
    Department STRING NOT NULL OPTIONS(description = "Hospital department or clinical service unit (e.g., ER, LAB)"),
    Resource STRING NOT NULL OPTIONS(description = "De-identified clinician or administrative staff identifier"),
    Data_Type STRING NOT NULL OPTIONS(description = "Data provenance indicator (SIMULATED or PROD)")
)
PARTITION BY DATE(Timestamp)
CLUSTER BY Case_ID, Activity_Name
OPTIONS(
    description = "Raw ingested simulated clinical pathway event logs for process mining."
);

