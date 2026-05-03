"""Collect data quality metrics and expose them via Prometheus."""
from __future__ import annotations

import logging

from prometheus_client import CollectorRegistry, Gauge, push_to_gateway

logger = logging.getLogger(__name__)


class DQMetricsCollector:
    def __init__(self, job: str = "data_quality", pushgateway: str = "localhost:9091"):
        self.job = job
        self.pushgateway = pushgateway
        self.registry = CollectorRegistry()

        self.row_count = Gauge("dq_row_count", "Row count for a dataset", ["table"], registry=self.registry)
        self.null_rate = Gauge("dq_null_rate", "Null rate for a column", ["table", "column"], registry=self.registry)
        self.anomaly_rate = Gauge("dq_anomaly_rate", "Anomaly rate for a column", ["table", "column"], registry=self.registry)
        self.freshness_hours = Gauge("dq_freshness_hours", "Hours since latest row", ["table"], registry=self.registry)
        self.ge_expectations_pass = Gauge("dq_ge_pass_pct", "GE pass percentage", ["suite"], registry=self.registry)

    def record_row_count(self, table: str, count: int) -> None:
        self.row_count.labels(table=table).set(count)

    def record_null_rate(self, table: str, column: str, rate: float) -> None:
        self.null_rate.labels(table=table, column=column).set(rate)

    def record_anomaly_rate(self, table: str, column: str, rate: float) -> None:
        self.anomaly_rate.labels(table=table, column=column).set(rate)

    def record_freshness(self, table: str, age_hours: float) -> None:
        self.freshness_hours.labels(table=table).set(age_hours)

    def record_ge_result(self, suite: str, pass_pct: float) -> None:
        self.ge_expectations_pass.labels(suite=suite).set(pass_pct)

    def push(self) -> None:
        try:
            push_to_gateway(self.pushgateway, job=self.job, registry=self.registry)
            logger.info("Metrics pushed to Prometheus Pushgateway at %s", self.pushgateway)
        except Exception as exc:
            logger.warning("Failed to push metrics: %s", exc)
