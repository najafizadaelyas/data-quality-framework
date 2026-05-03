# Data Quality Framework

Automated data observability & lineage monitoring built with **Great Expectations**, **Apache Airflow**, and **OpenLineage**.

## Features

- Automated data quality checks with Great Expectations
- DAG-driven orchestration via Apache Airflow
- Data lineage tracking with OpenLineage + Marquez
- Anomaly detection on key metrics (row counts, nulls, distributions)
- Alerting via Slack / email on quality failures
- HTML + JSON expectation reports stored in GCS/S3

## Project Structure

```
data-quality-framework/
├── dags/                        # Airflow DAGs
│   ├── dq_pipeline_dag.py       # Main DQ orchestration DAG
│   └── lineage_dag.py           # Lineage emission DAG
├── great_expectations/
│   ├── expectations/            # Expectation suites (JSON)
│   ├── checkpoints/             # GE checkpoint configs
│   └── great_expectations.yml   # GE project config
├── src/
│   ├── checks/
│   │   ├── __init__.py
│   │   ├── schema_checks.py     # Schema drift detection
│   │   ├── freshness_checks.py  # Data freshness / SLA
│   │   └── anomaly_checks.py    # Statistical anomaly detection
│   ├── lineage/
│   │   ├── __init__.py
│   │   ├── emitter.py           # OpenLineage event emitter
│   │   └── models.py            # Lineage models
│   ├── observability/
│   │   ├── __init__.py
│   │   ├── metrics_collector.py # Collect DQ metrics
│   │   └── reporter.py          # Generate HTML/JSON reports
│   └── utils/
│       ├── __init__.py
│       ├── db.py                # DB connection helpers
│       ├── config.py            # Config loader
│       └── alerts.py            # Slack/email alerting
├── tests/
│   ├── test_schema_checks.py
│   ├── test_freshness_checks.py
│   ├── test_anomaly_checks.py
│   └── test_lineage_emitter.py
├── docker-compose.yml           # Airflow + Marquez local stack
├── Dockerfile                   # Airflow image with DQ deps
├── requirements.txt
├── .env.example
└── pyproject.toml
```

## Quick Start

### 1. Clone & configure

```bash
git clone https://github.com/<your-org>/data-quality-framework.git
cd data-quality-framework
cp .env.example .env
# Fill in DB credentials, Slack webhook, etc.
```

### 2. Start local stack

```bash
docker-compose up -d
```

- Airflow UI: http://localhost:8080 (admin/admin)
- Marquez UI: http://localhost:3000

### 3. Run a quality check manually

```bash
pip install -r requirements.txt
python -m src.checks.schema_checks --dataset orders --env dev
```

### 4. Trigger the DAG

```bash
airflow dags trigger dq_pipeline
```

## Configuration

Set environment variables in `.env`:

| Variable | Description |
|---|---|
| `DB_HOST` | Source database host |
| `DB_NAME` | Database name |
| `DB_USER` | Database user |
| `DB_PASSWORD` | Database password |
| `SLACK_WEBHOOK_URL` | Slack incoming webhook for alerts |
| `GE_DOCS_BUCKET` | GCS/S3 bucket for GE HTML docs |
| `OPENLINEAGE_URL` | Marquez API URL |
| `OPENLINEAGE_NAMESPACE` | Lineage namespace |

## Great Expectations

Expectation suites live in `great_expectations/expectations/`. Each dataset has its own suite:

- `orders.json` — row count, not-null, value ranges
- `customers.json` — PK uniqueness, email format, country codes
- `products.json` — schema, price ranges, category enum

Run a checkpoint:

```bash
great_expectations checkpoint run orders_checkpoint
```

## Data Lineage

Lineage events are emitted to Marquez via OpenLineage on every DAG run. View the full lineage graph at `http://localhost:3000`.

## Testing

```bash
pytest tests/ -v --cov=src --cov-report=term-missing
```
