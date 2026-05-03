"""OpenLineage event emitter — posts lineage events to Marquez."""
from __future__ import annotations

import logging

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from src.lineage.models import Dataset, EventType, Job, LineageEvent, Run
from src.utils.config import config

logger = logging.getLogger(__name__)


class LineageEmitter:
    def __init__(self, namespace: str | None = None, marquez_url: str | None = None):
        self.namespace = namespace or config.openlineage_namespace
        self.marquez_url = (marquez_url or config.openlineage_url).rstrip("/")

    def _endpoint(self) -> str:
        return f"{self.marquez_url}/api/v1/lineage"

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
    def _post(self, event: LineageEvent) -> None:
        resp = requests.post(
            self._endpoint(),
            json=event.model_dump(by_alias=True),
            headers={"Content-Type": "application/json"},
            timeout=10,
        )
        resp.raise_for_status()
        logger.debug("Lineage event posted: %s %s", event.eventType, event.job.name)

    def emit(
        self,
        job_name: str,
        event_type: EventType,
        inputs: list[str] | None = None,
        outputs: list[str] | None = None,
        run_id: str | None = None,
        facets: dict | None = None,
    ) -> LineageEvent:
        run = Run(runId=run_id) if run_id else Run()
        job = Job(namespace=self.namespace, name=job_name, facets=facets or {})
        input_datasets = [Dataset(namespace=self.namespace, name=n) for n in (inputs or [])]
        output_datasets = [Dataset(namespace=self.namespace, name=n) for n in (outputs or [])]

        event = LineageEvent(
            eventType=event_type,
            run=run,
            job=job,
            inputs=input_datasets,
            outputs=output_datasets,
        )
        try:
            self._post(event)
        except Exception as exc:
            logger.warning("Failed to emit lineage event for %s: %s", job_name, exc)
        return event

    def start(self, job_name: str, inputs: list[str] | None = None, outputs: list[str] | None = None, run_id: str | None = None) -> LineageEvent:
        return self.emit(job_name, EventType.START, inputs, outputs, run_id)

    def complete(self, job_name: str, inputs: list[str] | None = None, outputs: list[str] | None = None, run_id: str | None = None) -> LineageEvent:
        return self.emit(job_name, EventType.COMPLETE, inputs, outputs, run_id)

    def fail(self, job_name: str, inputs: list[str] | None = None, outputs: list[str] | None = None, run_id: str | None = None) -> LineageEvent:
        return self.emit(job_name, EventType.FAIL, inputs, outputs, run_id)


emitter = LineageEmitter()
