"""Tests for data freshness checks."""
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest

from src.checks.freshness_checks import check_freshness


def _make_ts(hours_ago: float) -> datetime:
    return datetime.now(tz=timezone.utc) - timedelta(hours=hours_ago)


def test_passes_when_data_is_fresh():
    with patch("src.checks.freshness_checks.get_max_timestamp", return_value=_make_ts(2)):
        result = check_freshness("orders", "created_at", max_age_hours=24, send_alerts=False)
    assert result["passed"]
    assert result["age_hours"] < 24


def test_fails_when_data_is_stale():
    with patch("src.checks.freshness_checks.get_max_timestamp", return_value=_make_ts(30)):
        result = check_freshness("orders", "created_at", max_age_hours=24, send_alerts=False)
    assert not result["passed"]
    assert result["age_hours"] > 24


def test_fails_when_table_is_empty():
    with patch("src.checks.freshness_checks.get_max_timestamp", return_value=None):
        result = check_freshness("orders", "created_at", send_alerts=False)
    assert not result["passed"]
    assert result["latest_ts"] is None


def test_result_contains_expected_keys():
    with patch("src.checks.freshness_checks.get_max_timestamp", return_value=_make_ts(1)):
        result = check_freshness("orders", "created_at", max_age_hours=24, send_alerts=False)
    assert {"table", "latest_ts", "age_hours", "passed"}.issubset(result.keys())
