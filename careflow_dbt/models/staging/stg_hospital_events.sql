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
        ROW_NUMBER() OVER (
            PARTITION BY raw_case_id
            ORDER BY raw_timestamp ASC
        ) AS event_sequence,

        -- Previous activity in journey to model process transitions
        LAG(raw_activity_name) OVER (
            PARTITION BY raw_case_id
            ORDER BY raw_timestamp ASC
        ) AS previous_activity,

        -- Transition duration (minutes elapsed since preceding activity)
        TIMESTAMP_DIFF(
            raw_timestamp,
            LAG(raw_timestamp) OVER (
                PARTITION BY raw_case_id
                ORDER BY raw_timestamp ASC
            ),
            MINUTE
        ) AS transition_minutes_from_previous

    FROM source_events
    -- Guard against duplicate physical rows with identical case, activity, and timestamp.
    -- Note: Legitimate clinical re-triages have distinct timestamps and are fully preserved.
    QUALIFY ROW_NUMBER() OVER (
        PARTITION BY raw_case_id, raw_activity_name, raw_timestamp
        ORDER BY raw_timestamp ASC
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
