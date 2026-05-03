"""Standalone lineage emission DAG — demonstrates START/COMPLETE lifecycle."""
from __future__ import annotations

from datetime import timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago

DEFAULT_ARGS = {
    "owner": "data-engineering",
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
}


def emit_start(**context):
    from src.lineage.emitter import LineageEmitter

    run_id = context["run_id"]
    emitter = LineageEmitter()
    emitter.start(
        job_name="daily_ingestion",
        inputs=["raw.orders_landing"],
        outputs=["staging.orders"],
        run_id=run_id,
    )


def emit_complete(**context):
    from src.lineage.emitter import LineageEmitter

    run_id = context["run_id"]
    emitter = LineageEmitter()
    emitter.complete(
        job_name="daily_ingestion",
        inputs=["raw.orders_landing"],
        outputs=["staging.orders"],
        run_id=run_id,
    )


with DAG(
    dag_id="lineage_demo",
    default_args=DEFAULT_ARGS,
    description="Demonstrates OpenLineage START/COMPLETE events",
    schedule_interval="@daily",
    start_date=days_ago(1),
    catchup=False,
    tags=["lineage"],
) as dag:
    start_task = PythonOperator(task_id="emit_start", python_callable=emit_start)
    complete_task = PythonOperator(task_id="emit_complete", python_callable=emit_complete)
    start_task >> complete_task
