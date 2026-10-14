{{ config(
    materialized = 'view',
    description = 'Staging model for hospital event logs: standardizes naming, formats timestamps, calculates event sequencing, and derives transition intervals for process mining.'
) }}

WITH source_events AS (
    SELECT
        TRIM(Case_ID) AS raw_case_id,
        TRIM(Activity_Name) AS raw_activity_name,
        Timestamp AS raw_timestamp,
        TRIM(Department) AS raw_department,
        TRIM(Resource) AS raw_resource,
        TRIM(Data_Type) AS raw_data_type
    FROM {{ source('raw_hospital_data', 'hospital_events_raw') }}
    WHERE
        Case_ID IS NOT NULL
        AND TRIM(Case_ID) != ''
        AND Activity_Name IS NOT NULL
        AND TRIM(Activity_Name) != ''
        AND Timestamp IS NOT NULL
),

cleaned_and_normalized AS (
    SELECT
        raw_case_id AS case_id,
        raw_activity_name,
        -- Standardized lower/snake-case activity name for uniform querying
        LOWER(REPLACE(raw_activity_name, '-', '_')) AS activity_name,
        raw_timestamp AS event_timestamp,
        DATE(raw_timestamp) AS event_date,
        UPPER(raw_department) AS department,
        raw_resource AS resource_id,
        raw_data_type AS data_provenance,

        -- Event sequence within patient journey (1-indexed, chronological)
        -- Deterministic secondary ordering: When events within a case have identical timestamps,
        -- ordering by raw_activity_name ASC and raw_resource ASC provides query determinism across runs.
        -- Note: This ensures SQL execution reproducibility, but does not assert true clinical
        -- chronological precedence between concurrent events without sub-second logging or event IDs.
        -- If all ordering columns tie, remaining ambiguity represents physically identical events.
        ROW_NUMBER() OVER (
            PARTITION BY raw_case_id
            ORDER BY raw_timestamp ASC, raw_activity_name ASC, raw_resource ASC
        ) AS event_sequence,

        -- Previous activity in journey to model process transitions
        LAG(raw_activity_name) OVER (
            PARTITION BY raw_case_id
            ORDER BY raw_timestamp ASC, raw_activity_name ASC, raw_resource ASC
        ) AS previous_activity,

        -- Transition duration (minutes elapsed since preceding activity)
        TIMESTAMP_DIFF(
            raw_timestamp,
            LAG(raw_timestamp) OVER (
                PARTITION BY raw_case_id
                ORDER BY raw_timestamp ASC, raw_activity_name ASC, raw_resource ASC
            ),
            MINUTE
        ) AS transition_minutes_from_previous

    FROM source_events
    -- Downstream warehouse safeguard: Deduplicate records already present in the raw BigQuery table
    -- (e.g. from repeated ingestion batches or overlapping load jobs).
    -- Uniqueness key contract: The project intentionally defines (raw_case_id, raw_activity_name, raw_timestamp)
    -- as the event uniqueness key. Legitimate clinical re-triages and repeat consults have distinct timestamps
    -- and are fully preserved.
    -- Limitation: If two legitimate separate events occur at the exact same timestamp with the same activity name,
    -- this contract collapses them into a single staged event.
    -- Deterministic row selection: If duplicate records differ in resource or department metadata,
    -- order by raw_resource ASC, raw_department ASC to break ties deterministically.
    -- If all columns tie, duplicate rows are physically identical and dropping one is lossless.
    QUALIFY ROW_NUMBER() OVER (
        PARTITION BY raw_case_id, raw_activity_name, raw_timestamp
        ORDER BY raw_resource ASC, raw_department ASC
    ) = 1
)

SELECT
    case_id,
    event_sequence,
    raw_activity_name,
    activity_name,
    event_timestamp,
    event_date,
    department,
    resource_id,
    data_provenance,
    previous_activity,
    transition_minutes_from_previous
FROM cleaned_and_normalized
