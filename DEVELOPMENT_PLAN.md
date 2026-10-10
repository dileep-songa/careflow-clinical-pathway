# CareFlow: Clinical Pathway Process Mining

## Project Overview
This project analyzes hospital patient event logs to identify bottlenecks, inefficiencies, and opportunities to improve clinical operations.

## Objective
- Collect and clean hospital event logs
- Perform process mining to discover patient journey flows
- Identify bottlenecks and waiting time issues
- Create dashboards and visualizations
- Generate actionable insights for hospital administrators

## Key Technologies
- **Data Processing:** Python, Pandas, SQL
- **Process Mining:** PM4Py
- **Data Warehouse:** Google BigQuery
- **Visualization:** PowerBI, Looker, Matplotlib
- **Version Control:** Git & GitHub

## Project Structure
```text
careflow-clinical-pathway/
├── data/
│   ├── raw/
│   └── cleaned/
├── notebooks/
├── src/
├── reports/
├── README.md
├── .gitignore
├── requirements.txt
├── PROJECT_UNDERSTANDING.md
├── DATA_SCHEMA.md
├── DAILY_LOG.md
└── DEVELOPMENT_PLAN.md
```

## Timeline
- Week 1: EHR data setup and exploration
- Week 2: Data cleaning and normalization
- Week 3: Process mining and bottleneck analysis
- Week 4: Dashboard and final report

## Getting Started
```bash
git clone https://github.com/YOUR-USERNAME/careflow-clinical-pathway.git
cd careflow-clinical-pathway
python -m venv venv
source venv/bin/activate  # Mac/Linux
# or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

## Status
🟢 Project initialized
