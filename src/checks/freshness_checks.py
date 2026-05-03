"""Data freshness / SLA checks — ensure tables are updated within expected windows."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import text

from src.utils.db import get_connection
from src.utils.alerts import alert

logger = logging.getLogger(__name__)


def get_max_timestamp(
    table: str,
    timestamp_col: str,
    schema: str = "public",
    db_name: str | None = None,
) -> datetime | None:
    """Return the maximum value of *timestamp_col* in *table*."""
    sql = text(f"SELECT MAX({timestamp_col}) FROM {schema}.{table}")
    with get_connection(db_name) as conn:
        result = conn.execute(sql).scalar()
    if result is None:
        return None
    if result.tzinfo is None:
        return result.replace(tzinfo=timezone.utc)
    return result


def check_freshness(
    table: str,
    timestamp_col: str,
    max_age_hours: float = 24.0,
    schema: str = "public",
    db_name: str | None = None,
    send_alerts: bool = True,
) -> dict:
    """
    Raise an alert if the latest row in *table* is older than *max_age_hours*.

    Returns a result dict with keys: table, latest_ts, age_hours, passed.
    """
    latest = get_max_timestamp(table, timestamp_col, schema, db_name)
    now = datetime.now(tz=timezone.utc)

    if latest is None:
        msg = f"Freshness check FAILED for {table}.{timestamp_col} — table is empty."
        logger.error(msg)
        if send_alerts:
            alert(msg, subject=f"Freshness Failure — {table}", level="error")
        return {"table": table, "latest_ts": None, "age_hours": None, "passed": False}

    age_hours = (now - latest).total_seconds() / 3600
    passed = age_hours <= max_age_hours

    result = {"table": table, "latest_ts": latest.isoformat(), "age_hours": round(age_hours, 2), "passed": passed}

    if not passed:
        msg = (
            f"Freshness SLA breached for `{table}` — "
            f"latest row is {age_hours:.1f}h old (SLA: {max_age_hours}h)."
        )
        logger.warning(msg)
        if send_alerts:
            alert(msg, subject=f"Freshness SLA — {table}", level="warning")
    else:
        logger.info("Freshness OK for %s: %.1fh old (SLA: %.1fh)", table, age_hours, max_age_hours)

    return result
