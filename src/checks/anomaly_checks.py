"""Statistical anomaly detection on numeric columns using Z-score & IQR methods."""
from __future__ import annotations

import logging
from typing import Literal

import pandas as pd

from src.utils.db import get_connection
from src.utils.alerts import alert

logger = logging.getLogger(__name__)


def fetch_series(
    table: str,
    column: str,
    schema: str = "public",
    db_name: str | None = None,
    limit: int = 10_000,
) -> pd.Series:
    from src.utils.db import get_engine
    sql = f"SELECT {column} FROM {schema}.{table} WHERE {column} IS NOT NULL LIMIT {int(limit)}"
    engine = get_engine(db_name)
    with engine.connect() as conn:
        df = pd.read_sql(sql, conn.connection)
    return df[column].astype(float)


def zscore_anomalies(series: pd.Series, threshold: float = 3.0) -> pd.Series:
    """Return a boolean mask of rows with |Z-score| > threshold."""
    mean, std = series.mean(), series.std()
    if std == 0:
        return pd.Series([False] * len(series), index=series.index)
    return ((series - mean) / std).abs() > threshold


def iqr_anomalies(series: pd.Series, factor: float = 1.5) -> pd.Series:
    """Return a boolean mask of rows outside [Q1 - factor*IQR, Q3 + factor*IQR]."""
    q1, q3 = series.quantile(0.25), series.quantile(0.75)
    iqr = q3 - q1
    lower, upper = q1 - factor * iqr, q3 + factor * iqr
    return (series < lower) | (series > upper)


def check_anomalies(
    table: str,
    column: str,
    method: Literal["zscore", "iqr"] = "zscore",
    threshold: float = 3.0,
    schema: str = "public",
    db_name: str | None = None,
    send_alerts: bool = True,
) -> dict:
    """
    Detect anomalies in *table.column* and optionally alert.

    Returns a result dict with keys: table, column, method, anomaly_count, total, passed.
    """
    series = fetch_series(table, column, schema, db_name)
    total = len(series)

    if total == 0:
        return {"table": table, "column": column, "method": method, "anomaly_count": 0, "total": 0, "passed": True}

    mask = zscore_anomalies(series, threshold) if method == "zscore" else iqr_anomalies(series, threshold)
    anomaly_count = int(mask.sum())
    anomaly_pct = anomaly_count / total * 100
    passed = anomaly_pct < 1.0  # alert if >1% anomalies

    result = {
        "table": table,
        "column": column,
        "method": method,
        "anomaly_count": anomaly_count,
        "total": total,
        "anomaly_pct": round(anomaly_pct, 2),
        "passed": passed,
    }

    if not passed:
        msg = (
            f"Anomaly detected in `{table}.{column}` [{method}]: "
            f"{anomaly_count}/{total} rows ({anomaly_pct:.1f}%) flagged."
        )
        logger.warning(msg)
        if send_alerts:
            alert(msg, subject=f"Anomaly — {table}.{column}", level="warning")
    else:
        logger.info("Anomaly check OK for %s.%s: %d/%d flagged", table, column, anomaly_count, total)

    return result
