"""Main Data Quality orchestration DAG.

Runs schema drift, freshness, anomaly checks and a Great Expectations
checkpoint for each configured dataset, then emits lineage events.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago

logger = logging.getLogger(__name__)

DEFAULT_ARGS = {
    "owner": "data-engineering",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
    "email_on_failure": True,
}

# Datasets to check: (table, timestamp_col, numeric_col_for_anomaly)
DATASETS = [
    ("orders", "created_at", "amount"),
    ("customers", "updated_at", None),
    ("products", "updated_at", "price"),
]


def run_schema_check(table: str, **_):
    from src.checks.schema_checks import check_schema_drift

    result = check_schema_drift(table)
    if result.has_drift:
        raise ValueError(f"Schema drift detected for {table}: {result.summary()}")
    logger.info("Schema OK: %s", table)


def run_freshness_check(table: str, timestamp_col: str, **_):
    from src.checks.freshness_checks import check_freshness

    result = check_freshness(table, timestamp_col, max_age_hours=25)
    if not result["passed"]:
        raise ValueError(f"Freshness SLA breached for {table}")


def run_anomaly_check(table: str, column: str, **_):
    from src.checks.anomaly_checks import check_anomalies

    result = check_anomalies(table, column)
    if not result["passed"]:
        logger.warning("Anomalies found in %s.%s — see alert", table, column)


def run_ge_checkpoint(table: str, **_):
    import great_expectations as gx

    context = gx.get_context(context_root_dir="/opt/airflow/great_expectations")
    result = context.run_checkpoint(checkpoint_name=f"{table}_checkpoint")
    if not result["success"]:
        raise ValueError(f"GE checkpoint failed for {table}")


def emit_lineage(tables: list[str], **_):
    from src.lineage.emitter import LineageEmitter

    emitter = LineageEmitter()
    emitter.complete(
        job_name="dq_pipeline",
        inputs=tables,
        outputs=["dq_results"],
    )


with DAG(
    dag_id="dq_pipeline",
    default_args=DEFAULT_ARGS,
    description="Automated data quality checks + lineage",
    schedule_interval="0 6 * * *",
    start_date=days_ago(1),
    catchup=False,
    tags=["data-quality", "great-expectations", "lineage"],
) as dag:

    all_tables = [ds[0] for ds in DATASETS]

    prev_tasks = []
    for table, ts_col, num_col in DATASETS:
        schema_task = PythonOperator(
            task_id=f"schema_check_{table}",
            python_callable=run_schema_check,
            op_kwargs={"table": table},
        )

        freshness_task = PythonOperator(
            task_id=f"freshness_check_{table}",
            python_callable=run_freshness_check,
            op_kwargs={"table": table, "timestamp_col": ts_col},
        )

        schema_task >> freshness_task

        if num_col:
            anomaly_task = PythonOperator(
                task_id=f"anomaly_check_{table}",
                python_callable=run_anomaly_check,
                op_kwargs={"table": table, "column": num_col},
            )
            freshness_task >> anomaly_task
            prev_tasks.append(anomaly_task)
        else:
            prev_tasks.append(freshness_task)

        ge_task = PythonOperator(
            task_id=f"ge_checkpoint_{table}",
            python_callable=run_ge_checkpoint,
            op_kwargs={"table": table},
        )
        (prev_tasks[-1]) >> ge_task
        prev_tasks[-1] = ge_task

    lineage_task = PythonOperator(
        task_id="emit_lineage",
        python_callable=emit_lineage,
        op_kwargs={"tables": all_tables},
    )

    for t in prev_tasks:
        t >> lineage_task
