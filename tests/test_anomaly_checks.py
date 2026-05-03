"""Tests for anomaly detection."""
import pandas as pd
import pytest
from unittest.mock import patch

from src.checks.anomaly_checks import check_anomalies, iqr_anomalies, zscore_anomalies


def test_zscore_flags_outliers():
    s = pd.Series([10.0] * 100 + [9999.0])
    mask = zscore_anomalies(s, threshold=3.0)
    assert mask.iloc[-1]
    assert mask.sum() == 1


def test_zscore_no_outliers():
    s = pd.Series(range(100), dtype=float)
    mask = zscore_anomalies(s, threshold=3.0)
    assert mask.sum() == 0


def test_iqr_flags_outliers():
    s = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0, 9999.0])
    mask = iqr_anomalies(s, factor=1.5)
    assert mask.iloc[-1]


def test_check_anomalies_passes_when_clean():
    clean = pd.Series([float(i) for i in range(200)])
    with patch("src.checks.anomaly_checks.fetch_series", return_value=clean):
        result = check_anomalies("orders", "amount", send_alerts=False)
    assert result["passed"]


def test_check_anomalies_fails_with_many_outliers():
    # 5% of values are extreme outliers → should fail the >1% threshold
    normal = pd.Series([1.0] * 95 + [1_000_000.0] * 5)
    with patch("src.checks.anomaly_checks.fetch_series", return_value=normal):
        result = check_anomalies("orders", "amount", send_alerts=False)
    assert not result["passed"]


def test_empty_series_passes():
    with patch("src.checks.anomaly_checks.fetch_series", return_value=pd.Series([], dtype=float)):
        result = check_anomalies("orders", "amount", send_alerts=False)
    assert result["passed"]
    assert result["total"] == 0
