# CareFlow dbt Project: Initial Cleaning & Normalization

This dbt project implements the **initial data cleaning and normalization phase** for CareFlow: Clinical Pathway Process Mining on Google BigQuery.

---

## 1. Architecture & Pipeline

```text
Google BigQuery Raw Layer
  └── `hospital_events_raw` (Dataset: `careflow_raw`, ingested via src/bq_loader.py)
        │
        ▼ (dbt Source: raw_hospital_data.hospital_events_raw)
  dbt Staging View Layer
  └── `stg_hospital_events` (Dataset: `careflow_staging`)
        │
        ▼
  Downstream Process Mining (PM4Py) & BI Dashboards (Power BI)
```

> **Note on BigQuery Dataset Naming:** The dbt staging models inherit the target dataset directly from `BIGQUERY_DATASET_STAGING` (`careflow_staging`). Redundant custom schema suffixes are omitted to ensure models materialize directly in `careflow_staging` rather than `careflow_staging_staging`.

---

## 2. Staging Model Transformations (`stg_hospital_events`)

The initial cleaning model applies strict, non-destructive data engineering rules:
1. **Preserves Identity & Activities:** Retains `case_id`, original `raw_activity_name` (`Registration`, `Triage`, etc.), and creates standardized `activity_name` (`registration`, `triage`, etc.).
2. **Exposes Consistent Timestamps:** Extracts UTC `event_timestamp` and calendar `event_date`.
3. **Sequences Events:** Assigns 1-indexed `event_sequence` (`ROW_NUMBER() OVER (PARTITION BY Case_ID ORDER BY Timestamp)`) to enable trace reconstruction in PM4Py.
4. **Calculates Inter-Activity Intervals:** Computes `previous_activity` and `transition_minutes_from_previous` using window functions without inventing events.
5. **No Silent Clinical Deduplication:** Legitimate clinical re-triages and repeat consultations have distinct timestamps and are **100% preserved**. Only accidental identical duplicate records (identical case, activity, and timestamp) are filtered.

---

## 3. Prerequisites & Environment Setup

### Install dbt with BigQuery Adapter
```bash
pip install dbt-core dbt-bigquery
```

### Configure BigQuery Profile
1. Copy `profiles.yml.example` to `~/.dbt/profiles.yml` (or define `DBT_PROFILES_DIR`):
   ```bash
   cp careflow_dbt/profiles.yml.example ~/.dbt/profiles.yml
   ```
2. Authenticate with Google Cloud using Application Default Credentials (ADC):
   ```bash
   gcloud auth application-default login
   ```
3. Set your project environment variables in `.env`:
   ```bash
   export GCP_PROJECT_ID="your-project-id"
   export GCP_REGION="us-central1"
   export BIGQUERY_DATASET="careflow_raw"
   export BIGQUERY_DATASET_STAGING="careflow_staging"
   ```

---

## 4. Execution Commands

From the `careflow_dbt/` directory:

```bash
# 1. Test database connection
dbt debug

# 2. Compile SQL models and verify Jinja syntax
dbt compile

# 3. Build staging views in BigQuery
dbt run

# 4. Execute data quality tests (not_null, accepted_values, etc.)
dbt test
```

---

## 5. Offline Verification

When Google Cloud credentials or BigQuery access are not yet configured:
- Run project validation via the CareFlow test suite:
  ```bash
  pytest -v tests/test_dbt_setup.py
  ```
- This validates YAML schema compliance, Jinja source resolution, column mapping consistency, and verifies that the SQL logic preserves all 500 cases and 3,140 events from the local canonical CSV.
