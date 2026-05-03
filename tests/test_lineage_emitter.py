"""Tests for OpenLineage emitter."""
import pytest
import responses as resp_mock
from unittest.mock import patch

from src.lineage.emitter import LineageEmitter
from src.lineage.models import EventType


@resp_mock.activate
def test_emit_start_posts_to_marquez():
    marquez_url = "http://localhost:5000"
    resp_mock.add(resp_mock.POST, f"{marquez_url}/api/v1/lineage", status=200)

    emitter = LineageEmitter(namespace="test", marquez_url=marquez_url)
    event = emitter.start("my_job", inputs=["raw.orders"], outputs=["staging.orders"])

    assert event.eventType == EventType.START
    assert event.job.name == "my_job"
    assert len(resp_mock.calls) == 1


@resp_mock.activate
def test_emit_complete():
    marquez_url = "http://localhost:5000"
    resp_mock.add(resp_mock.POST, f"{marquez_url}/api/v1/lineage", status=200)

    emitter = LineageEmitter(namespace="test", marquez_url=marquez_url)
    event = emitter.complete("my_job")

    assert event.eventType == EventType.COMPLETE


@resp_mock.activate
def test_emit_fail():
    marquez_url = "http://localhost:5000"
    resp_mock.add(resp_mock.POST, f"{marquez_url}/api/v1/lineage", status=200)

    emitter = LineageEmitter(namespace="test", marquez_url=marquez_url)
    event = emitter.fail("my_job")

    assert event.eventType == EventType.FAIL


@resp_mock.activate
def test_emit_does_not_raise_on_server_error():
    """Emitter should log warning but not raise when Marquez is unavailable."""
    marquez_url = "http://localhost:5000"
    resp_mock.add(resp_mock.POST, f"{marquez_url}/api/v1/lineage", status=500)

    emitter = LineageEmitter(namespace="test", marquez_url=marquez_url)
    # Should not raise
    event = emitter.start("my_job")
    assert event.eventType == EventType.START


def test_lineage_event_has_run_id():
    emitter = LineageEmitter(namespace="test", marquez_url="http://localhost:5000")
    with patch.object(emitter, "_post"):
        event = emitter.start("job_x", run_id="fixed-run-id")
    assert event.run.runId == "fixed-run-id"
