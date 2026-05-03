"""Tests for schema drift detection."""
import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.checks.schema_checks import (
    SchemaDriftResult,
    check_schema_drift,
    load_baseline,
    save_baseline,
)


@pytest.fixture
def tmp_baselines(tmp_path, monkeypatch):
    monkeypatch.setattr("src.checks.schema_checks.BASELINES_DIR", tmp_path)
    return tmp_path


def test_no_drift_returns_clean_result(tmp_baselines):
    schema = {"id": "integer", "name": "text", "created_at": "timestamp with time zone"}
    save_baseline("orders", schema)

    with patch("src.checks.schema_checks.get_live_schema", return_value=schema):
        result = check_schema_drift("orders", send_alerts=False)

    assert not result.has_drift


def test_detects_added_column(tmp_baselines):
    baseline = {"id": "integer", "name": "text"}
    live = {"id": "integer", "name": "text", "email": "text"}
    save_baseline("customers", baseline)

    with patch("src.checks.schema_checks.get_live_schema", return_value=live):
        result = check_schema_drift("customers", send_alerts=False)

    assert result.has_drift
    assert "email" in result.added


def test_detects_removed_column(tmp_baselines):
    baseline = {"id": "integer", "name": "text", "legacy_col": "text"}
    live = {"id": "integer", "name": "text"}
    save_baseline("orders", baseline)

    with patch("src.checks.schema_checks.get_live_schema", return_value=live):
        result = check_schema_drift("orders", send_alerts=False)

    assert result.has_drift
    assert "legacy_col" in result.removed


def test_detects_type_change(tmp_baselines):
    baseline = {"price": "integer"}
    live = {"price": "numeric"}
    save_baseline("products", baseline)

    with patch("src.checks.schema_checks.get_live_schema", return_value=live):
        result = check_schema_drift("products", send_alerts=False)

    assert result.has_drift
    assert result.changed[0]["column"] == "price"


def test_saves_baseline_when_missing(tmp_baselines):
    live = {"id": "integer"}

    with patch("src.checks.schema_checks.get_live_schema", return_value=live):
        result = check_schema_drift("new_table", send_alerts=False)

    assert not result.has_drift
    loaded = load_baseline("new_table")
    assert loaded == live


def test_summary_message():
    result = SchemaDriftResult("orders", added=["x"], removed=[], changed=[])
    assert "Added columns" in result.summary()
    assert "orders" in result.summary()
